"""Jobs API routes."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class FetchJobsRequest(BaseModel):
    query: str = "machine learning engineer"
    location: str = "India"
    source: str = "adzuna"  # adzuna | local


@router.get("")
def list_jobs(
    q: Optional[str] = Query(None, description="Search term in title, company, or skills"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=50, description="Items per page"),
):
    """
    List locally stored job requirement files with search, filtering, and pagination.
    """
    try:
        from jobs.local_job_loader import load_local_jobs
        jobs = load_local_jobs()

        # Filtering
        filtered = jobs
        if q and q.strip():
            query_str = q.strip().lower()
            filtered = [
                j for j in jobs
                if query_str in str(j.get("title", "")).lower()
                or query_str in str(j.get("company", "")).lower()
                or any(query_str in str(s).lower() for s in (j.get("required_skills") or []))
                or any(query_str in str(s).lower() for s in (j.get("preferred_skills") or []))
            ]

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_jobs = filtered[start:end]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "dataset_disclaimer": "This is a curated local dataset of 13 job specifications used for prototype analysis, not a live global market survey.",
            "jobs": [
                {
                    "job_id": j.get("job_id"),
                    "title": j.get("title"),
                    "company": j.get("company"),
                    "location": j.get("location"),
                    "source": j.get("source", "local"),
                    "required_skills": j.get("required_skills") or [],
                    "preferred_skills": j.get("preferred_skills") or [],
                    "experience_requirements": j.get("experience_requirements") or [],
                    "responsibilities": j.get("responsibilities") or [],
                }
                for j in paginated_jobs
            ],
        }
    except FileNotFoundError:
        return {"total": 0, "page": page, "page_size": page_size, "jobs": [], "message": "No job data directory found."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{job_id}")
def get_job(job_id: str):
    """Return a specific job by ID from local storage."""
    try:
        from jobs.local_job_loader import load_local_jobs
        jobs = load_local_jobs()
        for job in jobs:
            if str(job.get("job_id")) == job_id:
                return job
        raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/fetch")
def fetch_jobs(request: FetchJobsRequest):
    """Fetch new jobs from Adzuna API and save locally."""
    if request.source == "local":
        from jobs.local_job_loader import load_local_jobs
        jobs = load_local_jobs()
        return {"status": "loaded_local", "count": len(jobs)}

    try:
        from jobs.api_client import fetch_jobs as adzuna_fetch, process_jobs
        url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
        data = adzuna_fetch(url, query=request.query)
        saved_jobs = process_jobs(data)
        return {
            "status": "fetched",
            "source": "adzuna",
            "count": len(saved_jobs),
            "jobs": [{"job_id": j.job_id, "title": j.title, "company": j.company} for j in saved_jobs],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Job fetch failed: {exc}")


@router.post("/{job_id}/analyze")
def analyze_job_endpoint(job_id: str, force_refresh: bool = False):
    """Analyze a job posting using Groq LLM."""
    try:
        from jobs.local_job_loader import load_local_jobs
        from jobs.analyzer import analyze_job
        jobs = load_local_jobs()
        job = next((j for j in jobs if str(j.get("job_id")) == job_id), None)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found.")
        result = analyze_job(job, use_cache=True, force_refresh=force_refresh)
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Job analysis failed: {exc}")
