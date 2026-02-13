"""
Pydantic models for API request/response validation.
"""

from typing import List, Optional, Literal, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator
from app.utils.validators import sanitize_query


class SourceReference(BaseModel):
    """Model for document source references."""
    
    document: str = Field(..., description="Document name or identifier")
    page: Optional[int] = Field(None, description="Page number if applicable")
    chunk_id: Optional[str] = Field(None, description="Chunk identifier")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    text_snippet: Optional[str] = Field(None, description="Relevant text excerpt")


class ContextFile(BaseModel):
    """Model for context file references."""

    id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Document filename")


class ChatRequest(BaseModel):
    """Request model for chat queries."""
    
    query: str = Field(..., min_length=1, max_length=10000, description="User query")
    session_id: Optional[str] = Field(None, description="Session identifier for chat history")
    user_id: Optional[int] = Field(None, description="User identifier for associating chat sessions")
    stream: bool = Field(default=False, description="Enable streaming response")
    context_document_ids: Optional[List[str]] = Field(default=None, description="Specific document IDs to use as context")
    mode: Optional[Literal["fast", "think"]] = Field(default=None, description="RAG mode: fast (hybrid retrieval) or think (PageIndex reasoning)")
    context_files: Optional[List[ContextFile]] = Field(default=None, description="Selected context files for UI display")
    
    @validator('query')
    def sanitize_query_input(cls, v):
        """Sanitize query input."""
        return sanitize_query(v)


class ChatResponse(BaseModel):
    """Response model for chat queries."""
    
    answer: str = Field(..., description="Generated answer")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence percentage")
    confidence_level: Literal["high", "medium", "low"] = Field(..., description="Confidence category")
    sources: List[SourceReference] = Field(default_factory=list, description="Source references")
    session_id: str = Field(..., description="Session identifier")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")
    reasoning: Optional[str] = Field(None, description="Think mode reasoning steps (only present in think mode)")
    mode: Optional[Literal["fast", "think"]] = Field(default="fast", description="RAG mode used for this response")
    diagram_xml: Optional[str] = Field(None, description="draw.io XML for generated diagrams")


class Message(BaseModel):
    """Model for a chat message."""
    
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Message timestamp")
    confidence_score: Optional[float] = Field(None, description="Confidence score for assistant messages")
    confidence_level: Optional[Literal["high", "medium", "low"]] = Field(
        default=None,
        description="Confidence level for assistant messages",
    )
    sources: Optional[List[SourceReference]] = Field(default=None, description="Source references for assistant messages")
    reasoning: Optional[str] = Field(None, description="Reasoning steps for think mode")
    mode: Optional[Literal["fast", "think"]] = Field(default=None, description="RAG mode used for this message")
    context_files: Optional[List[ContextFile]] = Field(default=None, description="Context files selected for the query")
    diagram_xml: Optional[str] = Field(None, description="draw.io XML for generated diagrams")


class ChatHistory(BaseModel):
    """Model for chat history."""
    
    session_id: str = Field(..., description="Session identifier")
    messages: List[Message] = Field(default_factory=list, description="Chat messages")


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    
    document_id: str = Field(..., description="Document identifier")
    status: Literal["processed", "failed", "processing"] = Field(..., description="Processing status")
    chunks_created: int = Field(..., description="Number of chunks created")
    message: str = Field(..., description="Status message")


class DocumentInfo(BaseModel):
    """Model for document information."""
    
    id: str = Field(..., description="Document identifier")
    filename: str = Field(..., description="Original filename")
    title: Optional[str] = Field(None, description="Document title")
    file_type: Optional[str] = Field(None, description="File extension")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    vector_count: int = Field(..., description="Number of vectors/chunks")
    category: Optional[str] = Field(None, description="Document category")
    upload_date: str = Field(..., description="Upload timestamp")


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    
    documents: List[DocumentInfo] = Field(default_factory=list, description="List of documents")
    total: int = Field(..., description="Total document count")


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: Literal["healthy", "unhealthy", "degraded"] = Field(..., description="Overall health status")
    components: dict = Field(..., description="Component health status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Health check timestamp")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")


class UserDocumentResponse(BaseModel):
    """Response model for user's documents in knowledge base."""
    
    documents: List[DocumentInfo] = Field(default_factory=list, description="List of user's documents")
    total: int = Field(..., description="Total document count")


class BulkDeleteRequest(BaseModel):
    """Request model for bulk document deletion."""
    
    document_ids: List[str] = Field(..., min_items=1, description="List of document IDs to delete")
    user_id: int = Field(..., description="User ID for authorization")


class BulkDeleteResponse(BaseModel):
    """Response model for bulk document deletion."""
    
    deleted_count: int = Field(..., description="Number of documents deleted")
    failed_ids: List[str] = Field(default_factory=list, description="IDs that failed to delete")
    message: str = Field(..., description="Operation status message")


class TreeGenerationRequest(BaseModel):
    """Request model for triggering tree generation on a document."""
    
    user_id: int = Field(..., description="User ID for authorization")


class TreeGenerationResponse(BaseModel):
    """Response model for tree generation status."""
    
    document_id: str = Field(..., description="Document identifier")
    status: Literal["processing", "completed", "failed", "pending"] = Field(..., description="Tree generation status")
    node_count: Optional[int] = Field(None, description="Number of nodes in tree")
    message: str = Field(..., description="Status message")


class ResumeFileInfo(BaseModel):
    """Model for uploaded resume file metadata."""

    id: str = Field(..., description="Resume file identifier")
    resume_id: str = Field(..., description="Human-readable resume identifier")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Processing status")
    created_at: str = Field(..., description="Upload timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")


class ResumeUploadResponse(BaseModel):
    """Response model for resume upload."""

    resume: ResumeFileInfo = Field(..., description="Uploaded resume metadata")


class ResumeListResponse(BaseModel):
    """Response model for resume listing."""

    list: List[ResumeFileInfo] = Field(default_factory=list, description="List of resumes")
    total: int = Field(..., description="Total resume count")


class ResumeAnalyzeRequest(BaseModel):
    """Request model for resume analysis."""

    user_id: int = Field(..., description="User ID")
    resume_id: str = Field(..., description="Resume identifier")
    job_description: str = Field(..., description="Job description text")


class ResumeAnalyzeResponse(BaseModel):
    """Response model for resume analysis."""

    analysis_id: str = Field(..., description="Analysis identifier")
    resume_id: str = Field(..., description="Resume identifier")
    overall_score: Optional[float] = Field(None, description="Overall score")
    job_description: Optional[str] = Field(None, description="Job description text")
    analysis: Dict[str, Any] = Field(..., description="Full analysis payload")
    refined_recommendations: Optional[Any] = Field(None, description="Extracted recommendations")
    refined_justifications: Optional[Any] = Field(None, description="Extracted justifications")
    resume_data: Optional[Dict[str, Any]] = Field(None, description="Extracted resume data")
    created_at: str = Field(..., description="Analysis timestamp")


class ResumeHistoryResponse(BaseModel):
    """Response model for resume analysis history."""

    list: List[ResumeAnalyzeResponse] = Field(default_factory=list, description="Analysis history")
    total: int = Field(..., description="Total analysis count")


class ResumeDashboardResponse(BaseModel):
    """Response model for resume dashboard metrics."""

    resume_stats: Dict[str, Any] = Field(..., description="Summary counts")
    monthly_stats: List[Dict[str, Any]] = Field(default_factory=list, description="Monthly breakdown")
    latest_analysis: Optional[ResumeAnalyzeResponse] = Field(None, description="Latest analysis")
