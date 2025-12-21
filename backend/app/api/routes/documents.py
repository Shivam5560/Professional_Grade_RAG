"""
Document management endpoints.
"""

import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.models.schemas import (
    DocumentUploadResponse, 
    DocumentListResponse, 
    DocumentInfo,
    UserDocumentResponse,
    BulkDeleteRequest,
    BulkDeleteResponse
)
from app.services.document_processor import get_document_processor
from app.services.vector_store import get_vector_store_service
from app.utils.validators import validate_file_extension, validate_file_size
from app.utils.logger import get_logger
from app.config import settings
from app.db.database import get_db
from app.db.models import Document

logger = get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    title: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document for a specific user.
    
    Limits:
        - Max file size: 50 MB (configurable via MAX_UPLOAD_SIZE_MB)
        - Allowed types: .txt, .md, .pdf, .docx
    
    Args:
        file: Document file to upload
        user_id: ID of the user uploading the document
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
            user_id=user_id,
        )
        
        # Process document
        doc_processor = get_document_processor()
        
        metadata = {
            "user_id": user_id,  # Critical: store user_id in metadata
        }
        if title:
            metadata["title"] = title
        if category:
            metadata["category"] = category
        
        document_id, num_chunks = await doc_processor.ingest_file(
            file_content=content,
            filename=file.filename,
            metadata=metadata
        )
        
        # Save document metadata to database
        file_extension = Path(file.filename).suffix.lower()
        db_document = Document(
            id=document_id,
            user_id=user_id,
            filename=file.filename,
            file_size=len(content),
            file_type=file_extension,
            vector_count=num_chunks,
            title=title,
            category=category,
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        logger.info(
            "document_upload_completed",
            document_id=document_id,
            filename=file.filename,
            num_chunks=num_chunks,
            user_id=user_id,
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


@router.get("/my-documents/{user_id}", response_model=UserDocumentResponse, status_code=status.HTTP_200_OK)
async def get_user_documents(user_id: int, db: Session = Depends(get_db)):
    """
    Get all documents uploaded by a specific user.
    
    Args:
        user_id: User identifier
        
    Returns:
        UserDocumentResponse with list of user's documents
    """
    try:
        # Query documents for this user
        documents = db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).all()
        
        document_list = []
        for doc in documents:
            document_list.append(DocumentInfo(
                id=doc.id,
                filename=doc.filename,
                title=doc.title,
                file_type=doc.file_type,
                file_size=doc.file_size,
                vector_count=doc.vector_count,
                category=doc.category,
                upload_date=doc.created_at.isoformat() if doc.created_at else "",
            ))
        
        logger.info("user_documents_listed", user_id=user_id, total=len(document_list))
        
        return UserDocumentResponse(
            documents=document_list,
            total=len(document_list)
        )
        
    except Exception as e:
        logger.error("failed_to_list_user_documents", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.post("/bulk-delete", response_model=BulkDeleteResponse, status_code=status.HTTP_200_OK)
async def bulk_delete_documents(request: BulkDeleteRequest, db: Session = Depends(get_db)):
    """
    Delete multiple documents belonging to a user.
    
    Args:
        request: BulkDeleteRequest with document IDs and user ID
        
    Returns:
        BulkDeleteResponse with deletion results
    """
    try:
        deleted_count = 0
        failed_ids = []
        doc_processor = get_document_processor()
        
        for document_id in request.document_ids:
            # Verify document belongs to user
            db_document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == request.user_id
            ).first()
            
            if not db_document:
                logger.warning(
                    "document_not_found_or_unauthorized",
                    document_id=document_id,
                    user_id=request.user_id
                )
                failed_ids.append(document_id)
                continue
            
            try:
                # Delete from vector store
                success = await doc_processor.delete_document(document_id)
                
                if success:
                    # Delete from database
                    db.delete(db_document)
                    db.commit()
                    deleted_count += 1
                    logger.info(
                        "document_deleted",
                        document_id=document_id,
                        user_id=request.user_id
                    )
                else:
                    failed_ids.append(document_id)
                    
            except Exception as e:
                logger.error(
                    "document_deletion_failed",
                    document_id=document_id,
                    error=str(e)
                )
                failed_ids.append(document_id)
        
        message = f"Successfully deleted {deleted_count} document(s)"
        if failed_ids:
            message += f". Failed to delete {len(failed_ids)} document(s)"
        
        return BulkDeleteResponse(
            deleted_count=deleted_count,
            failed_ids=failed_ids,
            message=message
        )
        
    except Exception as e:
        logger.error("bulk_deletion_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}"
        )


@router.get("/list", response_model=DocumentListResponse, status_code=status.HTTP_200_OK)
async def list_documents():
    """
    List all ingested documents (legacy endpoint).
    
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
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete a document and all its chunks.
    
    Args:
        document_id: Document identifier
    """
    try:
        # Delete from database first
        db_document = db.query(Document).filter(Document.id == document_id).first()
        if db_document:
            db.delete(db_document)
            db.commit()
        
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
