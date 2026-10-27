"""
CareerOS — Job Analyzer (Groq-based).

Analyzes raw job postings to extract structured requirements using Groq.
Caches results to avoid repeated LLM calls for the same job.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from core.config import get_settings
from core.llm import get_structured_llm, invoke_with_retry
from schemas.job_analysis import JobAnalysis

logger = logging.getLogger(__name__)


def _cache_path(job_id: str) -> Path:
    """Return path to cached analysis for a job ID."""
    settings = get_settings()
    cache_dir = settings.data_dir / "job_analysis_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    # Sanitize job_id for filesystem
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in job_id)
    return cache_dir / f"{safe_id}.json"


def _load_cache(job_id: str) -> JobAnalysis | None:
    """Load cached JobAnalysis if available."""
    path = _cache_path(job_id)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return JobAnalysis(**data)
        except Exception as exc:
            logger.warning("Could not load cached analysis for %s: %s", job_id, exc)
    return None


def _save_cache(job_id: str, analysis: JobAnalysis) -> None:
    """Persist JobAnalysis to cache."""
    path = _cache_path(job_id)
    try:
        path.write_text(
            json.dumps(analysis.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.warning("Could not cache analysis for %s: %s", job_id, exc)


_ANALYSIS_PROMPT = """You are an expert job requirements extraction system.

Analyze the job posting below and extract structured information.

RULES:
- Extract ONLY information present in the job description
- Do NOT invent requirements
- Skills should be concise (e.g., "Python" not "Python programming language")
- Separate required vs preferred skills based on language like "required", "must", "nice to have", "preferred"
- If not clear, put in required_skills

JOB TITLE: {title}
COMPANY: {company}
JOB DESCRIPTION:
{description}

Extract the JobAnalysis with these fields:
- job_id: "{job_id}"
- title: job title
- company: company name  
- required_skills: list of explicitly required technical skills
- preferred_skills: list of preferred/nice-to-have skills
- experience_requirements: list of experience requirements
- education_requirements: list of education requirements
- responsibilities: main job responsibilities (max 8)
- technologies: all tools, frameworks, platforms, and libraries mentioned
- key_requirements: 3-5 most critical requirements for this role"""


def analyze_job(
    job: dict[str, Any],
    *,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> JobAnalysis:
    """
    Analyze a job posting dict and return a structured JobAnalysis.

    Parameters
    ----------
    job:
        Job dict with at minimum 'job_id', 'title', 'description'.
    use_cache:
        If True, return cached analysis when available.
    force_refresh:
        If True, re-analyze even if cached result exists.

    Returns
    -------
    JobAnalysis with extracted structured data.
    """
    job_id = str(job.get("job_id", "unknown"))
    title = job.get("title", "Unknown")
    company = job.get("company") or "Unknown"
    description = job.get("description") or ""

    # Check cache first
    if use_cache and not force_refresh:
        cached = _load_cache(job_id)
        if cached:
            logger.debug("Returning cached analysis for job %s", job_id)
            return cached

    # Check if description is empty — fall back to structured fields
    if not description.strip():
        # Build description from structured local job fields
        parts = []
        for field in ["responsibilities", "required_skills", "preferred_skills",
                       "experience_requirements", "technologies", "key_requirements"]:
            vals = job.get(field, []) or []
            if vals:
                parts.append(f"{field.replace('_', ' ').title()}: {', '.join(str(v) for v in vals)}")
        description = "\n".join(parts) or f"{title} role at {company}"

    prompt = _ANALYSIS_PROMPT.format(
        job_id=job_id,
        title=title,
        company=company,
        description=description[:4000],  # Limit to avoid token overflow
    )

    structured_llm = get_structured_llm(JobAnalysis)

    try:
        result = invoke_with_retry(structured_llm, prompt)
    except Exception as exc:
        logger.error("Job analysis failed for job %s: %s", job_id, exc)
        raise RuntimeError(f"Job analysis failed for '{title}': {exc}") from exc

    if not isinstance(result, JobAnalysis):
        raise ValueError(f"LLM returned unexpected type {type(result)} for job {job_id}")

    # Override job_id in case LLM returned empty string
    if not result.job_id:
        result = result.model_copy(update={"job_id": job_id})

    # Save to cache
    _save_cache(job_id, result)

    logger.info(
        "Analyzed job %s (%s): %d required skills, %d preferred",
        job_id, title, len(result.required_skills), len(result.preferred_skills)
    )
    return result


def analyze_jobs_from_local_data() -> list[JobAnalysis]:
    """
    Analyze all local job requirement files that haven't been analyzed yet.
    """
    from jobs.local_job_loader import load_local_jobs
    jobs = load_local_jobs()
    results: list[JobAnalysis] = []
    for job in jobs:
        try:
            analysis = analyze_job(job, use_cache=True)
            results.append(analysis)
        except Exception as exc:
            logger.warning("Skipped job %s due to error: %s", job.get("job_id"), exc)
    return results
