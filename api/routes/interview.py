"""Interview API routes."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class CreateSessionRequest(BaseModel):
    target_role: str
    interview_type: str = "technical"
    difficulty: str = "mid"
    max_questions: int = 5
    job_id: str | None = None
    candidate_skills: list[str] = []


class AnswerRequest(BaseModel):
    answer: str


@router.get("")
def list_sessions():
    """List all interview sessions."""
    from intelligence.interview import get_all_sessions
    sessions = get_all_sessions()
    return {
        "count": len(sessions),
        "sessions": [
            {
                "session_id": s.get("session_id"),
                "target_role": s.get("target_role"),
                "status": s.get("status"),
                "interview_type": s.get("interview_type"),
                "turns_completed": len([t for t in s.get("turns", []) if t.get("answer")]),
                "max_questions": s.get("max_questions"),
                "created_at": s.get("created_at"),
            }
            for s in sessions
        ],
    }


@router.post("")
def create_session(request: CreateSessionRequest):
    """Create a new interview session and get the first question."""
    try:
        from intelligence.interview import create_session as _create
        # Load candidate skills from career state if not provided
        skills = request.candidate_skills
        if not skills:
            from core.persistence import load_resume_meta
            meta = load_resume_meta()
            skills = meta.get("skills", []) if meta else []

        session = _create(
            target_role=request.target_role,
            interview_type=request.interview_type,
            difficulty=request.difficulty,
            max_questions=request.max_questions,
            candidate_skills=skills,
            job_id=request.job_id,
        )
        return session
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Session creation failed: {exc}")


@router.post("/{session_id}/answer")
def submit_answer(session_id: str, request: AnswerRequest):
    """Submit an answer and get evaluation + next question."""
    if not request.answer or not request.answer.strip():
        raise HTTPException(status_code=422, detail="Answer cannot be empty.")
    try:
        from intelligence.interview import submit_answer as _submit
        return _submit(session_id, request.answer.strip())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Answer submission failed: {exc}")


@router.get("/{session_id}/results")
def get_session_results(session_id: str):
    """Return a completed interview session with evaluation."""
    from intelligence.interview import get_session
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found.")
    return session


@router.delete("/{session_id}")
def delete_session(session_id: str):
    """Delete an interview session."""
    from intelligence.interview import delete_session as _delete
    if not _delete(session_id):
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} not found.")
    return {"status": "deleted", "session_id": session_id}
