"""
Production-grade PPTX slide generator for analysis reports.
Applies DesignIntelligence agent output to create rich, professional presentations.

Architecture:
  - ThemeEngine: color tokens, typography scales, spacing grid
  - ShapeKit: decorative primitives (gradients, patterns, dividers, icon-shapes)
  - SlideBuilder: templated slide constructors
  - generate_slides(): top-level orchestrator
"""

from __future__ import annotations

import os
import math
from typing import Any, Dict, List, Optional, Tuple

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt, Emu

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Canvas ───────────────────────────────────────────────
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)
GRID = Inches(0.4)       # base spacing unit
MARGIN = Inches(0.8)
CONTENT_W = SLIDE_W - MARGIN * 2

# ── Pre-built palettes (extended from design_intelligence) ──
THEME_BG: Dict[str, str] = {
    "finance": "0A1F39", "healthcare": "0D2B1D", "sales": "3D1A00",
    "generic": "1A1A2E", "tech": "0D1120", "executive": "141414",
}


# ═══════════════════════════════════════════════════════════
# Theme Engine
# ═══════════════════════════════════════════════════════════

class ThemeEngine:
    """Color tokens, typography, and spacing for a presentation."""

    def __init__(self, palette: List[str], theme_name: str):
        if len(palette) < 4:
            palette = ["#4f81bd", "#9cbb58", "#f79646", "#8064a2"]
        self.p = [_hex(palette[i]) for i in range(4)]
        self.bg = _hex(THEME_BG.get(theme_name, "1A1A2E"))
        self.white = _hex("FFFFFF")
        self.off_white = _hex("E8ECF0")
        self.muted = _hex("8899AA")
        self.dark_muted = _hex("556677")
        self.surface = _opacity(self.p[0], 0.12)
        self.surface_light = _opacity(self.p[1], 0.08)

    def accent(self, i: int = 0) -> RGBColor:
        return self.p[i % 4]

    def gradient_stops(self, c1: RGBColor, c2: RGBColor) -> List[RGBColor]:
        """Return 6 interpolated stops between two colors."""
        return [
            RGBColor(
                int(c1[0] + (c2[0] - c1[0]) * t),
                int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t),
            )
            for t in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        ]


# ═══════════════════════════════════════════════════════════
# Shape Kit — decorative primitives
# ═══════════════════════════════════════════════════════════

def _add_rect(slide, x, y, w, h, fill: RGBColor, alpha: float = 1.0) -> Any:
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill if alpha >= 1.0 else _blend_to_dark(fill, alpha)
    s.line.fill.background()
    return s


def _add_oval(slide, x, y, w, h, fill: RGBColor, alpha: float = 1.0) -> Any:
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill if alpha >= 1.0 else _blend_to_dark(fill, alpha)
    s.line.fill.background()
    return s


def _blend_to_dark(color: RGBColor, alpha: float) -> RGBColor:
    """Approximate a transparent color on dark background by blending to near-black."""
    return RGBColor(
        max(0, min(255, int(color[0] * alpha))),
        max(0, min(255, int(color[1] * alpha))),
        max(0, min(255, int(color[2] * alpha))),
    )


def _add_text_box(slide, x, y, w, h, text: str, size: int, color: RGBColor,
                  bold: bool = False, align=PP_ALIGN.LEFT, font: str = "Calibri",
                  italic: bool = False, spacing: int = 0) -> Any:
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.italic = italic
    p.font.name = font
    p.alignment = align
    if spacing:
        p.line_spacing = Pt(spacing)
    return tb


