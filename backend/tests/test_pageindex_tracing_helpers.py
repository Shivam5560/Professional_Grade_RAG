import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.pageindex_rag_engine import _build_think_section_metadata


def test_build_think_section_metadata_excludes_text_and_keeps_required_keys() -> None:
    sections = [
        {
            "doc_name": "Design Spec.pdf",
            "title": "System Overview",
            "text": "Sensitive section text that must never be traced",
            "start_page": 2,
            "end_page": 4,
            "node_id": "0003",
            "extra": "ignored",
        },
        {
            "doc_name": "Runbook.md",
            "title": "Recovery Steps",
            "text": "Another secret body",
            "start_page": 7,
            "end_page": 9,
            "node_id": "0009",
        },
    ]

    payload = _build_think_section_metadata(sections)

    assert payload == [
        {
            "rank": 1,
            "document": "Design Spec.pdf",
            "section_title": "System Overview",
            "start_page": 2,
            "end_page": 4,
            "node_id": "0003",
        },
        {
            "rank": 2,
            "document": "Runbook.md",
            "section_title": "Recovery Steps",
            "start_page": 7,
            "end_page": 9,
            "node_id": "0009",
        },
    ]

    serialized = str(payload)
    assert "Sensitive section text" not in serialized
    assert "Another secret body" not in serialized
