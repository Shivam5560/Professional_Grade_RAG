"""
Analysis Workflow Orchestrator.
Runs the 8-step analysis pipeline with checkpoint recovery, per-step isolation,
circuit breaker protection, and timeout enforcement.

Steps: build_context → decompose → plan_strategy → dispatch_execution →
       prioritize_insights → generate_narrative → design → compose
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from sqlalchemy.orm import Session

from app.analysis.agents import (
    ContextBuilder,
    DesignIntelligence,
    ExecutionOrchestrator,
    InsightPrioritizer,
    NarrativeGenerator,
    StrategyPlanner,
    TaskDecomposer,
)
from app.analysis.cache import DatasetCache
from app.analysis.events import AnalysisCompleteResult
from app.analysis.resilience import CircuitBreaker
from app.analysis.state_store import WorkflowCheckpointStore
from app.config import settings
from app.db.models import AnalysisJob
from app.services.analysis.chart_generator import generate_charts
from app.services.analysis.report_builder import build_and_save_report
from app.utils.logger import get_logger

logger = get_logger(__name__)

STEP_NAMES = [
    "build_context",
    "decompose",
    "plan_strategy",
    "dispatch_execution",
    "prioritize_insights",
    "generate_narrative",
    "design",
    "compose",
]


class AnalysisWorkflow:
    """8-step data analysis workflow with resilience patterns."""

    def __init__(
        self,
        db: Session,
        user_id: int,
        job_id: str,
        manager: Optional[Any] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        self.db = db
        self.user_id = user_id
        self.job_id = job_id
        self.manager = manager
        self.checkpoint_store = WorkflowCheckpointStore(db)
        self.circuit_breaker = circuit_breaker or CircuitBreaker(
            name=f"analysis_{job_id}",
            failure_threshold=settings.analysis_circuit_breaker_threshold,
        )

    # ------------------------------------------------------------------
    # Event emission
    # ------------------------------------------------------------------

    def _emit(self, step_name: str, payload: Dict[str, Any]) -> None:
        """Emit progress event to WebSocket and persist to DB."""
        event = {
            "step_name": step_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        job = self.db.query(AnalysisJob).filter(AnalysisJob.id == self.job_id).first()
        if job:
            events = list(job.progress_events or [])
            events.append(event)
            job.progress_events = events
            job.status = "running"
            job.updated_at = datetime.now(timezone.utc)
            self.db.commit()

        if self.manager:
            try:
                self.manager.broadcast_sync(
                    self.job_id,
                    {"type": "event", "payload": event},
                )
            except Exception:
                pass

    def _send_ws(self, message_type: str, payload: Dict[str, Any]) -> None:
        if self.manager:
            try:
                self.manager.broadcast_sync(
                    self.job_id,
                    {"type": message_type, "payload": payload},
                )
            except Exception:
                pass

    def _checkpoint(self, step_name: str, state: Dict[str, Any]) -> None:
        self.checkpoint_store.save_checkpoint(
            workflow_id=self.job_id,
            job_id=self.job_id,
            user_id=self.user_id,
            step_name=step_name,
            state_dict=state,
        )

    # ------------------------------------------------------------------
    # Main orchestrator
    # ------------------------------------------------------------------

    async def run(
        self,
        query: str,
        source_id: str,
        config: Dict[str, Any],
        resume_from: Optional[str] = None,
    ) -> AnalysisCompleteResult:
        """Run the full 8-step analysis workflow with recovery support."""
        logger.log_operation("Workflow started", job_id=self.job_id, query=query)
        max_rows = config.get("max_rows", settings.analysis_max_rows)

        # Determine completed steps from checkpoint
        completed_steps: Set[str] = set()
        if resume_from:
            completed_steps = self.checkpoint_store.get_completed_steps(self.job_id)
            logger.log_operation("Resuming workflow", job_id=self.job_id, completed=list(completed_steps))

        context = None
        tasks = None
        strategy = None
        execution = None
        prioritized = None
        narrative = None
        design = None

        # --- Step 1: Build Context ---
        if "build_context" not in completed_steps:
            await self._run_with_timeout(
                self._step_build_context(source_id, max_rows),
                "build_context",
            )
            context = self.checkpoint_store.get_step_state(self.job_id, "build_context")
        else:
            logger.log_operation("Skipping completed step", step="build_context")

        # --- Step 2: Decompose ---
        if "decompose" not in completed_steps:
            profile = self._get_profile(context)
            await self._run_with_timeout(
                self._step_decompose(query, profile),
                "decompose",
            )
        else:
            logger.log_operation("Skipping completed step", step="decompose")

        # --- Step 3: Plan Strategy ---
        if "plan_strategy" not in completed_steps:
            profile = self._get_profile(context)
            tasks_data = self.checkpoint_store.get_step_state(self.job_id, "decompose")
            await self._run_with_timeout(
                self._step_plan_strategy(tasks_data, profile),
                "plan_strategy",
            )
        else:
            logger.log_operation("Skipping completed step", step="plan_strategy")

        # --- Step 4: Dispatch Execution ---
        if "dispatch_execution" not in completed_steps:
            await self._run_with_timeout(
                self._step_dispatch_execution(source_id, max_rows),
                "dispatch_execution",
            )
        else:
            logger.log_operation("Skipping completed step", step="dispatch_execution")

        # --- Step 5: Prioritize Insights ---
        if "prioritize_insights" not in completed_steps:
            exec_data = self.checkpoint_store.get_step_state(self.job_id, "dispatch_execution")
            await self._run_with_timeout(
                self._step_prioritize_insights(exec_data, query),
                "prioritize_insights",
            )
        else:
            logger.log_operation("Skipping completed step", step="prioritize_insights")

        # --- Step 6: Generate Narrative ---
        if "generate_narrative" not in completed_steps:
            profile = self._get_profile(context)
            pri_data = self.checkpoint_store.get_step_state(self.job_id, "prioritize_insights")
            await self._run_with_timeout(
                self._step_generate_narrative(pri_data, query, profile),
                "generate_narrative",
            )
        else:
            logger.log_operation("Skipping completed step", step="generate_narrative")

        # --- Step 7: Design ---
        if "design" not in completed_steps:
            profile = self._get_profile(context)
            pri_data = self.checkpoint_store.get_step_state(self.job_id, "prioritize_insights")
            await self._run_with_timeout(
                self._step_design(pri_data, profile, query),
                "design",
            )
        else:
            logger.log_operation("Skipping completed step", step="design")

        # --- Step 8: Compose ---
        if "compose" not in completed_steps:
            await self._run_with_timeout(
                self._step_compose(source_id, max_rows),
                "compose",
            )

        # Final cleanup
        DatasetCache.invalidate(source_id)
        logger.log_operation("Workflow completed", job_id=self.job_id)

        narr_state = self.checkpoint_store.get_step_state(self.job_id, "generate_narrative") or {}
        design_state = self.checkpoint_store.get_step_state(self.job_id, "design") or {}
        insight_state = self.checkpoint_store.get_step_state(self.job_id, "prioritize_insights") or {}
        compose_state = self.checkpoint_store.get_step_state(self.job_id, "compose") or {}

        return AnalysisCompleteResult(
            report_id=compose_state.get("report_id", ""),
            narrative=narr_state.get("summary", ""),
            sections=narr_state.get("sections", []),
            insights=insight_state.get("insights", []),
            chart_specs=design_state.get("chart_specs", []),
            design_spec={
                "theme": design_state.get("theme", "generic"),
                "color_palette": design_state.get("color_palette", []),
                "layout": design_state.get("layout", "grid"),
            },
        )

    # ------------------------------------------------------------------
    # Step implementations
    # ------------------------------------------------------------------

    async def _step_build_context(self, source_id: str, max_rows: int) -> None:
        self._emit("build_context", {"status": "started"})
        context_builder = ContextBuilder()
        context = context_builder.run(source_id, self.user_id, max_rows=max_rows)
        self._emit("build_context", {"status": "completed", "profile": context.profile_json})
        self._checkpoint("build_context", {"profile": context.profile_json, "quality_score": context.data_quality.overall_score if context.data_quality else None})

    async def _step_decompose(self, query: str, profile: Dict[str, Any]) -> None:
        self._emit("decompose", {"status": "started"})
        decomposer = TaskDecomposer()
        tasks = await decomposer.run(query, profile)
        task_dicts = [
            {"task_id": t.task_id, "description": t.description, "required_agents": t.required_agents}
            for t in tasks.tasks
        ]
        self._emit("decompose", {"status": "completed", "tasks": task_dicts})
        self._checkpoint("decompose", {"tasks": task_dicts})

    async def _step_plan_strategy(self, tasks_data: Dict, profile: Dict[str, Any]) -> None:
        self._emit("plan_strategy", {"status": "started"})
        from app.analysis.events import AnalysisTask, TaskDecomposedResult

        task_objs = [AnalysisTask(**t) for t in tasks_data.get("tasks", [])]
        planner = StrategyPlanner()
        strategy = await planner.run(TaskDecomposedResult(tasks=task_objs), profile)
        invocations = [
            {"agent_name": i.agent_name, "task_id": i.task_id, "parameters": i.parameters}
            for i in strategy.invocations
        ]
        self._emit("plan_strategy", {"status": "completed", "invocations": invocations})
        self._checkpoint("plan_strategy", {"invocations": invocations})

    async def _step_dispatch_execution(self, source_id: str, max_rows: int) -> None:
        strategy_data = self.checkpoint_store.get_step_state(self.job_id, "plan_strategy") or {}
        ctx_data = self.checkpoint_store.get_step_state(self.job_id, "build_context") or {}
        profile = ctx_data.get("profile", {})
        ctx_data_quality = ctx_data.get("quality_score", 1.0)

        self._emit("dispatch_execution", {"status": "started", "total": len(strategy_data.get("invocations", []))})

        # Load dataset once from cache for all agents
        df = DatasetCache.get_or_load(source_id, str(self.user_id), max_rows=max_rows)

        from app.analysis.validation import DataQualityReport

        quality = DataQualityReport(
            overall_score=float(ctx_data_quality) if ctx_data_quality else 1.0,
            total_rows=profile.get("row_count", 0),
            total_columns=profile.get("column_count", 0),
            missing_summary={},
            outlier_summary={},
            type_inferences={},
            numeric_columns=profile.get("numeric_columns", []),
            categorical_columns=profile.get("categorical_columns", []),
            datetime_columns=profile.get("datetime_columns", []),
        )

        from app.analysis.events import AgentInvocation

        invocations = [AgentInvocation(**i) for i in strategy_data.get("invocations", [])]
        executor = ExecutionOrchestrator()
        execution = await executor.run(invocations, df, profile, quality)

        result_summaries = []
        for r in execution.results:
            result_summaries.append({
                "agent_name": r.agent_name,
                "task_id": r.task_id,
                "finding_count": len(r.findings),
                "confidence": r.confidence,
                "findings": [{"metric": f.metric, "description": f.description, "significance": f.significance, "value": str(f.value)[:500]} for f in r.findings],
            })

        self._emit("dispatch_execution", {"status": "completed", "results": result_summaries})
        self._checkpoint("dispatch_execution", {"results": result_summaries})

    async def _step_prioritize_insights(self, exec_data: Dict, query: str) -> None:
        self._emit("prioritize_insights", {"status": "started"})
        from app.analysis.events import AgentFinding, AgentResult, ExecutionCompleteResult

        agent_results = []
        for r in exec_data.get("results", []):
            findings = [AgentFinding(**f) for f in r.get("findings", [])]
            agent_results.append(AgentResult(
                agent_name=r["agent_name"],
                task_id=r.get("task_id", ""),
                findings=findings,
                confidence=r.get("confidence", 0.5),
            ))

        prioritizer = InsightPrioritizer()
        prioritized = await prioritizer.run(ExecutionCompleteResult(results=agent_results), query)
        insight_dicts = [
            {"insight_id": ins.insight_id, "content": ins.content, "significance_score": ins.significance_score, "source_agents": ins.source_agents}
            for ins in prioritized.insights
        ]
        self._emit("prioritize_insights", {"status": "completed", "insights": insight_dicts})
        self._checkpoint("prioritize_insights", {"insights": insight_dicts})

    async def _step_generate_narrative(self, pri_data: Dict, query: str, profile: Dict[str, Any]) -> None:
        self._emit("generate_narrative", {"status": "started"})
        from app.analysis.events import Insight, InsightsPrioritizedResult

        insights = [Insight(**i) for i in pri_data.get("insights", [])]
        narrator = NarrativeGenerator()
        narrative = await narrator.run(InsightsPrioritizedResult(insights=insights), query, profile)
        sections_dicts = [{"title": s.title, "content": s.content} for s in narrative.sections]
        self._emit("generate_narrative", {"status": "completed", "summary": narrative.executive_summary[:200]})
        self._checkpoint("generate_narrative", {"summary": narrative.executive_summary, "sections": sections_dicts})

    async def _step_design(self, pri_data: Dict, profile: Dict[str, Any], query: str) -> None:
        self._emit("design", {"status": "started"})
        from app.analysis.events import Insight, InsightsPrioritizedResult

        insights = [Insight(**i) for i in pri_data.get("insights", [])]
        designer = DesignIntelligence()
        design = await designer.run(InsightsPrioritizedResult(insights=insights), profile, query)
        self._emit("design", {"status": "completed", "theme": design.theme, "charts": len(design.chart_specs)})
        self._checkpoint("design", {"theme": design.theme, "color_palette": design.color_palette, "layout": design.layout, "chart_specs": design.chart_specs})

    async def _step_compose(self, source_id: str, max_rows: int) -> None:
        self._emit("compose", {"status": "started"})
        narr_data = self.checkpoint_store.get_step_state(self.job_id, "generate_narrative") or {}
        design_data = self.checkpoint_store.get_step_state(self.job_id, "design") or {}
        insight_data = self.checkpoint_store.get_step_state(self.job_id, "prioritize_insights") or {}

        df = DatasetCache.get_or_load(source_id, str(self.user_id), max_rows=max_rows)
        chart_specs = design_data.get("chart_specs", [])
        chart_paths = generate_charts(chart_specs, df, self.job_id)

        summary = narr_data.get("summary", "Untitled Analysis")
        title = summary[:80] + "..." if len(summary) > 80 else summary

        report = build_and_save_report(
            db=self.db,
            job_id=self.job_id,
            user_id=self.user_id,
            title=title,
            narrative=summary,
            sections=narr_data.get("sections", []),
            insights=insight_data.get("insights", []),
            design_spec={
                "theme": design_data.get("theme", "generic"),
                "color_palette": design_data.get("color_palette", []),
                "layout": design_data.get("layout", "grid"),
            },
            chart_paths=chart_paths,
        )

        self._emit("compose", {"status": "completed", "report_id": report.id})
        self._checkpoint("compose", {"report_id": report.id, "chart_count": len(chart_paths)})
        self._send_ws("complete", {"report_id": report.id, "status": "completed"})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_profile(self, context_state: Optional[Dict]) -> Dict[str, Any]:
        if context_state:
            return context_state.get("profile", {})
        ctx_data = self.checkpoint_store.get_step_state(self.job_id, "build_context") or {}
        return ctx_data.get("profile", {})

    async def _run_with_timeout(self, coro, step_name: str) -> None:
        """Execute a step with timeout, circuit breaker, and per-step error isolation."""
        try:
            await asyncio.wait_for(
                coro,
                timeout=settings.analysis_subworkflow_timeout,
            )
        except asyncio.TimeoutError:
            logger.log_error("Step timed out", None, step=step_name, job_id=self.job_id)
            self._emit(step_name, {"status": "timeout", "error": f"Step '{step_name}' exceeded {settings.analysis_subworkflow_timeout}s timeout"})
            raise TimeoutError(f"Step '{step_name}' timed out after {settings.analysis_subworkflow_timeout}s")
        except Exception as exc:
            logger.log_error("Step failed", exc, step=step_name, job_id=self.job_id)
            self._emit(step_name, {"status": "error", "error": str(exc)[:500]})
            # Don't re-raise — allow subsequent steps to continue with fallbacks
            # The step's own checkpoint won't be saved, so recovery will re-run it.


# ------------------------------------------------------------------
# Entry point (background-thread-safe)
# ------------------------------------------------------------------

def run_analysis_workflow(
    db: Session,
    job_id: str,
    user_id: int,
    manager: Optional[Any] = None,
) -> None:
    """Run the analysis workflow in a background thread. Safe to call from any thread."""
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        logger.log_error("Job not found", None, job_id=job_id)
        return

    if job.status == "cancelled":
        logger.log_operation("Job cancelled before start", job_id=job_id)
        return

    workflow = AnalysisWorkflow(db, user_id, job_id, manager)

    async def _execute():
        try:
            await workflow.run(
                query=job.query,
                source_id=job.source_id,
                config=job.config or {},
            )
        except Exception as exc:
            logger.log_error("Workflow failed", exc, job_id=job_id)
            workflow._send_ws("error", {"message": str(exc), "status": "failed"})
            job.status = "failed"
            job.error_message = str(exc)[:2000]
            job.updated_at = datetime.now(timezone.utc)
            db.commit()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop — call directly
        asyncio.run(_execute())
    else:
        # Already inside an event loop — run in a thread
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, _execute())
            future.result(timeout=settings.analysis_workflow_timeout + 60)
