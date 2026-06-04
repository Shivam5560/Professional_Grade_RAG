"""
Design Intelligence Agent.
Selects visual identity, storytelling arc, layouts, and chart types
for data-driven presentations. Acts as a creative director for the
slide generator engine.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from app.analysis.base import BaseAnalysisAgent
from app.analysis.events import DesignSpec, Insight, InsightsPrioritizedResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Extended palette library ──────────────────────────────

DEFAULT_PALETTES: Dict[str, List[str]] = {
    "finance":     ["#1f4e79", "#2e75b5", "#70ad47", "#ffc000"],
    "healthcare":  ["#5b9bd5", "#a5d6a7", "#ffcc80", "#ef9a9a"],
    "sales":       ["#c55a11", "#ed7d31", "#4472c4", "#70ad47"],
    "generic":     ["#4f81bd", "#9cbb58", "#f79646", "#8064a2"],
    "tech":        ["#6c5ce7", "#00cec9", "#fd79a8", "#fdcb6e"],
    "executive":   ["#2c3e50", "#3498db", "#2ecc71", "#e74c3c"],
    "dark_mint":   ["#00b894", "#55efc4", "#81ecec", "#dfe6e9"],
    "amber_royal": ["#b8860b", "#daa520", "#483d8b", "#6a5acd"],
}

THEME_DOMAIN_HINTS: Dict[str, str] = {
    "finance":    "Financial data (revenue, profit, cost, budget, ROI, investment, risk). Trustworthy, precise, authoritative.",
    "healthcare": "Medical/health data (patients, clinical, trials, diagnosis, treatment). Clean, clinical, compassionate.",
    "sales":      "Sales/marketing data (pipeline, conversion, leads, growth, campaigns). Energetic, persuasive, bold.",
    "tech":       "Technology metrics (SaaS, engineering, performance, users, uptime). Modern, innovative, sharp.",
    "executive":  "C-suite/board-level data (strategy, quarterly results, high-level KPIs). Refined, authoritative, minimal.",
    "generic":    "General-purpose analysis. Balanced, professional, adaptable.",
}

TYPE_TOKENS = {
    "Calibri":          "Clean, modern, highly readable — Microsoft's default. Works for body and headings.",
    "Calibri Light":    "Airier sibling of Calibri — good for subheadings, quotes, and supporting text.",
    "Georgia":          "Serif with authority — excellent for executive reports, formal documents.",
    "Trebuchet MS":     "Humanist sans-serif — friendly yet professional. Good for tech/creative themes.",
    "Cambria":          "Strong serif — ideal for financial, legal, or academic presentations.",
    "Arial":            "Universal sans-serif — safe, neutral, compatible everywhere.",
    "Arial Black":      "Heavy impact sans-serif — good for hero titles and stat callouts.",
}

TEMPLATE_STYLES: Dict[str, str] = {
    "aurora": "Dark, cinematic gradients with geometric depth. Best for tech/innovation.",
    "editorial": "Light, magazine-like layout with serif headings and strong hierarchy.",
    "minimal": "Whitespace-forward, thin rules, restrained palette. Great for executive briefings.",
    "bold": "High-contrast color blocks, energetic emphasis, big stat moments.",
}

THEME_TEMPLATE_DEFAULT: Dict[str, str] = {
    "finance": "editorial",
    "healthcare": "minimal",
    "sales": "bold",
    "tech": "aurora",
    "executive": "minimal",
    "generic": "editorial",
}

THEME_TEMPLATE_OPTIONS: Dict[str, List[str]] = {
    "finance": ["editorial", "minimal", "aurora"],
    "healthcare": ["minimal", "editorial"],
    "sales": ["bold", "aurora", "editorial"],
    "tech": ["aurora", "bold", "minimal"],
    "executive": ["minimal", "editorial"],
    "generic": ["editorial", "minimal", "aurora", "bold"],
}

THEME_MOTIF_DEFAULT: Dict[str, str] = {
    "finance": "grid",
    "healthcare": "rings",
    "sales": "diagonal",
    "tech": "dots",
    "executive": "line",
    "generic": "grid",
}

THEME_MOTIF_OPTIONS: Dict[str, List[str]] = {
    "finance": ["grid", "line", "rings"],
    "healthcare": ["rings", "line", "dots"],
    "sales": ["diagonal", "dots", "grid"],
    "tech": ["dots", "grid", "diagonal"],
    "executive": ["line", "grid", "rings"],
    "generic": ["grid", "rings", "diagonal", "dots", "line"],
}

STYLE_TYPOGRAPHY: Dict[str, Dict[str, str]] = {
    "aurora": {"title_font": "Trebuchet MS", "body_font": "Calibri", "stat_font": "Arial Black"},
    "editorial": {"title_font": "Georgia", "body_font": "Calibri", "stat_font": "Arial Black"},
    "minimal": {"title_font": "Calibri Light", "body_font": "Calibri", "stat_font": "Calibri"},
    "bold": {"title_font": "Arial Black", "body_font": "Arial", "stat_font": "Arial Black"},
}


SYSTEM_PROMPT = """You are a senior creative director and presentation designer. Given a dataset profile and analytical insights, produce a comprehensive design brief for a data storytelling presentation.

