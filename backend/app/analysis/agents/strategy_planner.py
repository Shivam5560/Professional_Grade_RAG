"""
Strategy Planner Agent.
Selects optimal execution agents and determines invocation order based on tasks and dataset profile.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.analysis.base import BaseAnalysisAgent
from app.analysis.events import AgentInvocation, StrategyPlannedResult, TaskDecomposedResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a strategy planner. Given a set of analysis tasks and a dataset profile, select the optimal execution agents and determine invocation order.

Respond ONLY with a JSON object in this exact format:
{
  "invocations": [
    {
      "agent_name": "statistical",
      "task_id": "t1",
      "parameters": {"target_column": "revenue", "group_column": "region"}
    }
  ]
}

Available agents: statistical, pattern, correlation, predictive, nlp, time_series.
If a task does not need parameters, use an empty object {}."""


class StrategyPlanner(BaseAnalysisAgent):
    """Plans which agents to invoke and in what order."""

    def __init__(self):
        super().__init__(agent_name="StrategyPlanner", use_structured_llm=True)

    async def run(
        self,
        tasks: TaskDecomposedResult,
        profile: Dict[str, Any],
    ) -> StrategyPlannedResult:
        task_list = "\n".join(
            f"- {t.task_id}: {t.description} (agents: {', '.join(t.required_agents)})"
            for t in tasks.tasks
        )
        prompt = f"""Tasks:
{task_list}

Dataset Profile:
- Rows: {profile.get('row_count')}
- Columns: {profile.get('column_count')}
- Numeric: {profile.get('numeric_columns')}
- Categorical: {profile.get('categorical_columns')}
- Datetime: {profile.get('datetime_columns')}

Plan the agent invocations with relevant parameters."""

        try:
            data = await self._call_llm(prompt, SYSTEM_PROMPT)
            invocations = [
                AgentInvocation(
                    agent_name=i["agent_name"],
                    task_id=i["task_id"],
                    parameters=i.get("parameters", {}),
                )
                for i in data.get("invocations", [])
            ]
            logger.log_operation("Strategy planned", invocation_count=len(invocations))
            return StrategyPlannedResult(invocations=invocations)
        except Exception as exc:
            logger.log_error("Strategy planning failed", exc)
            invocations = []
            for t in tasks.tasks:
                for agent_name in t.required_agents[:2]:  # Max 2 agents per task in fallback
                    invocations.append(
                        AgentInvocation(agent_name=agent_name, task_id=t.task_id, parameters={})
                    )
            return StrategyPlannedResult(invocations=invocations)
