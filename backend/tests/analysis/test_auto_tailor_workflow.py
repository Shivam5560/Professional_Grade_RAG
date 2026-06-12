"""Unit and integration tests for the Auto-Tailor Resume LlamaIndex Workflow."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.analysis.workflows.auto_tailor_workflow import (
    AutoTailorWorkflow,
    ProfileRetrievedEvent,
    ResumeDraftedEvent,
    ResumeScoredEvent,
    RewriteEvent,
    ResumeApprovedEvent
)

class TestAutoTailorWorkflow:
    """Tests the structure and basic execution blocks of AutoTailorWorkflow."""

    def test_workflow_instantiation(self):
        db = MagicMock()
        workflow = AutoTailorWorkflow(db=db, analysis_id="test_analysis", disable_validation=True, timeout=300.0)
        assert workflow.analysis_id == "test_analysis"
        assert workflow.db == db

    @pytest.mark.asyncio
    @patch("app.analysis.workflows.auto_tailor_workflow.get_nexus_llm")
    async def test_retrieve_profile_step_with_cache(self, mock_get_llm):
        """Should retrieve profile from cached extracted_data if it exists."""
        db = MagicMock()
        mock_file = MagicMock()
        mock_file.extracted_data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "experiences": [{"title": "Software Engineer"}],
            "skills": {"languages": "Python, Go"}
        }
        db.query.return_value.filter.return_value.first.return_value = mock_file

        workflow = AutoTailorWorkflow(db=db, analysis_id="test_analysis", disable_validation=True, timeout=300.0)
        event = MagicMock()
        event.get.side_effect = lambda k, default=None: {
            "resume_id": "res_123",
            "job_description": "We need a Python developer.",
            "target_score": 85.0,
            "max_iterations": 3
        }.get(k, default)

        result = await workflow.retrieve_profile(event)

        assert isinstance(result, ProfileRetrievedEvent)
        assert result.analysis_id == "test_analysis"
        assert result.master_profile_json["name"] == "Jane Doe"
        assert result.job_description == "We need a Python developer."
        assert result.target_score == 85.0
        assert result.max_iterations == 3
        # Ensure LLM was not called since data was cached
        mock_get_llm.assert_not_called()

    @pytest.mark.asyncio
    async def test_retrieve_profile_step_without_resume_id(self):
        """Should skip profile retrieval and return None if resume_id is missing (e.g. custom event start)."""
        db = MagicMock()
        workflow = AutoTailorWorkflow(db=db, analysis_id="test_analysis", disable_validation=True, timeout=300.0)
        event = MagicMock()
        event.get.side_effect = lambda k, default=None: {
            "job_description": "We need a Python developer.",
            "target_score": 85.0,
            "max_iterations": 3
        }.get(k, default)

        result = await workflow.retrieve_profile(event)

        assert result is None
        db.query.assert_not_called()

    def test_synthesize_to_text(self):
        workflow = AutoTailorWorkflow(db=MagicMock(), analysis_id="test_analysis", disable_validation=True, timeout=300.0)
        sample_json = {
            "name": "John Doe",
            "email": "john@doe.com",
            "experiences": [
                {
                    "title": "Data Scientist",
                    "company": "AI Corp",
                    "dates": "2020 - 2022",
                    "responsibilities": ["Built machine learning pipelines", "Optimized queries"]
                }
            ],
            "skills": {
                "languages": "Python, SQL"
            }
        }
        text = workflow._synthesize_to_text(sample_json)
        assert "Name: John Doe" in text
        assert "Data Scientist" in text
        assert "AI Corp" in text
        assert "Built machine learning pipelines" in text
        assert "languages: Python, SQL" in text

    @pytest.mark.asyncio
    @patch("app.services.nexus_ai.core.analyzer.analyze_resume_v2")
    async def test_score_resume_step(self, mock_analyze_v2):
        """Should run scoring and critic feedback via analyze_resume_v2."""
        mock_analyze_v2.return_value = {
            "scores": {
                "overall": 77.5
            },
            "ats_analysis": {
                "score": 75.0,
                "matched_keywords": ["Python"],
                "missing_keywords": ["FastAPI"],
                "all_issues": []
            },
            "technical_score": {
                "score": 80.0,
                "matched_skills": ["Python"]
            },
            "gap_analysis": {
                "summary": "Gap Analysis Summary Text"
            },
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Add FastAPI experience",
                    "reason": "Required for backend"
                }
            ]
        }

        workflow = AutoTailorWorkflow(db=MagicMock(), analysis_id="test_analysis", disable_validation=True, timeout=300.0)
        
        ev = ResumeDraftedEvent(
            analysis_id="test_analysis",
            resume_data={"name": "Jane", "skills": {"languages": "Python"}},
            job_description="FastAPI dev",
            target_score=85.0,
            max_iterations=3,
            iteration=1
        )

        result = await workflow.score_resume(ev)

        assert isinstance(result, ResumeScoredEvent)
        assert result.scores["overall"] == 77.5
        assert "Gap Analysis Summary Text" in result.critic_feedback
        assert "Add FastAPI experience" in result.critic_feedback
        mock_analyze_v2.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.analysis.workflows.auto_tailor_workflow.generate_resume_pdf")
    async def test_evaluate_score_success(self, mock_generate_pdf):
        """Should compile PDF and complete workflow if overall score >= target."""
        mock_generate_pdf.return_value = {"success": True}
        db = MagicMock()
        workflow = AutoTailorWorkflow(db=db, analysis_id="test_analysis", disable_validation=True, timeout=300.0)

        ev = ResumeScoredEvent(
            analysis_id="test_analysis",
            resume_data={"name": "Jane"},
            scores={"overall": 87.0, "ats": {}, "technical": {}},
            critic_feedback="Looks great!",
            job_description="Dev",
            target_score=85.0,
            max_iterations=3,
            iteration=1
        )

        result = await workflow.evaluate_score(ev)
        assert result.result["status"] == "completed"
        assert result.result["latest_score"] == 87.0
        assert "pdf_path" in result.result

    @pytest.mark.asyncio
    @patch("app.analysis.workflows.auto_tailor_workflow.generate_resume_pdf")
    async def test_evaluate_score_paused(self, mock_generate_pdf):
        """Should pause and update database if overall score < target."""
        db = MagicMock()
        mock_analysis = MagicMock()
        mock_analysis.analysis = {"history": []}
        db.query.return_value.filter.return_value.first.return_value = mock_analysis

        workflow = AutoTailorWorkflow(db=db, analysis_id="test_analysis", disable_validation=True, timeout=300.0)

        ev = ResumeScoredEvent(
            analysis_id="test_analysis",
            resume_data={"name": "Jane"},
            scores={"overall": 72.0, "ats": {}, "technical": {}},
            critic_feedback="Needs FastAPI",
            job_description="Dev",
            target_score=85.0,
            max_iterations=3,
            iteration=1
        )

        result = await workflow.evaluate_score(ev)
        assert result.result["status"] == "paused_for_human"
        assert result.result["latest_score"] == 72.0
        
        # Verify db interaction
        assert mock_analysis.overall_score == 72.0
        assert mock_analysis.analysis["status"] == "paused_for_human"
        assert len(mock_analysis.analysis["history"]) == 1
        db.commit.assert_called_once()

    def test_latex_escaping_unicode(self):
        """Should sanitize unicode characters for safe LaTeX compilation."""
        from app.services.resume_generator import LatexResumeGenerator
        generator = LatexResumeGenerator()
        
        # Test string with various Unicode characters
        test_string = "Camunda\u2011driven microservice on Java\u202f21 with a 30% reduction, costing \u2248 $100 and utilizing • bullet points."
        escaped = generator._escape(test_string)
        
        # Non-breaking hyphen should be converted to standard dash
        assert "Camunda-driven" in escaped
        # Narrow no-break space should be converted to space
        assert "Java 21" in escaped
        # % should be escaped as \%
        assert "30\\%" in escaped
        # $ should be escaped as \$
        assert "100" in escaped
        # \u2248 should be mapped to approx.
        assert "approx." in escaped
        # Bullet • should be converted to *
        assert "*" in escaped
        # Verify it contains only ASCII characters (as pdflatex requires)
        assert all(ord(c) < 128 for c in escaped)

