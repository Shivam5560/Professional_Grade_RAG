"""Integration tests for the analysis workflow structure and entry points."""

import pytest


class TestWorkflowStructure:
    """Verify the workflow module has the expected structure."""

    def test_workflow_instance_creation(self):
        from unittest.mock import MagicMock

        from app.analysis.workflows.analysis_workflow import AnalysisWorkflow

        db = MagicMock()
        workflow = AnalysisWorkflow(db=db, user_id=1, job_id="test_job")
        assert workflow.job_id == "test_job"
        assert workflow.user_id == 1

    def test_step_names_are_defined(self):
        from app.analysis.workflows.analysis_workflow import STEP_NAMES

        assert "build_context" in STEP_NAMES
        assert "compose" in STEP_NAMES
        assert len(STEP_NAMES) == 8

    def test_entry_point_exists(self):
        from app.analysis.workflows.analysis_workflow import run_analysis_workflow
        assert callable(run_analysis_workflow)

    def test_circuit_breaker_is_created(self):
        from unittest.mock import MagicMock

        from app.analysis.workflows.analysis_workflow import AnalysisWorkflow

        db = MagicMock()
        workflow = AnalysisWorkflow(db=db, user_id=1, job_id="test_job")
        assert workflow.circuit_breaker is not None
        assert "analysis_test_job" in workflow.circuit_breaker.name

    def test_checkpoint_store_used(self):
        """Workflow uses checkpoints for state persistence."""
        from unittest.mock import MagicMock

        from app.analysis.workflows.analysis_workflow import AnalysisWorkflow

        db = MagicMock()
        workflow = AnalysisWorkflow(db=db, user_id=1, job_id="test_job")
        assert workflow.checkpoint_store is not None


class TestWorkflowEdgeCases:
    """Edge cases for the workflow run_analysis_workflow entry point."""

    def test_job_not_found(self):
        """Entry point handles missing job gracefully."""
        from unittest.mock import MagicMock

        from app.analysis.workflows.analysis_workflow import run_analysis_workflow

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        # Should not raise
        run_analysis_workflow(db, "missing_job", 1, None)

    def test_cancelled_job_skipped(self):
        """Entry point skips cancelled jobs."""
        from unittest.mock import MagicMock

        from app.analysis.workflows.analysis_workflow import run_analysis_workflow

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock(
            id="test_job", status="cancelled"
        )

        # Should not raise — just log and return
        run_analysis_workflow(db, "test_job", 1, None)
