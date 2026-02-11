"""Core module for Nexus Resume Analysis."""

from app.services.nexus_ai.core.analyzer import analyze_resume_v2
from app.services.nexus_ai.core.scorers_v2 import (
    compute_technical_score,
    compute_ats_score,
    compute_grammar_score,
    compute_section_score,
    compute_overall_score,
    # Utilities
    skills_match,
    get_canonical_skill,
    calculate_readability_scores,
    validate_contact_info,
    calculate_keyword_density,
    analyze_resume_length,
    # Constants
    SKILL_SYNONYMS,
    SKILL_CATEGORIES,
    STRONG_ACTION_VERBS,
)

__all__ = [
    "analyze_resume_v2",
    "compute_technical_score",
    "compute_ats_score",
    "compute_grammar_score",
    "compute_section_score",
    "compute_overall_score",
    "skills_match",
    "get_canonical_skill",
    "calculate_readability_scores",
    "validate_contact_info",
    "calculate_keyword_density",
    "analyze_resume_length",
    "SKILL_SYNONYMS",
    "SKILL_CATEGORIES",
    "STRONG_ACTION_VERBS",
]
