"""
Task Decomposer Agent.
Breaks a user query into specific analytical sub-tasks based on the dataset profile.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.analysis.base import BaseAnalysisAgent
from app.analysis.events import AnalysisTask, TaskDecomposedResult
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert data analyst. Given a user question and a dataset profile, break the request into 1-5 specific analytical sub-tasks.

Each task must have:
- task_id: a short unique identifier (e.g., "t1", "t2")
- description: what the task should accomplish
- required_agents: list of relevant analysis domains from: [statistical, pattern, correlation, predictive, nlp, time_series]

Respond ONLY with a JSON object in this exact format:
{
  "tasks": [
    {
      "task_id": "t1",
      "description": "...",
      "required_agents": ["statistical"]
    }
  ]
}"""


class TaskDecomposer(BaseAnalysisAgent):
    """Decomposes a natural-language query into structured analysis tasks."""

    def __init__(self):
        super().__init__(agent_name="TaskDecomposer", use_structured_llm=True)

    async def run(self, query: str, profile: Dict[str, Any]) -> TaskDecomposedResult:
        prompt = f"""Query: {query}

Dataset Profile:
- Rows: {profile.get('row_count', 'unknown')}
- Columns: {profile.get('column_count', 'unknown')}
- Numeric columns: {profile.get('numeric_columns', [])}
- Categorical columns: {profile.get('categorical_columns', [])}
- Datetime columns: {profile.get('datetime_columns', [])}

Break this into specific analytical tasks."""

        try:
            data = await self._call_llm(prompt, SYSTEM_PROMPT)
            tasks = [
                AnalysisTask(
                    task_id=t["task_id"],
                    description=t["description"],
                    required_agents=t.get("required_agents", []),
                )
                for t in data.get("tasks", [])
            ]
            logger.log_operation("Tasks decomposed", task_count=len(tasks))
            return TaskDecomposedResult(tasks=tasks)
        except Exception as exc:
            logger.log_error("Task decomposition failed", exc)
            return TaskDecomposedResult(
                tasks=[
                    AnalysisTask(
                        task_id="t1",
                        description=f"Analyze dataset to answer: {query}",
                        required_agents=["statistical", "correlation"],
                    )
                ]
            )
