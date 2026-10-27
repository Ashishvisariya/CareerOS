"""
CareerOS — Career Readiness Assessment.

Computes a transparent multi-dimensional readiness score for each target role.
All calculations are deterministic Python; Groq is NOT used here to prevent
presenting LLM-generated guesses as objective scores.

Methodology is explicitly documented in each function's docstring.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Score weights (documented and visible to users)
# ──────────────────────────────────────────────────────────────────────────────

DIMENSION_WEIGHTS = {
    "required_skill_coverage": 0.40,
    "preferred_skill_coverage": 0.15,
    "project_evidence": 0.15,
    "experience_alignment": 0.15,
    "interview_preparation": 0.15,
}

DISCLAIMER = (
    "This readiness score is an estimate based on structured comparisons "
    "between resume data and job requirements. It is NOT a hiring probability "
    "and does NOT measure overall ability or career potential."
)


# ──────────────────────────────────────────────────────────────────────────────
# Individual dimension calculations
# ──────────────────────────────────────────────────────────────────────────────

def _score_required_skills(
    matched_required: list[str],
    total_required: int,
) -> float:
    """Required skill coverage = matched_required / total_required × 100."""
    if total_required == 0:
        return 0.0
    return round((len(matched_required) / total_required) * 100, 2)


def _score_preferred_skills(
    matched_preferred: list[str],
    total_preferred: int,
) -> float:
    """Preferred skill coverage = matched_preferred / total_preferred × 100."""
    if total_preferred == 0:
        return 0.0
    return round((len(matched_preferred) / total_preferred) * 100, 2)


def _score_project_evidence(
    projects: list[str],
    required_skills: list[str],
) -> float:
    """
    Estimate how well projects demonstrate required skills.

    Method: For each required skill, check if any project description mentions
    a related keyword. Returns percentage of required skills with project evidence.
    """
    if not required_skills:
        return 50.0  # Neutral when no requirements specified

    if not projects:
        return 0.0

    project_text = " ".join(projects).lower()
    evidenced = sum(
        1 for skill in required_skills if skill.lower() in project_text
    )
    return round((evidenced / len(required_skills)) * 100, 2)


def _score_experience_alignment(
    experience: list[str],
    experience_requirements: list[str],
) -> float:
    """
    Keyword-based experience alignment.

    Checks how many experience requirement keywords appear in candidate experience.
    Returns 50.0 (neutral) when no experience requirements are specified.
    """
    if not experience_requirements:
        return 50.0

    if not experience:
        return 0.0

    exp_text = " ".join(experience).lower()
    req_text = " ".join(experience_requirements).lower()

    # Extract meaningful keywords (longer than 3 chars)
    keywords = [w for w in req_text.split() if len(w) > 3]
    if not keywords:
        return 50.0

    matched = sum(1 for kw in keywords if kw in exp_text)
    return round((matched / len(keywords)) * 100, 2)


def _score_interview_prep(interview_sessions: list[dict]) -> float:
    """
    Score based on completed interview practice sessions.

    0 sessions → 0%
    1 session  → 40%
    2 sessions → 60%
    3+ sessions → scales up to 80% (cap at 80 to reflect it's practice, not real interview)
    """
    n = len(interview_sessions)
    if n == 0:
        return 0.0
    if n == 1:
        return 40.0
    if n == 2:
        return 60.0
    return min(60.0 + (n - 2) * 10.0, 80.0)


# ──────────────────────────────────────────────────────────────────────────────
# Main readiness computation
# ──────────────────────────────────────────────────────────────────────────────

def compute_readiness(
    job_skill_gap: dict[str, Any],
    projects: list[str],
    experience: list[str],
    interview_sessions: list[dict] | None = None,
    experience_requirements: list[str] | None = None,
) -> dict[str, Any]:
    """
    Compute a multi-dimensional readiness score for one job.

    Parameters
    ----------
    job_skill_gap:
        Dict from calculate_skill_gap() with matched_required, missing_required, etc.
    projects:
        Candidate project descriptions from resume.
    experience:
        Candidate experience entries from resume.
    interview_sessions:
        List of completed interview session dicts for this role.
    experience_requirements:
        Job's experience requirements list.

    Returns
    -------
    dict with keys: overall_score, dimensions, methodology, disclaimer
    """
    interview_sessions = interview_sessions or []
    experience_requirements = experience_requirements or []

    matched_req = job_skill_gap.get("matched_required", [])
    missing_req = job_skill_gap.get("missing_required", [])
    matched_pref = job_skill_gap.get("matched_preferred", [])
    missing_pref = job_skill_gap.get("missing_preferred", [])

    total_required = len(matched_req) + len(missing_req)
    total_preferred = len(matched_pref) + len(missing_pref)
    all_required = matched_req + missing_req

    dim_scores = {
        "required_skill_coverage": _score_required_skills(matched_req, total_required),
        "preferred_skill_coverage": _score_preferred_skills(matched_pref, total_preferred),
        "project_evidence": _score_project_evidence(projects, all_required),
        "experience_alignment": _score_experience_alignment(experience, experience_requirements),
        "interview_preparation": _score_interview_prep(interview_sessions),
    }

    # Weighted overall score
    overall = sum(
        dim_scores[dim] * weight
        for dim, weight in DIMENSION_WEIGHTS.items()
    )
    overall = round(overall, 2)

    # Next actions by highest-impact dimension gap
    gaps_by_impact = sorted(
        [
            (dim, 100.0 - score, DIMENSION_WEIGHTS[dim])
            for dim, score in dim_scores.items()
        ],
        key=lambda x: x[1] * x[2],
        reverse=True,
    )

    next_actions: list[str] = []
    for dim, gap, weight in gaps_by_impact[:3]:
        if gap > 10:
            readable = dim.replace("_", " ").title()
            next_actions.append(
                f"Improve {readable} (currently {dim_scores[dim]:.0f}%, "
                f"weight {weight*100:.0f}%)"
            )

    return {
        "overall_score": overall,
        "dimensions": dim_scores,
        "dimension_weights": DIMENSION_WEIGHTS,
        "matched_required_skills": matched_req,
        "missing_required_skills": missing_req,
        "matched_preferred_skills": matched_pref,
        "missing_preferred_skills": missing_pref,
        "next_actions": next_actions,
        "methodology": (
            "overall = Σ(dimension_score × weight). "
            f"Weights: required_skills={DIMENSION_WEIGHTS['required_skill_coverage']}, "
            f"preferred_skills={DIMENSION_WEIGHTS['preferred_skill_coverage']}, "
            f"projects={DIMENSION_WEIGHTS['project_evidence']}, "
            f"experience={DIMENSION_WEIGHTS['experience_alignment']}, "
            f"interview={DIMENSION_WEIGHTS['interview_preparation']}."
        ),
        "disclaimer": DISCLAIMER,
    }


def compute_multi_role_readiness(
    career_state: dict,
    interview_sessions: list[dict] | None = None,
) -> dict[str, Any]:
    """
    Compute readiness scores across all target roles using career state data.

    Returns a dict mapping job_id → readiness result.
    """
    interview_sessions = interview_sessions or []
    job_gaps = career_state.get("job_skill_gaps", [])
    projects = career_state.get("projects", [])
    experience = career_state.get("experience", [])

    results: dict[str, Any] = {}

    for gap in job_gaps:
        job_id = gap.get("job_id", "unknown")
        gap_dict = {
            "matched_required": gap.get("matched_required", []),
            "missing_required": gap.get("missing_required", []),
            "matched_preferred": gap.get("matched_preferred", []),
            "missing_preferred": gap.get("missing_preferred", []),
        }

        # Filter interview sessions for this job
        job_sessions = [
            s for s in interview_sessions
            if s.get("job_id") == job_id
        ]

        results[job_id] = {
            "job_title": gap.get("job_title", "Unknown"),
            "company": gap.get("company"),
            **compute_readiness(
                job_skill_gap=gap_dict,
                projects=projects,
                experience=experience,
                interview_sessions=job_sessions,
            ),
        }

    return results
