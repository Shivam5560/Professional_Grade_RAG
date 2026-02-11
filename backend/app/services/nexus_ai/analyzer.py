"""In-process Nexus resume analysis runner.

Optimized for exactly 3 LLM calls per analysis:
  1. Resume extraction (TOON format)
  2. JD extraction (TOON format)  
  3. Recommendations generation

Uses the unified RAG provider factory for LLM access.
"""

import random
import string
import time
from typing import Dict, Optional

from fastapi import HTTPException

from app.services.rag_provider_factory import get_llm
from app.services.nexus_ai.services.resume_analyzer_service import PracticalResumeAnalyzer
from app.services.nexus_ai.services.query_service import generate_query_engine
from app.services.nexus_ai.services.recommendation_service import getRecommendations
from app.services.nexus_ai.templates.resume_template import TEMPLATE
from app.services.nexus_ai.templates.jd_template import JD_TEMPLATE
from app.services.nexus_ai.utils.text_util import advanced_ats_similarity, clean_text
from app.services.nexus_ai.utils.toon_util import decode_toon
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # seconds

# Minimal schema for recovery parsing
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
industry:
summary:"""


def _convert_to_normal_types(data: Dict) -> Dict:
    """Convert numpy types to native Python types recursively."""
    new_data: Dict = {}
    for key, value in data.items():
        if hasattr(value, "item"):
            new_data[key] = value.item()
        elif isinstance(value, dict):
            new_data[key] = _convert_to_normal_types(value)
        elif isinstance(value, list):
            new_data[key] = [item.item() if hasattr(item, "item") else item for item in value]
        else:
            new_data[key] = value
    return new_data


def _extract_response_text(response) -> str:
    """Best-effort extraction of LLM text across response shapes."""
    text = getattr(response, "text", "") or ""
    if text.strip():
        return text

    raw = getattr(response, "raw", None)
    if isinstance(raw, dict):
        choices = raw.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content") or ""
            if content.strip():
                logger.warning("LLM response text empty; using raw content fallback")
                return content

    message = getattr(response, "message", None)
    if message is not None:
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            logger.warning("LLM response text empty; using message content fallback")
            return content

    return text


def _process_resume_documents(documents) -> str:
    """Extract raw text from document objects."""
    texts = []
    for doc in documents:
        if hasattr(doc, "get_content") and callable(doc.get_content):
            texts.append(doc.get_content())
        elif hasattr(doc, "text"):
            texts.append(doc.text)
        elif hasattr(doc, "text_resource") and hasattr(doc.text_resource, "text"):
            texts.append(doc.text_resource.text)
    return "".join(texts)


def _extract_resume(resume_text: str, context_str: str) -> Dict:
    """
    LLM Call #1: Extract structured resume data.
    Uses a robust prompt that includes fallback instructions inline.
    Includes retry logic for transient LLM failures.
    """
    llm = get_llm()
    
    # Robust prompt with schema inline to avoid fallback calls
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
{context_str if context_str else resume_text[:15000]}"""
    
    logger.info(f"Resume extraction prompt: {len(prompt)} chars")
    
    # Retry loop for transient LLM failures
    last_error = None
    raw_response = ""
    for attempt in range(MAX_RETRIES):
        try:
            response = llm.complete(prompt)
            raw_response = _extract_response_text(response)
            
            logger.info(f"Resume LLM response: {len(raw_response)} chars (attempt {attempt + 1})")
            
            if raw_response.strip():
                break
            
            # Empty response - retry with backoff
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"Empty LLM response, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"LLM call failed: {e}, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM call failed after {MAX_RETRIES} retries: {str(last_error)}"
                )
    
    if not raw_response.strip():
        raise HTTPException(
            status_code=500,
            detail=f"LLM returned empty response for resume extraction after {MAX_RETRIES} attempts"
        )
    
    # Clean any accidental markdown fences
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


def _extract_jd(jd_text: str, context_str: str) -> Dict:
    """
    LLM Call #2: Extract structured job description data.
    Uses a robust prompt that includes fallback instructions inline.
    Includes retry logic for transient LLM failures.
    """
    llm = get_llm()
    
    # Robust prompt with schema inline to avoid fallback calls
    prompt = f"""{JD_TEMPLATE}

CRITICAL OUTPUT RULES:
- Return ONLY valid TOON format (indented key: value pairs)
- NO markdown code fences (no ```toon or ```)
- NO JSON format
- Use empty string "" for missing fields
- Use empty array notation for missing lists

TOON SCHEMA TO FOLLOW:
{_JD_TOON_SCHEMA}

Job Description Text:
{context_str if context_str else jd_text[:15000]}"""

    # Shorter fallback prompt for retries if the full template yields empty output
    fallback_prompt = f"""
Extract job description data into TOON format. Use ONLY explicit info.

Output rules:
- TOON format only
- No markdown code fences
- Empty string "" for missing fields
- Empty array notation for missing lists

TOON schema:
{_JD_TOON_SCHEMA}

Job Description Text:
{context_str if context_str else jd_text[:15000]}
"""
    
    logger.info(f"JD extraction prompt: {len(prompt)} chars")
    
    # Retry loop for transient LLM failures
    last_error = None
    raw_response = ""
    for attempt in range(MAX_RETRIES):
        try:
            prompt_to_use = prompt if attempt == 0 else fallback_prompt
            response = llm.complete(prompt_to_use)
            raw_response = _extract_response_text(response)
            
            logger.info(f"JD LLM response: {len(raw_response)} chars (attempt {attempt + 1})")
            
            if raw_response.strip():
                break
            
            # Empty response - retry with backoff
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"Empty LLM response for JD, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"LLM call failed for JD: {e}, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM call failed for JD after {MAX_RETRIES} retries: {str(last_error)}"
                )
    
    if not raw_response.strip():
        raise HTTPException(
            status_code=500,
            detail=f"LLM returned empty response for JD extraction after {MAX_RETRIES} attempts"
        )
    
    # Clean any accidental markdown fences
    cleaned = clean_text(raw_response)
    result = decode_toon(cleaned)
    
    if "_parse_error" in result:
        logger.error(f"JD TOON parse error: {result.get('_parse_error')}")
        logger.error(f"First 500 chars: {cleaned[:500]}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse JD extraction. LLM response format invalid."
        )
    
    return result