def _add_multi_text(slide, x, y, w, h, lines: List[Tuple[str, int, RGBColor, bool]],
                    font: str = "Calibri", align=PP_ALIGN.LEFT, spacing: int = 26) -> Any:
    """Add text box with multiple styled paragraphs."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, (text, size, color, bold) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = text
        p.font.size = Pt(size)
        p.font.color.rgb = color
        p.font.bold = bold
        p.font.name = font
        p.alignment = align
        p.line_spacing = Pt(spacing)
    return tb


# ── Decorative elements ──────────────────────────────────

def _geometric_background(slide, theme: ThemeEngine):
    """Layer abstract geometric shapes for visual depth on dark slides."""
    # Large faint circle top-right
    _add_oval(slide, Inches(10.5), Inches(-1.5), Inches(5), Inches(5),
              theme.accent(0), alpha=0.04)
    # Small accent circle bottom-left
    _add_oval(slide, Inches(-0.5), Inches(6.0), Inches(2.5), Inches(2.5),
              theme.accent(1), alpha=0.06)
    # Horizontal accent line near top
    _add_rect(slide, MARGIN, Inches(0.2), Inches(2), Inches(0.015),
              theme.accent(0), alpha=0.8)
    # Subtle grid dot bottom-right
    _add_oval(slide, Inches(12.2), Inches(6.8), Inches(0.25), Inches(0.25),
              theme.accent(2), alpha=0.15)


def _light_geometric_background(slide, theme: ThemeEngine):
    """Subtle geometric accents for light slides."""
    # Thin accent bar top
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(0.04), theme.accent(0))
    # Small corner accent
    _add_rect(slide, Inches(0), Inches(0), Inches(0.4), Inches(0.04), theme.accent(1))
    # Faint dot bottom-right
    _add_oval(slide, Inches(12.5), Inches(7.0), Inches(0.3), Inches(0.3),
              theme.accent(0), alpha=0.06)


def _accent_divider(slide, y, theme: ThemeEngine, width_ratio: float = 0.15):
    """Thin accent line at a given y position."""
    w = Inches(2.5 * width_ratio / 0.15)
    _add_rect(slide, MARGIN, y, w, Inches(0.025), theme.accent(0))


def _stat_card(slide, x, y, w, h, number: str, label: str, theme: ThemeEngine, idx: int):
    """Rendered stat callout card with number + label."""
    color = theme.accent(idx % 4)
    # Card background
    _add_rect(slide, x, y, w, h, theme.surface, alpha=0.9)
    # Top accent bar
    _add_rect(slide, x, y, w, Inches(0.05), color)
    # Number
    _add_text_box(slide, x + Inches(0.3), y + Inches(0.25), w - Inches(0.6), Inches(0.7),
                  number, 48, color, bold=True, align=PP_ALIGN.LEFT)
    # Label
    _add_text_box(slide, x + Inches(0.3), y + h - Inches(0.55), w - Inches(0.6), Inches(0.4),
                  label, 12, theme.muted, align=PP_ALIGN.LEFT)


def _icon_shape(slide, x, y, size, theme: ThemeEngine, idx: int, shape_type=MSO_SHAPE.OVAL):
    """Decorative icon placeholder using geometric shapes."""
    s = slide.shapes.add_shape(shape_type, x, y, size, size)
    s.fill.solid()
    s.fill.fore_color.rgb = _blend_to_dark(theme.accent(idx), 0.2)
    s.line.fill.background()
    # Inner shape
    inner_size = size * 0.5
    inner_x = x + (size - inner_size) // 2
    inner_y = y + (size - inner_size) // 2
    s2 = slide.shapes.add_shape(shape_type, inner_x, inner_y, inner_size, inner_size)
    s2.fill.solid()
    s2.fill.fore_color.rgb = _blend_to_dark(theme.accent(idx), 0.15)
    s2.line.fill.background()


def _side_accent_bar(slide, theme: ThemeEngine):
    """Vertical accent bar on the left side of the slide."""
    _add_rect(slide, Inches(0), Inches(0), Inches(0.08), SLIDE_H, theme.accent(0))


def _bottom_strip(slide, theme: ThemeEngine):
    """Subtle colored strip at the bottom."""
    _add_rect(slide, Inches(0), Inches(7.2), SLIDE_W, Inches(0.3), theme.accent(0), alpha=0.85)
    # Small color blocks
    for i in range(4):
        _add_rect(slide, Inches(0.8 + i * 0.4), Inches(7.3), Inches(0.28), Inches(0.06),
                  theme.accent(i))


# ═══════════════════════════════════════════════════════════
# Slide Builders
# ═══════════════════════════════════════════════════════════

def _title_slide(prs, title: str, theme: ThemeEngine, palette: List[str], brief: dict):
    """Hero / cover slide with big typography and geometric depth."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, theme.bg)
    _geometric_background(slide, theme)

    # Large decorative circle behind title area
    _add_oval(slide, Inches(-3), Inches(-2), Inches(8), Inches(8), theme.accent(0), alpha=0.04)
    _add_oval(slide, Inches(9), Inches(2), Inches(7), Inches(7), theme.accent(1), alpha=0.03)

    # Top accent line
    _add_rect(slide, MARGIN, Inches(0.8), Inches(3.5), Inches(0.04), theme.accent(0))

    # Category label
    _add_text_box(slide, MARGIN, Inches(1.1), Inches(6), Inches(0.4),
                  "DATA ANALYSIS REPORT", 11, theme.accent(0), bold=True,
                  font="Calibri", spacing=0)

    # Main title
    clean_title = title[:100]
    _add_text_box(slide, MARGIN, Inches(1.7), Inches(11.5), Inches(2.0),
                  clean_title, 44, theme.white, bold=True, font="Calibri", spacing=56)

    # Subtitle line
    mood = brief.get("mood_description", "")[:120] or "AI-Powered Insights & Recommendations"
    _add_text_box(slide, MARGIN, Inches(4.0), Inches(8), Inches(0.8),
                  mood, 16, theme.muted, italic=True, font="Calibri")

    # Divider
    _accent_divider(slide, Inches(5.0), theme)

    # Bottom metadata
    _add_text_box(slide, MARGIN, Inches(5.3), Inches(5), Inches(0.3),
                  f"Theme: {brief.get('theme', 'Professional')}  •  Layout: {brief.get('layout', 'slides')}",
                  10, theme.dark_muted, font="Calibri")

    _bottom_strip(slide, theme)


