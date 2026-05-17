# Slide Generator Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement text overflow pagination, placeholder cleanup, chart quality gating, and chart-background color harmonization for the PPTX slide generator.

**Architecture:** We will extend the `slide_generator.py` with text chunking logic for insights, enhance the markdown cleaner to drop filler text, add statistical checks in `chart_generator.py` to skip useless charts, and pass exact hex colors to Plotly to harmonize with the presentation theme.

**Tech Stack:** Python 3.11, `python-pptx`, `plotly`, `pandas`

---

### Task 1: Clean Placeholder Boilerplate

**Files:**
- Modify: `backend/app/services/analysis/slide_generator.py`
- Test: `backend/tests/test_slide_cleaning.py` (Create)

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest backend/tests/test_slide_cleaning.py -v`
Expected: FAIL due to missing logic in `_clean_markdown_text`.

- [ ] **Step 3: Write minimal implementation**

Modify `_clean_markdown_text` and `_extract_bullets` in `backend/app/services/analysis/slide_generator.py`:

```python
import re

def _clean_markdown_text(text: Any) -> str:
    """Remove lightweight Markdown artifacts and boilerplates before placing text in PPTX boxes."""
    cleaned = str(text or "").replace("\r", " ").replace("\n", " ")
    
    # Strip common LLM placeholders
    placeholders = [r"\[Insert text here\]", r"\[Insert.*?\]", r"\bTBD\b", r"Feature block", r"\[.*?\]"]
    for p in placeholders:
        cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)
        
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__(.*?)__", r"\1", cleaned)
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" -*•▸")

def _extract_bullets(md_text: str) -> List[str]:
    """Extract bullet points from markdown text, dropping empty or filler points."""
    bullets: List[str] = []
    for line in md_text.split("\n"):
        stripped = line.strip()
        bullet_text = ""
        if stripped.startswith(("- ", "* ", "• ", "▸ ")):
            bullet_text = _clean_markdown_text(stripped[2:].strip())
        elif stripped.startswith(tuple("0123456789")) and ". " in stripped[:4]:
            bullet_text = _clean_markdown_text(stripped.split(". ", 1)[1].strip())
            
        if bullet_text and len(bullet_text) > 3: # Skip empty or tiny filler
            bullets.append(bullet_text)
            
    return bullets[:8]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest backend/tests/test_slide_cleaning.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/analysis/slide_generator.py backend/tests/test_slide_cleaning.py
git commit -m "feat(analysis): strip template placeholders and filler from slide text"
```

---

### Task 2: Chart Quality Gating & Theming

**Files:**
- Modify: `backend/app/services/analysis/chart_generator.py`
- Modify: `backend/app/services/analysis/slide_generator.py`

- [ ] **Step 1: Write minimal implementation for chart gating**

Modify `create_chart` in `backend/app/services/analysis/chart_generator.py` to check for data validity. Return `None` if invalid.

```python
def create_chart(
    spec: Dict[str, Any],
    df: pd.DataFrame,
    job_id: str,
    chart_id: str,
) -> str | None:
    """Create a chart from a spec and save via the configured storage backend. Returns None if data is weak."""
    if df is None or df.empty:
        logger.warning(f"Skipping chart {chart_id} due to empty dataframe.")
        return None
        
    df, spec = _repair_chart_spec(spec, df)
    
    # Check for zero variance on numeric y columns
    y_col = spec.get("y_column")
    if y_col and y_col in df.select_dtypes(include="number").columns:
        if df[y_col].nunique(dropna=True) <= 1:
            logger.warning(f"Skipping chart {chart_id} due to zero variance in y_column {y_col}.")
            return None

    # (Rest of create_chart logic remains the same)
