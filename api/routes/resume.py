"""Resume API routes."""
from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core.config import get_settings
from core.persistence import (
    load_resume_meta,
    save_resume_meta,
    clear_resume_meta,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
_ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


class AnalyzeRequest(BaseModel):
    force_refresh: bool = False


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume file. Accepted: PDF, PNG, JPG."""
    settings = get_settings()

    # Validate extension
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{suffix}'. Accepted: {', '.join(_ALLOWED_EXTENSIONS)}"
        )

    # Read and check size
    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")
    if len(contents) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(contents) // 1024} KB). Max: {_MAX_FILE_SIZE // 1024 // 1024} MB."
        )

    # Save to uploads directory with sanitized name
    upload_id = str(uuid.uuid4())[:8]
    safe_name = f"resume_{upload_id}{suffix}"
    dest = settings.resumes_dir / safe_name

    dest.write_bytes(contents)
    logger.info("Resume uploaded: %s (%d bytes)", dest, len(contents))

    # Ingest into vector store
    try:
        from ingestion.pipeline import ingest_resume
        ingest_result = ingest_resume(str(dest), clear_existing=True)
    except Exception as exc:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}")

    # Clear cached analysis so the new resume gets re-analyzed
    clear_resume_meta()

    return {
        "status": "ingested",
        "filename": safe_name,
        "file_size_bytes": len(contents),
        **ingest_result,
    }


@router.get("/profile")
def get_resume_profile():
    """Return the cached resume analysis, or empty if none available."""
    meta = load_resume_meta()
    if not meta:
        return {"status": "no_resume", "message": "No resume has been uploaded and analyzed yet."}
    return {"status": "ok", "profile": meta}


@router.post("/analyze")
def analyze_resume_endpoint(request: AnalyzeRequest = None):
    """
    Analyze the uploaded resume using Groq and return structured profile.
    Uses cached result unless force_refresh=True.
    """
    if request is None:
        request = AnalyzeRequest()

    if not request.force_refresh:
        cached = load_resume_meta()
        if cached and not cached.get("error"):
            return {"status": "cached", "profile": cached}

    # Check resume is ingested
    from ingestion.pipeline import has_resume
    if not has_resume():
        raise HTTPException(
            status_code=400,
            detail="No resume ingested. Upload a resume first via POST /api/v1/resume/upload"
        )

    try:
        from career.resume_analyzer import analyze_resume
        result = analyze_resume()
        result_dict = result.model_dump()
        save_resume_meta(result_dict)
        return {"status": "analyzed", "profile": result_dict}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")
