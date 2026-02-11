"""
Main resume analyzer - LLM extraction + hybrid algorithmic scoring.
Clean architecture with comprehensive similarity analysis.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, List

from app.services.nexus_ai.core.prompts import build_analysis_prompt
from app.services.nexus_ai.core.scorers_v2 import (
    compute_technical_score,
    compute_ats_score,
    compute_grammar_score,
    compute_section_score,
    compute_overall_score,
)
from app.services.nexus_ai.core.similarity import (
    compute_ensemble_similarity,
    analyze_technical_gaps,
)
from app.services.rag_provider_factory import get_nexus_llm

logger = logging.getLogger(__name__)


async def analyze_resume_v2(
    resume_text: str,
    job_description: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Complete resume analysis with LLM extraction + hybrid algorithmic scoring.
    
    Flow:
    1. LLM call → JSON response with extraction + recommendations
    2. Ensemble similarity (BM25 + TF-IDF + Jaccard + Cosine + Skill match)
    3. ATS, Grammar, Section scoring (algorithmic)
    4. Technical gap analysis with learning paths
    5. Hybrid scoring (combine LLM insights with algorithmic scores)
    
    Returns:
        Complete analysis result with detailed scores and gap analysis
    """
    logger.info("Starting resume analysis v2 (hybrid)")
    
    # Step 1: Get LLM analysis (extraction + recommendations)
    llm_result = await _call_llm_for_analysis(
        resume_text, job_description, max_retries
    )
    
    if not llm_result:
        return _error_response("Failed to get LLM analysis after retries")
    
    # Extract data from LLM response
    resume_data = llm_result.get("resume_analysis", {})
    job_data = llm_result.get("job_analysis", {})
    
    candidate_skills = resume_data.get("skills", [])
    required_skills = job_data.get("required_skills", [])
    preferred_skills = job_data.get("preferred_skills", [])
    
    # Step 2: Compute ensemble similarity (BM25 + TF-IDF + Jaccard + Cosine + Skill)
    ensemble_result = compute_ensemble_similarity(
        resume_text=resume_text,
        jd_text=job_description,
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )
    
    # Step 3: Compute algorithmic scores
    technical = compute_technical_score(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        jd_text=job_description
    )
    
    ats = compute_ats_score(resume_text, job_description)
    grammar = compute_grammar_score(resume_text)
    
    section_assessment = llm_result.get("section_assessment", {})
    sections = compute_section_score(section_assessment)
    
    # Step 4: Technical gap analysis
    experience_years = _extract_experience_years(resume_data)
    gap_analysis = analyze_technical_gaps(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        candidate_experience_years=experience_years,
        job_title=job_data.get("title", "")
    )
    
    # Step 5: Hybrid scoring - combine ensemble similarity with algorithmic scores
    # Use ensemble for technical, keep algorithmic for others
    hybrid_technical = (ensemble_result["similarity_score"] * 0.6 + technical["score"] * 0.4)
    
    overall = compute_overall_score(
        technical_score=hybrid_technical,
        ats_score=ats["score"],
        grammar_score=grammar["score"],
        section_score=sections["score"]
    )
    
    # Build final result with comprehensive data
    result = {
        "success": True,
        "scores": {
            "overall": overall["overall_score"],
            "fit_category": overall["fit_category"],
            "fit_description": overall.get("fit_description", ""),
            "breakdown": overall["breakdown"]
        },
        "candidate": {
            "name": resume_data.get("name"),
            "email": resume_data.get("email"),
            "phone": resume_data.get("phone"),
            "location": resume_data.get("location"),
            "summary": resume_data.get("summary"),
            "experience_years": experience_years,
        },
        
        # Technical similarity breakdown (ensemble)
        "technical_score": {
            "similarity_score": round(hybrid_technical, 1),
            "ensemble_score": ensemble_result["similarity_score"],
            "algorithmic_score": technical["score"],
            "breakdown": ensemble_result["breakdown"],
            "matched_skills": [m["skill"] if isinstance(m, dict) else m for m in ensemble_result.get("matched_skills", [])],
            "missing_skills": [m["skill"] if isinstance(m, dict) else m for m in ensemble_result.get("missing_skills", [])],
            "matched_preferred": [m["skill"] if isinstance(m, dict) else m for m in ensemble_result.get("matched_preferred", [])],
            "category_scores": ensemble_result.get("category_scores", {}),
            "bm25_score": ensemble_result["breakdown"]["bm25"]["score"],
            "tfidf_score": ensemble_result["breakdown"]["tfidf"]["score"],
            "jaccard_score": ensemble_result["breakdown"]["jaccard"]["score"],
            "cosine_score": ensemble_result["breakdown"]["cosine"]["score"],
            "skill_match_score": ensemble_result["breakdown"]["skill_match"]["score"],
        },
        
        # Technical gap analysis
        "gap_analysis": {
            "severity": gap_analysis["gap_severity"],
            "total_gaps": gap_analysis["total_gaps"],
            "missing_required": gap_analysis["missing_required"],
            "missing_preferred": gap_analysis["missing_preferred"],
            "gaps_by_category": gap_analysis["gaps_by_category"],
            "seniority_assessment": gap_analysis["seniority_assessment"],
            "action_items": gap_analysis["action_items"],
            "summary": gap_analysis["summary"],
        },
        
        "skills_analysis": {
            "candidate_skills": candidate_skills,
            "matched_skills": [m["skill"] if isinstance(m, dict) else m for m in ensemble_result.get("matched_skills", [])],
            "missing_skills": [m["skill"] if isinstance(m, dict) else m for m in ensemble_result.get("missing_skills", [])],
            "matched_preferred": [m["skill"] if isinstance(m, dict) else m for m in ensemble_result.get("matched_preferred", [])],
            "technical_score": round(hybrid_technical, 1),
            "category_breakdown": ensemble_result.get("category_scores", {}),
        },
        
        "job_analysis": job_data,
        "match_analysis": llm_result.get("match_analysis", {}),
        
        "ats_analysis": {
            "score": ats["score"],
            "keyword_match": ats["keyword_match_score"],
            "section_coverage": ats["section_score"],
            "formatting_score": ats["formatting_score"],
            "contact_score": ats["contact_score"],
            "matched_keywords": ats["matched_keywords"],
            "sections_missing": ats["sections_missing"],
            "formatting_issues": ats["formatting_issues"],
            "all_issues": ats.get("all_issues", []),
            "components": ats.get("components", {}),
            "llm_feedback": llm_result.get("ats_feedback", {})
        },
        
        "grammar_analysis": {
            "score": grammar["score"],
            "clarity_score": grammar["clarity_score"],
            "action_verbs_used": grammar["action_verbs_used"],
            "quantified_achievements": grammar["quantified_achievements"],
            "passive_voice_issues": grammar["passive_voice_issues"],
            "spelling_issues": grammar.get("spelling_issues", []),
            "readability_scores": grammar.get("readability_scores", {}),
            "bullet_analysis": grammar.get("bullet_analysis", {}),
            "components": grammar.get("components", {}),
            "recommendations": grammar["suggestions"],
            "section_scores": {},
        },
        
        "section_analysis": {
            "score": sections["score"],
            "sections": sections["sections"],
            "summary": sections.get("summary", ""),
        },
        
        "recommendations": _format_recommendations(
            llm_result.get("recommendations", [])
        ),
        
        "resume_data": {
            "name": resume_data.get("name"),
            "email": resume_data.get("email"),
            "phone": resume_data.get("phone"),
            "skills": candidate_skills,
            "experience": resume_data.get("experience", []),
            "education": resume_data.get("education", []),
            "certifications": resume_data.get("certifications", []),
        },
        
        "jd_data": job_data,
        
        "experience": resume_data.get("experience", []),
        "education": resume_data.get("education", []),
        "certifications": resume_data.get("certifications", []),
    }
    
    logger.info(f"Analysis complete. Overall score: {overall['overall_score']}, Fit: {overall['fit_category']}")
    return result


