"""
SQLAlchemy models for the application.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
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
    sources = Column(JSON, nullable=True)  # Store source references for assistant messages
    reasoning = Column(Text, nullable=True)  # Store think-mode reasoning
    mode = Column(String, nullable=True)  # fast | think
    context_files = Column(JSON, nullable=True)  # Store selected context files for user messages
    diagram_xml = Column(Text, nullable=True)  # Store draw.io XML when diagrams are generated
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


class AuraSqlConnection(Base):
    """Stored database connections for AuraSQL."""

    __tablename__ = "aurasql_connections_nexus_rag"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users_nexus_rag.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    db_type = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    database = Column(String, nullable=False)
    schema_name = Column(String, nullable=True)
    ssl_required = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    secret = relationship("AuraSqlConnectionSecret", back_populates="connection", uselist=False, cascade="all, delete-orphan")
    contexts = relationship("AuraSqlContext", back_populates="connection", cascade="all, delete-orphan")


class AuraSqlConnectionSecret(Base):
    """Encrypted credentials for AuraSQL connections."""

    __tablename__ = "aurasql_connection_secrets_nexus_rag"

    id = Column(String, primary_key=True, index=True)
    connection_id = Column(String, ForeignKey("aurasql_connections_nexus_rag.id"), nullable=False, unique=True)
    encrypted_password = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    connection = relationship("AuraSqlConnection", back_populates="secret")


class AuraSqlContext(Base):
    """Saved table contexts with schema snapshots for AuraSQL."""

    __tablename__ = "aurasql_contexts_nexus_rag"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users_nexus_rag.id"), nullable=False, index=True)
    connection_id = Column(String, ForeignKey("aurasql_connections_nexus_rag.id"), nullable=False)
    name = Column(String, nullable=False)
    table_names = Column(JSON, nullable=False)
    schema_snapshot = Column(JSON, nullable=False)
    vector_context_id = Column(String, nullable=False)
    is_temporary = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    connection = relationship("AuraSqlConnection", back_populates="contexts")
    query_history = relationship("AuraSqlQueryHistory", back_populates="context", cascade="all, delete-orphan")


class AuraSqlQueryHistory(Base):
    """Logs for generated and executed SQL queries."""

    __tablename__ = "aurasql_query_history_nexus_rag"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users_nexus_rag.id"), nullable=False, index=True)
    connection_id = Column(String, ForeignKey("aurasql_connections_nexus_rag.id"), nullable=False)
    context_id = Column(String, ForeignKey("aurasql_contexts_nexus_rag.id"), nullable=True)
    natural_language_query = Column(Text, nullable=True)
    generated_sql = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="generated")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    context = relationship("AuraSqlContext", back_populates="query_history")
