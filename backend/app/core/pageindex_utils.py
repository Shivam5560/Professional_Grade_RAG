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
# Token / Rate-Limit Helpers
# ---------------------------------------------------------------------------

# Rate limiter: 250k tokens per minute budget
# We use a conservative 200k soft-limit so we never actually hit the hard 250k
_TPM_SOFT_LIMIT = 200_000
_TPM_WINDOW = 60.0  # seconds
_token_log: List[Tuple[float, int]] = []  # (timestamp, tokens_used)
_rate_lock = asyncio.Lock()


def count_tokens_approx(text: str) -> int:
    """Approximate token count (≈ 4 chars per token for English text)."""
    return max(1, len(text) // 4)


def _prune_token_log() -> int:
    """Remove expired entries from the token log, return current usage."""
    import time as _time
    now = _time.time()
    while _token_log and now - _token_log[0][0] > _TPM_WINDOW:
        _token_log.pop(0)
    return sum(t for _, t in _token_log)


async def _wait_for_token_budget(estimated_tokens: int) -> None:
    """
    Wait until we have enough token budget within the TPM window.
    Prevents 429 rate-limit errors from the LLM provider.
    """
    import time as _time

    while True:
        async with _rate_lock:
            used = _prune_token_log()
            if used + estimated_tokens <= _TPM_SOFT_LIMIT:
                _token_log.append((_time.time(), estimated_tokens))
                return  # Budget acquired

            # Calculate how long to wait for oldest entries to expire
            if _token_log:
                wait_until = _token_log[0][0] + _TPM_WINDOW
                sleep_secs = max(0.5, wait_until - _time.time() + 0.2)
            else:
                sleep_secs = 1.0

        # Sleep OUTSIDE the lock so other coroutines can proceed
        logger.log_operation(
            f"⏳ Rate-limit: waiting {sleep_secs:.1f}s (used ~{used} of {_TPM_SOFT_LIMIT} tokens)",
            level="INFO",
        )
        await asyncio.sleep(sleep_secs)


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
    max_retries: int = 3,
    use_reasoning: bool = True,
) -> str:
    """
    Call Groq LLM (via LlamaIndex Groq wrapper) with rate-limit awareness.
    This replaces PageIndex's `ChatGPT_API` and `ChatGPT_API_async`.

    Args:
        use_reasoning: If True, use the main LLM with reasoning_effort='high'.
                       If False, use the structured LLM (no reasoning tokens)
                       which is better for JSON extraction / summaries.

    Includes:
    - Token budget tracking to stay within 250k TPM
    - Automatic retry with exponential backoff on rate-limit errors
    """
    # Use a lighter estimate: only count prompt tokens (output is harder to predict
    # and the hard limit protects us). Divide by 2 to avoid over-reserving budget.
    estimated_tokens = count_tokens_approx(prompt) // 2 + 500
    await _wait_for_token_budget(estimated_tokens)

    for attempt in range(max_retries):
        try:
            if use_reasoning:
                llm = groq_service.get_llm()
            else:
                llm = groq_service.get_structured_llm()
            response = await llm.acomplete(prompt)
            result = response.text.strip()
            if not result:
                logger.log_operation(
                    "⚠️  LLM returned empty response, retrying with structured LLM",
                    level="WARNING",
                    attempt=attempt + 1,
                )
                # Fallback: if reasoning LLM returned empty, try structured
                if use_reasoning and attempt < max_retries - 1:
                    llm = groq_service.get_structured_llm()
                    response = await llm.acomplete(prompt)
                    result = response.text.strip()
                if not result:
                    continue  # Try next attempt
            return result
        except Exception as e:
            error_msg = str(e).lower()
            is_rate_limit = "rate" in error_msg or "429" in error_msg or "limit" in error_msg
            if is_rate_limit and attempt < max_retries - 1:
                wait = (2 ** attempt) * 5  # 5s, 10s, 20s
                logger.log_operation(
                    f"⏳ Rate-limited, retrying in {wait}s (attempt {attempt + 1}/{max_retries})",
                    level="WARNING",
                )
                await asyncio.sleep(wait)
                continue
            logger.log_error("Groq LLM call", e)
            raise

    # All retries exhausted — return empty string rather than crashing
    logger.log_operation("⚠️  All LLM call retries exhausted, returning empty", level="WARNING")
    return ""


