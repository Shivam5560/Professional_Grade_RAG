"""
LlamaIndex Workflow for Auto-Tailor Resume Optimization.
Iteratively refines and scores a resume JSON against a Job Description,
supporting Human-in-the-loop overrides.
"""

import json
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field

from llama_index.core.workflow import Workflow, step, StartEvent, StopEvent, Event
from llama_index.core.llms import ChatMessage, MessageRole

from app.db.models import NexusResumeFile, NexusResumeAnalysis
from app.services.resume_generator import generate_resume_pdf, LatexResumeGenerator
from app.services.nexus_ai.core.scorers_v2 import compute_ats_score, compute_technical_score
from app.services.rag_provider_factory import get_nexus_llm
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ─── Event Definitions ────────────────────────────────────────────────────────

class ProfileRetrievedEvent(Event):
    analysis_id: str
    master_profile_json: Dict[str, Any]
    job_description: str
    target_score: float
    max_iterations: int

class ResumeDraftedEvent(Event):
    analysis_id: str
    resume_data: Dict[str, Any]
    job_description: str
    target_score: float
    max_iterations: int
    iteration: int
    human_feedback: Optional[str] = None

class ResumeScoredEvent(Event):
    analysis_id: str
    resume_data: Dict[str, Any]
    scores: Dict[str, Any]
    critic_feedback: str
    job_description: str
    target_score: float
    max_iterations: int
    iteration: int
    human_feedback: Optional[str] = None

class RewriteEvent(Event):
    analysis_id: str
    resume_data: Dict[str, Any]
    critic_feedback: str  # Markdown list of improvements/keywords to insert
    job_description: str
    iteration: int
    target_score: float
    max_iterations: int
    human_feedback: Optional[str] = None

class ResumeApprovedEvent(Event):
    analysis_id: str
    resume_data: Dict[str, Any]
    job_description: str

class HumanInterruptEvent(Event):
    analysis_id: str
    resume_data: Dict[str, Any]
    scores: Dict[str, Any]
    critic_feedback: str
    job_description: str
    iteration: int
    target_score: float
    max_iterations: int


# ─── Pydantic Schemas for Structured LLM Outputs ─────────────────────────────

class ExperienceItem(BaseModel):
    title: str = Field(description="Job title or position")
    company: str = Field(description="Company or organization name")
    location: str = Field(description="Location of the job, e.g., 'San Francisco, CA' or 'Remote'")
    dates: str = Field(description="Dates of employment, e.g., 'Jan 2020 - Present'")
    responsibilities: List[str] = Field(description="3-5 detailed bullet points showing achievements, metrics, and technical contributions")

class EducationItem(BaseModel):
    institution: str = Field(description="University or institution name")
    degree: str = Field(description="Degree and major, e.g., 'B.S. in Computer Science'")
    graduation_date: str = Field(description="Graduation date or expected date, e.g., 'May 2022'")
    gpa: str = Field(default="", description="GPA (optional)")

class ProjectItem(BaseModel):
    title: str = Field(description="Project name")
    descriptions: List[str] = Field(description="1-3 bullet points describing the project, tech stack, and impact")

class SkillsData(BaseModel):
    languages: str = Field(default="", description="Comma-separated programming languages, e.g., 'Python, TypeScript, SQL'")
    frameworks: str = Field(default="", description="Comma-separated frameworks/libraries, e.g., 'FastAPI, React, PyTorch'")
    tools: str = Field(default="", description="Comma-separated tools/platforms, e.g., 'Docker, Kubernetes, Git, AWS'")
    databases: str = Field(default="", description="Comma-separated databases, e.g., 'PostgreSQL, Redis, MongoDB'")

class ResumeStructure(BaseModel):
    name: str = Field(description="Candidate's full name")
    email: str = Field(description="Email address")
    location: str = Field(default="", description="City, State / Country")
    linkedin_url: str = Field(default="", description="LinkedIn profile URL")
    github_url: str = Field(default="", description="GitHub profile URL")
    experiences: List[ExperienceItem] = Field(description="Professional work experience items")
    education: List[EducationItem] = Field(description="Education history items")
    projects: List[ProjectItem] = Field(description="Project showcase items")
    skills: SkillsData = Field(description="Technical skills broken down by category")


# ─── LlamaIndex Workflow Definition ──────────────────────────────────────────

