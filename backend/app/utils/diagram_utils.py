"""
Utilities for extracting and validating draw.io XML from model responses.
"""

from __future__ import annotations

import re
from defusedxml import ElementTree as ET
import zlib
import base64
from typing import Optional, Tuple


DIAGRAM_SPLIT_TOKEN = "||DIAGRAM_SPLIT||"


def extract_drawio_xml(text: str) -> Tuple[str, Optional[str]]:
    """
    Extract draw.io <mxfile> XML from a response string.

    Returns:
        Tuple of (cleaned_text, diagram_xml).
        If no valid XML is found, diagram_xml is None.
    """
    if not text:
        return text, None

    matches = re.findall(r"(<mxfile[\s\S]*?</mxfile>)", text)
    if not matches:
        # Strip any dangling mxfile fragments to avoid leaking broken XML to the UI.
        if "<mxfile" in text:
            cleaned_text = re.sub(r"<mxfile[\s\S]*$", "", text).strip()
            return cleaned_text, None
        return text, None

    cleaned_xml_list = []
    for raw_xml in matches:
        cleaned_xml = _strip_code_fences(raw_xml.strip())

        if not _is_valid_mxfile(cleaned_xml):
            cleaned_xml = _attempt_xml_repair(cleaned_xml)

        if not _is_valid_mxfile(cleaned_xml):
            continue

        cleaned_xml = _minify_xml(cleaned_xml)
        try:
            compressed_xml = _compress_xml(cleaned_xml)
            cleaned_xml = f"COMPRESSED:{compressed_xml}"
        except Exception:
            pass

        cleaned_xml_list.append(cleaned_xml)

    fenced_pattern = r"```(?:xml)?\s*<mxfile[\s\S]*?</mxfile>\s*```"
    cleaned_text = re.sub(fenced_pattern, "", text)
    cleaned_text = re.sub(r"<mxfile[\s\S]*?</mxfile>", "", cleaned_text).strip()

    if not cleaned_xml_list:
        return cleaned_text, None

    return cleaned_text, DIAGRAM_SPLIT_TOKEN.join(cleaned_xml_list)


def is_diagram_request(text: str) -> bool:
    if not text:
        return False
    return re.search(
        r"\b(diagram|flow|flowchart|architecture|sequence|draw\.io|drawio|uml|workflow)\b",
        text,
        re.IGNORECASE,
    ) is not None


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


def _minify_xml(xml_text: str) -> str:
    """
    Minify XML to reduce size and remove formatting issues.
    
    This helps:
    1. Reduce URL length for embed viewer
    2. Remove problematic whitespace/newlines
    3. Make XML more compact for transmission
    """
    try:
        # Parse and re-serialize without extra whitespace
        root = ET.fromstring(xml_text)
        
        # Remove text whitespace from all elements
        for elem in root.iter():
            if elem.text and elem.text.strip() == '':
                elem.text = None
            elif elem.text:
                elem.text = elem.text.strip()
            if elem.tail and elem.tail.strip() == '':
                elem.tail = None
            elif elem.tail:
                elem.tail = elem.tail.strip()
        
        # Serialize without pretty printing
        minified = ET.tostring(root, encoding='unicode', method='xml')
        
        # Additional cleanup: remove unnecessary spaces between tags
        minified = re.sub(r'>\s+<', '><', minified)
        
        # Remove XML declaration if present
        minified = re.sub(r'<\?xml[^>]+\?>', '', minified).strip()
        
        return minified
    except Exception:
        # If minification fails, return original (better than nothing)
        return xml_text


def _compress_xml(xml_text: str) -> str:
    """
    Compress XML using draw.io's URL format (raw DEFLATE + base64).

    draw.io expects a raw DEFLATE stream (no zlib header) when using #R links.
    """
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(xml_text.encode("utf-8")) + compressor.flush()
    return base64.b64encode(compressed).decode("utf-8")


def decompress_xml(compressed_text: str) -> str:
    """
    Decompress XML from draw.io's URL format (raw DEFLATE + base64).

    Args:
        compressed_text: Base64-encoded compressed XML

    Returns:
        Original XML string
    """
    compressed = base64.b64decode(compressed_text)
    return zlib.decompress(compressed, wbits=-15).decode("utf-8")
