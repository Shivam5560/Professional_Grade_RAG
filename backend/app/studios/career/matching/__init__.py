"""Deterministic requirement-to-evidence matching."""

from .optimizer import match_requirements
from .scoring import score_candidate_edge

__all__ = ["match_requirements", "score_candidate_edge"]
