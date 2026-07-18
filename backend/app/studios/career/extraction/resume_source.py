from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.platform.evidence import VerificationStatus
from app.services.nexus_ai.simple_extractor import (
    extract_jd_data,
    extract_resume_data,
    extract_text_from_file,
)
from app.studios.career.domain import (
    CareerClaim,
    ClaimObject,
    ClaimPredicate,
    ClaimSubject,
    ClaimSubjectKind,
    ClaimValueKind,
    RequirementCategory,
    RequirementPriority,
    RoleRequirement,
    SourceSpan,
    TemporalScope,
)


@dataclass(frozen=True)
class ExtractedResumeSource:
    source_id: str
    raw_text: str
    claims: tuple[CareerClaim, ...]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _source_span(source_id: str, locator: str, value: str, raw_text: str) -> SourceSpan:
    match_at = raw_text.lower().find(value.lower()) if value else -1
    exact = raw_text[match_at : match_at + len(value)] if match_at >= 0 else raw_text[:1000]
    return SourceSpan(source_id=source_id, locator=locator, exact_text=exact.strip())


def _claim(
    *,
    source_id: str,
    person: ClaimSubject,
    predicate: ClaimPredicate,
    kind: ClaimValueKind,
    value: str,
    locator: str,
    raw_text: str,
    temporal_label: str = "Unspecified resume period",
) -> CareerClaim:
    return CareerClaim.create(
        subject=person,
        predicate=predicate,
        object=ClaimObject(kind=kind, value=value),
        source_spans=(_source_span(source_id, locator, value, raw_text),),
        temporal_scope=TemporalScope(label=temporal_label or "Unspecified resume period"),
        verification_status=VerificationStatus.INFERRED,
        confidence=0.72,
        verifier_id="resume-extraction",
    )


def _claims_from_resume(source_id: str, raw_text: str, data: dict[str, Any]) -> tuple[CareerClaim, ...]:
    personal = data.get("personal_info") if isinstance(data.get("personal_info"), dict) else {}
    candidate_name = _safe_text(personal.get("name")) or "Candidate"
    person = ClaimSubject(kind=ClaimSubjectKind.PERSON, id=f"person-{source_id[7:]}", label=candidate_name)
    claims: list[CareerClaim] = []

    for index, skill in enumerate(_as_list(data.get("keywords"))):
        value = _safe_text(skill)
        if value:
            claims.append(_claim(source_id=source_id, person=person, predicate=ClaimPredicate.HAS_SKILL, kind=ClaimValueKind.SKILL, value=value, locator=f"skills:{index + 1}", raw_text=raw_text))

    for index, item in enumerate(_as_list(data.get("work_experience"))):
        if not isinstance(item, dict):
            continue
        dates = _safe_text(item.get("dates")) or "Unspecified resume period"
        company = _safe_text(item.get("company"))
        title = _safe_text(item.get("job_title") or item.get("title"))
        if company:
            claims.append(_claim(source_id=source_id, person=person, predicate=ClaimPredicate.WORKED_AT, kind=ClaimValueKind.EMPLOYER, value=company, locator=f"experience:{index + 1}:company", raw_text=raw_text, temporal_label=dates))
        if title:
            claims.append(_claim(source_id=source_id, person=person, predicate=ClaimPredicate.HELD_TITLE, kind=ClaimValueKind.TITLE, value=title, locator=f"experience:{index + 1}:title", raw_text=raw_text, temporal_label=dates))
        for responsibility_index, responsibility in enumerate(_as_list(item.get("responsibilities"))):
            value = _safe_text(responsibility)
            if value:
                claims.append(_claim(source_id=source_id, person=person, predicate=ClaimPredicate.PERFORMED, kind=ClaimValueKind.RESPONSIBILITY, value=value, locator=f"experience:{index + 1}:responsibility:{responsibility_index + 1}", raw_text=raw_text, temporal_label=dates))

    for index, item in enumerate(_as_list(data.get("education"))):
        if not isinstance(item, dict):
            continue
        value = _safe_text(item.get("degree"))
        if value:
            claims.append(_claim(source_id=source_id, person=person, predicate=ClaimPredicate.EARNED_DEGREE, kind=ClaimValueKind.DEGREE, value=value, locator=f"education:{index + 1}", raw_text=raw_text, temporal_label=_safe_text(item.get("graduation_date")) or "Education period"))

    for index, item in enumerate(_as_list(data.get("projects"))):
        if not isinstance(item, dict):
            continue
        project = _safe_text(item.get("name") or item.get("title"))
        if project:
            claims.append(_claim(source_id=source_id, person=person, predicate=ClaimPredicate.WORKED_ON, kind=ClaimValueKind.PROJECT, value=project, locator=f"projects:{index + 1}", raw_text=raw_text))
        for detail_index, detail in enumerate(_as_list(item.get("description"))):
            value = _safe_text(detail)
            if value:
                claims.append(_claim(source_id=source_id, person=person, predicate=ClaimPredicate.PERFORMED, kind=ClaimValueKind.RESPONSIBILITY, value=value, locator=f"projects:{index + 1}:highlight:{detail_index + 1}", raw_text=raw_text))

    for index, item in enumerate(_as_list(data.get("certifications"))):
        value = _safe_text(item.get("name")) if isinstance(item, dict) else _safe_text(item)
        if value:
            claims.append(_claim(source_id=source_id, person=person, predicate=ClaimPredicate.EARNED_CERTIFICATION, kind=ClaimValueKind.CERTIFICATION, value=value, locator=f"certifications:{index + 1}", raw_text=raw_text))

    if not claims:
        fallback = next((line.strip() for line in raw_text.splitlines() if line.strip()), "")
        if fallback:
            claims.append(_claim(source_id=source_id, person=person, predicate=ClaimPredicate.PERFORMED, kind=ClaimValueKind.RESPONSIBILITY, value=fallback[:500], locator="resume:1", raw_text=raw_text))
    return tuple(claims[:200])


