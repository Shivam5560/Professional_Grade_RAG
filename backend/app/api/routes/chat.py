"""
Chat endpoints for querying the RAG system.
"""

import uuid
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse, ChatHistory
from app.core.rag_engine import get_rag_engine
from app.core.context_manager import get_context_manager
from app.utils.logger import get_logger
from app.db.database import get_db
from app.db.models import ChatSession, ChatMessage
import json
from app.utils.diagram_utils import extract_drawio_xml, is_diagram_request
from app.models.prompts import DRAWIO_XML_PROMPT
from app.config import settings
import httpx

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


async def _determine_default_mode() -> str:
    """Return fast by default; fall back to think if any core service is unhealthy."""
    unhealthy = False

    # 1. Embedding service health
    if settings.embedding_provider == "cohere":
        try:
            from app.services.cohere_service import get_cohere_service
            if not await get_cohere_service().check_health():
                unhealthy = True
        except Exception:
            unhealthy = True
    elif settings.embedding_provider == "remote" or settings.use_remote_embedding_service:
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(f"{settings.remote_embedding_service_url}/health")
                if response.status_code != 200:
                    unhealthy = True
        except Exception:
            unhealthy = True
    else:
        try:
            from app.services.ollama_service import get_ollama_service
            if not await get_ollama_service().check_health():
                unhealthy = True
        except Exception:
            unhealthy = True

    # 2. Reranker health (remote shares embedding health)
    if settings.reranker_provider == "cohere":
        try:
            from app.services.cohere_service import get_cohere_service
            if not await get_cohere_service().check_health():
                unhealthy = True
        except Exception:
            unhealthy = True
    elif settings.reranker_provider == "remote" or settings.use_remote_embedding_service:
        if unhealthy:
            unhealthy = True

    # 3. LLM health (cached)
    try:
        from app.services.groq_service import get_groq_service
        if not await get_groq_service().check_health():
            unhealthy = True
    except Exception:
        unhealthy = True

    # 4. Database/vector store health
    try:
        from app.services.vector_store import get_vector_store_service
        if not get_vector_store_service().check_health():
            unhealthy = True
    except Exception:
        unhealthy = True

    # 5. BM25 index health
    try:
        from app.services.bm25_service import get_bm25_service
        bm25_stats = get_bm25_service().get_stats()
        if not bm25_stats.get("index_available", False):
            unhealthy = True
    except Exception:
        unhealthy = True

    return "think" if unhealthy else "fast"


def _serialize_sources(sources):
    if not sources:
        return []
    serialized = []
    for source in sources:
        if hasattr(source, "dict"):
            serialized.append(source.dict())
        else:
            serialized.append(source)
    return serialized


def _extract_confidence_fields(confidence_score):
    if isinstance(confidence_score, dict):
        return confidence_score.get("score"), confidence_score.get("level")
    if isinstance(confidence_score, (int, float)):
        return float(confidence_score), None
    return None, None


