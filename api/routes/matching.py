"""Matching API routes."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class MatchRequest(BaseModel):
    target_roles: list[str] = []
    frequency_threshold: float = 0.40


@router.post("/run")
def run_matching(request: MatchRequest):
    """
    Run resume-to-job matching and update Career State.
    Requires resume to be analyzed and local jobs to be available.
    """
    from core.persistence import load_resume_meta, save_career_state
    from jobs.local_job_loader import load_local_jobs
    from career.state import build_career_state

    # Load resume
    resume_meta = load_resume_meta()
    if not resume_meta or resume_meta.get("error"):
        raise HTTPException(
            status_code=400,
            detail="Resume not analyzed. Call POST /api/v1/resume/analyze first."
        )

    # Load jobs
    try:
        jobs = load_local_jobs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not load jobs: {exc}")

    if not jobs:
        raise HTTPException(status_code=400, detail="No local jobs found to match against.")

    # Build a simple resume-like object for career state
    class ResumeProxy:
        name = resume_meta.get("name")
        skills = resume_meta.get("skills", [])
        experience = resume_meta.get("experience", [])
        projects = resume_meta.get("projects", [])
        education = resume_meta.get("education", [])
        strengths = resume_meta.get("strengths", [])

    target_roles = request.target_roles or _infer_target_roles(resume_meta)
    career_state = build_career_state(
        resume_analysis=ResumeProxy(),
        target_roles=target_roles,
        jobs=jobs,
        frequency_threshold=request.frequency_threshold,
    )

    state_dict = career_state.model_dump()
    save_career_state(state_dict)

    return {
        "status": "matched",
        "jobs_analyzed": career_state.jobs_analyzed,
        "market_skill_coverage": career_state.market_skill_coverage,
        "recurring_skill_gaps": career_state.recurring_skill_gaps,
        "career_stage": career_state.career_stage,
        "summary": career_state.summary,
    }


@router.get("/results")
def get_matching_results():
    """Return the most recent matching results from Career State."""
    from core.persistence import load_career_state
    state = load_career_state()
    if not state:
        return {"status": "no_data", "message": "Run matching first via POST /api/v1/matching/run"}

    return {
        "status": "ok",
        "candidate_name": state.get("candidate_name"),
        "target_roles": state.get("target_roles", []),
        "career_stage": state.get("career_stage"),
        "jobs_analyzed": state.get("jobs_analyzed", 0),
        "market_skill_coverage": state.get("market_skill_coverage"),
        "recurring_skill_gaps": state.get("recurring_skill_gaps", []),
        "job_matches": [
            {
                "job_id": g.get("job_id"),
                "job_title": g.get("job_title"),
                "company": g.get("company"),
                "required_skill_coverage": g.get("required_skill_coverage"),
                "preferred_skill_coverage": g.get("preferred_skill_coverage"),
                "matched_required": g.get("matched_required", []),
                "missing_required": g.get("missing_required", []),
            }
            for g in state.get("job_skill_gaps", [])
        ],
        "summary": state.get("summary", ""),
    }


def _infer_target_roles(resume_meta: dict) -> list[str]:
    """Infer target roles from skills if not explicitly provided."""
    skills_lower = {s.lower() for s in (resume_meta.get("skills") or [])}
    roles = []
    if any(s in skills_lower for s in ["machine learning", "deep learning", "pytorch", "tensorflow"]):
        roles.append("Machine Learning Engineer")
    if any(s in skills_lower for s in ["llms", "rag", "langchain", "nlp"]):
        roles.append("AI Engineer")
    if any(s in skills_lower for s in ["python", "numpy", "pandas", "scikit-learn"]):
        roles.append("Data Scientist")
    return roles or ["AI/ML Engineer"]
