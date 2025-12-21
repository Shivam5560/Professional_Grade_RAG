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
    
    Args:
        request: ChatRequest with query and session_id
        
    Returns:
        ChatResponse with answer, confidence, and sources
    """
    try:
        # Get RAG engine
        rag_engine = get_rag_engine()
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Check if this is a new session
        is_new_session = False
        
        # Save session if it doesn't exist
        db_session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not db_session:
            is_new_session = True
            # Generate title from first message (truncate to 50 chars)
            title = request.query[:50] + "..." if len(request.query) > 50 else request.query
            
            db_session = ChatSession(
                id=session_id,
                user_id=request.user_id,
                title=title
            )
            db.add(db_session)
            db.commit()
            logger.info(
                "new_chat_session_created",
                session_id=session_id,
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
        
        logger.info(
            "chat_query_received",
            query=request.query,
            session_id=session_id,
            stream=request.stream,
            user_id=request.user_id,
            context_document_ids=request.context_document_ids,
            num_context_docs=len(request.context_document_ids) if request.context_document_ids else 0,
        )
        
        # Execute query with user_id filter and optional context documents
        result = await rag_engine.query(
            query=request.query,
            session_id=session_id,
            use_context=True,
            user_id=request.user_id,  # Pass user_id to filter documents
            context_document_ids=request.context_document_ids  # Pass selected document IDs
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
            processing_time_ms=result.get("processing_time_ms")
        )
        
        logger.info(
            "chat_query_completed",
            session_id=session_id,
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