def extract_resume_source(filename: str, content: bytes, *, source_id: str | None = None) -> ExtractedResumeSource:
    suffix = Path(filename).suffix.lower()
    source_id = source_id or f"source-{hashlib.sha256(content).hexdigest()[:24]}"
    temporary_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(content)
            temporary_path = handle.name
        raw_text = extract_text_from_file(temporary_path).strip()
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
    if not raw_text:
        raise ValueError("Resume text is empty or could not be extracted")
    data = extract_resume_data(raw_text[:50_000])
    return ExtractedResumeSource(source_id=source_id, raw_text=raw_text, claims=_claims_from_resume(source_id, raw_text, data))


def parse_job_description(job_description: str) -> tuple[str, tuple[RoleRequirement, ...]]:
    text = job_description.strip()
    if len(text) < 10:
        raise ValueError("Job description must contain at least 10 characters")
    data = extract_jd_data(text[:30_000])
    title = _safe_text(data.get("job_title")) or "Target role"
    requirements: list[RoleRequirement] = []
    groups = (
        ("required_skills", RequirementCategory.SKILL, RequirementPriority.REQUIRED, 3.0),
        ("key_responsibilities", RequirementCategory.RESPONSIBILITY, RequirementPriority.REQUIRED, 2.5),
        ("other_qualifications", RequirementCategory.DOMAIN, RequirementPriority.PREFERRED, 1.5),
    )
    seen: set[str] = set()
    for group, category, priority, weight in groups:
        for item in _as_list(data.get(group)):
            description = _safe_text(item)
            key = description.lower()
            if not description or key in seen:
                continue
            seen.add(key)
            slug = "-".join(part for part in "".join(char.lower() if char.isalnum() else " " for char in description).split()[:6]) or "requirement"
            requirement_id = f"req-{len(requirements) + 1}-{slug}"[:190].rstrip("-")
            requirements.append(
                RoleRequirement(
                    id=requirement_id,
                    priority=priority,
                    category=category,
                    description=description,
                    source_span=_source_span("role-description", f"{group}:{len(requirements) + 1}", description, text),
                    confidence=0.78,
                    weight=weight,
                )
            )
    if not requirements:
        requirements.append(
            RoleRequirement(
                id="req-1-role-description",
                priority=RequirementPriority.REQUIRED,
                category=RequirementCategory.RESPONSIBILITY,
                description=text[:1000],
                source_span=SourceSpan(source_id="role-description", locator="description:1", exact_text=text[:1000]),
                confidence=0.6,
                weight=1.0,
            )
        )
    return title, tuple(requirements[:200])
