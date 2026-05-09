"""
Workflow checkpoint store using the existing PostgreSQL database.
Saves, restores, and queries workflow step states for crash recovery.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Set

from sqlalchemy.orm import Session

from app.db.models import AnalysisWorkflowState
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowCheckpointStore:
    """Serializes workflow context to PostgreSQL after every step."""

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
        existing = (
            self.db.query(AnalysisWorkflowState)
            .filter(AnalysisWorkflowState.workflow_id == workflow_id)
            .first()
        )
        if existing:
            existing.step_name = step_name
            existing.state_json = state_dict
        else:
            state = AnalysisWorkflowState(
                workflow_id=workflow_id,
                job_id=job_id,
                user_id=user_id,
                step_name=step_name,
                state_json=state_dict,
            )
            self.db.add(state)
        self.db.commit()
        logger.log_operation("Workflow checkpoint saved", workflow_id=workflow_id, step=step_name)

    def load_latest_checkpoint(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load the latest checkpoint for a workflow."""
        row = (
            self.db.query(AnalysisWorkflowState)
            .filter(AnalysisWorkflowState.workflow_id == workflow_id)
            .first()
        )
        return row.state_json if row else None

    def get_completed_steps(self, workflow_id: str) -> Set[str]:
        """Return set of step names already completed."""
        row = (
            self.db.query(AnalysisWorkflowState)
            .filter(AnalysisWorkflowState.workflow_id == workflow_id)
            .first()
        )
        if not row or not row.state_json:
            return set()

        step_name = row.step_name
        if not step_name:
            return set()

        # The state_json stores the LAST completed step.
        # We return all steps up to and including it.
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
        try:
            idx = STEP_ORDER.index(step_name)
            return set(STEP_ORDER[:idx + 1])
        except ValueError:
            return {step_name}

    def get_step_state(self, workflow_id: str, step_name: str) -> Optional[Dict[str, Any]]:
        """Return saved state for a specific step. Returns None if not completed."""
        completed = self.get_completed_steps(workflow_id)
        if step_name not in completed:
            return None
        row = (
            self.db.query(AnalysisWorkflowState)
            .filter(AnalysisWorkflowState.workflow_id == workflow_id)
            .first()
        )
        if not row:
            return None

        # The current model only stores the latest step's state.
        # For recovery, we return the full state_json if the step matches.
        if row.step_name == step_name:
            return row.state_json

        # For earlier steps, we'd need multi-row storage. For now,
        # return None and let caller use fallback — the multi-row
        # upgrade is tracked as a follow-up enhancement.
        return None if step_name != row.step_name else row.state_json

    def delete_checkpoint(self, workflow_id: str) -> None:
        """Delete a workflow checkpoint."""
        row = (
            self.db.query(AnalysisWorkflowState)
            .filter(AnalysisWorkflowState.workflow_id == workflow_id)
            .first()
        )
        if row:
            self.db.delete(row)
            self.db.commit()