```

- [ ] **Step 2: Write minimal implementation for chart theming**

Modify `_apply_chart_theme` in `backend/app/services/analysis/chart_generator.py` to accept specific bg hex colors instead of guessing from `theme`. 
Wait, the `ThemeEngine` defines `self.bg`. We need to pass that down, but `chart_generator.py` doesn't have `ThemeEngine`. Let's pass the bg hex explicitly.

```python
def _apply_chart_theme(
    fig: go.Figure,
    spec: Dict[str, Any],
    theme: str,
    template_style: str,
    colors: List[str] | None,
    typography: Dict[str, Any],
    bg_hex: str | None = None, # NEW PARAM
) -> None:
    dark = template_style in DARK_STYLES
    paper_bg = bg_hex if bg_hex else (DARK_CHART_BG.get(theme, DARK_CHART_BG["generic"]) if dark else LIGHT_CHART_BG.get(theme, LIGHT_CHART_BG["generic"]))
    plot_bg = paper_bg
    # (Rest of _apply_chart_theme remains the same)
```

Update `create_chart` signature and call to `_apply_chart_theme` to forward `bg_hex`:
```python
def create_chart(
    spec: Dict[str, Any],
    df: pd.DataFrame,
    job_id: str,
    chart_id: str,
    bg_hex: str | None = None,
) -> str | None:
    # ...
    _apply_chart_theme(fig, spec, theme, template_style, colors, typography, bg_hex=bg_hex)
    # ...
```

Modify `generate_charts` in `backend/app/services/analysis/chart_generator.py`:
```python
def generate_charts(
    chart_specs: List[Dict[str, Any]],
    df: pd.DataFrame,
    job_id: str,
    bg_hex: str | None = None,
) -> List[str]:
    paths: List[str] = []
    for idx, spec in enumerate(chart_specs):
        chart_id = spec.get("chart_id") or f"chart_{idx}"
        try:
            path = create_chart(spec, df, job_id, chart_id, bg_hex=bg_hex)
            if path: # Only append if not None
                paths.append(path)
        except Exception as exc:
            logger.log_error("Chart generation skipped", exc, chart_id=chart_id, job_id=job_id)
    return paths