def _executive_summary_slide(prs, narrative: str, theme: ThemeEngine, sections: list):
    """Executive summary with key points extracted from narrative."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, theme.bg)
    _side_accent_bar(slide, theme)

    # Section header
    _section_label(slide, "EXECUTIVE SUMMARY", theme)
    _add_text_box(slide, MARGIN, Inches(0.65), Inches(8), Inches(0.7),
                  "Key Findings at a Glance", 28, theme.white, bold=True, font="Calibri")

    _accent_divider(slide, Inches(1.5), theme)

    # Extract the first meaningful paragraph
    para = narrative.strip()[:800] if narrative else "Analysis completed. See insights below."
    _add_text_box(slide, MARGIN, Inches(1.8), Inches(7.5), Inches(1.2),
                  para, 15, theme.off_white, font="Calibri", spacing=24)

    # Quick stat cards for sections
    if sections:
        _add_text_box(slide, MARGIN, Inches(3.3), Inches(4), Inches(0.4),
                      "REPORT SECTIONS", 10, theme.accent(0), bold=True)
        sec_list = "\n".join(
            f"▸  {s.get('title', 'Section')}" for s in sections[:4]
        )
        _add_text_box(slide, MARGIN, Inches(3.7), Inches(6), Inches(2.5),
                      sec_list, 13, theme.muted, font="Calibri", spacing=22)

    # Right column: design token preview
    _add_text_box(slide, Inches(8.5), Inches(3.3), Inches(4), Inches(0.4),
                  "DESIGN PALETTE", 10, theme.accent(0), bold=True)
    for i, c in enumerate(theme.p[:4]):
        _add_rect(slide, Inches(8.5 + i * 0.7), Inches(3.8), Inches(0.5), Inches(0.5), c)
        _add_text_box(slide, Inches(8.5 + i * 0.7), Inches(4.35), Inches(0.5), Inches(0.2),
                      f"#{_to_hex(c)}", 7, theme.dark_muted, align=PP_ALIGN.CENTER)

    _bottom_strip(slide, theme)


def _story_arc_slide(prs, design_spec: dict, theme: ThemeEngine):
    """Visual storytelling roadmap — shows the narrative journey before diving into insights."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, theme.bg)
    _side_accent_bar(slide, theme)

    _section_label(slide, "NARRATIVE JOURNEY", theme)
    arc = design_spec.get("storytelling_arc", "Context → Discovery → Evidence → Action")
    principle = design_spec.get("design_principle", "")

    _add_text_box(slide, MARGIN, Inches(0.65), Inches(10), Inches(0.7),
                  "The Data Story", 28, theme.white, bold=True, font="Calibri")
    _add_text_box(slide, MARGIN, Inches(1.3), Inches(9), Inches(0.4),
                  principle[:150] if principle else "Building insight through systematic data exploration.",
                  12, theme.muted, italic=True, font="Calibri")

    _accent_divider(slide, Inches(1.9), theme)

    # Arc phases as horizontal milestone cards
    phases = [p.strip() for p in arc.split("→")]
    if not phases or phases == [arc]:
        phases = ["Context", "Discovery", "Evidence", "Action"]

    card_w = Inches(2.6)
    card_h = Inches(3.2)
    gap = Inches(0.4)
    total_w = len(phases) * card_w + (len(phases) - 1) * gap
    start_x = (SLIDE_W - total_w) // 2
    card_y = Inches(2.5)

    phase_icons = ["🔍", "📊", "📈", "🎯", "💡", "🚀"]
    phase_labels = [
        "UNDERSTAND\nWhat the data contains", "DISCOVER\nPatterns & relationships",
        "ANALYZE\nDeep statistical tests", "VALIDATE\nSignificance & confidence",
        "SYNTHESIZE\nKey findings & narrative", "ACT\nRecommendations & next steps"
    ]

    for i, phase in enumerate(phases[:6]):
        cx = start_x + i * (card_w + gap)
        # Card background
        _add_rect(slide, cx, card_y, card_w, card_h, theme.surface)
        # Top accent
        _add_rect(slide, cx, card_y, card_w, Inches(0.05), theme.accent(i))
        # Phase number
        _add_text_box(slide, cx + Inches(0.2), card_y + Inches(0.2), Inches(1), Inches(0.4),
                      f"0{i + 1}", 14, theme.accent(i), bold=True, font="Calibri")
        # Phase name
        _add_text_box(slide, cx + Inches(0.2), card_y + Inches(0.7), card_w - Inches(0.4), Inches(0.6),
                      phase, 14, theme.white, bold=True, font="Calibri")
        # Phase description
        label_text = phase_labels[i] if i < len(phase_labels) else phase
        _add_text_box(slide, cx + Inches(0.2), card_y + Inches(1.5), card_w - Inches(0.4), Inches(1.5),
                      label_text, 10, theme.muted, font="Calibri", spacing=16)
        # Connector arrow (except last)
        if i < len(phases) - 1:
            arrow_x = cx + card_w
            arrow = slide.shapes.add_shape(
                MSO_SHAPE.RIGHT_ARROW, arrow_x, card_y + card_h // 2 - Inches(0.12),
                gap, Inches(0.24),
            )
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = _blend_to_dark(theme.accent(i), 0.3)
            arrow.line.fill.background()

    _bottom_strip(slide, theme)


