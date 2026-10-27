"""
CareerOS — Learning Roadmap Generator.

Generates a personalized, prioritized learning roadmap from actual skill gaps
and candidate career goals using Groq LLM for explanations,
and deterministic Python logic for prioritization.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from core.llm import get_llm, invoke_with_retry
from core.persistence import load_roadmap, save_roadmap

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Mission schema (internal, not exported as API schema)
# ──────────────────────────────────────────────────────────────────────────────

class LearningMission(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    skill: str
    category: str = "General"
    why_it_matters: str = ""
    target_competency: str = ""
    learning_objectives: list[str] = Field(default_factory=list)
    practical_exercise: str = ""
    mini_project: str = ""
    estimated_hours: int = 10
    priority_score: float = 0.0
    # job_frequency: how many jobs in dataset require this skill
    job_frequency: int = 0
    is_required_skill: bool = True
    status: str = "not_started"  # not_started | in_progress | completed
    notes: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ──────────────────────────────────────────────────────────────────────────────
# Priority calculation (deterministic)
# ──────────────────────────────────────────────────────────────────────────────

def _compute_priority(
    skill: str,
    job_frequency: int,
    total_jobs: int,
    is_required: bool,
    candidate_skills_lower: set[str],
) -> float:
    """
    Compute a priority score 0–100 using transparent deterministic factors.

    Factors:
    - Market demand (job_frequency / total_jobs) × 50
    - Required vs preferred: required adds 30, preferred adds 15
    - Candidate doesn't have it: already implied (we only prioritize gaps)
    """
    demand_score = (job_frequency / max(total_jobs, 1)) * 50
    requirement_score = 30.0 if is_required else 15.0
    return round(min(demand_score + requirement_score, 100.0), 2)


# ──────────────────────────────────────────────────────────────────────────────
# Groq-powered mission enrichment
# ──────────────────────────────────────────────────────────────────────────────

_MISSION_PROMPT = """You are a career coach creating a personalized learning mission for an AI/ML job candidate.

Skill to learn: {skill}
Target roles: {target_roles}
Candidate's current skills: {current_skills}

Create a focused learning mission with:
1. A one-sentence explanation of why this skill matters for the target roles
2. A clear target competency statement (what "done" looks like)
3. Three specific learning objectives (concise bullet points)
4. One practical exercise (a concrete coding task or project)
5. An estimated learning effort in hours (be realistic: 5–40)

Format your response as follows (use these exact labels):
WHY: <one sentence>
TARGET: <target competency>
OBJ1: <objective 1>
OBJ2: <objective 2>
OBJ3: <objective 3>
EXERCISE: <practical exercise>
HOURS: <number only>
"""


def _enrich_mission_with_llm(
    skill: str,
    target_roles: list[str],
    current_skills: list[str],
) -> dict[str, Any]:
    """Use Groq to generate human-readable mission content."""
    try:
        llm = get_llm(temperature=0.3, max_tokens=600)
        prompt = _MISSION_PROMPT.format(
            skill=skill,
            target_roles=", ".join(target_roles) or "AI/ML Engineer",
            current_skills=", ".join(current_skills[:15]) or "None listed",
        )
        response = invoke_with_retry(llm, prompt)
        text = response.content if hasattr(response, "content") else str(response)

        parsed: dict[str, Any] = {}
        for line in text.splitlines():
            for key, field in [
                ("WHY:", "why_it_matters"),
                ("TARGET:", "target_competency"),
                ("OBJ1:", "_obj1"),
                ("OBJ2:", "_obj2"),
                ("OBJ3:", "_obj3"),
                ("EXERCISE:", "practical_exercise"),
                ("HOURS:", "_hours"),
            ]:
                if line.startswith(key):
                    val = line[len(key):].strip()
                    parsed[field] = val

        objectives = [
            parsed.pop("_obj1", ""),
            parsed.pop("_obj2", ""),
            parsed.pop("_obj3", ""),
        ]
        parsed["learning_objectives"] = [o for o in objectives if o]

        try:
            parsed["estimated_hours"] = int(parsed.pop("_hours", 10))
        except (ValueError, TypeError):
            parsed["estimated_hours"] = 10

        return parsed

    except Exception as exc:
        logger.warning("LLM enrichment failed for skill '%s': %s", skill, exc)
        return {}


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def generate_roadmap(
    recurring_gaps: list[str],
    target_roles: list[str],
    current_skills: list[str],
    market_skill_stats: list[dict] | None = None,
    max_missions: int = 10,
    enrich_with_llm: bool = True,
) -> list[dict]:
    """
    Generate a prioritized learning roadmap.

    Parameters
    ----------
    recurring_gaps:
        Skills missing across multiple jobs (from career state).
    target_roles:
        Candidate's target role titles.
    current_skills:
        Candidate's current skills.
    market_skill_stats:
        List of MarketSkillStat dicts with 'skill', 'job_count', etc.
    max_missions:
        Maximum number of missions to generate.
    enrich_with_llm:
        If True, use Groq to enrich each mission with objectives and exercises.

    Returns
    -------
    List of mission dicts, persisted to disk.
    """
    stats_by_skill: dict[str, dict] = {}
    total_jobs = 1
    if market_skill_stats:
        for stat in market_skill_stats:
            name = stat.get("skill", "")
            stats_by_skill[name] = stat
        # Infer total jobs from max job_count / demand_percentage
        for stat in market_skill_stats:
            pct = stat.get("demand_percentage", 0)
            cnt = stat.get("job_count", 0)
            if pct > 0:
                total_jobs = max(total_jobs, round(cnt / (pct / 100)))

    current_lower = {s.lower() for s in current_skills}
    candidate_lower = {s.lower() for s in current_skills}

    # Deduplicate and filter: only gaps the candidate doesn't have
    seen: set[str] = set()
    gap_skills: list[str] = []
    for s in recurring_gaps:
        if s.lower() not in candidate_lower and s not in seen:
            seen.add(s)
            gap_skills.append(s)

    # Sort by priority
    def priority(skill: str) -> float:
        stat = stats_by_skill.get(skill, {})
        job_count = stat.get("job_count", 1)
        is_required = not stat.get("candidate_has_skill", False)
        return _compute_priority(skill, job_count, total_jobs, is_required, candidate_lower)

    gap_skills.sort(key=priority, reverse=True)
    gap_skills = gap_skills[:max_missions]

    missions: list[LearningMission] = []
    for skill in gap_skills:
        stat = stats_by_skill.get(skill, {})
        job_count = stat.get("job_count", 1)
        p_score = _compute_priority(skill, job_count, total_jobs, True, candidate_lower)

        mission = LearningMission(
            skill=skill,
            job_frequency=job_count,
            priority_score=p_score,
        )

        if enrich_with_llm:
            enrichment = _enrich_mission_with_llm(skill, target_roles, current_skills)
            for field, val in enrichment.items():
                if hasattr(mission, field) and val:
                    setattr(mission, field, val)

        missions.append(mission)

    mission_dicts = [m.model_dump() for m in missions]
    save_roadmap(mission_dicts)
    logger.info("Generated and saved %d learning missions", len(mission_dicts))
    return mission_dicts


def get_roadmap() -> list[dict]:
    """Return the currently persisted roadmap missions."""
    return load_roadmap()


def complete_mission(mission_id: str, notes: str = "") -> bool:
    """Mark a mission as completed and persist."""
    from core.persistence import update_mission_status
    return update_mission_status(mission_id, "completed", notes)


def start_mission(mission_id: str) -> bool:
    """Mark a mission as in_progress."""
    from core.persistence import update_mission_status
    return update_mission_status(mission_id, "in_progress")
