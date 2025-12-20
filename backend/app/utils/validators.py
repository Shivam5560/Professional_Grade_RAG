"""
Input validation utilities for the RAG system.
"""

import re
from typing import Optional


def sanitize_query(query: str) -> str:
    """
    Sanitize user query input.
    
    Args:
        query: Raw user query
        
    Returns:
        Sanitized query string
    """
    # Remove excessive whitespace
    query = " ".join(query.split())
    
    # Remove potentially harmful characters but keep punctuation
    query = re.sub(r'[^\w\s\?\.\,\!\-\'\"]', '', query)
    
    return query.strip()


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format.
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if valid format
    """
    # UUID v4 format or alphanumeric
    uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$'
    alphanum_pattern = r'^[a-zA-Z0-9_-]{8,64}$'
    
    return bool(re.match(uuid_pattern, session_id.lower()) or re.match(alphanum_pattern, session_id))


def validate_file_extension(filename: str, allowed_extensions: Optional[list] = None) -> bool:
    """
    Validate file extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (default: pdf, txt, md, docx)
        
    Returns:
        True if extension is allowed
    """
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.txt', '.md', '.docx', '.doc']
    
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)


def validate_file_size(size_bytes: int, max_size_mb: int = 50) -> bool:
    """
    Validate file size is within limits.
    
    Args:
        size_bytes: File size in bytes
        max_size_mb: Maximum allowed size in megabytes
        
    Returns:
        True if file size is within limit
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return size_bytes <= max_size_bytes
