"""
CareerOS — AI Career Agent.

Answers career questions using actual Career State, resume data, job analyses,
roadmap progress, and interview history. Grounds all responses in retrieved data.

Uses Groq for language generation.
Does NOT modify data or scores without explicit calculation.
"""
from __future__ import annotations

import logging
from typing import Any

from core.llm import get_llm, invoke_with_retry
from core.persistence import (
    load_career_state,
    load_roadmap,
    list_interview_sessions,
    load_resume_meta,
)
from jobs.local_job_loader import load_local_jobs

logger = logging.getLogger(__name__)


def _build_context(career_state: dict, resume_meta: dict, roadmap: list, sessions: list) -> str:
    """Build a rich context string from all available application data."""
    parts = []

    # Candidate profile
    name = career_state.get("candidate_name") or resume_meta.get("name") or "the candidate"
    skills = career_state.get("current_skills") or resume_meta.get("skills") or []
    target_roles = career_state.get("target_roles") or []
    experience = career_state.get("experience") or resume_meta.get("experience") or []
    projects = career_state.get("projects") or resume_meta.get("projects") or []
    education = career_state.get("education") or resume_meta.get("education") or []

    parts.append(f"=== CANDIDATE: {name} ===")
    parts.append(f"Target roles: {', '.join(target_roles) or 'Not specified'}")
    parts.append(f"Career stage: {career_state.get('career_stage', 'unknown')}")
    parts.append(f"Skills ({len(skills)}): {', '.join(skills[:20])}")
    if experience:
        parts.append(f"Experience: {'; '.join(experience[:5])}")
    if projects:
        parts.append(f"Projects: {'; '.join(projects[:5])}")
    if education:
        parts.append(f"Education: {'; '.join(education[:3])}")

    # Market insights
    recurring_gaps = career_state.get("recurring_skill_gaps") or []
    market_coverage = career_state.get("market_skill_coverage")
    jobs_analyzed = career_state.get("jobs_analyzed", 0)

    if jobs_analyzed > 0:
        parts.append(f"\n=== MARKET ANALYSIS ({jobs_analyzed} jobs) ===")
        parts.append(f"Market skill coverage: {market_coverage}%")
        if recurring_gaps:
            parts.append(f"Recurring skill gaps: {', '.join(recurring_gaps[:10])}")

    # Job matches
    job_gaps = career_state.get("job_skill_gaps") or []
    if job_gaps:
        parts.append(f"\n=== JOB MATCHES (top 5) ===")
        sorted_gaps = sorted(
            job_gaps,
            key=lambda x: x.get("required_skill_coverage") or 0,
            reverse=True,
        )
        for gap in sorted_gaps[:5]:
            cov = gap.get("required_skill_coverage")
            cov_str = f"{cov}%" if cov is not None else "N/A"
            parts.append(
                f"- {gap['job_title']} @ {gap.get('company', 'Unknown')}: "
                f"{cov_str} required skill coverage, "
                f"missing: {', '.join(gap.get('missing_required', [])[:5])}"
            )

    # Roadmap
    if roadmap:
        pending = [m for m in roadmap if m.get("status") != "completed"]
        completed = [m for m in roadmap if m.get("status") == "completed"]
        parts.append(f"\n=== LEARNING ROADMAP ===")
        parts.append(f"Total missions: {len(roadmap)}, Completed: {len(completed)}, Pending: {len(pending)}")
        if pending:
            top = pending[0]
            parts.append(f"Next mission: {top['skill']} (priority: {top.get('priority_score', '?')})")

    # Interview history
    if sessions:
        parts.append(f"\n=== INTERVIEW HISTORY ({len(sessions)} sessions) ===")
        for s in sessions[:3]:
            status = s.get("status", "unknown")
            role = s.get("target_role", "?")
            score = s.get("summary", {}).get("session_score", "N/A")
            parts.append(f"- {role}: {status}, score {score}/10")

    return "\n".join(parts)


_SYSTEM_PROMPT = """You are CareerOS Agent — an AI career advisor with access to a candidate's full career data.

Your capabilities:
- Answer questions about skill gaps and job matches
- Recommend specific next learning missions based on actual data
- Explain why specific jobs match or don't match
- Summarize career progress
- Suggest interview preparation strategies

Your rules:
- Base ALL responses on the candidate data provided in the context
- When data is unavailable, say so clearly
- Do NOT fabricate job listings, scores, or achievements
- Do NOT claim that interview scores predict hiring outcomes
- Do NOT provide job search services, resume submission, or application tracking
- When asked to compare jobs, use the actual skill coverage data
- Be concise but specific — reference actual skills and job titles from the data

Context about the candidate:
{context}"""


def chat(
    user_message: str,
    history: list[dict] | None = None,
    career_state: dict | None = None,
) -> str:
    """
    Process a user message and return the agent's response.

    Parameters
    ----------
    user_message:
        The user's question or request.
    history:
        List of prior messages: [{"role": "user"|"assistant", "content": "..."}]
    career_state:
        Optional pre-loaded career state dict (avoids repeated disk reads).

    Returns
    -------
    The agent's response string.
    """
    history = history or []

    # Load application data
    try:
        cs = career_state or load_career_state()
        resume_meta = load_resume_meta()
        roadmap = load_roadmap()
        sessions = list_interview_sessions()
    except Exception as exc:
        logger.warning("Could not load career data: %s", exc)
        cs, resume_meta, roadmap, sessions = {}, {}, [], []

    context = _build_context(cs, resume_meta, roadmap, sessions)
    system_prompt = _SYSTEM_PROMPT.format(context=context)

    # Build messages
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-10:]:  # Keep last 10 turns for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        llm = get_llm(temperature=0.3, max_tokens=1000)
        response = llm.invoke(messages)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as exc:
        logger.error("Agent chat failed: %s", exc)
        raise RuntimeError(f"Career Agent is unavailable: {exc}") from exc
