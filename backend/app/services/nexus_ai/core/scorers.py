"""
Algorithmic scorers for resume analysis.
All scoring is done without LLM calls - pure computation.
"""

import re
from typing import Dict, List, Any, Set
from collections import Counter


def compute_technical_score(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str] = None
) -> Dict[str, Any]:
    """
    Compute technical match score based on skills overlap.
    
    Score breakdown:
    - 70% weight on required skills match
    - 30% weight on preferred skills match
    """
    if not required_skills:
        return {
            "score": 100,
            "matched_required": [],
            "missing_required": [],
            "matched_preferred": [],
            "details": "No specific skills required"
        }
    
    # Normalize skills for comparison (lowercase, strip)
    candidate_set = {s.lower().strip() for s in candidate_skills if s}
    required_set = {s.lower().strip() for s in required_skills if s}
    preferred_set = {s.lower().strip() for s in (preferred_skills or []) if s}
    
    # Find matches (using fuzzy substring matching)
    matched_required = []
    missing_required = []
    
    for req in required_skills:
        req_lower = req.lower().strip()
        # Check exact match or substring match
        if req_lower in candidate_set or any(req_lower in c or c in req_lower for c in candidate_set):
            matched_required.append(req)
        else:
            missing_required.append(req)
    
    matched_preferred = []
    for pref in (preferred_skills or []):
        pref_lower = pref.lower().strip()
        if pref_lower in candidate_set or any(pref_lower in c or c in pref_lower for c in candidate_set):
            matched_preferred.append(pref)
    
    # Calculate scores
    required_score = (len(matched_required) / len(required_set) * 100) if required_set else 100
    preferred_score = (len(matched_preferred) / len(preferred_set) * 100) if preferred_set else 100
    
    # Weighted average
    total_score = required_score * 0.7 + preferred_score * 0.3
    
    return {
        "score": round(total_score, 1),
        "matched_required": matched_required,
        "missing_required": missing_required,
        "matched_preferred": matched_preferred,
        "required_match_pct": round(required_score, 1),
        "preferred_match_pct": round(preferred_score, 1)
    }


def compute_ats_score(resume_text: str, job_description: str) -> Dict[str, Any]:
    """
    Compute ATS (Applicant Tracking System) compatibility score.
    
    Factors:
    - Keyword density from JD
    - Standard section headers
    - Clean formatting indicators
    - Contact info presence
    """
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()
    
    # Extract keywords from JD (words 4+ chars, excluding common words)
    stop_words = {
        'the', 'and', 'or', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare',
        'for', 'with', 'about', 'against', 'between', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'from', 'up', 'down',
        'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom',
        'work', 'team', 'role', 'position', 'company', 'experience', 'looking',
        'join', 'ability', 'strong', 'excellent', 'good', 'great', 'best',
        'required', 'preferred', 'plus', 'bonus', 'years', 'year', 'responsibilities'
    }
    
    jd_words = re.findall(r'\b[a-z]{4,}\b', jd_lower)
    jd_keywords = [w for w in jd_words if w not in stop_words]
    keyword_counts = Counter(jd_keywords)
    
    # Get top 20 most common keywords from JD
    top_keywords = [word for word, count in keyword_counts.most_common(20)]
    
    # Check how many appear in resume
    matched_keywords = [kw for kw in top_keywords if kw in resume_lower]
    keyword_score = (len(matched_keywords) / len(top_keywords) * 100) if top_keywords else 100
    
    # Check for standard section headers
    section_headers = {
        'experience': ['experience', 'employment', 'work history', 'professional experience'],
        'education': ['education', 'academic', 'qualifications'],
        'skills': ['skills', 'technical skills', 'competencies', 'expertise'],
        'summary': ['summary', 'objective', 'profile', 'about'],
        'contact': ['email', 'phone', 'address', 'linkedin']
    }
    
    sections_found = 0
    sections_missing = []
    for section, keywords in section_headers.items():
        if any(kw in resume_lower for kw in keywords):
            sections_found += 1
        else:
            sections_missing.append(section)
    
    section_score = (sections_found / len(section_headers)) * 100
    
    # Check for problematic formatting (tables, graphics indicators)
    formatting_issues = []
    if resume_text.count('|') > 5:
        formatting_issues.append("Possible table formatting detected - may not parse well")
    if '■' in resume_text or '●' in resume_text or '►' in resume_text:
        formatting_issues.append("Special bullet characters - consider using standard bullets")
    if len(re.findall(r'\t{2,}', resume_text)) > 3:
        formatting_issues.append("Heavy tab usage - consider cleaner formatting")
    
    formatting_score = max(0, 100 - len(formatting_issues) * 15)
    
    # Contact info check
    has_email = bool(re.search(r'[\w.-]+@[\w.-]+\.\w+', resume_text))
    has_phone = bool(re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text))
    contact_score = 100 if (has_email and has_phone) else (50 if (has_email or has_phone) else 0)
    
    # Weighted total
    total_score = (
        keyword_score * 0.40 +
        section_score * 0.30 +
        formatting_score * 0.15 +
        contact_score * 0.15
    )
    
    return {
        "score": round(total_score, 1),
        "keyword_match_score": round(keyword_score, 1),
        "section_score": round(section_score, 1),
        "formatting_score": round(formatting_score, 1),
        "contact_score": round(contact_score, 1),
        "matched_keywords": matched_keywords[:10],  # Top 10
        "sections_missing": sections_missing,
        "formatting_issues": formatting_issues
    }