## Your Task

Design a visual narrative that guides the audience through the data story. Consider:
1. **Domain**: What industry/context does the data suggest? Choose a theme that reinforces the message.
2. **Mood**: What emotional response should the presentation evoke? Trust, excitement, urgency, calm?
3. **Hierarchy**: Which insights deserve hero treatment? Which are supporting evidence?
4. **Rhythm**: Alternate between dense information slides and visual breathers.
5. **Storytelling**: Charts are evidence, not the story. Include context, interpretation, decision implications, and next moves.
6. **Typography**: Font choices affect perceived credibility. Match to the domain.
7. **Template variety**: Do not always choose the safest default. Pick a template family that gives the deck a distinct visual point of view.
8. **Theme-prone visuals**: Chart specs must carry the same palette, typography, and mood as the slide deck so exported chart images feel native to the presentation.

## Available Design Tokens

Themes and their best-fit domains:
- finance: trustworthy, precise — for financial reports, revenue analysis, risk assessment
- healthcare: clean, clinical, caring — for patient data, clinical trials, health trends
- sales: energetic, persuasive — for pipelines, market analysis, growth reports
- tech: modern, innovative — for product analytics, engineering metrics, SaaS
- executive: refined, authoritative — for C-suite briefings, board decks, annual reviews
- generic: balanced, professional — for general multi-domain analysis

Chart types mapped to analytical intent:
- bar: comparison across categories
- line: trend over time
- scatter: correlation / distribution
- histogram: frequency distribution
- heatmap: correlation matrix / intensity
- box: statistical distribution with outliers
- pie: part-to-whole (use sparingly, max 5 categories)
- area: volume / cumulative trends
- violin: distribution shape comparison

Slide structure options (ordered list; this is a recommendation, not a fixed slide count):
- title: hero/cover slide
- summary: executive summary with key numbers
- insights: one big insight per slide with evidence
- charts: embedded visualizations
- recommendations: action-oriented next steps
- closing: thank you / call to action

Template style families (choose one):
- aurora: dark cinematic gradients with geometric depth
- editorial: light magazine-like layouts with serif titles
- minimal: whitespace-forward with subtle accents
- bold: high-contrast color blocks and strong emphasis

Visual motifs (choose one):
- grid, rings, diagonal, dots, line

## Response Format

Respond ONLY with a valid JSON object — no markdown, no backticks:

