# backend/tests/test_slide_cleaning.py
from app.services.analysis.slide_generator import _clean_markdown_text, _extract_bullets

def test_clean_markdown_text_strips_boilerplate():
    text = "Here is some real text. [Insert text here] Also this. TBD."
    cleaned = _clean_markdown_text(text)
    assert "[Insert text here]" not in cleaned
    assert "TBD" not in cleaned
    assert "Here is some real text. Also this." in cleaned

def test_extract_bullets_drops_empty_and_filler():
    md_text = "- Valid point\n- [Insert detail]\n- TBD\n- Another valid point"
    bullets = _extract_bullets(md_text)
    assert len(bullets) == 2
    assert bullets[0] == "Valid point"
    assert bullets[1] == "Another valid point"

def test_clean_markdown_text_preserves_citations():
    text = "Important fact [1]. Another point [23]."
    cleaned = _clean_markdown_text(text)
    assert "[1]" in cleaned
    assert "[23]" in cleaned

def test_clean_markdown_text_handles_links_properly():
    text = "Check this [Link Text](https://example.com) for info."
    cleaned = _clean_markdown_text(text)
    assert "Check this Link Text for info." in cleaned
    assert "(https://example.com)" not in cleaned
