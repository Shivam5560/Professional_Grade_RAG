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

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


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
        mode = request.mode or "fast"
        
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
            content=request.query
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
        
        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=result["answer"],
            confidence_score=json.loads(json.dumps({"score": result["confidence_score"], "level": result["confidence_level"]}))
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
            # Add to context manager for RAG engine
            context_manager.add_message(
                session_id=session_id,
                role=db_msg.role,
                content=db_msg.content,
                confidence_score=db_msg.confidence_score.get('score') if db_msg.confidence_score else None
            )
            
            # Add to response
            messages.append(Message(
                role=db_msg.role,
                content=db_msg.content,
                timestamp=db_msg.created_at.isoformat(),
                confidence_score=db_msg.confidence_score.get('score') if db_msg.confidence_score else None
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
