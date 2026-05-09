"""
Narrative Generator Agent.
Writes executive summaries and detailed report sections from prioritized insights.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.analysis.base import BaseAnalysisAgent
from app.analysis.events import Insight, InsightsPrioritizedResult, NarrativeGeneratedResult, ReportSection
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a senior data storyteller. Write an executive summary and detailed sections in Markdown.
Each insight must have a 'So What?' and an actionable recommendation.

Respond ONLY with a JSON object in this exact format:
{
  "executive_summary": "...",
  "sections": [
    {"title": "Key Findings", "content": "..."},
    {"title": "Recommendations", "content": "..."}
  ]
}"""


class NarrativeGenerator(BaseAnalysisAgent):
    """Generates narrative reports from prioritized insights."""

    def __init__(self):
        # Narrative generation needs reasoning quality, not speed
        super().__init__(agent_name="NarrativeGenerator", use_structured_llm=False)

    async def run(
        self,
        insights: InsightsPrioritizedResult,
        query: str,
        profile: Dict[str, Any],
    ) -> NarrativeGeneratedResult:
        insights_text = "\n".join(
            f"- [{ins.significance_score:.2f}] {ins.content}"
            for ins in insights.insights
        )

        prompt = f"""User Query: {query}

Dataset: {profile.get('row_count', 'unknown')} rows, {profile.get('column_count', 'unknown')} columns.

Insights:
{insights_text}

Generate a narrative report."""

        try:
            data = await self._call_llm(prompt, SYSTEM_PROMPT)
            sections = [
                ReportSection(title=s["title"], content=s["content"])
                for s in data.get("sections", [])
            ]
            logger.log_operation("Narrative generated", sections=len(sections))
            return NarrativeGeneratedResult(
                executive_summary=data.get("executive_summary", ""),
                sections=sections,
            )
        except Exception as exc:
            logger.log_error("Narrative generation failed", exc)
            summary = f"## Analysis Summary\n\nQuery: {query}\n\n### Key Insights\n\n"
            for ins in insights.insights:
                summary += f"- {ins.content}\n"
            return NarrativeGeneratedResult(
                executive_summary=summary,
                sections=[ReportSection(title="Key Insights", content=summary)],
            )
