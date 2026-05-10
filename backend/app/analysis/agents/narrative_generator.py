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

SYSTEM_PROMPT = """You are a senior data storyteller. Write an executive-ready analytical report in Markdown.
Each insight must have a 'So What?' and an actionable recommendation. Make the content specific, structured, and presentation-ready.

Respond ONLY with a JSON object in this exact format:
{
  "executive_summary": "A concise but substantive summary of the analytical story, key risks, and recommended direction.",
  "sections": [
    {"title": "Executive Overview", "content": "..."},
    {"title": "Key Findings", "content": "..."},
    {"title": "Evidence and Drivers", "content": "..."},
    {"title": "Risks and Watchouts", "content": "..."},
    {"title": "Recommendations", "content": "..."}
  ]
}

Rules:
- Produce 4-6 sections unless the input is genuinely tiny
- Use concrete numbers, column names, and evidence when available
- Avoid generic filler; every paragraph should explain what changed, why it matters, or what to do next
- Recommendations must be action-oriented bullets"""


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
            sections = _ensure_substantive_sections(sections, insights.insights)
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
                sections=_fallback_sections(insights.insights),
            )


def _ensure_substantive_sections(sections: List[ReportSection], insights: List[Insight]) -> List[ReportSection]:
    """Prevent thin reports when the LLM returns too few sections."""
    if len(sections) >= 4:
        return sections

    existing_titles = {section.title.lower() for section in sections}
    for section in _fallback_sections(insights):
        if section.title.lower() not in existing_titles:
            sections.append(section)
            existing_titles.add(section.title.lower())
        if len(sections) >= 5:
            break
    return sections


def _fallback_sections(insights: List[Insight]) -> List[ReportSection]:
    top = insights[:8]
    overview = (
        "This analysis surfaces the strongest patterns from the available dataset and organizes them into a decision narrative. "
        "The findings below should be read as evidence-backed priorities: what appears material, why it matters, and where action should focus first."
    )
    findings = "\n".join(
        f"- **Finding {idx + 1}:** {ins.content} *(significance: {ins.significance_score:.0%})*"
        for idx, ins in enumerate(top)
    ) or "- No prioritized findings were available."
    evidence = "\n".join(
        f"- {ins.content}\n  - **So What?** This signal should be considered in planning because it ranked highly against the rest of the analysis output."
        for ins in top[:5]
    ) or "- Evidence was insufficient to produce a ranked driver view."
    risks = "\n".join(
        f"- Validate finding {idx + 1} with stakeholder context and monitor it in future refreshes."
        for idx, _ in enumerate(top[:4])
    ) or "- Review data quality, missingness, and target definitions before taking action."
    recommendations = "\n".join(
        f"- Convert finding {idx + 1} into an owner, metric, and follow-up decision."
        for idx, _ in enumerate(top[:5])
    ) or "- Rerun the analysis with a narrower business question or richer target variable."

    return [
        ReportSection(title="Executive Overview", content=overview),
        ReportSection(title="Key Findings", content=findings),
        ReportSection(title="Evidence and Drivers", content=evidence),
        ReportSection(title="Risks and Watchouts", content=risks),
        ReportSection(title="Recommendations", content=recommendations),
    ]
