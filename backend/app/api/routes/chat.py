"""
Chat endpoints for querying the RAG system.
"""

import uuid
import inspect
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.schemas import ChatRequest, ChatResponse, ChatHistory, AskFileExtractResponse
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
from app.services.llm_service import get_llm_service
from app.services.document_processor import get_document_processor
from app.utils.validators import validate_file_extension, validate_file_size
import asyncio

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


async def _determine_default_mode() -> str:
    """Return fast by default; fall back to think if any core service is unhealthy."""
    unhealthy = False
    embedding_unhealthy = False

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
                    embedding_unhealthy = True
                    unhealthy = True
        except Exception:
            embedding_unhealthy = True
            unhealthy = True
    else:
        unhealthy = True

    # 2. Reranker health (remote shares embedding health)
    if settings.reranker_provider == "cohere":
        try:
            from app.services.cohere_service import get_cohere_service
            if not await get_cohere_service().check_health():
                unhealthy = True
        except Exception:
            unhealthy = True
    elif settings.reranker_provider == "remote" or settings.use_remote_reranker_service:
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                response = await client.get(f"{settings.remote_embedding_service_url}/health")
                if response.status_code != 200:
                    unhealthy = True
        except Exception:
            unhealthy = True
        if settings.use_remote_embedding_service and embedding_unhealthy:
            unhealthy = True
    else:
        unhealthy = True

    # 3. LLM health (cached)
    try:
        from app.services.llm_service import get_llm_service
        if not await get_llm_service().check_health():
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


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _extract_prompt_tokens_from_response(response) -> Optional[int]:
    if response is None:
        return None

    def _read_usage(obj) -> Optional[int]:
        if not isinstance(obj, dict):
            return None
        usage = obj.get("usage") if isinstance(obj.get("usage"), dict) else obj
        if not isinstance(usage, dict):
            return None
        value = usage.get("prompt_tokens", usage.get("input_tokens"))
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    candidates = [
        getattr(response, "raw", None),
        getattr(response, "additional_kwargs", None),
        getattr(response, "usage", None),
        response,
    ]
    for candidate in candidates:
        prompt_tokens = _read_usage(candidate)
        if prompt_tokens is not None:
            return prompt_tokens
    return None


def _build_token_usage(prompt_tokens: Optional[int], prompt: str, compaction_applied: bool = False) -> dict:
    context_max = max(1, settings.llm_context_window)
    used = prompt_tokens if prompt_tokens is not None else _estimate_tokens(prompt)
    pct = round((used / context_max) * 100, 2)
    return {
        "context_tokens_used": int(used),
        "context_tokens_max": context_max,
        "context_utilization_pct": pct,
        "near_limit": used >= int(context_max * 0.85),
        "compaction_applied": compaction_applied,
    }


async def _emit_text_tokens(text: str, chunk_size: int = 18):
    """Yield small chunks of text for smoother SSE rendering on frontend."""
    if not text:
        return
    for idx in range(0, len(text), chunk_size):
        yield text[idx: idx + chunk_size]
        await asyncio.sleep(0)


async def _iter_llm_tokens(llm, prompt: str):
    """Yield tokens robustly for wrappers returning async iterator OR awaitable."""
    def _suffix_delta(previous: str, current: str) -> str:
        if not current:
            return ""
        if not previous:
            return current
        if current == previous:
            return ""
        if current.startswith(previous):
            return current[len(previous):]
        if previous.startswith(current):
            return ""

        max_prefix = min(len(previous), len(current))
        prefix_len = 0
        while prefix_len < max_prefix and previous[prefix_len] == current[prefix_len]:
            prefix_len += 1
        return current[prefix_len:]

    stream_obj = llm.astream_complete(prompt)

    if inspect.isawaitable(stream_obj):
        stream_obj = await stream_obj

    streamed_any = False
    last_text = ""
    emitted_text = ""

    if hasattr(stream_obj, "__aiter__"):
        async for chunk in stream_obj:
            delta = getattr(chunk, "delta", None)
            text = getattr(chunk, "text", None)

            if text:
                candidate = _suffix_delta(last_text, text)
                last_text = text
            elif delta:
                candidate = delta
            else:
                candidate = ""

            token = _suffix_delta(emitted_text, candidate)

            if token:
                streamed_any = True
                emitted_text += token
                yield token
    else:
        candidate = getattr(stream_obj, "text", None) or str(stream_obj or "")
        token = _suffix_delta(emitted_text, candidate)
        if token:
            streamed_any = True
            emitted_text += token
            yield token

    if not streamed_any:
        fallback_response = await llm.acomplete(prompt)
        fallback_text = (getattr(fallback_response, "text", None) or str(fallback_response)).strip()
        if fallback_text:
            yield fallback_text


def _load_recent_session_messages(db: Session, session_id: str, limit: int = 12) -> List[ChatMessage]:
    """Load recent session messages from DB in ascending order."""
    recent_desc = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(recent_desc))