def _extract_experience_years(resume_data: Dict[str, Any]) -> float:
    """Extract total years of experience from resume data."""
    # Check if directly provided
    if "experience_years" in resume_data:
        try:
            return float(resume_data["experience_years"])
        except (ValueError, TypeError):
            pass
    
    # Calculate from experience entries
    experience = resume_data.get("experience", [])
    if not experience:
        return 0.0
    
    total_months = 0
    current_year = 2026  # Current year
    
    for exp in experience:
        duration = exp.get("duration", "")
        # Try to parse duration (e.g., "2020 - Present", "Jan 2020 - Dec 2022")
        if "present" in duration.lower() or "current" in duration.lower():
            # Approximate months from start to now
            years_match = re.search(r'(\d{4})', duration)
            if years_match:
                start_year = int(years_match.group(1))
                total_months += (current_year - start_year) * 12
        else:
            # Try to find two years
            years = re.findall(r'(\d{4})', duration)
            if len(years) >= 2:
                try:
                    start = int(years[0])
                    end = int(years[1])
                    total_months += (end - start) * 12
                except ValueError:
                    pass
    
    return round(total_months / 12, 1)
    return result


async def _call_llm_for_analysis(
    resume_text: str,
    job_description: str,
    max_retries: int
) -> Optional[Dict[str, Any]]:
    """
    Make single LLM call and parse JSON response.
    Includes retry logic with exponential backoff.
    """
    prompt = build_analysis_prompt(resume_text, job_description)
    prompt_length = len(prompt)
    logger.info(f"Built analysis prompt: {prompt_length} chars, resume: {len(resume_text)} chars, jd: {len(job_description)} chars")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"LLM call attempt {attempt + 1}/{max_retries}")
            
            llm = get_nexus_llm()
            response = await llm.acomplete(prompt)
            
            # Log response object details
            logger.debug(f"Response type: {type(response)}, has text: {hasattr(response, 'text')}, has raw: {hasattr(response, 'raw')}, has delta: {hasattr(response, 'delta')}")
            
            # Extract response text - try multiple approaches
            response_text = ""
            
            # Approach 1: Direct text attribute (llama-index style)
            if hasattr(response, 'text'):
                text_val = response.text
                if text_val and text_val.strip():  # Check for non-empty after stripping
                    response_text = text_val
                    logger.debug(f"Got response via .text attribute, length={len(response_text)}")
            
            # Approach 2: Check for delta/content (streaming response)
            if not response_text and hasattr(response, 'delta'):
                delta_val = response.delta
                if delta_val and delta_val.strip():
                    response_text = delta_val
                    logger.debug(f"Got response via .delta attribute, length={len(response_text)}")
            
            # Approach 3: Raw OpenAI-style response
            if not response_text and hasattr(response, 'raw'):
                raw = response.raw
                if hasattr(raw, 'choices') and raw.choices:
                    choice = raw.choices[0]
                    
                    # Check finish_reason for token limit issues
                    finish_reason = getattr(choice, 'finish_reason', None)
                    if finish_reason == 'length':
                        logger.error(f"LLM hit token limit (finish_reason=length). Consider increasing max_tokens or using a different model.")
                    
                    if hasattr(choice, 'message'):
                        message = choice.message
                        # Try content first
                        if hasattr(message, 'content'):
                            content_val = message.content
                            if content_val and content_val.strip():
                                response_text = content_val
                                logger.debug(f"Got response via .raw.choices.message.content, length={len(response_text)}")
                        
                        # If content is empty but reasoning exists (reasoning models), log warning
                        if not response_text and hasattr(message, 'reasoning'):
                            reasoning = message.reasoning
                            if reasoning:
                                logger.warning(f"Model spent {len(reasoning)} chars on reasoning but returned empty content. This model may not be suitable for JSON generation.")
                                logger.warning(f"Reasoning preview: {reasoning[:500]}...")
                    
                    if not response_text and hasattr(choice, 'text'):
                        text_val = choice.text
                        if text_val and text_val.strip():
                            response_text = text_val
                            logger.debug(f"Got response via .raw.choices.text, length={len(response_text)}")
            
            # Approach 4: String representation as last resort
            if not response_text:
                response_str = str(response)
                if response_str and response_str != "None" and len(response_str) > 50:
                    response_text = response_str
                    logger.debug(f"Got response via str(), length={len(response_text)}")
            
            if not response_text:
                logger.warning(f"Empty response on attempt {attempt + 1}, response type: {type(response)}, attrs: {[a for a in dir(response) if not a.startswith('_')][:10]}")
                if hasattr(response, 'text'):
                    logger.warning(f"response.text value: {repr(response.text)}, type: {type(response.text)}")
                if hasattr(response, 'raw'):
                    logger.warning(f"response.raw: {response.raw}")
                continue
            
            # Log response preview
            logger.info(f"Got LLM response: {len(response_text)} chars, first 200: {response_text[:200]}")
            
            # Parse JSON
            parsed = _parse_json_response(response_text)
            if parsed:
                logger.info(f"Successfully parsed JSON response on attempt {attempt + 1}")
                return parsed
            
            logger.warning(f"Failed to parse JSON on attempt {attempt + 1}, response preview: {response_text[:300]}...")
            
        except Exception as e:
            logger.error(f"LLM error on attempt {attempt + 1}: {e}", exc_info=True)
        
        # Exponential backoff
        if attempt < max_retries - 1:
            import asyncio
            wait_time = 2 ** attempt
            logger.info(f"Waiting {wait_time}s before retry...")
            await asyncio.sleep(wait_time)
    
    return None