def compute_grammar_score(resume_text: str) -> Dict[str, Any]:
    """
    Compute grammar and writing quality score.
    
    Factors:
    - Action verb usage
    - Quantified achievements (numbers/percentages)
    - Sentence structure variety
    - Readability indicators
    """
    lines = [l.strip() for l in resume_text.split('\n') if l.strip()]
    
    # Action verbs commonly used in strong resumes
    strong_action_verbs = [
        'achieved', 'accelerated', 'accomplished', 'analyzed', 'architected',
        'built', 'championed', 'consolidated', 'created', 'delivered',
        'designed', 'developed', 'directed', 'drove', 'engineered',
        'established', 'executed', 'expanded', 'generated', 'grew',
        'implemented', 'improved', 'increased', 'initiated', 'innovated',
        'integrated', 'launched', 'led', 'managed', 'maximized',
        'mentored', 'negotiated', 'optimized', 'orchestrated', 'organized',
        'pioneered', 'produced', 'reduced', 'redesigned', 'resolved',
        'revamped', 'scaled', 'spearheaded', 'streamlined', 'strengthened',
        'supervised', 'surpassed', 'transformed', 'upgraded'
    ]
    
    text_lower = resume_text.lower()
    
    # Count action verbs used
    action_verbs_found = [v for v in strong_action_verbs if v in text_lower]
    action_verb_score = min(100, len(action_verbs_found) * 10)  # 10 verbs = 100%
    
    # Check for quantified achievements
    # Numbers, percentages, dollar amounts
    numbers = re.findall(r'\b\d+[%$KMB]?\b|\$\d+|\d+\+', resume_text)
    percentages = re.findall(r'\d+%', resume_text)
    quantification_score = min(100, (len(numbers) + len(percentages) * 2) * 5)
    
    # Sentence variety - check for varied sentence starts
    sentence_starts = []
    for line in lines:
        words = line.split()
        if words and len(words) > 3:
            sentence_starts.append(words[0].lower())
    
    unique_starts = len(set(sentence_starts))
    total_starts = len(sentence_starts)
    variety_score = (unique_starts / total_starts * 100) if total_starts > 0 else 100
    
    # Check for passive voice indicators (penalty)
    passive_indicators = ['was responsible for', 'duties included', 'tasked with', 'was assigned']
    passive_count = sum(1 for p in passive_indicators if p in text_lower)
    passive_penalty = passive_count * 10
    
    # Calculate clarity based on average words per bullet
    bullet_points = [l for l in lines if l.startswith(('-', '•', '*', '–')) or l[0].isdigit()]
    if bullet_points:
        avg_words = sum(len(b.split()) for b in bullet_points) / len(bullet_points)
        # Ideal is 10-20 words per bullet
        if 10 <= avg_words <= 20:
            clarity_score = 100
        elif avg_words < 10:
            clarity_score = 70  # Too brief
        else:
            clarity_score = max(50, 100 - (avg_words - 20) * 2)  # Too verbose
    else:
        clarity_score = 70  # No clear bullet structure
    
    # Weighted total
    total_score = max(0, (
        action_verb_score * 0.30 +
        quantification_score * 0.25 +
        variety_score * 0.20 +
        clarity_score * 0.25 -
        passive_penalty
    ))
    
    return {
        "score": round(min(100, total_score), 1),
        "action_verbs_used": action_verbs_found[:10],
        "action_verb_count": len(action_verbs_found),
        "quantified_achievements": len(numbers) + len(percentages),
        "clarity_score": round(clarity_score, 1),
        "variety_score": round(variety_score, 1),
        "passive_voice_issues": passive_count,
        "suggestions": _get_writing_suggestions(
            action_verbs_found, numbers, passive_count, clarity_score
        )
    }