def _format_history_for_prompt(messages: List[ChatMessage], max_chars: int = 6000) -> str:
    """Format DB messages into a compact conversation block for prompting."""
    if not messages:
        return ""

    # Keep the most recent turns first, then restore chronological order.
    parts: List[str] = []
    current_len = 0
    for msg in reversed(messages):
        role = "User" if msg.role == "user" else "Assistant"
        content = (msg.content or "").strip()
        if not content:
            continue

        # Prevent a single very long message from starving newer turns.
        if len(content) > 1200:
            content = f"{content[:1200]}\n...[truncated]"

        mode_tag = f" [{msg.mode}]" if getattr(msg, "mode", None) else ""
        block = f"{role}{mode_tag}: {content}"
        if current_len + len(block) + 1 > max_chars:
            break
        parts.append(block)
        current_len += len(block) + 1

    return "\n".join(reversed(parts))


def _sync_context_manager_from_db(session_id: str, messages: List[ChatMessage]) -> None:
    """Hydrate in-memory chat context from persisted DB history."""
    context_manager = get_context_manager()
    context_manager.clear_session(session_id)

    for db_msg in messages:
        score_value, _ = _extract_confidence_fields(db_msg.confidence_score)
        context_manager.add_message(
            session_id=session_id,
            role=db_msg.role,
            content=db_msg.content,
            confidence_score=score_value,
        )


def _build_ask_prompt(query: str, ask_files, conversation_history: Optional[str] = None) -> str:
    """Build ask-mode prompt with optional in-memory files and chat history."""
    file_blocks = []
    total_chars = 0
    max_chars = 60000
    for item in ask_files or []:
        content = (item.content or "").strip()
        if not content:
            continue
        remaining = max_chars - total_chars
        if remaining <= 0:
            break
        clipped = content[:remaining]
        total_chars += len(clipped)
        file_blocks.append(f"[File: {item.filename}]\n{clipped}")

    history_block = f"Conversation History:\n{conversation_history}\n\n" if conversation_history else ""

    if file_blocks:
        return (
            "You are a helpful assistant. Answer the user clearly and concisely. "
            "Use conversation history to maintain continuity, and provided file contents when relevant. "
            "If details are missing, say so explicitly.\n\n"
            f"{history_block}"
            f"User Question:\n{query}\n\n"
            "Provided File Content:\n"
            + "\n\n".join(file_blocks)
        )

    return (
        "You are a helpful assistant. Answer the user clearly and concisely. "
        "Use conversation history to maintain continuity when relevant.\n\n"
        f"{history_block}"
        f"User Question:\n{query}"
    )


def _sanitize_ask_markdown(text: str) -> str:
    """Normalize malformed emphasis markers in ask-mode output."""
    if not text:
        return text

    def _normalize_unmatched_delimiters(value: str, delimiter: str) -> str:
        parts = value.split(delimiter)
        if len(parts) <= 2:
            return value
        delimiter_count = len(parts) - 1
        if delimiter_count % 2 == 0:
            return value

        last_index = value.rfind(delimiter)
        if last_index == -1:
            return value
        return f"{value[:last_index]}{value[last_index + len(delimiter):]}"

    def _normalize_table_cell_emphasis(value: str) -> str:
        normalized_lines = []
        for line in value.split("\n"):
            trimmed = line.strip()
            if not trimmed.startswith("|") or "|" not in trimmed:
                normalized_lines.append(line)
                continue

            cells = line.split("|")
            if len(cells) < 3:
                normalized_lines.append(line)
                continue

            normalized_cells = []
            for idx, cell in enumerate(cells):
                if idx == 0 or idx == len(cells) - 1:
                    normalized_cells.append(cell)
                    continue

                cleaned = _normalize_unmatched_delimiters(cell, "**")
                cleaned = _normalize_unmatched_delimiters(cleaned, "__")
                normalized_cells.append(cleaned)

            normalized_lines.append("|".join(normalized_cells))

        return "\n".join(normalized_lines)

    sanitized = _normalize_table_cell_emphasis(text)
    sanitized_lines = []
    for line in sanitized.split("\n"):
        line = _normalize_unmatched_delimiters(line, "**")
        line = _normalize_unmatched_delimiters(line, "__")
        sanitized_lines.append(line)

    return "\n".join(sanitized_lines)


async def _query_ask_mode(query: str, ask_files, conversation_history: Optional[str] = None) -> dict:
    """Direct LLM response without retrieval/vector lookup."""
    llm = get_llm_service().get_llm()
    prompt = _build_ask_prompt(query=query, ask_files=ask_files, conversation_history=conversation_history)

    response = await llm.acomplete(prompt)
    answer = getattr(response, "text", None) or str(response)
    answer = _sanitize_ask_markdown(answer)
    token_usage = _build_token_usage(
        prompt_tokens=_extract_prompt_tokens_from_response(response),
        prompt=prompt,
    )
    return {
        "answer": answer,
        "confidence_score": 72.0,
        "confidence_level": "medium",
        "sources": [],
        "processing_time_ms": None,
        "reasoning": None,
        "token_usage": token_usage,
    }


