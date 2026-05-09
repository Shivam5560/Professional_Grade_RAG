"""
Design Intelligence Agent.
Selects layouts, color palettes, and chart types for data insights.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.analysis.base import BaseAnalysisAgent
from app.analysis.events import DesignSpec, Insight, InsightsPrioritizedResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_PALETTES = {
    "finance": ["#1f4e79", "#2e75b5", "#70ad47", "#ffc000"],
    "healthcare": ["#5b9bd5", "#a5d6a7", "#ffcc80", "#ef9a9a"],
    "sales": ["#c55a11", "#ed7d31", "#4472c4", "#70ad47"],
    "generic": ["#4f81bd", "#9cbb58", "#f79646", "#8064a2"],
}

SYSTEM_PROMPT = """You are a design intelligence agent. Select layouts, color palettes, and chart types for data insights.

Respond ONLY with a JSON object in this exact format:
{
  "theme": "generic",
  "color_palette": ["#4f81bd", "#9cbb58", "#f79646", "#8064a2"],
  "layout": "grid",
  "chart_specs": [
    {
      "chart_id": "c1",
      "chart_type": "bar",
      "x_column": "region",
      "y_column": "revenue",
      "title": "Revenue by Region"
    }
  ]
}

Available chart_types: bar, line, scatter, histogram, heatmap, box, pie.
Available layouts: grid, list, slides.
Available themes: finance, healthcare, sales, generic."""


class DesignIntelligence(BaseAnalysisAgent):
    """Designs visual specs for the analysis report."""

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

        prompt = f"""User Query: {query}

Dataset Columns: {columns}
Numeric: {numeric}
Categorical: {categorical}

Insights:
{" ".join(ins.content for ins in insights.insights)}

Design the visualization specs."""

        try:
            data = await self._call_llm(prompt, SYSTEM_PROMPT)
            theme = data.get("theme", "generic")
            palette = data.get("color_palette", DEFAULT_PALETTES["generic"])
            layout = data.get("layout", "grid")
            chart_specs = data.get("chart_specs", [])

            logger.log_operation("Design spec generated", theme=theme, charts=len(chart_specs))
            return DesignSpec(
                theme=theme,
                color_palette=palette,
                layout=layout,
                chart_specs=chart_specs,
            )
        except Exception as exc:
            logger.log_error("Design generation failed", exc)
            return _fallback_design(numeric, categorical)


def _fallback_design(numeric: List[str], categorical: List[str]) -> DesignSpec:
    specs = []
    if numeric and categorical:
        specs.append({
            "chart_id": "c1", "chart_type": "bar",
            "x_column": categorical[0], "y_column": numeric[0],
            "title": f"{numeric[0]} by {categorical[0]}",
        })
    if len(numeric) >= 2:
        specs.append({
            "chart_id": "c2", "chart_type": "heatmap",
            "title": "Correlation Matrix",
        })
    return DesignSpec(
        theme="generic",
        color_palette=DEFAULT_PALETTES["generic"],
        layout="grid",
        chart_specs=specs,
    )
