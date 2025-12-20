"""
Document management endpoints.
"""

import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from typing import Optional
from app.models.schemas import DocumentUploadResponse, DocumentListResponse, DocumentInfo
from app.services.document_processor import get_document_processor
from app.services.vector_store import get_vector_store_service
from app.utils.validators import validate_file_extension, validate_file_size
from app.utils.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(None)
):
    """
    Upload and process a document.
    
    Limits:
        - Max file size: 50 MB (configurable via MAX_UPLOAD_SIZE_MB)
        - Allowed types: .txt, .md, .pdf, .docx
    
    Args:
        file: Document file to upload
        title: Optional document title
        category: Optional document category
        
    Returns:
        DocumentUploadResponse with processing status
    """
    try:
        # Validate file extension
        if not validate_file_extension(file.filename, settings.allowed_file_extensions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(settings.allowed_file_extensions)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        file_size_mb = len(content) / (1024 * 1024)
        if not validate_file_size(len(content), settings.max_upload_size_mb):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large ({file_size_mb:.2f} MB). Maximum allowed: {settings.max_upload_size_mb} MB"
            )
        
        logger.info(
            "document_upload_started",
            filename=file.filename,
            size_bytes=len(content),
            size_mb=round(file_size_mb, 2),
            title=title,
        )
        
        # Process document
        doc_processor = get_document_processor()
        
        metadata = {}
        if title:
            metadata["title"] = title
        if category:
            metadata["category"] = category
        
        document_id, num_chunks = await doc_processor.ingest_file(
            file_content=content,
            filename=file.filename,
            metadata=metadata
        )
        
        logger.info(
            "document_upload_completed",
            document_id=document_id,
            filename=file.filename,
            num_chunks=num_chunks,
        )
        
        return DocumentUploadResponse(
            document_id=document_id,
            status="processed",
            chunks_created=num_chunks,
            message=f"Document '{file.filename}' successfully processed into {num_chunks} chunks"
        )
        
    except ValueError as e:
        logger.error("document_upload_validation_error", error=str(e), filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("document_upload_failed", error=str(e), filename=file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("/list", response_model=DocumentListResponse, status_code=status.HTTP_200_OK)
async def list_documents():
    """
    List all ingested documents.
    
    Returns:
        DocumentListResponse with list of documents
    """
    try:
        vector_store = get_vector_store_service()
        stats = vector_store.get_collection_stats()
        
        # Note: In a real implementation, we'd track documents separately
        # For now, we'll return collection statistics
        
        logger.info("documents_listed", total_chunks=stats.get("total_chunks", 0))
        
        return DocumentListResponse(
            documents=[],  # Would populate with actual document records
            total=0  # Would be actual document count
        )
        
    except Exception as e:
        logger.error("failed_to_list_documents", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str):
    """
    Delete a document and all its chunks.
    
    Args:
        document_id: Document identifier
    """
    try:
        doc_processor = get_document_processor()
        success = await doc_processor.delete_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        logger.info("document_deleted", document_id=document_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("document_deletion_failed", error=str(e), document_id=document_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