def analyze_resume(abs_path: str, jd: str, resume_id: str, cached_resume_data: Optional[Dict] = None) -> Dict:
    """
    Main resume analysis entry point.
    
    Performs 2-3 LLM calls per analysis:
      1. Resume extraction (SKIPPED if cached_resume_data provided)
      2. JD extraction
      3. Recommendations generation
    
    Technical scoring and grammar analysis are done algorithmically (no LLM).
    
    Args:
        abs_path: Path to resume file
        jd: Job description text
        resume_id: Unique resume identifier
        cached_resume_data: If provided, skips LLM Call #1 (for subsequent analyses)
    
    Returns:
        Dict with analysis results and `_extracted_resume_data` key for caching
    """
    from llama_index.core.schema import QueryBundle
    
    analyzer = PracticalResumeAnalyzer()

    # --- Step 1: Load and chunk resume ---
    retriever, documents = generate_query_engine(abs_path, resume_id, read_from_text=False)
    if not retriever or not documents:
        raise HTTPException(status_code=400, detail="Failed to process resume document")

    resume_text = _process_resume_documents(documents)
    
    # Check if we can use cached resume data
    if cached_resume_data and isinstance(cached_resume_data, dict) and len(cached_resume_data) > 0:
        logger.info("Using cached resume extraction (skipping LLM Call #1)")
        resume_dict = cached_resume_data
    else:
        # Retrieve relevant chunks for context
        nodes = retriever.retrieve(QueryBundle(
            query_str="extract resume information personal info education work experience skills projects"
        ))
        logger.info(f"Retrieved {len(nodes)} resume chunks")
        context_str = "\n\n".join([node.node.get_content() for node in nodes])

        # --- LLM CALL #1: Resume extraction ---
        logger.info("LLM Call #1: Resume extraction")
        resume_dict = _extract_resume(resume_text, context_str)
    
    # --- Step 2: Load and chunk JD ---
    jd_id = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    jd_retriever, jd_documents = generate_query_engine(jd, jd_id, read_from_text=True, jd=True)
    
    if not jd_retriever or not jd_documents:
        raise HTTPException(status_code=400, detail="Failed to process job description")
    
    # Retrieve relevant chunks for context
    jd_nodes = jd_retriever.retrieve(QueryBundle(
        query_str="extract job requirements skills responsibilities qualifications"
    ))
    logger.info(f"Retrieved {len(jd_nodes)} JD chunks")
    jd_context_str = "\n\n".join([node.node.get_content() for node in jd_nodes])

    # --- LLM CALL #2: JD extraction ---
    logger.info("LLM Call #2: JD extraction")
    job_description_dict = _extract_jd(jd, jd_context_str)

    # --- Step 3: Technical scoring (algorithmic, no LLM) ---
    logger.info("Computing technical score (algorithmic)")
    technical = advanced_ats_similarity(resume_dict, job_description_dict)
    technical = _convert_to_normal_types(technical)

    # --- Step 4: Grammar analysis (algorithmic, no LLM) ---
    logger.info("Computing grammar score (algorithmic)")
    grammar_score, recommendations, section_scores, justifications = analyzer.analyze_resume(
        resume_text, resume_dict, industry=job_description_dict.get("industry", "default")
    )

    # --- Step 5: Calculate overall score ---
    overall_score = (technical["similarity_score"] * 0.55 + grammar_score * 0.45)
    overall_score = min(round(overall_score, 2), 100)

    analysis_results = {
        "overall_score": overall_score,
        "technical_score": technical,
        "grammar_analysis": {
            "score": grammar_score,
            "recommendations": recommendations,
            "section_scores": section_scores,
        },
        "justifications": justifications,
        "resume_data": dict(resume_dict),
        "jd_data": dict(job_description_dict),
    }

    # --- LLM CALL #3: Generate recommendations ---
    logger.info("LLM Call #3: Generate recommendations")
    refined_out = getRecommendations(analysis_results)
    
    if isinstance(refined_out, dict):
        if "error" in refined_out:
            logger.error(f"Recommendation error: {refined_out.get('details')}")
        else:
            rec_count = len(refined_out.get("refined_recommendations", []))
            just_count = len(refined_out.get("refined_justifications", []))
            logger.info(f"Generated {rec_count} recommendations, {just_count} justifications")
        
        analysis_results.update(refined_out)
    else:
        logger.warning(f"getRecommendations returned non-dict: {type(refined_out)}")

    # Include extracted resume data for caching (only if we did the extraction this time)
    if not cached_resume_data:
        analysis_results["_extracted_resume_data"] = dict(resume_dict)

    logger.info(f"Analysis complete. Overall score: {overall_score}")
    return analysis_results
