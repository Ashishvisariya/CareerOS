"""
CareerOS — FastAPI backend.

Entry point: python -m uvicorn api.main:app --reload
API docs:   http://127.0.0.1:8000/docs
UI Web App: http://127.0.0.1:8000/
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Ensure repo root is on sys.path so all modules resolve correctly
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from api.routes import resume, jobs, matching, career, roadmap, interview, agent, data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CareerOS API",
    description="AI Career Operating System — Backend API & Static Application",
    version="1.0.0",
)

# Standardized error envelope handler
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status_code": exc.status_code,
                "detail": exc.detail if isinstance(exc.detail, str) else exc.detail,
                "path": str(request.url.path),
            }
        },
    )

# Restrained CORS for same-origin and common local dev ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── API Routes ─────────────────────────────────────────────────────────────
app.include_router(resume.router, prefix="/api/v1/resume", tags=["Resume"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["Matching"])
app.include_router(career.router, prefix="/api/v1/career", tags=["Career"])
app.include_router(roadmap.router, prefix="/api/v1/roadmap", tags=["Roadmap"])
app.include_router(interview.router, prefix="/api/v1/interviews", tags=["Interview"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])
app.include_router(data.router, prefix="/api/v1/data", tags=["Data & Privacy"])


@app.get("/health", tags=["Health"])
def health() -> dict:
    """Liveness check — instant status without any external API or storage calls."""
    return {
        "status": "healthy",
        "service": "CareerOS",
        "version": "1.0.0",
    }


@app.get("/ready", tags=["Health"])
def readiness() -> dict:
    """
    Readiness check — verifies local storage accessibility and config status
    WITHOUT making paid external API calls.
    """
    from core.config import get_settings
    from ingestion.pipeline import has_resume

    settings = get_settings()
    storage_ok = settings.data_dir.exists() and settings.chroma_dir.exists()

    return {
        "status": "ready" if storage_ok else "unready",
        "storage": {
            "data_directory_ok": settings.data_dir.exists(),
            "chroma_directory_ok": settings.chroma_dir.exists(),
        },
        "providers_configured": {
            "groq": settings.groq_configured,
            "google_embeddings": settings.google_configured,
            "adzuna": settings.adzuna_configured,
        },
        "resume_ingested": has_resume(),
    }


@app.get("/api/v1/status", tags=["Health"])
def status() -> dict:
    """Detailed configuration status without exposing secrets."""
    from core.config import get_settings
    from core.persistence import load_career_state, load_roadmap, list_interview_sessions
    from ingestion.pipeline import has_resume
    settings = get_settings()
    career_state = load_career_state()
    return {
        "groq": {
            "configured": settings.groq_configured,
            "model": settings.groq_model if settings.groq_configured else None,
        },
        "embeddings": {
            "provider": "Google Gemini",
            "configured": settings.google_configured,
            "model": settings.embedding_model,
        },
        "adzuna": {"configured": settings.adzuna_configured},
        "resume_ingested": has_resume(),
        "career_state_loaded": bool(career_state),
        "jobs_analyzed": career_state.get("jobs_analyzed", 0),
        "roadmap_missions": len(load_roadmap()),
        "interview_sessions": len(list_interview_sessions()),
    }


# ── Mount Static Frontend ──────────────────────────────────────────────────
_FRONTEND_DIR = _REPO_ROOT / "frontend"

if _FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=_FRONTEND_DIR / "css"), name="css")
    app.mount("/js", StaticFiles(directory=_FRONTEND_DIR / "js"), name="js")

    @app.get("/")
    async def serve_index():
        return FileResponse(_FRONTEND_DIR / "index.html")

    # SPA catch-all fallback for non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API or docs routes
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json", "health", "ready"):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = _FRONTEND_DIR / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_FRONTEND_DIR / "index.html")