{
  "theme": "finance",
  "color_palette": ["#1f4e79", "#2e75b5", "#70ad47", "#ffc000"],
  "layout": "slides",
  "slide_structure": ["title", "summary", "insights", "charts", "recommendations", "closing"],
  "typography": {
    "title_font": "Georgia",
    "body_font": "Calibri",
    "stat_font": "Arial Black"
  },
  "template_style": "editorial",
  "visual_motif": "grid",
  "slide_density": "medium",
  "animation_hint": "minimal",
  "storytelling_arc": "Context → Discovery → Evidence → Action",
  "design_principle": "Less is more — let data breathe. Use white space as a design element. One message per slide.",
  "mood_description": "Confident, structured, and executive-ready with quiet authority.",
  "chart_specs": [
    {
      "chart_id": "c1",
      "chart_type": "bar",
      "x_column": "region",
      "y_column": "revenue",
      "title": "Revenue by Region",
      "highlight_insight": true,
      "narrative_role": "Establishes geographic performance baseline",
      "colors": ["#1f4e79", "#2e75b5", "#70ad47", "#ffc000"],
      "template_style": "editorial",
      "visual_motif": "grid",
      "theme": "finance"
    }
  ]
}

Rules:
- color_palette must have exactly 4 hex colors with # prefix
- slide_structure must be ordered and use only: title, summary, insights, charts, recommendations, closing; the PPTX generator will still decide final slide count from content depth
- slide_density must be: minimal, medium, or rich
- animation_hint must be: none, minimal, or moderate
- storytelling_arc should be 3-5 short phases separated by →, for example: Context → Discovery → Evidence → Action
- template_style must be one of: aurora, editorial, minimal, bold
- visual_motif must be one of: grid, rings, diagonal, dots, line
- Choose different template_style/visual_motif combinations when the domain, query, or dataset shape calls for a different deck personality
- Each chart_spec must include narrative_role explaining its purpose in the story
- Prefer fewer meaningful charts over many shallow chart types; do not create a chart unless it answers a real analytical question
- If a chart repeats a metric, make its narrative_role different: baseline, driver, risk, segment, trend, or decision implication
- The deck must include non-chart storytelling moments: overview, implications, watchouts, future plan, or decision roadmap
- Each chart_spec should include colors, template_style, visual_motif, and theme so chart images match the deck
- Limit to top 8 most impactful insights (for chart specs)
"""


class DesignIntelligence(BaseAnalysisAgent):
    """Creative director agent — produces design briefs for the slide generator."""

    def __init__(self):
        super().__init__(agent_name="DesignIntelligence", use_structured_llm=True)

    async def run(
        self,
        insights: InsightsPrioritizedResult,
        profile: Dict[str, Any],
        query: str,
    ) -> DesignSpec:
        columns = profile.get("columns", [])
        numeric = profile.get("numeric_columns", [])
        categorical = profile.get("categorical_columns", [])
        datetime_cols = profile.get("datetime_columns", [])

        # Gather insight texts
        insight_texts = "\n".join(
            f"[{ins.significance_score:.2f}] {ins.content}" for ins in insights.insights[:10]
        )

        # Domain hints based on column names
        domain_hint = _infer_domain(columns)

        prompt = f"""User Query: {query}

Dataset Snapshot:
- Rows: {profile.get('row_count', 'unknown')}
- Numeric columns: {numeric}
- Categorical columns: {categorical}
- Datetime columns: {datetime_cols}
- Analyst brief: {profile.get('analysis_brief', {})}
- Domain hint: {domain_hint}

Prioritized Insights:
{insight_texts}