@router.post("/query", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def query(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Query the RAG system with a question.
    Supports three modes:
    - fast (default): Hybrid BM25 + Vector retrieval with reranking
    - think: PageIndex reasoning-based tree search
    - ask: Direct LLM answer without retrieval/vector search
    
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

        recent_history = _load_recent_session_messages(db, session_id=session_id)
        conversation_history = _format_history_for_prompt(recent_history)
        _sync_context_manager_from_db(session_id, recent_history)
        
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
        if mode == "ask":
            result = await _query_ask_mode(
                query=request.query,
                ask_files=request.ask_files,
                conversation_history=conversation_history,
            )
            result["session_id"] = session_id
        elif mode == "think":
            from app.core.pageindex_rag_engine import get_pageindex_rag_engine
            think_engine = get_pageindex_rag_engine()
            result = await think_engine.query(
                query=request.query,
                db=db,
                session_id=session_id,
                user_id=request.user_id,
                context_document_ids=request.context_document_ids,
                conversation_history=conversation_history,
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
                llm = get_llm_service().get_llm()
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
            token_usage=result.get("token_usage"),
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

    recent_history = _load_recent_session_messages(db, session_id=session_id)
    conversation_history = _format_history_for_prompt(recent_history)
    _sync_context_manager_from_db(session_id, recent_history)

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

            if mode == "ask":
                llm = get_llm_service().get_llm()
                prompt = _build_ask_prompt(
                    query=request.query,
                    ask_files=request.ask_files,
                    conversation_history=conversation_history,
                )
                answer_parts = []
                async for token in _iter_llm_tokens(llm, prompt):
                    answer_parts.append(token)
                    yield _sse_event("token", {"token": token})

                answer = "".join(answer_parts).strip()
                answer = _sanitize_ask_markdown(answer)

                result = {
                    "answer": answer,
                    "confidence_score": 72.0,
                    "confidence_level": "medium",
                    "sources": [],
                    "processing_time_ms": None,
                    "reasoning": None,
                    "session_id": session_id,
                    "token_usage": _build_token_usage(prompt_tokens=None, prompt=prompt),
                }

                cleaned_answer, diagram_xml = extract_drawio_xml(result["answer"])
                result["answer"] = cleaned_answer

                if diagram_xml is None and is_diagram_request(request.query):
                    try:
                        llm = get_llm_service().get_llm()
                        diagram_prompt = DRAWIO_XML_PROMPT.format(
                            query=request.query,
                            answer=cleaned_answer,
                        )
                        diagram_response = await llm.acomplete(diagram_prompt)
                        diagram_text = getattr(diagram_response, "text", None) or str(diagram_response)
                        _, diagram_xml = extract_drawio_xml(diagram_text)
                    except Exception as e:
                        logger.warning("diagram_generation_failed", error=str(e))

                final_payload = {
                    **result,
                    "mode": mode,
                    "diagram_xml": diagram_xml,
                    "sources": [],
                }

                assistant_msg = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=cleaned_answer,
                    confidence_score=json.loads(json.dumps({
                        "score": result["confidence_score"],
                        "level": result["confidence_level"],
                    })),
                    sources=[],
                    reasoning=None,
                    mode=mode,
                    diagram_xml=diagram_xml,
                )
                db.add(assistant_msg)
                from datetime import datetime
                db_session.updated_at = datetime.utcnow()
                db.commit()

                yield _sse_event("final", final_payload)
                return

            if mode == "think":
                from app.core.pageindex_rag_engine import get_pageindex_rag_engine
                think_engine = get_pageindex_rag_engine()
                result = await think_engine.query(
                    query=request.query,
                    db=db,
                    session_id=session_id,
                    user_id=request.user_id,
                    context_document_ids=request.context_document_ids,
                    conversation_history=conversation_history,
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
                        llm = get_llm_service().get_llm()
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

                async for token in _emit_text_tokens(cleaned_answer):
                    yield _sse_event("token", {"token": token})

                result_payload = {
                    **result,
                    "mode": mode,
                    "diagram_xml": diagram_xml,
                    "sources": _serialize_sources(result.get("sources")),
                    "token_usage": result.get("token_usage"),
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
                            llm = get_llm_service().get_llm()
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
            logger.exception("chat_stream_failed", error=str(e))
            yield _sse_event("error", {"message": "An internal server error occurred"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/extract-file", response_model=AskFileExtractResponse, status_code=status.HTTP_200_OK)
async def extract_file_for_ask_mode(file: UploadFile = File(...)):
    """Extract plain text from a file for ask mode without persisting or indexing it."""
    try:
        if not validate_file_extension(file.filename, settings.allowed_file_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(settings.allowed_file_extensions)}",
            )

        content = await file.read()
        if not validate_file_size(len(content), settings.max_upload_size_mb):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum allowed: {settings.max_upload_size_mb} MB",
            )

        processor = get_document_processor()
        extracted_text = await processor.extract_text_from_file(content, file.filename)

        return AskFileExtractResponse(
            id=str(uuid.uuid4()),
            filename=file.filename,
            content=extracted_text,
            content_length=len(extracted_text),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("ask_file_extract_failed", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract file text: {str(e)}",
        )


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
