"""
Utilities for extracting and validating draw.io XML from model responses.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zlib
import base64
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

    # Minify and compress the XML for efficient storage and transmission
    cleaned_xml = _minify_xml(cleaned_xml)
    
    # Use draw.io's native compressed format (deflate + base64)
    # This reduces size by ~80% and is more reliable for embedding
    try:
        compressed_xml = _compress_xml(cleaned_xml)
        # Store with compression marker so frontend knows to decompress
        cleaned_xml = f"COMPRESSED:{compressed_xml}"
    except Exception:
        # If compression fails, use minified version
        pass

    fenced = re.search(r"```(?:xml)?\s*<mxfile[\s\S]*?</mxfile>\s*```", text)
    if fenced:
        cleaned_text = text.replace(fenced.group(0), "").strip()
    else:
        cleaned_text = text.replace(match.group(1), "").strip()
    return cleaned_text, cleaned_xml


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