def _sse_event(event: str, data) -> str:
    payload = json.dumps(data, default=lambda obj: obj.dict() if hasattr(obj, "dict") else str(obj))
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/query", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def query(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Query the RAG system with a question.
    Supports two modes:
    - fast (default): Hybrid BM25 + Vector retrieval with reranking
    - think: PageIndex reasoning-based tree search
    
    Args:
        request: ChatRequest with query, session_id, and mode
        
    Returns:
        ChatResponse with answer, confidence, sources, and optional reasoning
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        mode = request.mode or await _determine_default_mode()
        
        # Save session if it doesn't exist
        db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not db_session:
            title = request.query[:50] + "..." if len(request.query) > 50 else request.query
            
            db_session = ChatSession(
                id=session_id,
                user_id=request.user_id,
                title=title
            )
            db.add(db_session)
            db.commit()
            logger.log_operation(
                "💬 New chat session created",
                session_id=session_id[:8] + "...",
                user_id=request.user_id,
                title=title
            )
        
        # Save user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.query,
            context_files=[cf.dict() for cf in request.context_files] if request.context_files else None,
        )
        db.add(user_msg)
        db.commit()
        
        # Log query with mode info
        context_info = {"mode": mode}
        if request.context_document_ids:
            context_info['context_docs'] = len(request.context_document_ids)
        
        logger.log_query(
            query=request.query,
            session_id=session_id[:8] + "...",
            user_id=request.user_id,
            **context_info
        )
        
        # Route to the appropriate engine based on mode
        if mode == "think":
            from app.core.pageindex_rag_engine import get_pageindex_rag_engine
            think_engine = get_pageindex_rag_engine()
            result = await think_engine.query(
                query=request.query,
                db=db,
                session_id=session_id,
                user_id=request.user_id,
                context_document_ids=request.context_document_ids,
            )
        else:
            # Fast mode — existing hybrid RAG
            rag_engine = get_rag_engine()
            result = await rag_engine.query(
                query=request.query,
                session_id=session_id,
                use_context=True,
                user_id=request.user_id,
                context_document_ids=request.context_document_ids,
            )
        
        # Extract draw.io XML if present
        cleaned_answer, diagram_xml = extract_drawio_xml(result["answer"])
        result["answer"] = cleaned_answer

        logger.info(
            "diagram_extraction",
            session_id=session_id,
            mode=mode,
            has_diagram_xml=diagram_xml is not None,
        )

        if diagram_xml is None and is_diagram_request(request.query):
            try:
                from app.services.groq_service import get_groq_service
                llm = get_groq_service().get_llm()
                logger.info(
                    "diagram_fallback_start",
                    session_id=session_id,
                    mode=mode,
                )
                diagram_prompt = DRAWIO_XML_PROMPT.format(
                    query=request.query,
                    answer=cleaned_answer,
                )
                diagram_response = await llm.acomplete(diagram_prompt)
                diagram_text = getattr(diagram_response, "text", None) or str(diagram_response)
                _, diagram_xml = extract_drawio_xml(diagram_text)
                logger.info(
                    "diagram_fallback_complete",
                    session_id=session_id,
                    mode=mode,
                    has_diagram_xml=diagram_xml is not None,
                )
            except Exception as e:
                logger.warning("diagram_generation_failed", error=str(e))

        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=result["answer"],
            confidence_score=json.loads(json.dumps({"score": result["confidence_score"], "level": result["confidence_level"]})),
            sources=_serialize_sources(result.get("sources")),
            reasoning=result.get("reasoning"),
            mode=mode,
            diagram_xml=diagram_xml,
        )
        db.add(assistant_msg)
        
        # Update session's updated_at timestamp
        from datetime import datetime
        db_session.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Convert to response model
        response = ChatResponse(
            answer=result["answer"],
            confidence_score=result["confidence_score"],
            confidence_level=result["confidence_level"],
            sources=result["sources"],
            session_id=result["session_id"],
            processing_time_ms=result.get("processing_time_ms"),
            reasoning=result.get("reasoning"),
            mode=mode,
            diagram_xml=diagram_xml,
        )
        
        logger.info(
            "chat_query_completed",
            session_id=session_id,
            mode=mode,
            confidence_score=response.confidence_score,
            num_sources=len(response.sources),
        )
        
        return response
        
    except Exception as e:
        logger.error("chat_query_failed", error=str(e), query=request.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/stream", status_code=status.HTTP_200_OK)
async def stream_query(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Stream a chat response using Server-Sent Events (SSE).
    """
    session_id = request.session_id or str(uuid.uuid4())
    mode = request.mode or await _determine_default_mode()

    # Save session if it doesn't exist
    db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not db_session:
        title = request.query[:50] + "..." if len(request.query) > 50 else request.query
        db_session = ChatSession(
            id=session_id,
            user_id=request.user_id,
            title=title,
        )
        db.add(db_session)
        db.commit()

    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.query,
        context_files=[cf.dict() for cf in request.context_files] if request.context_files else None,
    )
    db.add(user_msg)
    db.commit()

    async def event_generator():
        try:
            yield _sse_event("session", {"session_id": session_id, "mode": mode})

            if mode == "think":
                from app.core.pageindex_rag_engine import get_pageindex_rag_engine
                think_engine = get_pageindex_rag_engine()
                result = await think_engine.query(
                    query=request.query,
                    db=db,
                    session_id=session_id,
                    user_id=request.user_id,
                    context_document_ids=request.context_document_ids,
                )

                cleaned_answer, diagram_xml = extract_drawio_xml(result["answer"])
                result["answer"] = cleaned_answer

                logger.info(
                    "diagram_extraction",
                    session_id=session_id,
                    mode=mode,
                    has_diagram_xml=diagram_xml is not None,
                )

                if diagram_xml is None and is_diagram_request(request.query):
                    try:
                        from app.services.groq_service import get_groq_service
                        llm = get_groq_service().get_llm()
                        logger.info(
                            "diagram_fallback_start",
                            session_id=session_id,
                            mode=mode,
                        )
                        diagram_prompt = DRAWIO_XML_PROMPT.format(
                            query=request.query,
                            answer=cleaned_answer,
                        )
                        diagram_response = await llm.acomplete(diagram_prompt)
                        diagram_text = getattr(diagram_response, "text", None) or str(diagram_response)
                        _, diagram_xml = extract_drawio_xml(diagram_text)
                        logger.info(
                            "diagram_fallback_complete",
                            session_id=session_id,
                            mode=mode,
                            has_diagram_xml=diagram_xml is not None,
                        )
                    except Exception as e:
                        logger.warning("diagram_generation_failed", error=str(e))

                # Emit the answer as a single token for think mode
                yield _sse_event("token", {"token": cleaned_answer})

                result_payload = {
                    **result,
                    "mode": mode,
                    "diagram_xml": diagram_xml,
                    "sources": _serialize_sources(result.get("sources")),
                }

                assistant_msg = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=cleaned_answer,
                    confidence_score=json.loads(json.dumps({
                        "score": result["confidence_score"],
                        "level": result["confidence_level"],
                    })),
                    sources=_serialize_sources(result.get("sources")),
                    reasoning=result.get("reasoning"),
                    mode=mode,
                    diagram_xml=diagram_xml,
                )
                db.add(assistant_msg)
                from datetime import datetime
                db_session.updated_at = datetime.utcnow()
                db.commit()

                yield _sse_event("final", result_payload)
                return

            rag_engine = get_rag_engine()
            async for event in rag_engine.stream_query(
                query=request.query,
                session_id=session_id,
                use_context=True,
                user_id=request.user_id,
                context_document_ids=request.context_document_ids,
            ):
                if event.get("type") == "token":
                    yield _sse_event("token", {"token": event["data"]})
                elif event.get("type") == "final":
                    data = event["data"]
                    cleaned_answer, diagram_xml = extract_drawio_xml(data["answer"])
                    data["answer"] = cleaned_answer

                    logger.info(
                        "diagram_extraction",
                        session_id=session_id,
                        mode=mode,
                        has_diagram_xml=diagram_xml is not None,
                    )

                    if diagram_xml is None and is_diagram_request(request.query):
                        try:
                            from app.services.groq_service import get_groq_service
                            llm = get_groq_service().get_llm()
                            logger.info(
                                "diagram_fallback_start",
                                session_id=session_id,
                                mode=mode,
                            )
                            diagram_prompt = DRAWIO_XML_PROMPT.format(
                                query=request.query,
                                answer=cleaned_answer,
                            )
                            diagram_response = await llm.acomplete(diagram_prompt)
                            diagram_text = getattr(diagram_response, "text", None) or str(diagram_response)
                            _, diagram_xml = extract_drawio_xml(diagram_text)
                            logger.info(
                                "diagram_fallback_complete",
                                session_id=session_id,
                                mode=mode,
                                has_diagram_xml=diagram_xml is not None,
                            )
                        except Exception as e:
                            logger.warning("diagram_generation_failed", error=str(e))
                    data["mode"] = mode
                    data["diagram_xml"] = diagram_xml
                    data["sources"] = _serialize_sources(data.get("sources"))

                    assistant_msg = ChatMessage(
                        session_id=session_id,
                        role="assistant",
                        content=cleaned_answer,
                        confidence_score=json.loads(json.dumps({
                            "score": data["confidence_score"],
                            "level": data["confidence_level"],
                        })),
                        sources=_serialize_sources(data.get("sources")),
                        reasoning=data.get("reasoning"),
                        mode=mode,
                        diagram_xml=diagram_xml,
                    )
                    db.add(assistant_msg)
                    from datetime import datetime
                    db_session.updated_at = datetime.utcnow()
                    db.commit()

                    yield _sse_event("final", data)
        except Exception as e:
            logger.error("chat_stream_failed", error=str(e))
            yield _sse_event("error", {"message": "Streaming failed"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history/{session_id}", response_model=ChatHistory, status_code=status.HTTP_200_OK)
async def get_history(session_id: str, db: Session = Depends(get_db)):
    """
    Get conversation history for a session from database.
    Also syncs the messages to in-memory context manager for RAG use.
    
    Args:
        session_id: Session identifier
        db: Database session
        
    Returns:
        ChatHistory with all messages
    """
    try:
        # Load messages from database (audit trail)
        db_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        # Convert database messages to Message schema
        from app.models.schemas import Message
        messages = []
        
        # Sync to context manager for RAG to use
        context_manager = get_context_manager()
        context_manager.clear_session(session_id)  # Clear old context first
        
        for db_msg in db_messages:
            score_value, level_value = _extract_confidence_fields(db_msg.confidence_score)
            # Add to context manager for RAG engine
            context_manager.add_message(
                session_id=session_id,
                role=db_msg.role,
                content=db_msg.content,
                confidence_score=score_value
            )
            
            # Add to response
            messages.append(Message(
                role=db_msg.role,
                content=db_msg.content,
                timestamp=db_msg.created_at.isoformat(),
                confidence_score=score_value,
                confidence_level=level_value,
                sources=db_msg.sources,
                reasoning=db_msg.reasoning,
                mode=db_msg.mode,
                context_files=db_msg.context_files,
                diagram_xml=db_msg.diagram_xml,
            ))
        
        logger.info(
            "chat_history_retrieved",
            session_id=session_id,
            num_messages=len(messages),
        )
        
        return ChatHistory(
            session_id=session_id,
            messages=messages
        )
        
    except Exception as e:
        logger.error("failed_to_get_chat_history", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )


@router.delete("/history/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(session_id: str):
    """
    Clear conversation history for a session from in-memory context.
    This clears the RAG context but keeps database audit trail intact.
    
    Args:
        session_id: Session identifier
    """
    try:
        # Clear only in-memory context (for RAG engine)
        # Database messages are preserved for audit purposes
        context_manager = get_context_manager()
        context_manager.clear_session(session_id)
        
        logger.info("chat_history_cleared", session_id=session_id)
        
    except Exception as e:
        logger.error("failed_to_clear_chat_history", error=str(e), session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear chat history: {str(e)}"
        )
