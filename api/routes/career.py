"""Career state API routes."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/state")
def get_career_state():
    """Return the current Career State."""
    from core.persistence import load_career_state
    state = load_career_state()
    if not state:
        return {"status": "no_data", "message": "No career state found. Run matching first."}
    return {"status": "ok", "state": state}


@router.get("/readiness")
def get_readiness():
    """Return multi-dimensional readiness scores for all target roles."""
    from core.persistence import load_career_state, list_interview_sessions
    from intelligence.readiness import compute_multi_role_readiness
    state = load_career_state()
    if not state:
        raise HTTPException(status_code=400, detail="No career state. Run matching first.")
    sessions = list_interview_sessions()
    readiness = compute_multi_role_readiness(state, sessions)
    return {
        "status": "ok",
        "disclaimer": (
            "Readiness scores are estimates for self-improvement purposes only. "
            "They are not hiring probabilities."
        ),
        "readiness": readiness,
    }