def _insight_slides(prs, insights: list, chart_paths: list, theme: ThemeEngine, palette: list, design_spec: dict):
    """One insight per slide — with storytelling context and visual chart integration."""
    arc = design_spec.get("storytelling_arc", "Context → Discovery → Evidence → Action")

    for idx, ins in enumerate(insights[:8]):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _set_bg(slide, theme.bg)

        # Large number watermark
        num = f"{idx + 1:02d}"
        txb = slide.shapes.add_textbox(Inches(-0.5), Inches(-0.3), Inches(3), Inches(2))
        tf = txb.text_frame
        p = tf.paragraphs[0]
        p.text = num
        p.font.size = Pt(140)
        p.font.bold = True
        p.font.color.rgb = _blend_to_dark(theme.accent(idx % 4), 0.08)
        p.font.name = "Calibri"

        # Section label with storytelling phase
        _section_label(slide, f"INSIGHT {idx + 1}  •  {arc}", theme)

        # LEFT COLUMN: Text content
        content = ins.get("content", "")
        score = ins.get("significance_score", 0)
        sources = ins.get("source_agents", [])

        # Main insight statement
        _add_text_box(slide, MARGIN, Inches(1.2), Inches(6.8), Inches(1.8),
                      content, 22, theme.white, bold=True, font="Calibri", spacing=34)

        _accent_divider(slide, Inches(3.0), theme, width_ratio=0.12)

        # Storytelling context
        story_context = _story_context_for_insight(idx, content, arc)
        _add_text_box(slide, MARGIN, Inches(3.3), Inches(6.8), Inches(0.8),
                      story_context, 12, theme.muted, italic=True, font="Calibri", spacing=18)

        # Significance score bar
        bar_y = Inches(4.3)
        _add_rect(slide, MARGIN, bar_y, Inches(3.5), Inches(0.05), theme.dark_muted)
        _add_rect(slide, MARGIN, bar_y, Inches(3.5 * score), Inches(0.05), theme.accent(idx % 4))
        _add_text_box(slide, Inches(4.5), Inches(4.2), Inches(1.2), Inches(0.3),
                      f"{score:.0%}", 12, theme.accent(idx % 4), bold=True)
        _add_text_box(slide, MARGIN, Inches(4.5), Inches(4), Inches(0.3),
                      f"Confidence  •  {', '.join(sources[:2]) if sources else 'Multiple agents'}",
                      9, theme.dark_muted)

        # Evidence data points
        evidence = ins.get("data_evidence", {})
        if evidence:
            ev_items = []
            for k, v in list(evidence.items())[:4]:
                ev_items.append(f"▸  {k}: {v}")
            _add_text_box(slide, MARGIN, Inches(5.0), Inches(6.8), Inches(2.0),
                          "\n".join(ev_items), 10, theme.off_white, font="Calibri", spacing=16)

        # RIGHT COLUMN: Visual chart reference
        right_x = Inches(7.8)
        # Chart image area
        chart_img = _find_chart_for_insight(idx, chart_paths)
        if chart_img:
            try:
                slide.shapes.add_picture(chart_img, right_x, Inches(1.2), Inches(4.8), Inches(3.8))
            except Exception:
                _chart_placeholder(slide, right_x, Inches(1.2), Inches(4.8), Inches(3.8),
                                   theme, idx, "Chart visualization")
        else:
            # Decorative placeholder with insight number
            _chart_placeholder(slide, right_x, Inches(1.2), Inches(4.8), Inches(3.8),
                               theme, idx, f"Insight {idx + 1}")

        # Right-side insight tag
        tag_y = Inches(5.3)
        _add_rect(slide, right_x, tag_y, Inches(4.8), Inches(0.04), theme.accent(idx % 4))
        _add_text_box(slide, right_x, tag_y + Inches(0.15), Inches(4.8), Inches(0.5),
                      f"Key Insight #{idx + 1}: {content[:100]}...",
                      9, theme.muted, font="Calibri", spacing=14)

        _bottom_strip(slide, theme)


