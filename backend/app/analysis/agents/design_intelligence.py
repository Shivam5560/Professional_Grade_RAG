"""
Design Intelligence Agent.
Selects visual identity, storytelling arc, layouts, and chart types
for data-driven presentations. Acts as a creative director for the
slide generator engine.
"""

from __future__ import annotations

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


SYSTEM_PROMPT = """You are a senior creative director and presentation designer. Given a dataset profile and analytical insights, produce a comprehensive design brief for a data storytelling presentation.

## Your Task

Design a visual narrative that guides the audience through the data story. Consider:
1. **Domain**: What industry/context does the data suggest? Choose a theme that reinforces the message.
2. **Mood**: What emotional response should the presentation evoke? Trust, excitement, urgency, calm?
3. **Hierarchy**: Which insights deserve hero treatment? Which are supporting evidence?
4. **Rhythm**: Alternate between dense information slides and visual breathers.
5. **Typography**: Font choices affect perceived credibility. Match to the domain.

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

Slide structure options (ordered list):
- title: hero/cover slide
- summary: executive summary with key numbers
- insights: one big insight per slide with evidence
- charts: embedded visualizations
- recommendations: action-oriented next steps
- closing: thank you / call to action

## Response Format

Respond ONLY with a valid JSON object — no markdown, no backticks:

{
  "theme": "finance",
  "color_palette": ["#1f4e79", "#2e75b5", "#70ad47", "#ffc000"],
  "layout": "slides",
  "slide_structure": ["title", "summary", "insights", "charts", "recommendations", "closing"],
  "mood_description": "A confident, data-rich narrative that builds from macro context to specific recommendations. The palette conveys institutional trust with energy accents.",
  "typography": {
    "title_font": "Calibri",
    "body_font": "Calibri",
    "stat_font": "Arial Black"
  },
  "slide_density": "medium",
  "animation_hint": "minimal",
  "storytelling_arc": "Context → Discovery → Evidence → Action",
  "chart_specs": [
    {
      "chart_id": "c1",
      "chart_type": "bar",
      "x_column": "region",
      "y_column": "revenue",
      "title": "Revenue by Region",
      "highlight_insight": true,
      "narrative_role": "Establishes geographic performance baseline"
    }
  ],
  "design_principle": "Less is more — let data breathe. Use white space as a design element. One message per slide."
}

Rules:
- color_palette must have exactly 4 hex colors with # prefix
- slide_structure must be ordered and use only: title, summary, insights, charts, recommendations, closing
- slide_density must be: minimal, medium, or rich
- animation_hint must be: none, minimal, or moderate
- storytelling_arc should be a 3-5 word narrative framing
- Each chart_spec must include narrative_role explaining its purpose in the story
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
- Domain hint: {domain_hint}

Prioritized Insights:
{insight_texts}

Design a professional presentation for this analysis. Match the theme to the domain.
Assign chart types to insights based on their analytical intent."""

        try:
            data = await self._call_llm(prompt, SYSTEM_PROMPT)

            theme = data.get("theme", "generic")
            palette = data.get("color_palette") or DEFAULT_PALETTES.get(theme, DEFAULT_PALETTES["generic"])
            layout = data.get("layout", "slides")
            chart_specs = data.get("chart_specs", [])
            slide_structure = data.get("slide_structure", ["title", "summary", "insights", "charts", "recommendations", "closing"])
            typography = data.get("typography", {})
            slide_density = data.get("slide_density", "medium")
            animation_hint = data.get("animation_hint", "minimal")
            storytelling_arc = data.get("storytelling_arc", "")
            design_principle = data.get("design_principle", "")

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
    financial_kw = ["revenue", "profit", "cost", "budget", "income", "expense", "financial", "roi", "revenue"]
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


def _fallback_design(numeric: List[str], categorical: List[str], profile: Dict[str, Any]) -> DesignSpec:
    """Generate a sensible design fallback from the dataset profile."""
    domain = _infer_domain(profile.get("columns", []))
    theme = domain.split(" ")[0] if domain else "generic"
    palette = DEFAULT_PALETTES.get(theme, DEFAULT_PALETTES["generic"])

    specs = []
    if numeric and categorical:
        specs.append({
            "chart_id": "c1", "chart_type": "bar",
            "x_column": categorical[0], "y_column": numeric[0],
            "title": f"{numeric[0]} by {categorical[0]}",
            "highlight_insight": True,
            "narrative_role": "Baseline comparison across categories",
        })
    if len(numeric) >= 2:
        specs.append({
            "chart_id": "c2", "chart_type": "heatmap",
            "title": "Correlation Matrix",
            "highlight_insight": False,
            "narrative_role": "Relationship overview between numeric variables",
        })
    if len(numeric) >= 1:
        specs.append({
            "chart_id": "c3", "chart_type": "histogram",
            "x_column": numeric[0], "title": f"Distribution of {numeric[0]}",
            "highlight_insight": False,
            "narrative_role": "Data distribution and outlier visibility",
        })

    return DesignSpec(
        theme=theme,
        color_palette=palette,
        layout="slides",
        chart_specs=specs,
        slide_structure=["title", "summary", "insights", "charts", "recommendations", "closing"],
        typography={"title_font": "Calibri", "body_font": "Calibri", "stat_font": "Arial Black"},
        slide_density="medium",
        animation_hint="minimal",
    )
