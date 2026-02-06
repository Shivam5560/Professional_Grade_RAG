"""
PageIndex utility functions adapted for Groq LLM.
Provides PDF parsing, tree building, and LLM-based tree generation
without relying on the PageIndex API — uses local code only.
"""

import os
import re
import json
import copy
import asyncio
from typing import List, Tuple, Dict, Any, Optional
from io import BytesIO

import PyPDF2

from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Token Helpers
# ---------------------------------------------------------------------------

def count_tokens_approx(text: str) -> int:
    """Approximate token count (≈ 4 chars per token for English text)."""
    return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# PDF Extraction
# ---------------------------------------------------------------------------

def get_page_texts(pdf_path: str) -> List[Tuple[str, int]]:
    """
    Extract text and token counts from each page of a PDF.

    Returns:
        List of (page_text, token_count) tuples, 1-indexed conceptually.
    """
    reader = PyPDF2.PdfReader(pdf_path)
    pages: List[Tuple[str, int]] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        tokens = count_tokens_approx(text)
        pages.append((text, tokens))
    return pages


def get_pdf_title(pdf_path: str) -> str:
    """Extract title from PDF metadata, fallback to filename."""
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        meta = reader.metadata
        if meta and meta.title:
            return meta.title
    except Exception:
        pass
    return os.path.splitext(os.path.basename(pdf_path))[0]


def get_text_of_pages(pages: List[Tuple[str, int]], start: int, end: int, tag: bool = True) -> str:
    """
    Get concatenated text for pages [start, end] (1-indexed inclusive).
    Optionally wraps each page in <physical_index_X> tags.
    """
    text = ""
    for idx in range(start - 1, min(end, len(pages))):
        page_text = pages[idx][0]
        if tag:
            text += f"<physical_index_{idx+1}>\n{page_text}\n</physical_index_{idx+1}>\n\n"
        else:
            text += page_text + "\n"
    return text


# ---------------------------------------------------------------------------
# LLM Helper — wraps Groq calls
# ---------------------------------------------------------------------------

async def groq_llm_call(
    prompt: str,
    groq_service,
    temperature: float = 0.0,
) -> str:
    """
    Call Groq LLM (via LlamaIndex Groq wrapper).
    This replaces PageIndex's `ChatGPT_API` and `ChatGPT_API_async`.
    """
    try:
        llm = groq_service.get_llm()
        response = await llm.acomplete(prompt)
        return response.text.strip()
    except Exception as e:
        logger.log_error("Groq LLM call", e)
        raise


def extract_json_from_response(text: str) -> Any:
    """
    Extract JSON from an LLM response that may contain markdown fences.
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = cleaned.strip().rstrip("`")
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object/array in text
    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    logger.log_operation("⚠️  Could not extract JSON from LLM response", level="WARNING")
    return {}


# ---------------------------------------------------------------------------
# Tree Generation Prompts and Functions
# ---------------------------------------------------------------------------

GENERATE_TOC_PROMPT = """You are an expert at extracting hierarchical structure from documents.

Analyze the following document text and generate a hierarchical tree structure (table of contents) that represents the document's natural sections and subsections.

Each node should have:
- "structure": a numeric hierarchy index (e.g., "1", "1.1", "1.2", "2", "2.1")
- "title": the original section title from the text
- "physical_index": the page number (1-indexed) where this section starts

The document pages are wrapped in <physical_index_X> tags to indicate page boundaries.

Return ONLY a JSON array in this exact format:
[
    {{
        "structure": "1",
        "title": "Section Title",
        "physical_index": 1
    }},
    ...
]

Document text:
{document_text}
"""


GENERATE_SUMMARY_PROMPT = """You are given a section of a document. Generate a concise summary (2-4 sentences) that captures the main points covered in this section.

Section Title: {title}
Section Text: {text}

Return ONLY the summary text, nothing else."""


GENERATE_DOC_DESCRIPTION_PROMPT = """You are given the table of contents structure of a document with section summaries. Generate a one-sentence description for the entire document that captures its main purpose and content.

Document structure:
{tree_json}

