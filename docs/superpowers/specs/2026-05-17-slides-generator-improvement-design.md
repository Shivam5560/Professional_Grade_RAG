# Slide Generator Improvements: Narrative-First Adaptive Deck

## Overview
This design improves the PPTX slide generation pipeline to prioritize readability, aesthetic harmony (Editorial Premium style), storytelling flow, and the removal of low-quality content.

## Target Audience & Scope
- **Audience:** Business stakeholders (concise, decision-oriented).
- **Deck Length:** Capped at 12-16 slides for readability.
- **Visual Style:** Editorial Premium (clean hierarchy, whitespace, elegant typography).

## Architecture & Components

### 1. Smart Content Pagination (Overflow Handling)
Instead of aggressively shrinking text until it is unreadable, we will implement a text-chunking mechanism.
- **Component:** `app/services/analysis/slide_generator.py`
- **Logic:** If an insight or narrative block exceeds a character threshold (e.g., 350-400 characters) that would trigger extreme font-scaling, the text is split.
- **Output:** Spawns "Continuation Slides" (e.g., "Insight 1: Continued") to maintain a comfortable reading size (`BODY_SIZE`).

### 2. Placeholder & Feature Block Stripper
- **Component:** `_clean_markdown_text` in `slide_generator.py` (and potentially agent prompt tuning).
- **Logic:** Introduce strict regex/heuristics to detect and remove filler boilerplate (e.g., "[Insert text here]", "TBD", "Feature block"). 
- **Output:** Empty or purely boilerplate bullet points are dropped completely, ensuring only LLM-generated meaningful copy is presented.

### 3. Chart Quality Gating
- **Component:** `app/services/analysis/chart_generator.py` / orchestrator.
- **Logic:** Before a chart is embedded into a slide, it passes through a validation gate.
    - Checks for empty data frames.
    - Checks for zero variance (e.g., all values are the same).
- **Output:** Low-value or broken charts are skipped. The slide planner dynamically adjusts to omit the chart slide rather than showing a blank/useless graph.

### 4. Aesthetic Harmonization (Chart & Background Sync)
- **Component:** `ThemeEngine` integration with `chart_generator.py`.
- **Logic:** Extract the exact background hex colors computed by the `ThemeEngine` (including dark/light mode context) and pass them directly to Plotly's `paper_bgcolor` and `plot_bgcolor`.
- **Output:** Charts blend seamlessly into the slide background without harsh boundaries, enforcing the high-contrast but clean "Editorial Premium" look.

## Error Handling
- If text chunking fails, fallback to standard text fitting with a hard minimum size limit (moving excess text off-screen rather than shrinking to 4pt font).
- If a chart fails quality gating, log the exclusion and proceed with text-only insights.

## Testing Strategy
- Generate a sample deck using a highly verbose narrative and ensure continuation slides are spawned.
- Inject placeholder text and verify it does not appear in the final PPTX.
- Provide a zero-variance dataframe and verify the chart slide is omitted.
