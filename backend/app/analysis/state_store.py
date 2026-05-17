"""
Workflow checkpoint store using the existing PostgreSQL database.
Saves, restores, and queries workflow step states for crash recovery.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import AnalysisWorkflowState
from app.utils.json_safety import sanitize_json
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowCheckpointStore:
    """Serializes workflow context to PostgreSQL after every step."""

    STEP_ORDER = [
        "build_context",
        "decompose",
        "plan_strategy",
        "dispatch_execution",
        "prioritize_insights",
        "generate_narrative",
        "design",
        "compose",
    ]

    def __init__(self, db: Session):
        self.db = db

    def save_checkpoint(
        self,
        workflow_id: str,
        job_id: str,
        user_id: int,
        step_name: str,
        state_dict: dict,
    ) -> None:
        """Save or update a workflow checkpoint."""
        state_dict = sanitize_json(state_dict)
        checkpoint_id = self._checkpoint_id(workflow_id, step_name)
        existing = (
            self.db.query(AnalysisWorkflowState)
            .filter(AnalysisWorkflowState.workflow_id == checkpoint_id)
            .first()
        )
        if existing:
            existing.step_name = step_name
            existing.state_json = state_dict
        else:
            state = AnalysisWorkflowState(
                workflow_id=checkpoint_id,
                job_id=job_id,
                user_id=user_id,
                step_name=step_name,
                state_json=state_dict,
            )
            self.db.add(state)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        logger.log_operation("Workflow checkpoint saved", workflow_id=workflow_id, step=step_name)

    def load_latest_checkpoint(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load the latest checkpoint for a workflow."""
        rows = self._rows_for_workflow(workflow_id)
        row = self._latest_row(rows)
        return row.state_json if row else None

    def get_completed_steps(self, workflow_id: str) -> Set[str]:
        """Return set of step names already completed."""
        rows = self._rows_for_workflow(workflow_id)
        if not rows:
            return set()

        completed = {row.step_name for row in rows if row.step_name and row.state_json}
        # Backward compatibility for old single-row checkpoints that only stored
        # the latest step: those cannot recover older state payloads, but they can
        # still report progress up to that step.
        if len(rows) == 1 and rows[0].workflow_id == workflow_id and rows[0].step_name in self.STEP_ORDER:
            idx = self.STEP_ORDER.index(rows[0].step_name)
            return set(self.STEP_ORDER[:idx + 1])
        return completed

    def get_step_state(self, workflow_id: str, step_name: str) -> Optional[Dict[str, Any]]:
        """Return saved state for a specific step. Returns None if not completed."""
        row = (
            self.db.query(AnalysisWorkflowState)
            .filter(AnalysisWorkflowState.workflow_id == self._checkpoint_id(workflow_id, step_name))
            .first()
        )
        if row:
            return row.state_json

        # Backward compatibility for old single-row checkpoints.
        legacy = (
            self.db.query(AnalysisWorkflowState)
            .filter(
                AnalysisWorkflowState.workflow_id == workflow_id,
                AnalysisWorkflowState.step_name == step_name,
            )
            .first()
        )
        return legacy.state_json if legacy else None

    def delete_checkpoint(self, workflow_id: str) -> None:
        """Delete a workflow checkpoint."""
        rows = self._rows_for_workflow(workflow_id)
        for row in rows:
            self.db.delete(row)
        if rows:
            self.db.commit()

    @staticmethod
    def _checkpoint_id(workflow_id: str, step_name: str) -> str:
        return f"{workflow_id}:{step_name}"

    def _rows_for_workflow(self, workflow_id: str) -> List[AnalysisWorkflowState]:
        return (
            self.db.query(AnalysisWorkflowState)
            .filter(
                or_(
                    AnalysisWorkflowState.workflow_id == workflow_id,
                    AnalysisWorkflowState.workflow_id.like(f"{workflow_id}:%"),
                )
            )
            .all()
        )

    def _latest_row(self, rows: List[AnalysisWorkflowState]) -> Optional[AnalysisWorkflowState]:
        if not rows:
            return None
        order = {step: idx for idx, step in enumerate(self.STEP_ORDER)}
        return max(rows, key=lambda row: order.get(row.step_name, -1))