Return ONLY the description text, nothing else."""


async def generate_tree_from_pdf(
    pdf_path: str,
    groq_service,
    max_pages_per_chunk: int = 15,
) -> Dict[str, Any]:
    """
    Generate a PageIndex-style hierarchical tree from a PDF using Groq LLM.

    This is the self-hosted equivalent of PageIndex's `page_index_main()`.

    Steps:
    1. Extract all pages from PDF
    2. Send pages (in groups) to LLM to generate TOC structure
    3. Build hierarchical tree from flat TOC
    4. Attach text content and summaries to each node

    Returns:
        Dict with 'doc_name', 'doc_description', 'structure' keys.
    """
    logger.log_operation("🌲 Starting PageIndex tree generation", pdf=pdf_path)

    # Step 1: Extract pages
    pages = get_page_texts(pdf_path)
    total_pages = len(pages)
    logger.log_operation(f"📄 Extracted {total_pages} pages")

    if total_pages == 0:
        return {
            "doc_name": get_pdf_title(pdf_path),
            "doc_description": "Empty document",
            "structure": [],
        }

    # Step 2: Generate TOC by processing page groups
    all_toc_items: List[Dict] = []
    for chunk_start in range(0, total_pages, max_pages_per_chunk):
        chunk_end = min(chunk_start + max_pages_per_chunk, total_pages)
        page_text = get_text_of_pages(pages, chunk_start + 1, chunk_end, tag=True)

        prompt = GENERATE_TOC_PROMPT.format(document_text=page_text)
        response = await groq_llm_call(prompt, groq_service)
        toc_items = extract_json_from_response(response)

        if isinstance(toc_items, list):
            all_toc_items.extend(toc_items)

    logger.log_operation(f"📋 Generated {len(all_toc_items)} TOC items")

    # Deduplicate and clean
    seen_titles = set()
    unique_items = []
    for item in all_toc_items:
        title = item.get("title", "").strip()
        if title and title not in seen_titles:
            seen_titles.add(title)
            # Ensure physical_index is int
            pi = item.get("physical_index", 1)
            if isinstance(pi, str):
                pi = int(re.sub(r"\D", "", pi) or "1")
            item["physical_index"] = max(1, min(pi, total_pages))
            unique_items.append(item)

    if not unique_items:
        # Fallback: create a single root node for the whole document
        unique_items = [
            {
                "structure": "1",
                "title": get_pdf_title(pdf_path),
                "physical_index": 1,
            }
        ]

    # Step 3: Build hierarchical tree
    tree = _build_tree_from_flat(unique_items, total_pages)

    # Step 4: Attach text content
    _attach_text_to_nodes(tree, pages)

    # Step 5: Generate summaries
    await _generate_summaries(tree, groq_service)

    # Step 6: Generate document description
    tree_for_desc = _remove_text_fields(copy.deepcopy(tree))
    desc_prompt = GENERATE_DOC_DESCRIPTION_PROMPT.format(
        tree_json=json.dumps(tree_for_desc, indent=2)[:8000]
    )
    doc_description = await groq_llm_call(desc_prompt, groq_service)

    result = {
        "doc_name": get_pdf_title(pdf_path),
        "doc_description": doc_description,
        "structure": tree,
    }

    logger.log_operation("✅ Tree generation complete", nodes=_count_nodes(tree))
    return result


# ---------------------------------------------------------------------------
# Internal Tree Helpers
# ---------------------------------------------------------------------------

def _build_tree_from_flat(
    items: List[Dict], total_pages: int
) -> List[Dict]:
    """Convert flat TOC list with structure indices into a hierarchical tree."""
    # Sort by structure index
    items.sort(key=lambda x: [int(p) for p in str(x.get("structure", "0")).split(".")])

    # Calculate end pages
    for i, item in enumerate(items):
        item["start_index"] = item.get("physical_index", 1)
        if i < len(items) - 1:
            item["end_index"] = max(item["start_index"], items[i + 1]["physical_index"] - 1)
        else:
            item["end_index"] = total_pages

    # Build tree using structure hierarchy
    root_nodes: List[Dict] = []
    node_map: Dict[str, Dict] = {}
    node_counter = 0

    for item in items:
        structure = str(item.get("structure", ""))
        node_id = str(node_counter).zfill(4)
        node_counter += 1

        node = {
            "title": item.get("title", "Untitled"),
            "node_id": node_id,
            "start_index": item["start_index"],
            "end_index": item["end_index"],
            "nodes": [],
        }
        node_map[structure] = node

        # Find parent
        parts = structure.split(".")
        parent_structure = ".".join(parts[:-1]) if len(parts) > 1 else None

        if parent_structure and parent_structure in node_map:
            node_map[parent_structure]["nodes"].append(node)
            # Expand parent's end_index if needed
            node_map[parent_structure]["end_index"] = max(
                node_map[parent_structure]["end_index"], node["end_index"]
            )
        else:
            root_nodes.append(node)

    # Clean empty nodes lists
    def _clean(nodes):
        for n in nodes:
            if not n["nodes"]:
                del n["nodes"]
            else:
                _clean(n["nodes"])

    _clean(root_nodes)
    return root_nodes


def _attach_text_to_nodes(nodes: Any, pages: List[Tuple[str, int]]):
    """Recursively attach the full page text to each node."""
    if isinstance(nodes, list):
        for node in nodes:
            _attach_text_to_nodes(node, pages)
    elif isinstance(nodes, dict):
        start = nodes.get("start_index", 1)
        end = nodes.get("end_index", start)
        text = get_text_of_pages(pages, start, end, tag=False)
        nodes["text"] = text
        if "nodes" in nodes:
            _attach_text_to_nodes(nodes["nodes"], pages)


async def _generate_summaries(nodes: Any, groq_service):
    """Recursively generate summaries for all nodes using Groq."""
    if isinstance(nodes, list):
        tasks = [_generate_summaries(node, groq_service) for node in nodes]
        await asyncio.gather(*tasks)
    elif isinstance(nodes, dict):
        text = nodes.get("text", "")
        title = nodes.get("title", "")
        if text:
            # Truncate very long text for summary
            truncated = text[:6000]
            prompt = GENERATE_SUMMARY_PROMPT.format(title=title, text=truncated)
            try:
                summary = await groq_llm_call(prompt, groq_service)
                nodes["summary"] = summary
            except Exception:
                nodes["summary"] = f"Section: {title}"
        else:
            nodes["summary"] = f"Section: {title}"

        if "nodes" in nodes:
            await _generate_summaries(nodes["nodes"], groq_service)


def _remove_text_fields(data: Any) -> Any:
    """Remove 'text' fields from tree structure (for description prompt)."""
    if isinstance(data, dict):
        return {k: _remove_text_fields(v) for k, v in data.items() if k != "text"}
    elif isinstance(data, list):
        return [_remove_text_fields(item) for item in data]
    return data


def _count_nodes(nodes: Any) -> int:
    """Count total nodes in tree."""
    if isinstance(nodes, list):
        return sum(_count_nodes(n) for n in nodes)
    elif isinstance(nodes, dict):
        count = 1
        if "nodes" in nodes:
            count += _count_nodes(nodes["nodes"])
        return count
    return 0


# ---------------------------------------------------------------------------
# Tree Search / Retrieval Helpers
# ---------------------------------------------------------------------------

def flatten_tree_nodes(tree: Any, parent_id: Optional[str] = None, depth: int = 0) -> List[Dict]:
    """
    Flatten a hierarchical tree into a list of node dicts.
    Each dict includes parent_node_id and depth for DB storage.
    """
    flat: List[Dict] = []
    items = tree if isinstance(tree, list) else [tree]
    for node in items:
        flat_node = {
            "node_id": node.get("node_id", ""),
            "title": node.get("title", ""),
            "summary": node.get("summary", ""),
            "text_content": node.get("text", ""),
            "start_page": node.get("start_index"),
            "end_page": node.get("end_index"),
            "parent_node_id": parent_id,
            "depth": depth,
        }
        flat.append(flat_node)
        if "nodes" in node:
            flat.extend(flatten_tree_nodes(node["nodes"], node.get("node_id"), depth + 1))
    return flat


def get_tree_without_text(tree: Any) -> Any:
    """
    Return a copy of the tree with 'text' fields removed.
    Keeps title, node_id, summary, start/end_index, and child nodes.
    """
    return _remove_text_fields(copy.deepcopy(tree))


def build_node_map(tree: Any) -> Dict[str, Dict]:
    """
    Build a flat map of node_id -> node dict (with text) for fast lookup.
    """
    node_map: Dict[str, Dict] = {}

    def _walk(nodes):
        items = nodes if isinstance(nodes, list) else [nodes]
        for node in items:
            nid = node.get("node_id")
            if nid:
                node_map[nid] = node
            if "nodes" in node:
                _walk(node["nodes"])

    _walk(tree)
    return node_map
