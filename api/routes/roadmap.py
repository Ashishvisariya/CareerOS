"""Roadmap API routes."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class GenerateRoadmapRequest(BaseModel):
    max_missions: int = 10
    enrich_with_llm: bool = True


class CompleteMissionRequest(BaseModel):
    notes: str = ""


@router.get("")
def get_roadmap():
    """Return all current learning missions."""
    from intelligence.roadmap import get_roadmap as _get
    missions = _get()
    return {
        "count": len(missions),
        "missions": missions,
        "completed": sum(1 for m in missions if m.get("status") == "completed"),
        "in_progress": sum(1 for m in missions if m.get("status") == "in_progress"),
    }


@router.post("/generate")
def generate_roadmap(request: GenerateRoadmapRequest):
    """Generate a personalized learning roadmap from Career State skill gaps."""
    from core.persistence import load_career_state
    from intelligence.roadmap import generate_roadmap as _gen

    state = load_career_state()
    if not state:
        raise HTTPException(
            status_code=400,
            detail="No career state found. Run matching first via POST /api/v1/matching/run"
        )

    missions = _gen(
        recurring_gaps=state.get("recurring_skill_gaps", []),
        target_roles=state.get("target_roles", []),
        current_skills=state.get("current_skills", []),
        market_skill_stats=state.get("market_skill_stats", []),
        max_missions=request.max_missions,
        enrich_with_llm=request.enrich_with_llm,
    )

    return {
        "status": "generated",
        "count": len(missions),
        "missions": missions,
    }


@router.post("/missions/{mission_id}/complete")
def complete_mission(mission_id: str, request: CompleteMissionRequest):
    """Mark a learning mission as completed."""
    from intelligence.roadmap import complete_mission as _complete
    success = _complete(mission_id, request.notes)
    if not success:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id!r} not found.")
    return {"status": "completed", "mission_id": mission_id}


@router.post("/missions/{mission_id}/start")
def start_mission(mission_id: str):
    """Mark a learning mission as in_progress."""
    from intelligence.roadmap import start_mission as _start
    success = _start(mission_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id!r} not found.")
    return {"status": "in_progress", "mission_id": mission_id}
