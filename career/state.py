from collections import Counter
from typing import Any

from jobs.local_job_loader import load_local_jobs
from matching.skill_gap import calculate_skill_gap, normalize_skill
from schemas.career_state import CareerState, JobSkillGapResult, MarketSkillStat


def calculate_job_skill_gaps(
    candidate_skills: list[str],
    jobs: list[dict[str, Any]],
) -> list[JobSkillGapResult]:
    """
    Compute structured skill gap for each job in the dataset against candidate skills.
    """
    results: list[JobSkillGapResult] = []

    for job in jobs:
        required = job.get("required_skills", []) or []
        preferred = job.get("preferred_skills", []) or []

        gap = calculate_skill_gap(
            candidate_skills=candidate_skills,
            required_skills=required,
            preferred_skills=preferred,
        )

        result = JobSkillGapResult(
            job_id=str(job.get("job_id", "")),
            job_title=str(job.get("title", "Unknown")),
            company=job.get("company"),
            matched_required=gap["matched_required"],
            missing_required=gap["missing_required"],
            matched_preferred=gap["matched_preferred"],
            missing_preferred=gap["missing_preferred"],
            required_skill_coverage=gap["required_skill_coverage"],
            preferred_skill_coverage=gap["preferred_skill_coverage"],
        )
        results.append(result)

    return results


def aggregate_market_skills(
    jobs: list[dict[str, Any]],
    candidate_skills: list[str] | None = None,
    frequency_threshold: float = 0.40,
) -> dict[str, Any]:
    """
    Aggregate skill requirements across the local job dataset.

    - Normalizes and deduplicates skills within each job to avoid inflation.
    - Computes job count, market demand percentage, and missing frequency.
    - Flags recurring missing skills based on the frequency_threshold (default: 40%).
    - Calculates overall market-level skill coverage across unique required skills.
    """
    candidate_skills = candidate_skills or []
    candidate_norm = {
        normalize_skill(s)
        for s in candidate_skills
        if s and str(s).strip()
    }

    total_jobs = len(jobs)
    if total_jobs == 0:
        return {
            "market_skill_stats": [],
            "frequently_required_skills": [],
            "common_candidate_skills": [],
            "recurring_skill_gaps": [],
            "market_skill_coverage": None,
        }

    # Track skill frequencies and display name mapping
    skill_job_counts: Counter[str] = Counter()
    canonical_display: dict[str, str] = {}

    for job in jobs:
        # Deduplicate required skills within each individual job
        raw_reqs = job.get("required_skills", []) or []
        job_unique_norm: set[str] = set()

        for raw_s in raw_reqs:
            if not raw_s or not str(raw_s).strip():
                continue
            norm = normalize_skill(str(raw_s))
            if norm not in canonical_display:
                canonical_display[norm] = str(raw_s).strip()
            job_unique_norm.add(norm)

        for norm in job_unique_norm:
            skill_job_counts[norm] += 1

    # Build market statistics
    stats: list[MarketSkillStat] = []
    frequently_required: list[str] = []
    common_candidate: list[str] = []
    recurring_gaps: list[str] = []

    # Sort skills by job count descending, then alphabetically
    sorted_skills = sorted(
        skill_job_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )

    threshold_pct = frequency_threshold * 100

    for norm_skill, count in sorted_skills:
        display_name = canonical_display.get(norm_skill, norm_skill.title())
        demand_pct = round((count / total_jobs) * 100, 2)
        has_skill = norm_skill in candidate_norm
        missing_count = 0 if has_skill else count

        stat = MarketSkillStat(
            skill=display_name,
            job_count=count,
            demand_percentage=demand_pct,
            candidate_has_skill=has_skill,
            missing_count=missing_count,
        )
        stats.append(stat)

        if demand_pct >= threshold_pct:
            frequently_required.append(display_name)
            if has_skill:
                common_candidate.append(display_name)
            else:
                recurring_gaps.append(display_name)

    # Market-level skill coverage: % of unique dataset-required skills possessed
    all_unique_required = set(skill_job_counts.keys())
    if all_unique_required:
        matched_unique = candidate_norm.intersection(all_unique_required)
        market_coverage = round(
            (len(matched_unique) / len(all_unique_required)) * 100, 2
        )
    else:
        market_coverage = None

    return {
        "market_skill_stats": stats,
        "frequently_required_skills": frequently_required,
        "common_candidate_skills": common_candidate,
        "recurring_skill_gaps": recurring_gaps,
        "market_skill_coverage": market_coverage,
    }


def determine_career_stage(experience: list[str]) -> str:
    """
    Determine approximate career stage based on candidate experience evidence.
    """
    if not experience:
        return "entry-level / fresher"
    num_entries = len(experience)
    if num_entries <= 2:
        return "early-career"
    elif num_entries <= 5:
        return "mid-level"
    return "senior"