```

- [ ] **Step 3: Update Analysis Workflow to pass bg_hex**

Modify `backend/app/analysis/workflows/analysis_workflow.py` around line 480 to extract the bg_hex if possible, or we can just let `slide_generator` do it later. Actually, `slide_generator` loads existing images. Since charts are generated *before* slides, `analysis_workflow.py` generates the charts.

We need to deduce `bg_hex` in `analysis_workflow.py`.
```python
# backend/app/analysis/workflows/analysis_workflow.py
# Inside compose_presentation (around line 462):
        # Extract bg_hex logic
        from app.services.analysis.slide_generator import THEME_BG, LIGHT_BG
        theme_name = design_data.get("theme", "generic")
        style = design_data.get("template_style", "editorial").lower()
        mode = "dark" if style in ["aurora", "bold"] else "light"
        bg_hex_str = THEME_BG.get(theme_name, "1A1A2E") if mode == "dark" else LIGHT_BG.get(theme_name, "F7F8FB")
        bg_hex = f"#{bg_hex_str}"

        chart_paths = generate_charts(
            chart_specs=design.chart_specs,
            df=df,
            job_id=report.id,
            bg_hex=bg_hex
        )
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/analysis/chart_generator.py backend/app/analysis/workflows/analysis_workflow.py
git commit -m "feat(analysis): gate low quality charts and harmonize chart backgrounds"
```

---

### Task 3: Text Chunking & Insight Pagination

**Files:**
- Modify: `backend/app/services/analysis/slide_generator.py`

- [ ] **Step 1: Write text chunker utility**

In `backend/app/services/analysis/slide_generator.py`, add `_chunk_text`:

```python
def _chunk_text(text: str, max_chars: int = 350) -> List[str]:
    """Split long text into readable chunks without breaking words."""
    if not text:
        return []
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        if current_length + len(word) + 1 > max_chars and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 1
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks
```

- [ ] **Step 2: Update `_insight_slides` to use chunking**

In `_insight_slides` (around line 666):
```python
def _insight_slides(prs, insights: list, chart_paths: list, theme: ThemeEngine, palette: list,
                    design_spec: dict, style: str, typography: Dict[str, str],
                    insight_limit: int | None = None):
    # ... setup code ...
    
    selected_insights = insights[:insight_limit] if insight_limit else insights
    for idx, ins in enumerate(selected_insights):
        content = _clean_markdown_text(ins.get("content", ""))
        chunks = _chunk_text(content, max_chars=350)
        
        for chunk_idx, chunk in enumerate(chunks):
            slide = prs.slides.add_slide(prs.slide_layouts[6])
            _set_bg(slide, theme.bg)
            if style in ("editorial", "minimal"):
                _light_geometric_background(slide, theme)
            else:
                _geometric_background(slide, theme)
            _apply_motif(slide, theme, motif)

            # Compact slide number marker
            num = f"{idx + 1:02d}" + (f".{chunk_idx+1}" if len(chunks) > 1 else "")
            # ... draw number ...

            # Section label
            label = f"INSIGHT {idx + 1}" + (" (CONTINUED)" if chunk_idx > 0 else "") + f"  •  {arc}"
            _section_label(slide, label, theme, body_font)

            # Main insight statement (using chunk instead of full content)
            h2_size, h2_max = TITLE_LEVELS["H2"]
            _add_text_box_fit(slide, MARGIN, Inches(1.2), Inches(6.8), Inches(1.8),
                      chunk, h2_size, theme.white, bold=True, font=title_font, spacing=34,
                      max_chars=h2_max, min_size=14)

            # Only show story context and score bar on the first chunk slide
            if chunk_idx == 0:
                _accent_divider(slide, Inches(3.0), theme, width_ratio=0.12)
                
                story_context = _story_context_for_insight(idx, chunk, arc)
                _add_text_box(slide, MARGIN, Inches(3.3), Inches(6.8), Inches(0.8),
                          story_context, BODY_SIZE, theme.muted, italic=True, font=body_font, spacing=18)
                
                score = ins.get("significance_score", 0)
                sources = ins.get("source_agents", [])
                
                bar_y = Inches(4.3)
                _add_rect(slide, MARGIN, bar_y, Inches(3.5), Inches(0.05), theme.dark_muted)
                _add_rect(slide, MARGIN, bar_y, Inches(3.5 * score), Inches(0.05), theme.accent(idx % 4))
                _add_text_box(slide, Inches(4.5), Inches(4.2), Inches(1.2), Inches(0.3),
                          f"{score:.0%}", 12, theme.accent(idx % 4), bold=True, font=stat_font)
                _add_text_box(slide, MARGIN, Inches(4.5), Inches(4), Inches(0.3),
                          f"Confidence  •  {', '.join(sources[:2]) if sources else 'Multiple agents'}",
                          BODY_SMALL - 1, theme.dark_muted, font=body_font)

            # RIGHT COLUMN: Visual chart reference
            right_x = Inches(7.8)
            chart_img = _find_chart_for_insight(idx, chart_paths)
            if chart_img:
                try:
                    _add_rect(slide, right_x - Inches(0.08), Inches(1.12), Inches(4.96), Inches(3.96), theme.surface)
                    slide.shapes.add_picture(chart_img, right_x, Inches(1.2), Inches(4.8), Inches(3.8))
                except Exception:
                    _chart_placeholder(slide, right_x, Inches(1.2), Inches(4.8), Inches(3.8),
                                       theme, idx, "Chart visualization", body_font)
            else:
                _chart_placeholder(slide, right_x, Inches(1.2), Inches(4.8), Inches(3.8),
                                   theme, idx, f"Insight {idx + 1}", body_font)

            # Right-side insight tag
            if chunk_idx == 0:
                tag_y = Inches(5.3)
                _add_rect(slide, right_x, tag_y, Inches(4.8), Inches(0.04), theme.accent(idx % 4))
                _add_text_box(slide, right_x, tag_y + Inches(0.15), Inches(4.8), Inches(0.5),
                          f"Key Insight #{idx + 1}: {chunk[:100]}...",
                          9, theme.muted, font=body_font, spacing=14)

            _bottom_strip(slide, theme, alpha=0.45 if style in ("editorial", "minimal") else 0.85)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/analysis/slide_generator.py
git commit -m "feat(analysis): add text chunking and pagination for long insight slides"
```

---
````