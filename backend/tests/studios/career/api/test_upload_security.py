from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.studios.career.api.contracts import SourceIngestionRequest
from app.studios.career.api.service import UnsupportedCareerCapability

from .test_router import claim_payload


def test_source_ingestion_rejects_paths_unsupported_media_and_oversized_claim_sets() -> None:
    base = {
        "filename": "resume.json",
        "media_type": "application/json",
        "ingestion_mode": "structured",
        "claims": [claim_payload()],
    }
    for filename in ("../resume.json", "/tmp/resume.json", "folder\\resume.json"):
        with pytest.raises(ValidationError):
            SourceIngestionRequest.model_validate({**base, "filename": filename})
    with pytest.raises(ValidationError):
        SourceIngestionRequest.model_validate({**base, "media_type": "application/pdf"})
    with pytest.raises(ValidationError):
        SourceIngestionRequest.model_validate({**base, "claims": [claim_payload()] * 201})


def test_free_form_extraction_is_an_explicit_unsupported_capability() -> None:
    request = SourceIngestionRequest(
        filename="resume.txt",
        media_type="text/plain",
        ingestion_mode="free-form",
        raw_text="A resume that would otherwise require extraction.",
    )
    with pytest.raises(UnsupportedCareerCapability, match="free-form-extraction"):
        request.require_structured_claims()
