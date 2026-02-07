"""
Chat history routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.db.database import get_db
from app.db.models import ChatSession, ChatMessage, User

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

@router.get("/{user_id}", response_model=List[ChatSessionResponse])
def get_chat_history(user_id: int, db: Session = Depends(get_db)):
    """Get all chat sessions for a user."""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()
    return sessions

@router.get("/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages for a specific session."""
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return messages