Design a detailed professional presentation for this analysis. Match the theme to the domain.
Assign chart types only where visualization improves the story. The rest of the deck should explain context, meaning, implications, and future actions."""

        try:
            data = await self._call_llm(prompt, SYSTEM_PROMPT)

            theme = _normalize_theme(str(data.get("theme", "generic")))
            palette = _normalize_palette(data.get("color_palette"), theme)
            layout = data.get("layout", "slides")
            chart_specs = data.get("chart_specs", [])
            slide_structure = data.get("slide_structure", ["title", "summary", "insights", "charts", "recommendations", "closing"])
            typography = data.get("typography", {})
            slide_density = data.get("slide_density", "medium")
            if _query_requests_depth(query):
                slide_density = "rich"
            animation_hint = data.get("animation_hint", "minimal")
            storytelling_arc = data.get("storytelling_arc", "")
            design_principle = data.get("design_principle", "")
            mood_description = data.get("mood_description", "")
            context_key = _context_key(query, profile, insight_texts)
            template_style = (data.get("template_style") or "").lower()
            if template_style not in TEMPLATE_STYLES:
                template_style = _choose_varied(THEME_TEMPLATE_OPTIONS, THEME_TEMPLATE_DEFAULT, theme, context_key)

            visual_motif = (data.get("visual_motif") or "").lower()
            if visual_motif not in {"grid", "rings", "diagonal", "dots", "line"}:
                visual_motif = _choose_varied(THEME_MOTIF_OPTIONS, THEME_MOTIF_DEFAULT, theme, context_key, salt="motif")

            typography = _normalize_typography(typography, template_style)

            for spec in chart_specs:
                if isinstance(spec, dict):
                    spec.setdefault("colors", palette)
                    spec.setdefault("template_style", template_style)
                    spec.setdefault("visual_motif", visual_motif)
                    spec.setdefault("theme", theme)
                    spec.setdefault("typography", typography)

            logger.log_operation(
                "Design spec generated",
                theme=theme,
                charts=len(chart_specs),
                arc=storytelling_arc,
            )

            return DesignSpec(
                theme=theme,
                color_palette=palette,
                layout=layout,
                chart_specs=chart_specs,
                slide_structure=slide_structure,
                typography=typography,
                slide_density=slide_density,
                animation_hint=animation_hint,
                storytelling_arc=storytelling_arc,
                design_principle=design_principle,
                mood_description=mood_description,
                template_style=template_style,
                visual_motif=visual_motif,
            )
        except Exception as exc:
            logger.log_error("Design generation failed", exc)
            return _fallback_design(numeric, categorical, profile)


# ── Helpers ────────────────────────────────────────────────

def _infer_domain(columns: List[Any]) -> str:
    """Guess the dataset domain from column names. Handles both string lists and dict lists."""
    # Extract names from dict format if needed
    if columns and isinstance(columns[0], dict):
        col_names = [c.get("name", "") for c in columns]
    else:
        col_names = [str(c) for c in columns]
    cols_lower = " ".join(col_names).lower()
    financial_kw = [
        "revenue", "profit", "cost", "budget", "income", "expense", "financial", "roi",
        "credit", "default", "loan", "limit_bal", "bill_amt", "pay_amt", "payment",
        "balance", "delinquency", "risk", "debt",
    ]
    health_kw = ["patient", "diagnosis", "treatment", "clinical", "hospital", "medical", "drug", "health"]
    sales_kw = ["sales", "lead", "conversion", "pipeline", "campaign", "customer", "churn", "deal"]
    tech_kw = ["cpu", "memory", "latency", "uptime", "request", "error_rate", "user", "api", "server"]

    scores = {
        "finance": sum(1 for kw in financial_kw if kw in cols_lower),
        "healthcare": sum(1 for kw in health_kw if kw in cols_lower),
        "sales": sum(1 for kw in sales_kw if kw in cols_lower),
        "tech": sum(1 for kw in tech_kw if kw in cols_lower),
    }
    best = max(scores, key=lambda k: scores[k])  # type: ignore[arg-type]
    if scores[best] > 0:
        return f"{best} ({THEME_DOMAIN_HINTS[best]})"
    return f"generic ({THEME_DOMAIN_HINTS['generic']})"


def _context_key(query: str, profile: Dict[str, Any], insight_texts: str) -> str:
    columns = profile.get("columns", [])
    raw = f"{query}|{profile.get('row_count')}|{columns}|{insight_texts[:500]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _normalize_theme(theme: str) -> str:
    theme = theme.lower().strip()
    return theme if theme in THEME_DOMAIN_HINTS else "generic"


def _normalize_palette(palette: Any, theme: str) -> List[str]:
    default = DEFAULT_PALETTES.get(theme, DEFAULT_PALETTES["generic"])
    if not isinstance(palette, list):
        return default
    cleaned = [str(c) for c in palette if isinstance(c, str) and c.startswith("#") and len(c) == 7]
    return (cleaned + default)[:4]


def _choose_varied(
    options_by_theme: Dict[str, List[str]],
    defaults_by_theme: Dict[str, str],
    theme: str,
    context_key: str,
    salt: str = "style",
) -> str:
    options = options_by_theme.get(theme) or [defaults_by_theme.get(theme, defaults_by_theme["generic"])]
    idx = int(hashlib.sha1(f"{salt}:{context_key}".encode("utf-8")).hexdigest()[:8], 16) % len(options)
    return options[idx]


def _normalize_typography(typography: Dict[str, Any], template_style: str) -> Dict[str, str]:
    defaults = STYLE_TYPOGRAPHY.get(template_style, STYLE_TYPOGRAPHY["editorial"])
    return {
        "title_font": str(typography.get("title_font") or defaults["title_font"]),
        "body_font": str(typography.get("body_font") or defaults["body_font"]),
        "stat_font": str(typography.get("stat_font") or defaults["stat_font"]),
    }


def _query_requests_depth(query: str) -> bool:
    q = query.lower()
    return any(token in q for token in ("detailed", "comprehensive", "deep", "storytelling", "slides", "ppt", "presentation"))


def _fallback_design(numeric: List[str], categorical: List[str], profile: Dict[str, Any]) -> DesignSpec:
    """Generate a sensible design fallback from the dataset profile."""
    domain = _infer_domain(profile.get("columns", []))
    theme = _normalize_theme(domain.split(" ")[0] if domain else "generic")
    palette = DEFAULT_PALETTES.get(theme, DEFAULT_PALETTES["generic"])
    context_key = _context_key("", profile, "")
    template_style = _choose_varied(THEME_TEMPLATE_OPTIONS, THEME_TEMPLATE_DEFAULT, theme, context_key)
    visual_motif = _choose_varied(THEME_MOTIF_OPTIONS, THEME_MOTIF_DEFAULT, theme, context_key, salt="motif")
    typography = _normalize_typography({}, template_style)

    specs = []
    if numeric and categorical:
        specs.append({
            "chart_id": "c1", "chart_type": "bar",
            "x_column": categorical[0], "y_column": numeric[0],
            "title": f"{numeric[0]} by {categorical[0]}",
            "highlight_insight": True,
            "narrative_role": "Baseline comparison across categories",
            "colors": palette,
            "template_style": template_style,
            "visual_motif": visual_motif,
            "theme": theme,
            "typography": typography,
        })
    if len(numeric) >= 2:
        specs.append({
            "chart_id": "c2", "chart_type": "heatmap",
            "title": "Correlation Matrix",
            "highlight_insight": False,
            "narrative_role": "Relationship overview between numeric variables",
            "colors": palette,
            "template_style": template_style,
            "visual_motif": visual_motif,
            "theme": theme,
            "typography": typography,
        })
    if len(numeric) >= 1:
        specs.append({
            "chart_id": "c3", "chart_type": "histogram",
            "x_column": numeric[0], "title": f"Distribution of {numeric[0]}",
            "highlight_insight": False,
            "narrative_role": "Data distribution and outlier visibility",
            "colors": palette,
            "template_style": template_style,
            "visual_motif": visual_motif,
            "theme": theme,
            "typography": typography,
        })

    return DesignSpec(
        theme=theme,
        color_palette=palette,
        layout="slides",
        chart_specs=specs,
        slide_structure=["title", "summary", "insights", "charts", "recommendations", "closing"],
        typography=typography,
        slide_density="medium",
        animation_hint="minimal",
        storytelling_arc="Context → Discovery → Evidence → Action",
        design_principle="One insight per slide with breathing room.",
        mood_description="Clear, structured, and professional.",
        template_style=template_style,
        visual_motif=visual_motif,
    )
