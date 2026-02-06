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
    tree_structure = relationship("DocumentTreeStructure", back_populates="document", uselist=False)


class DocumentTreeStructure(Base):
    """Stores PageIndex hierarchical tree structures for Think mode RAG."""
    __tablename__ = "document_tree_structures_nexus_rag"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String, ForeignKey("documents_nexus_rag.id"), unique=True, nullable=False)
    tree_json = Column(JSON, nullable=False)       # Full tree structure JSON
    doc_description = Column(Text, nullable=True)   # LLM-generated document description
    node_count = Column(Integer, default=0)         # Total nodes in tree
    status = Column(String, default="pending")      # pending | processing | completed | failed
    error_message = Column(Text, nullable=True)     # Error details if generation failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    document = relationship("Document", back_populates="tree_structure")
    nodes = relationship("TreeNode", back_populates="tree_structure", cascade="all, delete-orphan")


class TreeNode(Base):
    """Individual flattened nodes from the tree for fast retrieval queries."""
    __tablename__ = "tree_nodes_nexus_rag"

    id = Column(Integer, primary_key=True, index=True)
    tree_id = Column(Integer, ForeignKey("document_tree_structures_nexus_rag.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents_nexus_rag.id"), nullable=False)
    node_id = Column(String, nullable=False)         # e.g., "0001", "0002"
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    text_content = Column(Text, nullable=True)       # Full section text
    start_page = Column(Integer, nullable=True)
    end_page = Column(Integer, nullable=True)
    parent_node_id = Column(String, nullable=True)   # node_id of parent
    depth = Column(Integer, default=0)               # Depth in tree (0 = root)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tree_structure = relationship("DocumentTreeStructure", back_populates="nodes")
