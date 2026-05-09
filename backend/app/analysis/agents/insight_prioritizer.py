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

SYSTEM_PROMPT = """You are an insight prioritizer. Given a set of analytical findings, rank them by significance, relevance, and actionability. Eliminate redundancies.

Respond ONLY with a JSON object in this exact format:
{
  "insights": [
    {
      "insight_id": "i1",
      "content": "Revenue correlates strongly with marketing spend (r=0.82).",
      "significance_score": 0.92,
      "source_agents": ["correlation"]
    }
  ]
}

Rules:
- significance_score must be between 0.0 and 1.0
- Each insight should be concise and actionable
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
                )
                for idx, i in enumerate(data.get("insights", []))
            ]
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
            insights.append(Insight(
                insight_id=f"i{idx}",
                content=f"{f.metric}: {f.description}",
                significance_score=f.significance,
                source_agents=[r.agent_name],
            ))
    insights.sort(key=lambda x: x.significance_score, reverse=True)
    return insights[:10]
