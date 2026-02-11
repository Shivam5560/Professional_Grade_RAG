"""
Simplified resume/JD text extraction and LLM processing.

No retriever, no chunking, no embeddings for analysis.
Direct text extraction + direct LLM calls.
"""

import time
from typing import Dict, Optional
from pathlib import Path

from fastapi import HTTPException

from app.services.rag_provider_factory import get_nexus_llm
from app.services.nexus_ai.templates.resume_template import TEMPLATE
from app.services.nexus_ai.templates.jd_template import JD_TEMPLATE
from app.services.nexus_ai.utils.text_util import clean_text
from app.services.nexus_ai.utils.toon_util import decode_toon
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.5  # seconds

# TOON schemas for prompts
_RESUME_TOON_SCHEMA = """personal_info:
    name:
    email:
    phone:
education[0]:
    degree:
    institution:
    graduation_date:
work_experience[0]:
    job_title:
    company:
    dates:
    responsibilities[0]:
keywords[0]:
projects[0]:
    name:
    description[0]:
certifications[0]:
    name:
    description:
summary:
key_responsibilities[0]:"""

_JD_TOON_SCHEMA = """job_title:
company_name:
location:
required_skills[0]:
required_experience_years:
key_responsibilities[0]:
other_qualifications[0]:
industry: tech
summary:"""


def extract_text_from_file(filepath: str) -> str:
    """
    Extract raw text from resume file (PDF, DOCX, TXT).
    No chunking, no embeddings - just raw text.
    """
    path = Path(filepath)
    ext = path.suffix.lower()
    
    try:
        if ext == ".pdf":
            import fitz  # PyMuPDF
            doc = fitz.open(filepath)
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            doc.close()
            return "\n".join(text_parts)
        
        elif ext in (".docx", ".doc"):
            from docx import Document
            doc = Document(filepath)
            return "\n".join([para.text for para in doc.paragraphs])
        
        elif ext == ".txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    
    except ImportError as e:
        logger.error(f"Missing dependency for {ext}: {e}")
        raise HTTPException(status_code=500, detail=f"Cannot process {ext} files: missing dependency")
    except Exception as e:
        logger.error(f"Failed to extract text from {filepath}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")


def _call_llm_with_retry(prompt: str, description: str) -> str:
    """
    Call LLM with retry logic. Returns raw response text.
    """
    llm = get_nexus_llm()
    model_name = getattr(llm, "model", "unknown")
    
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"{description}: attempt {attempt + 1}, model={model_name}, prompt length {len(prompt)} chars")
            response = llm.complete(prompt)
            
            # Extract text from response
            text = getattr(response, "text", "") or ""
            
            # Fallback to raw content if text is empty
            if not text.strip():
                raw = getattr(response, "raw", None)
                if isinstance(raw, dict):
                    choices = raw.get("choices") or []
                    if choices:
                        message = choices[0].get("message") or {}
                        text = message.get("content") or ""
            
            logger.info(f"{description}: got {len(text)} chars (attempt {attempt + 1})")

            if not text.strip():
                raw = getattr(response, "raw", None)
                if raw is not None:
                    logger.warning(f"{description}: empty text; raw response keys={list(raw.keys()) if isinstance(raw, dict) else type(raw)}")
            
            if text.strip():
                return text
            
            # Empty response - retry with backoff
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"{description}: empty response, retrying in {delay}s")
                time.sleep(delay)
                
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"{description}: error {e}, retrying in {delay}s")
                time.sleep(delay)
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"{description} failed after {MAX_RETRIES} attempts: {str(last_error)}"
                )
    
    raise HTTPException(
        status_code=500,
        detail=f"{description}: empty response after {MAX_RETRIES} attempts"
    )


def extract_resume_data(resume_text: str) -> Dict:
    """
    Extract structured data from resume text using LLM.
    Called ONCE on upload, result is cached in DB.
    """
    # Limit text to avoid token overflow (leave room for prompt + response)
    max_chars = 50000  # ~12k tokens, safe for 128k context
    trimmed_text = resume_text[:max_chars] if len(resume_text) > max_chars else resume_text
    
    prompt = f"""{TEMPLATE}

CRITICAL OUTPUT RULES:
- Return ONLY valid TOON format (indented key: value pairs)
- NO markdown code fences (no ```toon or ```)
- NO JSON format
- Use empty string "" for missing fields
- Use empty array notation for missing lists

TOON SCHEMA TO FOLLOW:
{_RESUME_TOON_SCHEMA}

Resume Text:
{trimmed_text}"""
    
    raw_response = _call_llm_with_retry(prompt, "Resume extraction")
    
    # Clean and parse
    cleaned = clean_text(raw_response)
    result = decode_toon(cleaned)
    
    if "_parse_error" in result:
        logger.error(f"Resume TOON parse error: {result.get('_parse_error')}")
        logger.error(f"First 500 chars: {cleaned[:500]}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse resume extraction. LLM response format invalid."
        )
    
    return result


def extract_jd_data(jd_text: str) -> Dict:
    """
    Extract structured data from job description text using LLM.
    Called each time during analysis.
    """
    # Limit text
    max_chars = 30000
    trimmed_text = jd_text[:max_chars] if len(jd_text) > max_chars else jd_text
    
    # Use shorter prompt for JD (less complex than resume)
    prompt = f"""Extract job description details into TOON format.

CRITICAL RULES:
- TOON format only (key: value pairs with indentation for nesting)
- NO markdown code fences
- NO JSON
- Extract ALL skills, responsibilities, qualifications mentioned
- Use empty string "" for missing fields

TOON SCHEMA:
{_JD_TOON_SCHEMA}

Job Description:
{trimmed_text}"""
    
    raw_response = _call_llm_with_retry(prompt, "JD extraction")
    
    # Clean and parse
    cleaned = clean_text(raw_response)
    result = decode_toon(cleaned)
    
    if "_parse_error" in result:
        logger.error(f"JD TOON parse error: {result.get('_parse_error')}")
        # For JD, return minimal structure on parse error instead of failing
        logger.warning("Returning minimal JD structure due to parse error")
        return {
            "job_title": "",
            "company_name": "",
            "required_skills": [],
            "key_responsibilities": [],
            "industry": "tech",
            "summary": jd_text[:1000]
        }
    
    return result
