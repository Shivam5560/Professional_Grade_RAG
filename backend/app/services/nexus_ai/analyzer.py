"""In-process Nexus resume analysis runner."""

import json
import random
import string
from typing import Dict

from fastapi import HTTPException

from app.services.groq_service import get_groq_service
from app.services.nexus_ai.services.resume_analyzer_service import PracticalResumeAnalyzer
from app.services.nexus_ai.services.query_service import generate_query_engine
from app.services.nexus_ai.services.recommendation_service import getRecommendations
from app.services.nexus_ai.templates.resume_template import TEMPLATE
from app.services.nexus_ai.templates.jd_template import JD_TEMPLATE
from app.services.nexus_ai.utils.text_util import advanced_ats_similarity, clean_text
from app.services.nexus_ai.utils.toon_util import decode_toon
from app.utils.logger import get_logger

logger = get_logger(__name__)

_EMPTY_RESPONSE_MARKERS = {"empty response"}

_RESUME_TOON_SCHEMA = """
personal_info:
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
key_responsibilities[0]:
"""

_JD_TOON_SCHEMA = """
job_title:
company_name:
location:
required_skills[0]:
required_experience_years:
key_responsibilities[0]:
other_qualifications[0]:
industry:
summary:
"""


def _is_empty_response(text: str) -> bool:
        if not text:
                return True
        stripped = text.strip()
        if not stripped:
                return True
        return stripped.lower() in _EMPTY_RESPONSE_MARKERS


def _trim_source(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
                return text
        head = text[: int(max_chars * 0.7)]
        tail = text[-int(max_chars * 0.3) :]
        return f"{head}\n...\n{tail}"


def _fallback_toon_extract(source_text: str, schema: str, label: str, max_chars: int) -> str:
        llm = get_groq_service().get_llm()
        trimmed = _trim_source(source_text, max_chars)
        prompt = (
                "Return TOON only. No markdown or code fences.\n\n"
                "Use this schema exactly:\n"
                f"{schema}\n"
                "\nSource text:\n"
                f"{trimmed}"
        )
        logger.warning("%s fallback prompt length: %s chars", label, len(prompt))
        response = llm.complete(prompt)
        return response.text or ""


def _convert_to_normal_types(data: Dict) -> Dict:
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


def _process_resume_documents(documents) -> str:
    texts = []
    for doc in documents:
        if hasattr(doc, "get_content") and callable(doc.get_content):
            texts.append(doc.get_content())
        elif hasattr(doc, "text"):
            texts.append(doc.text)
        elif hasattr(doc, "text_resource") and hasattr(doc.text_resource, "text"):
            texts.append(doc.text_resource.text)
    return "".join(texts)


def _process_job_description(jd: str) -> Dict:
    from llama_index.core.schema import QueryBundle
    
    jd_id = "".join(random.choices(string.ascii_letters + string.digits, k=10))
    retriever, documents_jd = generate_query_engine(jd, jd_id, read_from_text=True, jd=True)

    if not retriever or not documents_jd:
        raise HTTPException(status_code=400, detail="Query engine for job description failed")

    logger.info("Querying LLM for JD extraction")
    
    # Retrieve nodes
    nodes = retriever.retrieve(QueryBundle(query_str=JD_TEMPLATE[:200]))  # Use snippet as query
    
    # Build context from nodes
    context_str = "\n\n".join([node.node.get_content() for node in nodes])
    
    # Direct LLM call with full template (128k context model)
    llm = get_groq_service().get_llm()
    prompt = f"{JD_TEMPLATE}\n\nJob Description Text:\n{context_str}"
    logger.info(f"JD prompt length: {len(prompt)} chars")
    
    response_jd = llm.complete(prompt)
    
    logger.info(f"JD LLM response length: {len(response_jd.text)} chars")

    raw_jd = response_jd.text or ""
    if _is_empty_response(raw_jd):
        logger.warning("JD response empty; retrying with fallback prompt")
        raw_jd = _fallback_toon_extract(jd, _JD_TOON_SCHEMA, "JD", max_chars=8000)

    result = decode_toon(raw_jd)
    
    # Validate parsing succeeded
    if "_parse_error" in result:
        logger.error(f"JD TOON parsing failed: {result.get('_parse_error')}")
        logger.error(f"Raw JD response (first 1000 chars): {raw_jd[:1000]}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to parse job description from LLM response. The response may be truncated."
        )
    
    return result


def analyze_resume(abs_path: str, jd: str, resume_id: str) -> Dict:
    from llama_index.core.schema import QueryBundle
    
    analyzer = PracticalResumeAnalyzer()

    retriever, documents = generate_query_engine(abs_path, resume_id, read_from_text=False)
    if not retriever or not documents:
        raise HTTPException(status_code=400, detail="Failed to process documents")

    resume_text = _process_resume_documents(documents)

    logger.info("Querying LLM for resume extraction")
    
    # Retrieve nodes using template snippet as query
    nodes = retriever.retrieve(QueryBundle(query_str="extract resume information personal info education work experience"))
    logger.info(f"Retrieved {len(nodes)} nodes for resume")
    
    # Build context from nodes
    context_str = "\n\n".join([node.node.get_content() for node in nodes])
    
    # Direct LLM call with full templates (128k context model)
    llm = get_groq_service().get_llm()
    prompt = f"{TEMPLATE}\n\nResume Text:\n{context_str}"
    logger.info(f"Prompt length: {len(prompt)} chars")
    
    response = llm.complete(prompt)
    logger.info(f"LLM response length: {len(response.text)} chars")

    raw_resume = response.text or ""
    if _is_empty_response(raw_resume):
        logger.warning("Resume response empty; retrying with fallback prompt")
        raw_resume = _fallback_toon_extract(resume_text, _RESUME_TOON_SCHEMA, "Resume", max_chars=12000)

    response_text = clean_text(raw_resume)
    logger.info(f"Cleaned response length: {len(response_text)} chars")
    
    resume_dict = decode_toon(response_text)
    
    # Validate resume parsing succeeded
    if "_parse_error" in resume_dict:
        logger.error(f"Resume TOON parsing failed: {resume_dict.get('_parse_error')}")
        logger.error(f"Raw response (first 1000 chars): {raw_resume[:1000]}")
        logger.error(f"Cleaned text (first 1000 chars): {response_text[:1000]}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to parse resume from LLM response. The response may be truncated due to context limits."
        )

    job_description_dict = _process_job_description(jd)

    technical = advanced_ats_similarity(resume_dict, job_description_dict)
    technical = _convert_to_normal_types(technical)

    grammar_score, recommendations, section_scores, justifications = analyzer.analyze_resume(
        resume_text, resume_dict, industry=job_description_dict.get("industry", "default")
    )

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
    }

    logger.info("Calling getRecommendations to generate refined output")
    refined_out = getRecommendations(analysis_results)
    
    if isinstance(refined_out, dict):
        if "error" in refined_out:
            logger.error(f"Recommendation generation error: {refined_out.get('details')}")
        else:
            rec_count = len(refined_out.get("refined_recommendations", []))
            just_count = len(refined_out.get("refined_justifications", []))
            logger.info(f"Generated {rec_count} recommendations, {just_count} justifications")
        
        analysis_results.update(refined_out)
    else:
        logger.warning(f"getRecommendations returned non-dict: {type(refined_out)}")

    return analysis_results
