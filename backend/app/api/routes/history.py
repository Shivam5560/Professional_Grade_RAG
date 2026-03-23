"""
Chat history routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.db.database import get_db
from app.db.models import ChatSession, ChatMessage, User
from app.api.deps import get_current_user

router = APIRouter()

class ChatSessionResponse(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class ChatMessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime
    confidence_score: Optional[dict] = None
    sources: Optional[List[Any]] = None
    reasoning: Optional[str] = None
    mode: Optional[str] = None
    context_files: Optional[List[Any]] = None
    diagram_xml: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ChatBootstrapResponse(BaseModel):
    sessions: List[ChatSessionResponse]
    active_session_id: Optional[str] = None
    messages: List[ChatMessageResponse] = Field(default_factory=list)


@router.get("/bootstrap", response_model=ChatBootstrapResponse)
def get_chat_bootstrap(
    active_session_id: Optional[str] = Query(default=None),
    session_limit: int = Query(default=50, ge=1, le=200),
    message_limit: int = Query(default=200, ge=1, le=1000),
    include_messages: bool = Query(default=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch chat sessions and one active session's messages in a single request."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(session_limit)
        .all()
    )

    target_session = None
    if active_session_id:
        target_session = (
            db.query(ChatSession)
            .filter(ChatSession.id == active_session_id, ChatSession.user_id == current_user.id)
            .first()
        )

    if target_session is None and sessions:
        target_session = sessions[0]

    if not target_session:
        return ChatBootstrapResponse(sessions=sessions, active_session_id=None, messages=[])

    if not include_messages:
        return ChatBootstrapResponse(
            sessions=sessions,
            active_session_id=target_session.id,
            messages=[],
        )

    recent_messages_desc = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == target_session.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(message_limit)
        .all()
    )
    messages = list(reversed(recent_messages_desc))

    return ChatBootstrapResponse(
        sessions=sessions,
        active_session_id=target_session.id,
        messages=messages,
    )

@router.get("/{user_id}", response_model=List[ChatSessionResponse])
def get_chat_history(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all chat sessions for a user."""
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()
    return sessions

@router.get("/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all messages for a specific session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return messages


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(session_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a chat session and all associated messages."""
    try:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.query(ChatSession).filter(ChatSession.id == session_id).delete()
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete chat session") from e


@router.delete("/user/{user_id}/all", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_chat_history(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete all chat sessions and messages for a user."""
    try:
        if user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        user_exists = db.query(User.id).filter(User.id == user_id).first()
        if not user_exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        session_ids = [row[0] for row in db.query(ChatSession.id).filter(ChatSession.user_id == user_id).all()]
        if session_ids:
            db.query(ChatMessage).filter(ChatMessage.session_id.in_(session_ids)).delete(synchronize_session=False)
            db.query(ChatSession).filter(ChatSession.user_id == user_id).delete(synchronize_session=False)
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete chat history") from e