class AutoTailorWorkflow(Workflow):
    """
    Stateful Auto-Tailor Resume Workflow using LlamaIndex core Workflows.
    Optimizes a resume iteratively, pausing if scores are below target.
    """

    def __init__(self, db, analysis_id: str, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.analysis_id = analysis_id

    @step()
    async def retrieve_profile(self, ev: StartEvent) -> Optional[ProfileRetrievedEvent]:
        """Step 1: Retrieve user profile from NexusResumeFile."""
        resume_id = ev.get("resume_id")
        if not resume_id:
            logger.info("[AutoTailorWorkflow] StartEvent received without resume_id. Skipping profile retrieval.")
            return None

        job_description = ev.get("job_description")
        target_score = float(ev.get("target_score", 85.0))
        max_iterations = int(ev.get("max_iterations", 3))

        logger.info(f"[AutoTailorWorkflow] Retrieving profile for resume_id={resume_id}")

        # Fetch record from database
        resume_file = (
            self.db.query(NexusResumeFile)
            .filter(NexusResumeFile.resume_id == resume_id)
            .first()
        )
        if not resume_file:
            raise ValueError(f"NexusResumeFile with ID {resume_id} not found")

        # Check if we already have extracted JSON data in extracted_data
        master_profile_json = {}
        cached_data = resume_file.extracted_data or {}
        raw_text = cached_data.get("_raw_text", "")

        # Check if structured data is cached
        if cached_data.get("experiences") or cached_data.get("skills"):
            # Load cached structured fields
            master_profile_json = {
                "name": cached_data.get("name", ""),
                "email": cached_data.get("email", ""),
                "location": cached_data.get("location", ""),
                "linkedin_url": cached_data.get("linkedin_url", ""),
                "github_url": cached_data.get("github_url", ""),
                "experiences": cached_data.get("experiences", []),
                "education": cached_data.get("education", []),
                "projects": cached_data.get("projects", []),
                "skills": cached_data.get("skills", {}),
            }
        
        # If we don't have structured data, run a quick extraction LLM call
        if not master_profile_json or not master_profile_json.get("experiences"):
            logger.info("[AutoTailorWorkflow] Extracted JSON not cached. Extracting via LLM...")
            llm = get_nexus_llm()
            
            prompt = (
                "Extract structural resume details from the raw resume text. "
                "Output a structured JSON conforming strictly to the requested schema.\n\n"
                f"Raw Text:\n{raw_text}"
            )
            
            schema_json = ResumeStructure.model_json_schema()
            system_prompt = (
                "You are a data extraction bot. Parse raw resume text into structured JSON. Respond only with JSON.\n"
                f"Parse raw text into this JSON format:\n{json.dumps(schema_json)}"
            )
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
                ChatMessage(role=MessageRole.USER, content=prompt)
            ]
            
            response = await llm.achat(messages)
            parsed = self._extract_json(response.message.content)
            master_profile_json = parsed

            # Cache the extracted JSON in database
            resume_file.extracted_data = {
                **cached_data,
                **master_profile_json
            }
            self.db.commit()

        return ProfileRetrievedEvent(
            analysis_id=self.analysis_id,
            master_profile_json=master_profile_json,
            job_description=job_description,
            target_score=target_score,
            max_iterations=max_iterations
        )

    @step()
    async def draft_resume(self, ev: Union[ProfileRetrievedEvent, RewriteEvent]) -> ResumeDraftedEvent:
        """Step 2: Use LLM to tailor structured resume JSON based on JD and feedback."""
        iteration = 1
        human_feedback = None

        if isinstance(ev, ProfileRetrievedEvent):
            master_profile = ev.master_profile_json
            jd = ev.job_description
            target_score = ev.target_score
            max_iterations = ev.max_iterations
            rewrite_prompt = "Draft the first tailored version based on the Job Description."
        else:
            # It is a RewriteEvent (subsequent iterations)
            jd = ev.job_description
            target_score = ev.target_score
            max_iterations = ev.max_iterations
            iteration = ev.iteration
            master_profile = ev.resume_data
            
            # Combine Critic feedback + User manual feedback
            critic = ev.critic_feedback
            human_feedback = ev.human_feedback
            
            rewrite_prompt = (
                f"This is iteration {iteration}. Please revise the previous tailored resume draft.\n\n"
                f"AI Critic Analysis of previous draft:\n{critic}\n\n"
            )
            if human_feedback:
                rewrite_prompt += f"Human User Request / Guidance:\n{human_feedback}\n\n"
            
            rewrite_prompt += "Ensure you address these issues specifically while retaining a clean, factual tone."

        logger.info(f"[AutoTailorWorkflow] Drafting tailored resume. Iteration={iteration}")

        llm = get_nexus_llm()

        system_prompt = (
            "You are a professional resume editor. Given a candidate's master resume details and a target Job Description (JD), "
            "generate an optimized, tailored version of their resume in JSON. "
            "Rules:\n"
            "1. Align the candidate's achievements, projects, and skills to highlight match with the JD.\n"
            "2. DO NOT fabricate experiences, companies, degrees, or skills. Only rephrase, emphasize, or contextualize their actual history.\n"
            "3. Use strong, action-oriented verbs. Bullet points must be detailed and metrics-driven (e.g. 'Improved response time by 20%').\n"
            "4. Respond ONLY with valid JSON conforming to the requested schema. No markdown fences outside the JSON."
        )

        prompt = (
            f"Job Description:\n{jd}\n\n"
            f"Candidate Master Resume:\n{json.dumps(master_profile, indent=2)}\n\n"
            f"Instructions:\n{rewrite_prompt}"
        )

        schema_json = ResumeStructure.model_json_schema()
        schema_str = f"Respond in this JSON schema:\n{json.dumps(schema_json)}"

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=f"{system_prompt}\n\n{schema_str}"),
            ChatMessage(role=MessageRole.USER, content=prompt)
        ]
        response = await llm.achat(messages)
        resume_data = self._extract_json(response.message.content)

        return ResumeDraftedEvent(
            analysis_id=self.analysis_id,
            resume_data=resume_data,
            job_description=jd,
            target_score=target_score,
            max_iterations=max_iterations,
            iteration=iteration,
            human_feedback=human_feedback
        )

    @step()
    async def score_resume(self, ev: ResumeDraftedEvent) -> ResumeScoredEvent:
        """Step 3: Score the tailored JSON against JD using the existing resume scorer."""
        resume_data = ev.resume_data
        jd = ev.job_description
        target_score = ev.target_score
        max_iterations = ev.max_iterations
        iteration = ev.iteration
        human_feedback = ev.human_feedback

        logger.info(f"[AutoTailorWorkflow] Scoring draft via analyze_resume_v2. Iteration={iteration}")

        # Synthesize resume JSON into raw text format for scoring
        resume_text = self._synthesize_to_text(resume_data)

        # Call the existing resume analyzer
        from app.services.nexus_ai.core.analyzer import analyze_resume_v2
        analysis = await analyze_resume_v2(resume_text, jd)

        # Map results to scores structure
        scores = {
            "overall": analysis["scores"]["overall"],
            "ats": analysis["ats_analysis"],
            "technical": analysis["technical_score"]
        }

        # Build critic feedback from the analyzer's recommendations & gaps
        critic_lines = []
        
        gap_summary = analysis.get("gap_analysis", {}).get("summary")
        if gap_summary:
            critic_lines.append(f"### Gap Analysis Summary\n{gap_summary}\n")
            
        critic_lines.append("### Actionable Recommendations")
        recs = analysis.get("recommendations", [])
        if recs:
            for r in recs:
                priority = r.get("priority", "medium").upper()
                action = r.get("action")
                reason = r.get("reason")
                critic_lines.append(f"- **[{priority}]** {action}\n  *Reason:* {reason}")
        else:
            critic_lines.append("- No specific gaps identified. Resume aligns well.")

        critic_feedback = "\n".join(critic_lines)

        return ResumeScoredEvent(
            analysis_id=self.analysis_id,
            resume_data=resume_data,
            scores=scores,
            critic_feedback=critic_feedback,
            job_description=jd,
            target_score=target_score,
            max_iterations=max_iterations,
            iteration=iteration,
            human_feedback=human_feedback
        )

    @step()
    async def evaluate_score(self, ev: ResumeScoredEvent) -> StopEvent:
        """Step 4: Suspend workflow and store intermediate draft results, waiting for human approval."""
        analysis_id = ev.analysis_id
        resume_data = ev.resume_data
        scores = ev.scores
        critic = ev.critic_feedback
        jd = ev.job_description
        target_score = ev.target_score
        max_iterations = ev.max_iterations
        iteration = ev.iteration

        overall = scores["overall"]
        logger.info(f"[AutoTailorWorkflow] Suspending workflow to allow Human-in-the-loop iteration approvals. Iteration={iteration}")

        # Save 'needs_approval_attention' state in database and compute diff
        analysis_record = (
            self.db.query(NexusResumeAnalysis)
            .filter(NexusResumeAnalysis.id == self.analysis_id)
            .first()
        )
        
        old_data = {}
        if analysis_record and analysis_record.analysis:
            history = analysis_record.analysis.get("history", [])
            if history:
                old_data = history[-1].get("resume_data", {})
            else:
                resume_file = self.db.query(NexusResumeFile).filter(NexusResumeFile.resume_id == analysis_record.resume_id).first()
                if resume_file and resume_file.extracted_data:
                    old_data = resume_file.extracted_data
        
        # Inject old experiences directly into resume_data to support frontend's Diff View
        if old_data.get("experiences"):
            resume_data["original_experiences"] = old_data.get("experiences")
        elif old_data.get("resume_data", {}).get("experiences"):
            resume_data["original_experiences"] = old_data.get("resume_data", {}).get("experiences")
        else:
            resume_data["original_experiences"] = resume_data.get("experiences", [])
        
        diff_state = {
            "old": old_data,
            "new": resume_data
        }

        if analysis_record:
            analysis_record.overall_score = overall
            history = analysis_record.analysis.get("history", []) if analysis_record.analysis else []
            history.append({
                "iteration": iteration,
                "overall_score": overall,
                "resume_data": resume_data,
                "critic_feedback": critic,
                "scores_breakdown": scores
            })
            
            analysis_record.analysis = {
                **analysis_record.analysis,
                "status": "paused_for_human",
                "current_iteration": iteration,
                "target_score": target_score,
                "latest_score": overall,
                "resume_data": resume_data,
                "scores_breakdown": scores,
                "critic_feedback": critic,
                "history": history,
                "diff": diff_state
            }
            self.db.commit()

        paused_payload = {
            "status": "paused_for_human",
            "current_iteration": iteration,
            "target_score": target_score,
            "latest_score": overall,
            "resume_data": resume_data,
            "scores_breakdown": scores,
            "critic_feedback": critic,
            "diff": diff_state
        }
        return StopEvent(result=paused_payload)

    # ─── Helper Methods ────────────────────────────────────────────────────────

    def _extract_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        # Clean trailing commas
        import re
        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r",\s*\]", "]", text)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"[AutoTailorWorkflow] JSON parsing failed: {e}. Raw text: {text[:500]}")
            # Fallback structure
            return {}

    def _synthesize_to_text(self, data: Dict[str, Any]) -> str:
        """Convert structured resume JSON into a clean text block for computational scoring."""
        lines = []
        lines.append(f"Name: {data.get('name', '')}")
        lines.append(f"Email: {data.get('email', '')}")
        lines.append(f"Location: {data.get('location', '')}")
        
        lines.append("\nWork Experience:")
        for exp in data.get("experiences", []):
            lines.append(f"- {exp.get('title')} at {exp.get('company')} ({exp.get('dates')})")
            for bullet in exp.get("responsibilities", []):
                lines.append(f"  * {bullet}")
                
        lines.append("\nEducation:")
        for edu in data.get("education", []):
            lines.append(f"- {edu.get('degree')} from {edu.get('institution')} ({edu.get('graduation_date')})")

        lines.append("\nProjects:")
        for proj in data.get("projects", []):
            lines.append(f"- {proj.get('title')}")
            for desc in proj.get("descriptions", []):
                lines.append(f"  * {desc}")

        lines.append("\nSkills:")
        skills = data.get("skills", {})
        if isinstance(skills, dict):
            for cat, val in skills.items():
                lines.append(f"- {cat}: {val}")
        else:
            lines.append(str(skills))

        return "\n".join(lines)

    def _compile_pdf_file(self, resume_data: Dict[str, Any]) -> Optional[str]:
        """Compile final resume LaTeX source into a PDF file using the existing generator."""
        import tempfile
        import os
        from app.config import settings

        upload_dir = settings.nexus_resume_upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        pdf_filename = f"tailored_{self.analysis_id}.pdf"
        pdf_path = os.path.join(upload_dir, pdf_filename)

        logger.info(f"[AutoTailorWorkflow] Compiling LaTeX resume to PDF at: {pdf_path}")
        try:
            result = generate_resume_pdf(resume_data, pdf_path)
            if result.get("success"):
                return pdf_path
            else:
                logger.error(f"[AutoTailorWorkflow] PDF compilation failed: {result.get('message')}")
                return None
        except Exception as e:
            logger.error(f"[AutoTailorWorkflow] Exception during PDF compilation: {e}")
            return None
