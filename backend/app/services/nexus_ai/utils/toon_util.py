"""Helpers for decoding TOON responses."""

import re
from typing import Any, Dict, List, Tuple


def extract_toon_block(text: str) -> str:
    marker = "```toon"
    if marker in text:
        start_index = text.index(marker) + len(marker)
        end_index = text.rindex("```")
        return text[start_index:end_index].strip()
    return text.strip()


def _parse_toon(text: str) -> Dict[str, Any]:
    lines = [line.rstrip() for line in text.splitlines()]
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(-1, root)]
    list_key_re = re.compile(r"^(?P<key>[^\[]+)\[(?P<idx>\d+)\]$")

    for line in lines:
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()

        if ":" not in content:
            continue

        key_part, value_part = content.split(":", 1)
        key_part = key_part.strip()
        value_part = value_part.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        parent = stack[-1][1]

        match = list_key_re.match(key_part)
        if match:
            list_key = match.group("key")
            idx = int(match.group("idx"))
            if list_key not in parent or not isinstance(parent[list_key], list):
                parent[list_key] = []
            target_list = parent[list_key]
            while len(target_list) <= idx:
                target_list.append(None)

            if value_part:
                target_list[idx] = value_part
            else:
                target_list[idx] = {}
                stack.append((indent, target_list[idx]))
            continue

        if value_part:
            parent[key_part] = value_part
        else:
            parent[key_part] = {}
            stack.append((indent, parent[key_part]))

    return root


def decode_toon(text: str) -> Dict[str, Any]:
    """Decode TOON format text to dictionary with validation."""
    cleaned = extract_toon_block(text)
    try:
        from toon_format import decode
        result = decode(cleaned)
    except Exception:
        result = _parse_toon(cleaned)
    
    # Ensure result is always a dict
    if not isinstance(result, dict):
        return {"_raw": str(result), "_parse_error": "TOON parsing returned non-dict"}
    return result
