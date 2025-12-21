"""
Document processing service for ingestion and chunking.
"""

import os
import hashlib
import tempfile
from typing import List, Optional, BinaryIO
from datetime import datetime
from pathlib import Path
import aiofiles
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from app.config import settings
from app.services.vector_store import get_vector_store_service
from app.services.bm25_service import get_bm25_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    """Service for processing and ingesting documents."""
    
    def __init__(self):
        """Initialize document processor."""
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        
        # Initialize node parser (text splitter)
        self.node_parser = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        
        # Storage for document metadata
        self.documents_dir = os.path.join(settings.data_dir, "documents")
        os.makedirs(self.documents_dir, exist_ok=True)
        
        logger.info(
            "document_processor_initialized",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
    
    def _generate_document_id(self, content: str, filename: str, user_id: Optional[int] = None) -> str:
        """
        Generate a unique document ID based on content hash and user_id.
        This prevents collisions when different users upload the same file.
        
        Args:
            content: Document content
            filename: Document filename
            user_id: User ID to ensure uniqueness across users
            
        Returns:
            Unique document identifier
        """
        # Include user_id in hash to prevent collisions between different users
        hash_input = f"{content}{filename}{user_id}" if user_id else content
        content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        return f"doc_{content_hash}"
    
    async def extract_text_from_file(
        self,
        file_content: bytes,
        filename: str
    ) -> str:
        """
        Extract text from various file formats using LlamaIndex readers.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            
        Returns:
            Extracted text content
        """
        # Create a temporary file with the correct extension
        file_extension = Path(filename).suffix.lower()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        try:
            # Use SimpleDirectoryReader to load the file
            # It automatically detects file type and uses appropriate reader
            reader = SimpleDirectoryReader(
                input_files=[tmp_file_path],
                filename_as_id=True
            )
            
            documents = reader.load_data()
            
            if not documents:
                raise ValueError(f"No text could be extracted from {filename}")
            
            # Combine all document text
            text = "\n\n".join(doc.text for doc in documents)
            
            logger.info(
                "text_extracted_from_file",
                filename=filename,
                file_type=file_extension,
                text_length=len(text)
            )
            
            return text
            
        except Exception as e:
            logger.error(
                "text_extraction_failed",
                filename=filename,
                file_type=file_extension,
                error=str(e)
            )
            raise ValueError(f"Failed to extract text from {filename}: {str(e)}")
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    async def process_text(
        self,
        text: str,
        filename: str,
        metadata: Optional[dict] = None
    ) -> tuple[str, List[TextNode]]:
        """
        Process raw text into chunks.
        
        Args:
            text: Raw text content
            filename: Source filename
            metadata: Additional metadata (must include user_id)
            
        Returns:
            Tuple of (document_id, list of TextNode objects)
        """
        try:
            # Ensure user_id is in metadata
            if not metadata or "user_id" not in metadata:
                raise ValueError("user_id is required in metadata for document processing")
            
            user_id = metadata.get("user_id")
            
            # Generate document ID with user_id to prevent collisions
            document_id = self._generate_document_id(text, filename, user_id)
            
            # Create LlamaIndex Document
            doc_metadata = {
                "filename": filename,
                "document_id": document_id,
                "upload_date": datetime.utcnow().isoformat(),
                "size_bytes": len(text.encode()),
                **(metadata or {})
            }
            
            document = Document(
                text=text,
                metadata=doc_metadata,
            )
            
            # Parse into nodes (chunks)
            nodes = self.node_parser.get_nodes_from_documents([document])
            
            # Convert to TextNode and add metadata
            text_nodes = []
            for idx, node in enumerate(nodes):
                text_node = TextNode(
                    text=node.text,
                    metadata={
                        **doc_metadata,
                        "chunk_id": f"{document_id}_chunk_{idx}",
                        "chunk_index": idx,
                    },
                    id_=f"{document_id}_chunk_{idx}",
                    ref_doc_id=document_id,  # Set ref_doc_id during initialization
                )
                text_nodes.append(text_node)
            
            logger.info(
                "document_processed",
                document_id=document_id,
                filename=filename,
                num_chunks=len(text_nodes),
                text_length=len(text),
                user_id=metadata.get("user_id"),
            )
            
            return document_id, text_nodes
            
        except Exception as e:
            logger.error("document_processing_failed", error=str(e), filename=filename)
            raise
    
    async def ingest_document(
        self,
        text: str,
        filename: str,
        metadata: Optional[dict] = None
    ) -> tuple[str, int]:
        """
        Process and ingest a document into the vector store and BM25 index.
        
        Args:
            text: Document text content
            filename: Source filename
            metadata: Additional metadata
            
        Returns:
            Tuple of (document_id, number of chunks created)
        """
        try:
            # Process document into chunks
            document_id, nodes = await self.process_text(text, filename, metadata)
            
            # Add to vector store
            vector_store = get_vector_store_service()
            vector_store.add_nodes(nodes)
            
            # Add to BM25 index
            bm25_service = get_bm25_service()
            bm25_service.add_nodes(nodes)
            
            logger.info(
                "document_ingested",
                document_id=document_id,
                filename=filename,
                num_chunks=len(nodes),
            )
            
            return document_id, len(nodes)
            
        except Exception as e:
            logger.error("document_ingestion_failed", error=str(e), filename=filename)
            raise
    
    async def ingest_file(
        self,
        file_content: bytes,
        filename: str,
        metadata: Optional[dict] = None
    ) -> tuple[str, int]:
        """
        Ingest a file (supports PDF, DOCX, TXT, MD, and more via LlamaIndex readers).
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            metadata: Additional metadata
            
        Returns:
            Tuple of (document_id, number of chunks created)
        """
        try:
            # Extract text using LlamaIndex readers
            text = await self.extract_text_from_file(file_content, filename)
            
            # Ingest the extracted text
            return await self.ingest_document(text, filename, metadata)
            
        except Exception as e:
            logger.error("file_ingestion_failed", error=str(e), filename=filename)
            raise
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks from both vector store and BM25 index.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful
        """
        try:
            # Delete from vector store
            vector_store = get_vector_store_service()
            vector_store.delete_document(document_id)
            
            # Delete from BM25 index
            from app.services.bm25_service import get_bm25_service
            bm25_service = get_bm25_service()
            bm25_success = bm25_service.delete_document(document_id)
            
            if not bm25_success:
                logger.warning(
                    "bm25_deletion_partial_failure",
                    document_id=document_id,
                    note="Vector store deleted but BM25 deletion had issues"
                )
            
            logger.info(
                "document_deleted",
                document_id=document_id,
                vector_deleted=True,
                bm25_deleted=bm25_success
            )
            return True
            
        except Exception as e:
            logger.error("document_deletion_failed", error=str(e), document_id=document_id)
            return False


# Global instance
_document_processor: Optional[DocumentProcessor] = None


def get_document_processor() -> DocumentProcessor:
    """Get or create the global document processor instance."""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor
