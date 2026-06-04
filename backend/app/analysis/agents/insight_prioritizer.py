"""
Insight Prioritizer Agent.
Ranks analytical findings by significance and eliminates redundancies.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.analysis.base import BaseAnalysisAgent
from app.analysis.events import AgentResult, ExecutionCompleteResult, Insight, InsightsPrioritizedResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an insight prioritizer and consulting analyst. Given analytical findings from a CSV/XLSX dataset, rank them by significance, relevance, decision value, and actionability. Eliminate redundancies.

Your output is raw material for an executive PPTX. Each insight must have:
- a business-facing headline
- a concise evidence statement
- the implication / so-what
- a recommended action
- a narrative role showing where it belongs in the story

Respond ONLY with a JSON object in this exact format:
{
  "insights": [
    {
      "insight_id": "i1",
      "title": "Marketing Spend Drives Revenue Momentum",
      "subtitle": "Revenue correlates strongly with marketing spend (r=0.82).",
      "content": "Revenue correlates strongly with marketing spend (r=0.82), making marketing intensity a material growth driver rather than background context.",
      "recommendation": "Test budget reallocation toward the highest-return segments before scaling spend broadly.",
      "narrative_role": "Driver evidence",
      "significance_score": 0.92,
      "source_agents": ["correlation"]
    }
  ]
}

Rules:
- significance_score must be between 0.0 and 1.0
- Each insight should be specific, decision-oriented, and grounded in the finding
- Do not include weak findings only because they are available
- Avoid raw statistical wording as the headline; translate it into business meaning
- narrative_role should be one of: context, driver, risk, opportunity, segment, trend, forecast, recommendation
- Eliminate duplicate or near-duplicate findings
- Limit to the top 10 most significant insights"""


class InsightPrioritizer(BaseAnalysisAgent):
    """Prioritizes and deduplicates analytical findings."""

    def __init__(self):
        super().__init__(agent_name="InsightPrioritizer", use_structured_llm=True)

    async def run(self, execution_result: ExecutionCompleteResult, query: str) -> InsightsPrioritizedResult:
        findings_text = _format_findings(execution_result.results)

        prompt = f"""User Query: {query}

Findings:
{findings_text}

Prioritize these insights."""

        try:
            data = await self._call_llm(prompt, SYSTEM_PROMPT)
            insights = [
                Insight(
                    insight_id=i.get("insight_id", f"i{idx}"),
                    content=i["content"],
                    significance_score=max(0.0, min(1.0, i.get("significance_score", 0.5))),
                    source_agents=i.get("source_agents", []),
                    title=str(i.get("title", "")).strip(),
                    subtitle=str(i.get("subtitle", "")).strip(),
                    recommendation=str(i.get("recommendation", "")).strip(),
                    narrative_role=str(i.get("narrative_role", "")).strip(),
                )
                for idx, i in enumerate(data.get("insights", []))
            ]
            if not insights:
                insights = _fallback_insights(execution_result.results)
            logger.log_operation("Insights prioritized", count=len(insights))
            return InsightsPrioritizedResult(insights=insights)
        except Exception as exc:
            logger.log_error("Insight prioritization failed", exc)
            insights = _fallback_insights(execution_result.results)
            return InsightsPrioritizedResult(insights=insights)


def _format_findings(results: List[AgentResult]) -> str:
    parts = []
    for r in results:
        agent_block = f"Agent: {r.agent_name} (confidence: {r.confidence})\n"
        agent_block += "\n".join(
            f"- [{f.metric}] significance={f.significance}: {f.description}"
            for f in r.findings
            if f.significance > 0.1  # Skip trivial findings
        )
        parts.append(agent_block)
    return "\n\n".join(parts)


def _fallback_insights(results: List[AgentResult]) -> List[Insight]:
    insights = []
    idx = 0
    for r in results:
        for f in r.findings:
            idx += 1
            desc = f.description
            if desc.startswith(f"{f.metric}: "):
                desc = desc[len(f.metric) + 2:]
            elif isinstance(f.metric, str) and desc.startswith(f.metric):
                desc = desc[len(f.metric):].lstrip(": ")
            insights.append(Insight(
                insight_id=f"i{idx}",
                content=desc,
                significance_score=f.significance,
                source_agents=[r.agent_name],
                title=_fallback_headline(desc),
                subtitle=desc[:140],
                recommendation="Validate this signal with stakeholder context and convert it into a monitored decision metric.",
                narrative_role="evidence",
            ))
    insights.sort(key=lambda x: x.significance_score, reverse=True)
    return insights[:10]


def _fallback_headline(description: str) -> str:
    cleaned = " ".join(str(description or "").split())
    if not cleaned:
        return "Material Data Signal"
    words = cleaned.replace(":", " ").replace("(", " ").split()
    words = [w.strip(".,;") for w in words if len(w.strip(".,;")) > 2]
    return " ".join(words[:5]).title() or "Material Data Signal"
