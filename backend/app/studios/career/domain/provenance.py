from __future__ import annotations

MAX_EVIDENCE_SNIPPET_LENGTH = 1000


def safe_evidence_snippet(text: str) -> str:
    """Bound exact source text for the shared EvidenceReference contract."""

    if len(text) <= MAX_EVIDENCE_SNIPPET_LENGTH:
        return text
    return text[: MAX_EVIDENCE_SNIPPET_LENGTH - 1] + "…"
