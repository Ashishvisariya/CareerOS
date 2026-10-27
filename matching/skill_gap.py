def normalize_skill(skill: str) -> str:
    return " ".join(
        skill.lower().strip().split()
    )


def calculate_skill_gap(
    candidate_skills,
    required_skills,
    preferred_skills=None,
):

    preferred_skills = preferred_skills or []

    candidate = {
        normalize_skill(skill)
        for skill in candidate_skills
        if skill and skill.strip()
    }

    required = {
        normalize_skill(skill)
        for skill in required_skills
        if skill and skill.strip()
    }

    preferred = {
        normalize_skill(skill)
        for skill in preferred_skills
        if skill and skill.strip()
    }

    matched_required = candidate.intersection(required)
    missing_required = required - candidate

    matched_preferred = candidate.intersection(preferred)
    missing_preferred = preferred - candidate

    if required:
        required_coverage = round(
            (len(matched_required) / len(required)) * 100, 2
        )
    else:
        required_coverage = None

    if preferred:
        preferred_coverage = round(
            (len(matched_preferred) / len(preferred)) * 100, 2
        )
    else:
        preferred_coverage = None

    return {
        "matched_required": sorted(matched_required),
        "missing_required": sorted(missing_required),
        "matched_preferred": sorted(matched_preferred),
        "missing_preferred": sorted(missing_preferred),
        "required_skill_coverage": required_coverage,
        "preferred_skill_coverage": preferred_coverage,
    }