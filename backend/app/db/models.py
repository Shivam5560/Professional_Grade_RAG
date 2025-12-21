"""
SQLAlchemy models for the application.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users_nexus_rag"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    chat_sessions = relationship("ChatSession", back_populates="user")
    documents = relationship("Document", back_populates="user")

class ChatSession(Base):
    __tablename__ = "chat_sessions_nexus_rag"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users_nexus_rag.id"))
    title = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    messages = relationship("ChatMessage", back_populates="session")
    user = relationship("User", back_populates="chat_sessions")

class ChatMessage(Base):
    __tablename__ = "chat_messages_nexus_rag"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions_nexus_rag.id"))
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    confidence_score = Column(JSON, nullable=True)  # Store confidence metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    session = relationship("ChatSession", back_populates="messages")


class Document(Base):
    """Track uploaded documents per user."""
    __tablename__ = "documents_nexus_rag"

    id = Column(String, primary_key=True, index=True)  # document_id
    user_id = Column(Integer, ForeignKey("users_nexus_rag.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    file_type = Column(String, nullable=True)  # Extension like .pdf, .txt
    vector_count = Column(Integer, default=0)  # Number of chunks/vectors
    title = Column(String, nullable=True)
    category = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="documents")
