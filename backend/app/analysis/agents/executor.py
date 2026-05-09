"""
Execution Orchestrator Agent.
Dispatches analysis tasks to specialized execution agents with concurrency control.
Each agent receives the cached DataFrame — no redundant disk I/O.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import pandas as pd

from app.analysis.agents.execution_agents import (
    CorrelationAgent,
    NLPAgent,
    PatternAgent,
    PredictiveAgent,
    StatisticalAgent,
    TimeSeriesAgent,
)
from app.analysis.events import (
    AgentFinding,
    AgentInvocation,
    AgentResult,
    ExecutionCompleteResult,
)
from app.analysis.validation import DataQualityReport
from app.utils.logger import get_logger

logger = get_logger(__name__)

AGENT_REGISTRY = {
    "statistical": StatisticalAgent,
    "correlation": CorrelationAgent,
    "pattern": PatternAgent,
    "predictive": PredictiveAgent,
    "nlp": NLPAgent,
    "time_series": TimeSeriesAgent,
}


class ExecutionOrchestrator:
    """Runs data analysis agents against the dataset."""

    def __init__(self):
        self._semaphore: asyncio.Semaphore | None = None

    async def run(
        self,
        invocations: List[AgentInvocation],
        df: pd.DataFrame,
        profile: Dict[str, Any],
        quality: DataQualityReport,
        max_concurrency: int = 4,
    ) -> ExecutionCompleteResult:
        """Execute all planned agent invocations with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrency)

        async def run_one(inv: AgentInvocation) -> AgentResult:
            async with semaphore:
                return await self._dispatch(inv, df, profile, quality)

        coros = [run_one(inv) for inv in invocations]
        results: List[Any] = await asyncio.gather(*coros, return_exceptions=True)

        successful: List[AgentResult] = []
        for r in results:
            if isinstance(r, Exception):
                logger.log_error("Agent execution failed with exception", r)
                continue
            successful.append(r)

        logger.log_operation(
            "Execution complete",
            total=len(invocations),
            successful=len(successful),
        )
        return ExecutionCompleteResult(results=successful)

    async def _dispatch(
        self,
        inv: AgentInvocation,
        df: pd.DataFrame,
        profile: Dict[str, Any],
        quality: DataQualityReport,
    ) -> AgentResult:
        """Dispatch a single invocation to the correct execution agent."""
        agent_name = inv.agent_name

        if agent_name not in AGENT_REGISTRY:
            return AgentResult(
                agent_name=agent_name,
                task_id=inv.task_id,
                findings=[AgentFinding(
                    metric="unknown_agent",
                    value=f"Unknown agent: {agent_name}. Available: {list(AGENT_REGISTRY.keys())}",
                    description="No execution logic registered for this agent type.",
                    significance=0.0,
                )],
                confidence=0.0,
            )

        try:
            agent_class = AGENT_REGISTRY[agent_name]
            agent = agent_class()
            params = dict(inv.parameters or {})
            params["task_id"] = inv.task_id
            return await agent.run(df, params, profile, quality)
        except Exception as exc:
            logger.log_error("Agent dispatch failed", exc, agent_name=agent_name, task_id=inv.task_id)
            return AgentResult(
                agent_name=agent_name,
                task_id=inv.task_id,
                findings=[AgentFinding(
                    metric="dispatch_error",
                    value=str(exc),
                    description=f"Failed to execute {agent_name} agent.",
                    significance=0.0,
                )],
                confidence=0.0,
            )
