"""Data privacy and management routes."""
from __future__ import annotations

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException

from core.config import get_settings
from core.persistence import (
    clear_career_state,
    clear_resume_meta,
    load_career_state,
    load_resume_meta,
    load_roadmap,
    list_interview_sessions,
    save_roadmap,
)
from ingestion.pipeline import get_retriever, _RESUME_COLLECTION, _get_chroma

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
def get_stored_data_summary():
    """Return overview of all data currently stored on disk."""
    settings = get_settings()
    resume_meta = load_resume_meta()
    career_state = load_career_state()
    roadmap = load_roadmap()
    interviews = list_interview_sessions()

    # Check resumes stored on disk
    resume_files = []
    if settings.resumes_dir.exists():
        for f in settings.resumes_dir.glob("*"):
            if f.is_file():
                resume_files.append({"name": f.name, "size_bytes": f.stat().st_size})

    return {
        "status": "ok",
        "storage_location": "Local Disk (JSON & ChromaDB)",
        "has_resume": bool(resume_meta),
        "candidate_name": resume_meta.get("name") or career_state.get("candidate_name") or None,
        "resume_files_count": len(resume_files),
        "resume_files": resume_files,
        "career_state_present": bool(career_state),
        "career_state_updated": career_state.get("last_updated"),
        "roadmap_missions_count": len(roadmap),
        "interview_sessions_count": len(interviews),
        "privacy_notice": "CareerOS stores all data locally on your machine. No telemetry or profile data is sold or shared."
    }


@router.delete("/purge")
def purge_all_candidate_data():
    """
    Permanently delete all candidate-specific data:
    - Chroma vector store chunks
    - Uploaded resume files
    - Cached resume profile metadata
    - Career state
    - Roadmap missions
    - Interview sessions
    """
    settings = get_settings()
    errors = []

    # 1. Clear Chroma collection
    try:
        store = _get_chroma(_RESUME_COLLECTION)
        existing = store.get()
        if existing and existing.get("ids"):
            store.delete(ids=existing["ids"])
            logger.info("Chroma vector store purged")
    except Exception as exc:
        logger.warning("Could not clear vector store: %s", exc)
        errors.append(f"Vector store: {exc}")

    # 2. Clear uploaded resume files
    try:
        if settings.resumes_dir.exists():
            for f in settings.resumes_dir.glob("*"):
                if f.is_file():
                    f.unlink(missing_ok=True)
            logger.info("Uploaded resumes directory cleared")
    except Exception as exc:
        errors.append(f"Resume files: {exc}")

    # 3. Clear career state
    try:
        clear_career_state()
    except Exception as exc:
        errors.append(f"Career state: {exc}")

    # 4. Clear resume meta
    try:
        clear_resume_meta()
    except Exception as exc:
        errors.append(f"Resume meta: {exc}")

    # 5. Clear roadmap
    try:
        save_roadmap([])
    except Exception as exc:
        errors.append(f"Roadmap: {exc}")

    # 6. Clear interview sessions
    try:
        if settings.interviews_dir.exists():
            for f in settings.interviews_dir.glob("*.json"):
                f.unlink(missing_ok=True)
    except Exception as exc:
        errors.append(f"Interviews: {exc}")

    if errors:
        raise HTTPException(
            status_code=500,
            detail={"message": "Partial purge completed with errors", "errors": errors}
        )

    return {
        "status": "purged",
        "message": "All candidate files, vectors, state, and interview records have been permanently deleted from this machine."
    }