def extract_json_from_response(text: str) -> Any:
    """
    Extract JSON from an LLM response that may contain:
    - Markdown code fences (```json ... ```)
    - Reasoning model <think>...</think> blocks
    - XML/HTML wrapper tags
    - Plain text preamble/postscript around the JSON
    """
    # Step 0: Strip reasoning model thinking blocks (e.g. DeepSeek, QwQ, etc.)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Also strip <|thinking|>...<|/thinking|> variant
    cleaned = re.sub(r"<\|thinking\|>.*?<\|/thinking\|>", "", cleaned, flags=re.DOTALL)
    # Strip any other XML-style wrapper tags that aren't part of JSON
    cleaned = re.sub(r"</?(?:response|output|result|answer)>", "", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    # Step 1: Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Step 2: Strip markdown code fences
    no_fences = re.sub(r"```(?:json)?\s*", "", cleaned)
    no_fences = no_fences.strip().rstrip("`")
    try:
        return json.loads(no_fences)
    except json.JSONDecodeError:
        pass

    # Step 3: Find the outermost JSON array [...] — most common for TOC
    # Use a bracket-counting approach for robustness with nested structures
    for open_ch, close_ch in [("[", "]"), ("{", "}")]:
        start_idx = cleaned.find(open_ch)
        if start_idx == -1:
            continue
        depth = 0
        for i in range(start_idx, len(cleaned)):
            if cleaned[i] == open_ch:
                depth += 1
            elif cleaned[i] == close_ch:
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start_idx : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break  # Try next bracket type

    # Step 4: Last resort — greedy regex
    for pattern in [r"\[\s*\{[\s\S]*\}\s*\]", r"\{[\s\S]*\}"]:
        match = re.search(pattern, cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue

    logger.log_operation(
        "⚠️  Could not extract JSON from LLM response",
        level="WARNING",
        response_preview=cleaned[:300],
    )
    return {}


# ---------------------------------------------------------------------------
# Tree Generation Prompts and Functions
# ---------------------------------------------------------------------------

GENERATE_TOC_INIT_PROMPT = """You are an expert at extracting hierarchical tree structure from documents.

Analyze the following document text and generate a hierarchical tree structure (table of contents) that represents the document's natural sections and subsections.

The structure variable is a PURELY NUMERIC dot-notation index representing the hierarchy position.
Rules:
- Top-level sections: "1", "2", "3", ...
- Subsections: "1.1", "1.2", "2.1", ...
- Deeper levels: "1.1.1", "1.2.3", ...
- ALWAYS use numbers only — never letters or words.
- Appendices, annexes, and back-matter sections MUST continue the numeric sequence after the last chapter.
  Example: if the last chapter is 5, use "6", "6.1", "6.2" for Appendix A and its subsections.

For the title, extract the original section title from the text. Only fix space inconsistency.

The provided text contains tags like <physical_index_X> to indicate the start of page X.

For the physical_index, extract the page number (1-indexed integer) where this section starts.

Return ONLY a JSON array in this exact format:
[
    {{
        "structure": "1",
        "title": "Section Title",
        "physical_index": 1
    }},
    ...
]

Be thorough — capture ALL sections and subsections visible in the text. Think carefully about the hierarchy depth.

Document text:
{document_text}
"""


GENERATE_TOC_CONTINUE_PROMPT = """You are an expert at extracting hierarchical tree structure from documents.

You are given a tree structure of the previous part and the text of the current part.
Your task is to CONTINUE the tree structure from the previous part to include the current part.

The structure variable is a PURELY NUMERIC dot-notation index representing the hierarchy position.
Rules:
- ALWAYS use numbers only — never letters or words.
- Continue numbering from where the previous structure left off.
- Appendices, annexes, and back-matter sections MUST continue the numeric sequence.
  Example: if the last item in the previous structure is "5.3", the next top-level section is "6",
  and its subsections are "6.1", "6.2", etc. — even if the document calls them "Appendix A", "Annex B", etc.

For the title, extract the original section title from the text. Only fix space inconsistency.

The provided text contains tags like <physical_index_X> to indicate the start of page X.

For the physical_index, extract the page number (1-indexed integer) where this section starts.

Return ONLY the ADDITIONAL items as a JSON array (do not repeat items from the previous structure):
[
    {{
        "structure": "x.x.x",
        "title": "Section Title",
        "physical_index": 5
    }},
    ...
]

Be thorough — capture ALL new sections and subsections visible in the current part.

Previous tree structure:
{previous_toc}

Current part text:
{document_text}
"""


GENERATE_SUMMARY_PROMPT = """You are given a section of a document. Generate a concise but detailed summary (3-5 sentences) that captures the main points, key data, and conclusions covered in this section. Include specific figures, terms, or names that would help identify whether this section is relevant to a given question.

Section Title: {title}
Section Text: {text}

Return ONLY the summary text, nothing else."""


GENERATE_DOC_DESCRIPTION_PROMPT = """You are given the table of contents structure of a document with section summaries. Generate a one-sentence description for the entire document that captures its main purpose and content.

Document structure:
{tree_json}

Return ONLY the description text, nothing else."""


def _build_page_groups(
    pages: List[Tuple[str, int]],
    max_pages_per_chunk: int,
    max_tokens_per_group: int = 20000,
) -> List[Tuple[int, int]]:
    """
    Split pages into groups for TOC generation, respecting both page count
    and token budget (mirrors PageIndex's `page_list_to_group_text`).

    Returns list of (start_page, end_page) tuples (1-indexed, inclusive).
    """
    total_pages = len(pages)
    if total_pages == 0:
        return []

    groups: List[Tuple[int, int]] = []
    group_start = 0
    group_tokens = 0

    for i, (_, tok) in enumerate(pages):
        if (
            group_tokens + tok > max_tokens_per_group
            or (i - group_start) >= max_pages_per_chunk
        ) and i > group_start:
            # Close current group
            groups.append((group_start + 1, i))  # 1-indexed, inclusive
            group_start = max(i - 1, group_start)  # 1-page overlap
            group_tokens = pages[max(i - 1, 0)][1] + tok
        else:
            group_tokens += tok

    # Add the final group
    if group_start < total_pages:
        groups.append((group_start + 1, total_pages))

    return groups


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

    # Step 2: Generate TOC using continuation strategy (like PageIndex source)
    #   - First chunk: generate initial TOC
    #   - Subsequent chunks: continue TOC with awareness of previous structure
    # This produces a much more coherent and accurate tree.
    all_toc_items: List[Dict] = []

    # Build page groups using token-based grouping (mirrors PageIndex's page_list_to_group_text)
    page_groups = _build_page_groups(pages, max_pages_per_chunk)
    logger.log_operation(f"📑 Split PDF into {len(page_groups)} page groups for TOC")

    for group_idx, (group_start, group_end) in enumerate(page_groups):
        page_text = get_text_of_pages(pages, group_start, group_end, tag=True)

        if group_idx == 0:
            # First group: generate initial TOC
            prompt = GENERATE_TOC_INIT_PROMPT.format(document_text=page_text)
        else:
            # Subsequent groups: continue TOC with previous context
            prompt = GENERATE_TOC_CONTINUE_PROMPT.format(
                previous_toc=json.dumps(all_toc_items, indent=2)[:8000],
                document_text=page_text,
            )

        response = await groq_llm_call(prompt, groq_service, use_reasoning=False)
        toc_items = extract_json_from_response(response)

        if isinstance(toc_items, list):
            all_toc_items.extend(toc_items)

        logger.log_operation(
            f"📋 TOC group {group_idx + 1}/{len(page_groups)}: +{len(toc_items) if isinstance(toc_items, list) else 0} items"
        )

    logger.log_operation(f"📋 Generated {len(all_toc_items)} TOC items total")

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

    # Step 5: Generate summaries (batched to stay within TPM limit)
    await _generate_summaries_batched(tree, groq_service)

    # Step 6: Generate document description
    tree_for_desc = _remove_text_fields(copy.deepcopy(tree))
    desc_prompt = GENERATE_DOC_DESCRIPTION_PROMPT.format(
        tree_json=json.dumps(tree_for_desc, indent=2)[:8000]
    )
    doc_description = await groq_llm_call(desc_prompt, groq_service, use_reasoning=False)

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

def _safe_struct_sort_key(structure: str) -> List[int]:
    """
    Safe sort key for structure strings — handles non-numeric parts gracefully.
    Non-numeric / mixed parts (e.g. 'Appendix A', 'A') sort after all numeric parts.
    """
    parts = str(structure).split(".")
    result = []
    for p in parts:
        digits = re.sub(r"\D", "", p.strip())
        result.append(int(digits) if digits else 9999)
    return result


def _normalize_toc_structures(items: List[Dict]) -> List[Dict]:
    """
    Remap any non-numeric structure strings to purely numeric dot-notation.
    Preserves the hierarchy: 'Appendix A' → next top-level number,
    'Appendix A.1' → '<parent_num>.1', etc.
    Items that are already purely numeric are untouched.
    """
    # Determine the highest existing top-level numeric index
    max_top = 0
    for item in items:
        s = str(item.get("structure", "1")).strip()
        top = s.split(".")[0].strip()
        if re.match(r"^\d+$", top):
            max_top = max(max_top, int(top))

    next_top = max_top + 1
    prefix_map: Dict[str, str] = {}  # original prefix → numeric equivalent

    for item in items:
        s = str(item.get("structure", "1")).strip()
        parts = [p.strip() for p in s.split(".")]

        # Check if every part is already purely numeric
        if all(re.match(r"^\d+$", p) for p in parts):
            continue  # Nothing to fix

        new_parts: List[str] = []
        for depth, p in enumerate(parts):
            if re.match(r"^\d+$", p):
                new_parts.append(p)
            else:
                orig_prefix = ".".join(parts[: depth + 1])
                if orig_prefix not in prefix_map:
                    if depth == 0:
                        prefix_map[orig_prefix] = str(next_top)
                        next_top += 1
                    else:
                        numeric_parent = ".".join(new_parts)  # already converted
                        # Count how many siblings under this numeric parent already mapped
                        sibling_count = sum(
                            1
                            for v in prefix_map.values()
                            if v.startswith(numeric_parent + ".")
                            and v.count(".") == depth
                        )
                        prefix_map[orig_prefix] = f"{numeric_parent}.{sibling_count + 1}"

                # Keep only the last component to build the new structure
                mapped = prefix_map[orig_prefix]
                new_parts.append(mapped.split(".")[-1])

        item["structure"] = ".".join(new_parts)

    return items


def _build_tree_from_flat(
    items: List[Dict], total_pages: int
) -> List[Dict]:
    """Convert flat TOC list with structure indices into a hierarchical tree."""
    # Normalise any non-numeric structure strings BEFORE sorting
    items = _normalize_toc_structures(items)

    # Sort by structure index (safe against any remaining edge-cases)
    items.sort(key=lambda x: _safe_struct_sort_key(x.get("structure", "0")))

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


def _collect_all_nodes(nodes: Any) -> List[Dict]:
    """Collect all nodes from tree into a flat list (by reference)."""
    result: List[Dict] = []
    items = nodes if isinstance(nodes, list) else [nodes]
    for node in items:
        if isinstance(node, dict):
            result.append(node)
            if "nodes" in node:
                result.extend(_collect_all_nodes(node["nodes"]))
    return result


async def _generate_summaries_batched(
    tree: Any,
    groq_service,
    batch_size: int = 5,
):
    """
    Generate summaries for all nodes in small batches to stay within TPM limits.
    Instead of firing all summaries concurrently (which blows through 250k TPM),
    we process them in batches of `batch_size` with rate-limit-aware calls.
    """
    all_nodes = _collect_all_nodes(tree)
    total = len(all_nodes)
    logger.log_operation(f"📝 Generating summaries for {total} nodes (batch_size={batch_size})")

    for i in range(0, total, batch_size):
        batch = all_nodes[i : i + batch_size]

        async def _summarize(node: Dict) -> None:
            text = node.get("text", "")
            title = node.get("title", "")
            if text:
                truncated = text[:6000]
                prompt = GENERATE_SUMMARY_PROMPT.format(title=title, text=truncated)
                try:
                    summary = await groq_llm_call(prompt, groq_service, use_reasoning=False)
                    node["summary"] = summary
                except Exception:
                    node["summary"] = f"Section: {title}"
            else:
                node["summary"] = f"Section: {title}"

        tasks = [_summarize(node) for node in batch]
        await asyncio.gather(*tasks)
        logger.log_operation(
            f"📝 Summaries: {min(i + batch_size, total)}/{total} done"
        )


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