def _parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from LLM response, handling markdown code blocks.
    """
    # Remove markdown code blocks if present
    text = text.strip()
    
    # Try extracting from code block
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if json_match:
        text = json_match.group(1)
    
    # Try to find JSON object in the text
    brace_start = text.find('{')
    brace_end = text.rfind('}')
    
    if brace_start != -1 and brace_end != -1:
        text = text[brace_start:brace_end + 1]
    
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        logger.debug(f"Failed text: {text[:500]}...")
        return None


def _format_recommendations(recommendations: list) -> list:
    """Format recommendations with consistent structure for frontend display."""
    formatted = []
    
    for rec in recommendations:
        if isinstance(rec, dict):
            formatted.append({
                "priority": rec.get("priority", "medium"),
                "category": rec.get("category", "general"),
                "action": rec.get("action", str(rec)),
                "reason": rec.get("reason", ""),
                "impact": rec.get("impact", ""),
                "effort": rec.get("effort", "medium"),
                "timeframe": rec.get("timeframe", ""),
            })
        elif isinstance(rec, str):
            formatted.append({
                "priority": "medium",
                "category": "general",
                "action": rec,
                "reason": "",
                "impact": "",
                "effort": "medium",
                "timeframe": "",
            })
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    formatted.sort(key=lambda x: priority_order.get(x["priority"], 1))
    
    return formatted


def _error_response(message: str) -> Dict[str, Any]:
    """Return error response structure."""
    return {
        "success": False,
        "error": message,
        "scores": {
            "overall": 0,
            "fit_category": "Error",
            "breakdown": {}
        },
        "recommendations": []
    }


# Sync wrapper for non-async contexts
def analyze_resume_sync(
    resume_text: str,
    job_description: str,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Synchronous wrapper for analyze_resume_v2."""
    import asyncio
    return asyncio.run(analyze_resume_v2(resume_text, job_description, max_retries))