def _story_context_for_insight(idx: int, content: str, arc: str) -> str:
    """Generate a short storytelling bridge for an insight based on its position in the arc."""
    contexts = [
        "Setting the foundation — this finding establishes the baseline understanding of the data landscape.",
        "Drilling deeper — uncovering the structural patterns that drive the observed outcomes.",
        "Connecting the dots — revealing how different variables interact and influence each other.",
        "Statistical validation — confirming whether these patterns are signal or noise.",
        "Quantifying impact — measuring the magnitude and practical significance of key effects.",
        "Synthesizing across dimensions — this multi-faceted finding bridges multiple analytical perspectives.",
        "The actionable insight — translating statistical evidence into strategic direction.",
        "Looking forward — this finding points toward future trends and emerging opportunities.",
    ]
    return contexts[idx] if idx < len(contexts) else "A critical piece of the analytical mosaic."


def _find_chart_for_insight(idx: int, chart_paths: list) -> str | None:
    """Match an insight index to a corresponding chart image path."""
    png_paths = [_resolve_png_path(p) for p in chart_paths]
    valid = [p for p in png_paths if p and os.path.exists(p)]
    if idx < len(valid):
        return valid[idx]
    return None


def _chart_placeholder(slide, x, y, w, h, theme: ThemeEngine, idx: int, label: str):
    """Decorative chart area placeholder with geometric design."""
    # Border rectangle
    _add_rect(slide, x, y, w, h, theme.surface)
    # Inner decorative elements
    _icon_shape(slide, x + w // 2 - Inches(0.5), y + h // 2 - Inches(0.5), Inches(1.0), theme, idx)
    _add_text_box(slide, x + Inches(0.2), y + h - Inches(0.4), w - Inches(0.4), Inches(0.3),
                  label, 9, theme.dark_muted, align=PP_ALIGN.CENTER)


def _chart_slides(prs, chart_paths: list, theme: ThemeEngine, palette: list):
    """Chart deep-dive slides with large embedded images."""
    for idx, chart_path in enumerate(chart_paths):
        png_path = _resolve_png_path(chart_path)
        if not png_path or not os.path.exists(png_path):
            continue

        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _set_bg(slide, theme.bg)

        # Chart name from filename
        chart_name = os.path.splitext(os.path.basename(png_path))[0].replace("_", " ").title()
        _section_label(slide, "DATA VISUALIZATION", theme)
        _add_text_box(slide, MARGIN, Inches(0.65), Inches(10), Inches(0.7),
                      chart_name, 24, theme.white, bold=True, font="Calibri")

        _accent_divider(slide, Inches(1.35), theme)

        # Embed image centered
        try:
            max_w = Inches(11.5)
            max_h = Inches(5.0)
            pic = slide.shapes.add_picture(png_path, MARGIN, Inches(1.7), max_w, max_h)
        except Exception as exc:
            logger.log_error("Failed to embed chart image", exc, chart_path=png_path)
            _add_text_box(slide, MARGIN, Inches(3.5), Inches(10), Inches(1),
                          f"(Chart image unavailable: {chart_name})", 14, theme.muted)

        _bottom_strip(slide, theme)


def _recommendations_slide(prs, sections: list, theme: ThemeEngine, palette: list):
    """Action-oriented recommendations with icon cards."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, theme.bg)
    _side_accent_bar(slide, theme)

    _section_label(slide, "RECOMMENDATIONS", theme)
    _add_text_box(slide, MARGIN, Inches(0.65), Inches(8), Inches(0.7),
                  "Strategic Actions & Next Steps", 28, theme.white, bold=True, font="Calibri")

    _accent_divider(slide, Inches(1.5), theme)

    # Try to find a recommendations section, otherwise use last section
    rec_section = next(
        (s for s in sections if "recommend" in s.get("title", "").lower()), None
    )
    content_text = ""
    if rec_section:
        content_text = rec_section.get("content", "")
    elif sections:
        content_text = sections[-1].get("content", "")

    # Parse bullet points from markdown content
    bullets = _extract_bullets(content_text)
    if not bullets:
        # Fallback: use insight content as bullets
        bullets = ["Review the full analysis for domain-specific actions",
                   "Share findings with key stakeholders",
                   "Set up periodic data reviews to track progress",
                   "Integrate insights into decision-making workflows"]

    # Display as action cards in a 2×2 grid
    card_w = Inches(5.5)
    card_h = Inches(2.2)
    positions = [
        (MARGIN, Inches(2.0)),
        (MARGIN + card_w + Inches(0.5), Inches(2.0)),
        (MARGIN, Inches(4.5)),
        (MARGIN + card_w + Inches(0.5), Inches(4.5)),
    ]

    for i, (bx, by) in enumerate(positions):
        if i >= len(bullets):
            break
        # Card
        _add_rect(slide, bx, by, card_w, card_h, theme.surface)
        # Left color bar
        _add_rect(slide, bx, by, Inches(0.08), card_h, theme.accent(i))
        # Number
        _add_text_box(slide, bx + Inches(0.35), by + Inches(0.2), Inches(0.5), Inches(0.5),
                      f"{i + 1}", 28, theme.accent(i), bold=True)
        # Bullet text
        _add_text_box(slide, bx + Inches(0.35), by + Inches(0.9), card_w - Inches(0.7), card_h - Inches(1.1),
                      bullets[i][:180], 13, theme.off_white, font="Calibri", spacing=20)

    _bottom_strip(slide, theme)


def _closing_slide(prs, theme: ThemeEngine, brief: dict):
    """Thank you / closing slide."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_bg(slide, theme.bg)
    _geometric_background(slide, theme)

    _add_text_box(slide, Inches(0), Inches(2.0), SLIDE_W, Inches(1.2),
                  "Thank You", 52, theme.white, bold=True, align=PP_ALIGN.CENTER, font="Calibri")

    _add_text_box(slide, Inches(0), Inches(3.5), SLIDE_W, Inches(0.6),
                  "AI-Powered Analysis  •  Data-Driven Decisions", 16, theme.muted,
                  align=PP_ALIGN.CENTER, italic=True, font="Calibri")

    # Centered accent line
    _add_rect(slide, Inches(5.5), Inches(4.3), Inches(2.3), Inches(0.03), theme.accent(0))

    _add_text_box(slide, Inches(0), Inches(5.0), SLIDE_W, Inches(0.5),
                  f"Analysis powered by NexusMind Studio  •  Theme: {brief.get('theme', 'Professional')}",
                  10, theme.dark_muted, align=PP_ALIGN.CENTER)

    _bottom_strip(slide, theme)


# ═══════════════════════════════════════════════════════════
# Orchestrator
# ═══════════════════════════════════════════════════════════

def generate_slides(
    title: str,
    narrative: str,
    sections: List[Dict[str, Any]],
    insights: List[Dict[str, Any]],
    design_spec: Dict[str, Any],
    chart_paths: List[str],
    job_id: str,
) -> str:
    """Generate a professional PPTX from analysis results."""
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    palette = design_spec.get("color_palette", ["#4f81bd", "#9cbb58", "#f79646", "#8064a2"])
    theme_name = design_spec.get("theme", "generic")
    theme = ThemeEngine(palette, theme_name)

    slide_structure = design_spec.get("slide_structure", ["title", "summary", "insights", "charts", "recommendations", "closing"])

    # Inject storytelling arc slide between summary and insights
    if "insights" in slide_structure and design_spec.get("storytelling_arc"):
        try:
            _story_arc_slide(prs, design_spec, theme)
        except Exception as exc:
            logger.log_error("Slide generation failed for: story_arc", exc, job_id=job_id)

    # Build slides based on structure
    for element in slide_structure:
        try:
            if element == "title":
                _title_slide(prs, title, theme, palette, design_spec)
            elif element == "summary":
                _executive_summary_slide(prs, narrative, theme, sections)
            elif element == "insights" and insights:
                _insight_slides(prs, insights, chart_paths, theme, palette, design_spec)
            elif element == "charts" and chart_paths:
                _chart_slides(prs, chart_paths, theme, palette)
            elif element == "recommendations":
                _recommendations_slide(prs, sections, theme, palette)
            elif element == "closing":
                _closing_slide(prs, theme, design_spec)
        except Exception as exc:
            logger.log_error(f"Slide generation failed for: {element}", exc, job_id=job_id)

    # Persist
    output_dir = os.path.join("data", "slides")
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{job_id}.pptx")
    prs.save(path)
    logger.log_operation("Slides generated", job_id=job_id, slide_count=len(prs.slides), path=path)
    return path


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _hex(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _to_hex(c: RGBColor) -> str:
    return f"{c[0]:02x}{c[1]:02x}{c[2]:02x}"


def _opacity(c: RGBColor, alpha: float) -> RGBColor:
    """Return a color that visually approximates the base color at alpha
    when rendered over a dark background. Used for surfaces/cards."""
    return RGBColor(
        max(0, min(255, int(c[0] * alpha + 26 * (1 - alpha)))),
        max(0, min(255, int(c[1] * alpha + 26 * (1 - alpha)))),
        max(0, min(255, int(c[2] * alpha + 30 * (1 - alpha)))),
    )


def _set_bg(slide, color: RGBColor):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def _section_label(slide, text: str, theme: ThemeEngine):
    """Small uppercase section label at top of slide."""
    _add_text_box(slide, MARGIN, Inches(0.25), Inches(6), Inches(0.3),
                  text, 9, theme.accent(0), bold=True, font="Calibri")


def _resolve_png_path(path: str) -> str | None:
    """Get the PNG version of a chart path if available."""
    if not path:
        return None
    if path.endswith(".png"):
        return path if os.path.exists(path) else None
    if path.endswith(".json"):
        png = path.replace(".json", ".png")
        return png if os.path.exists(png) else None
    return path if os.path.exists(path) else None


def _extract_bullets(md_text: str) -> List[str]:
    """Extract bullet points from markdown text."""
    bullets: List[str] = []
    for line in md_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "• ", "▸ ")):
            bullets.append(stripped[2:].strip())
        elif stripped.startswith(tuple("0123456789")) and ". " in stripped[:4]:
            bullets.append(stripped.split(". ", 1)[1].strip())
    return bullets[:8]
