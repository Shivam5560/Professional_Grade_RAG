"""
Utilities for extracting and validating draw.io XML from model responses.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Optional, Tuple


def extract_drawio_xml(text: str) -> Tuple[str, Optional[str]]:
    """
    Extract draw.io <mxfile> XML from a response string.

    Returns:
        Tuple of (cleaned_text, diagram_xml).
        If no valid XML is found, diagram_xml is None.
    """
    if not text:
        return text, None

    match = re.search(r"(<mxfile[\s\S]*?</mxfile>)", text)
    if not match:
        return text, None

    raw_xml = match.group(1).strip()
    cleaned_xml = _strip_code_fences(raw_xml)

    if not _is_valid_mxfile(cleaned_xml):
        cleaned_xml = _attempt_xml_repair(cleaned_xml)

    if not _is_valid_mxfile(cleaned_xml):
        return text, None

    fenced = re.search(r"```(?:xml)?\s*<mxfile[\s\S]*?</mxfile>\s*```", text)
    if fenced:
        cleaned_text = text.replace(fenced.group(0), "").strip()
    else:
        cleaned_text = text.replace(match.group(1), "").strip()
    return cleaned_text, cleaned_xml


def _strip_code_fences(xml_text: str) -> str:
    xml_text = re.sub(r"^```(?:xml)?\s*", "", xml_text.strip())
    xml_text = re.sub(r"```$", "", xml_text.strip())
    return xml_text.strip()


def _is_valid_mxfile(xml_text: str) -> bool:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return False
    return root.tag == "mxfile"


def _attempt_xml_repair(xml_text: str) -> str:
    """
    Best-effort cleanup for malformed XML.
    """
    # Remove any leading/trailing non-XML text around the mxfile tag
    match = re.search(r"(<mxfile[\s\S]*?</mxfile>)", xml_text)
    if match:
        xml_text = match.group(1)

    # Normalize whitespace
    return xml_text.strip()
