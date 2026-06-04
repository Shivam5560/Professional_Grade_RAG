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

SYSTEM_PROMPT = """You are a senior data storyteller and presentation strategist. Write an executive-ready analytical report in Markdown.
Name the work using business/story language, not technical/statistical labels. Good titles sound like an analysis theme or decision brief, for example "Customer Retention Outlook", "Revenue Momentum Review", or "Portfolio Risk Priorities". Do not hardcode those examples; infer the title from the query, dataset, and insights.
Each insight must have a 'So What?' and an actionable recommendation. Make the content specific, structured, and presentation-ready.

Respond ONLY with a JSON object in this exact format:
{
  "report_title": "A concise business-facing title, 3-7 words, not a raw metric name",
  "report_subtitle": "One sentence explaining the decision story and audience value",
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
- Include at least one section that explains the story behind the evidence, not just the numbers
- Include at least one forward-looking section such as future plans, recommended roadmap, watchouts, or next decisions when the data supports it
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
Columns: {profile.get('columns', [])}
Analyst brief: {profile.get('analysis_brief', {})}

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
                report_title=_clean_title(data.get("report_title", "")),
                report_subtitle=str(data.get("report_subtitle", "")).strip(),
            )
        except Exception as exc:
            logger.log_error("Narrative generation failed", exc)
            summary = f"## Analysis Summary\n\nQuery: {query}\n\n### Key Insights\n\n"
            for ins in insights.insights:
                summary += f"- {ins.content}\n"
            return NarrativeGeneratedResult(
                executive_summary=summary,
                sections=_fallback_sections(insights.insights),
                report_title=_fallback_title(query),
                report_subtitle="Patterns, evidence, and recommended next decisions from the dataset.",
            )


def _clean_title(title: Any) -> str:
    title = str(title or "").strip().strip('"')
    if len(title) > 80:
        title = title[:77].rstrip(" .,;:") + "..."
    return title


def _fallback_title(query: str) -> str:
    words = [w.strip(" ,.;:!?()[]{}") for w in str(query or "").split()]
    words = [w for w in words if len(w) > 2 and w.lower() not in {"what", "are", "the", "and", "for", "with", "from", "data", "analysis"}]
    if words:
        return " ".join(words[:5]).title()
    return "Analysis Overview"


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