def build_summary(
    candidate_name: str | None,
    current_skills: list[str],
    target_roles: list[str],
    jobs_analyzed: int,
    market_coverage: float | None,
    common_skills: list[str],
    recurring_gaps: list[str],
    single_coverage: float | None = None,
) -> str:
    """
    Construct a concise, transparent summary of candidate readiness.
    """
    name = candidate_name or "The candidate"
    roles = ", ".join(target_roles) if target_roles else "target technical roles"
    num_skills = len(current_skills)

    parts = [
        f"{name} possesses {num_skills} identified skills, targeting {roles}."
    ]

    if jobs_analyzed > 0:
        parts.append(
            f"Based on analysis of {jobs_analyzed} local job requirements, "
            f"overall dataset skill coverage is "
            f"{market_coverage if market_coverage is not None else 'N/A'}%."
        )
        if common_skills:
            parts.append(
                f"Strongest high-demand skills matched: {', '.join(common_skills[:5])}."
            )
        if recurring_gaps:
            parts.append(
                f"Key recurring skill gaps across the dataset: {', '.join(recurring_gaps[:5])}."
            )
        else:
            parts.append("No critical recurring skill gaps were identified above threshold.")
    elif single_coverage is not None:
        parts.append(
            f"Evaluated against single target role with {single_coverage}% required skill coverage."
        )

    return " ".join(parts)


def build_career_state(
    resume_analysis: Any,
    target_roles: list[str] | None = None,
    jobs: list[dict[str, Any]] | None = None,
    skill_gap: dict[str, Any] | None = None,
    frequency_threshold: float = 0.40,
    auto_load_jobs: bool = False,
) -> CareerState:
    """
    Construct a comprehensive CareerState representing candidate profile and
    local job market insights.
    """
    target_roles = target_roles or []
    candidate_name = getattr(resume_analysis, "name", None)
    current_skills = getattr(resume_analysis, "skills", []) or []
    experience = getattr(resume_analysis, "experience", []) or []
    projects = getattr(resume_analysis, "projects", []) or []
    education = getattr(resume_analysis, "education", []) or []
    strengths = getattr(resume_analysis, "strengths", []) or []

    # If jobs not explicitly passed and auto_load_jobs is True, load local dataset
    if jobs is None and auto_load_jobs:
        try:
            jobs = load_local_jobs()
        except Exception:
            jobs = []

    # Local job dataset analysis
    job_skill_gaps: list[JobSkillGapResult] = []
    market_stats: list[MarketSkillStat] = []
    frequently_req: list[str] = []
    common_cand: list[str] = []
    recurring_gaps: list[str] = []
    market_cov: float | None = None

    if jobs is not None and len(jobs) > 0:
        job_skill_gaps = calculate_job_skill_gaps(current_skills, jobs)
        market_agg = aggregate_market_skills(
            jobs=jobs,
            candidate_skills=current_skills,
            frequency_threshold=frequency_threshold,
        )
        market_stats = market_agg["market_skill_stats"]
        frequently_req = market_agg["frequently_required_skills"]
        common_cand = market_agg["common_candidate_skills"]
        recurring_gaps = market_agg["recurring_skill_gaps"]
        market_cov = market_agg["market_skill_coverage"]

    # Backwards compatibility: single-job skill_gap support
    skill_gap = skill_gap or {}
    matched_skills = skill_gap.get("matched_required", [])
    missing_skills = skill_gap.get("missing_required", [])
    single_coverage = skill_gap.get("required_skill_coverage", 0.0)

    # Determine stage and summary
    career_stage = determine_career_stage(experience)
    summary = build_summary(
        candidate_name=candidate_name,
        current_skills=current_skills,
        target_roles=target_roles,
        jobs_analyzed=len(jobs) if jobs else 0,
        market_coverage=market_cov,
        common_skills=common_cand,
        recurring_gaps=recurring_gaps,
        single_coverage=single_coverage if skill_gap else None,
    )

    return CareerState(
        candidate_name=candidate_name,
        current_skills=current_skills,
        experience=experience,
        projects=projects,
        education=education,
        strengths=strengths,
        target_roles=target_roles,
        jobs_analyzed=len(jobs) if jobs else 0,
        job_skill_gaps=job_skill_gaps,
        market_skill_stats=market_stats,
        frequently_required_skills=frequently_req,
        common_candidate_skills=common_cand,
        recurring_skill_gaps=recurring_gaps,
        market_skill_coverage=market_cov,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        skill_coverage=single_coverage if single_coverage is not None else 0.0,
        career_stage=career_stage,
        summary=summary,
    )


def analyze_job_market(
    candidate_skills_or_resume: Any,
    jobs: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """
    Analyze local job market against candidate skills and return formatted results.
    """
    if hasattr(candidate_skills_or_resume, "skills"):
        candidate_skills = candidate_skills_or_resume.skills
    elif isinstance(candidate_skills_or_resume, list):
        candidate_skills = candidate_skills_or_resume
    else:
        candidate_skills = []

    if jobs is None:
        jobs = load_local_jobs()

    gaps = calculate_job_skill_gaps(candidate_skills, jobs)

    results = []
    for g in gaps:
        results.append({
            "job_id": g.job_id,
            "job_title": g.job_title,
            "company": g.company,
            "skill_gap": {
                "matched_required": g.matched_required,
                "missing_required": g.missing_required,
                "matched_preferred": g.matched_preferred,
                "missing_preferred": g.missing_preferred,
                "required_skill_coverage": g.required_skill_coverage,
                "preferred_skill_coverage": g.preferred_skill_coverage,
            },
        })

    return results