def _get_writing_suggestions(
    action_verbs: List[str],
    numbers: List[str],
    passive_count: int,
    clarity_score: float
) -> List[str]:
    """Generate writing improvement suggestions."""
    suggestions = []
    
    if len(action_verbs) < 5:
        suggestions.append("Use more action verbs to start bullet points (e.g., 'Developed', 'Led', 'Implemented')")
    
    if len(numbers) < 3:
        suggestions.append("Add more quantified achievements (e.g., 'Increased sales by 25%', 'Managed team of 8')")
    
    if passive_count > 0:
        suggestions.append("Replace passive phrases like 'was responsible for' with active verbs")
    
    if clarity_score < 70:
        suggestions.append("Adjust bullet point length - aim for 10-20 words per point")
    
    if not suggestions:
        suggestions.append("Writing quality is strong - maintain consistent style")
    
    return suggestions


def compute_section_score(section_assessment: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute section completeness score based on LLM's section assessment.
    
    This takes the section_assessment from LLM and converts to numerical score.
    """
    quality_scores = {'good': 100, 'fair': 70, 'poor': 40}
    
    sections = ['contact_info', 'summary', 'experience', 'education', 'skills']
    weights = {
        'contact_info': 0.15,
        'summary': 0.15,
        'experience': 0.35,
        'education': 0.15,
        'skills': 0.20
    }
    
    total_score = 0
    section_scores = {}
    
    for section in sections:
        section_data = section_assessment.get(section, {})
        present = section_data.get('present', False)
        quality = section_data.get('quality', 'poor').lower()
        
        if present:
            score = quality_scores.get(quality, 50)
        else:
            score = 0
        
        section_scores[section] = {
            "present": present,
            "quality": quality,
            "score": score,
            "feedback": section_data.get('feedback', '')
        }
        
        total_score += score * weights.get(section, 0.15)
    
    return {
        "score": round(total_score, 1),
        "sections": section_scores
    }


def compute_overall_score(
    technical_score: float,
    ats_score: float,
    grammar_score: float,
    section_score: float
) -> Dict[str, Any]:
    """
    Compute weighted overall score from all components.
    """
    weights = {
        'technical': 0.35,  # Skills match is most important
        'ats': 0.25,        # ATS compatibility
        'grammar': 0.15,    # Writing quality
        'section': 0.25     # Resume completeness
    }
    
    overall = (
        technical_score * weights['technical'] +
        ats_score * weights['ats'] +
        grammar_score * weights['grammar'] +
        section_score * weights['section']
    )
    
    # Determine fit category
    if overall >= 80:
        fit = "Strong Match"
    elif overall >= 60:
        fit = "Good Match"
    elif overall >= 40:
        fit = "Moderate Match"
    else:
        fit = "Needs Improvement"
    
    return {
        "overall_score": round(overall, 1),
        "fit_category": fit,
        "breakdown": {
            "technical_match": round(technical_score, 1),
            "ats_compatibility": round(ats_score, 1),
            "writing_quality": round(grammar_score, 1),
            "section_completeness": round(section_score, 1)
        },
        "weights": weights
    }
