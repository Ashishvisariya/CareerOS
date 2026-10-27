from ingestion.embeddings import get_embeddings
from matching.skill_gap import calculate_skill_gap

def calculate_skill_match(
    candidate_skills: list[str],
    required_skills: list[str],
    preferred_skills: list[str],
):
    candidate = {
        skill.lower().strip()
        for skill in candidate_skills
    }

    required = {
        skill.lower().strip()
        for skill in required_skills
    }

    preferred = {
        skill.lower().strip()
        for skill in preferred_skills
    }

    if not required and not preferred:
        return 0.0, [], []

    matched_required = candidate.intersection(required)

    matched_preferred = candidate.intersection(preferred)

    matched = matched_required.union(
        matched_preferred
    )

    missing = required - candidate

    if required and preferred:
        required_score = (len(matched_required) / len(required)) * 100
        preferred_score = (len(matched_preferred) / len(preferred)) * 100
        score = required_score * 0.8 + preferred_score * 0.2
    elif required:
        score = (len(matched_required) / len(required)) * 100
    elif preferred:
        score = (len(matched_preferred) / len(preferred)) * 100
    else:
        score = 0.0

    return (
        round(score, 2),
        sorted(matched),
        sorted(missing),
    )
    
def calculate_experience_match(
    candidate_experience: list[str],
    job_requirements: list[str],
) -> float | None:
    if not job_requirements:
        # No experience requirements specified; return None (unknown/not applicable)
        return None

    if not candidate_experience:
        return 0.0

    candidate_text = " ".join(
        candidate_experience
    ).lower()

    job_text = " ".join(
        job_requirements
    ).lower()

    # Simple keyword-based baseline
    keywords = [
        "python",
        "machine learning",
        "deep learning",
        "sql",
        "tensorflow",
        "pytorch",
        "aws",
        "docker",
        "kubernetes",
    ]

    required_keywords = [
        keyword
        for keyword in keywords
        if keyword in job_text
    ]

    if not required_keywords:
        return 70.0

    matched = [
        keyword
        for keyword in required_keywords
        if keyword in candidate_text
    ]

    return round(
        len(matched)
        / len(required_keywords)
        * 100,
        2,
    )
    
    
def calculate_semantic_match(
    resume_text: str,
    job_text: str,
):
    embeddings = get_embeddings()

    resume_vector = embeddings.embed_query(
        resume_text
    )

    job_vector = embeddings.embed_query(
        job_text
    )

    return calculate_cosine_similarity(
        resume_vector,
        job_vector,
    )
    
import math


def calculate_cosine_similarity(
    vector_a,
    vector_b,
):
    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    magnitude_a = math.sqrt(
        sum(a * a for a in vector_a)
    )

    magnitude_b = math.sqrt(
        sum(b * b for b in vector_b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    similarity = (
        dot_product
        / (magnitude_a * magnitude_b)
    )

    return round(
        max(0, similarity) * 100,
        2,
    )
    

def calculate_overall_score(
    skill_score: float,
    experience_score: float | None,
    semantic_score: float,
):
    if experience_score is None:
        # Re-weight between skill (62.5%) and semantic (37.5%) when experience requirements are not specified
        score = skill_score * 0.625 + semantic_score * 0.375
    else:
        score = (
            skill_score * 0.50
            + experience_score * 0.20
            + semantic_score * 0.30
        )

    return round(score, 2)

def match_job(
    candidate_skills,
    candidate_experience,
    resume_text,
    job_analysis,
    job,
):
    # ---------------------------------------
    # 1. SKILL GAP ANALYSIS
    # ---------------------------------------

    skill_gap = calculate_skill_gap(
        candidate_skills=candidate_skills,
        required_skills=job_analysis.required_skills,
        preferred_skills=job_analysis.preferred_skills,
    )

    # ---------------------------------------
    # 2. SKILL MATCH SCORE
    # ---------------------------------------

    skill_score, matched, missing = calculate_skill_match(
        candidate_skills,
        job_analysis.required_skills,
        job_analysis.preferred_skills,
    )

    # ---------------------------------------
    # 3. EXPERIENCE MATCH
    # ---------------------------------------

    experience_score = calculate_experience_match(
        candidate_experience,
        job_analysis.experience_requirements,
    )

    # ---------------------------------------
    # 4. BUILD JOB TEXT
    # ---------------------------------------

    job_text = " ".join([
        job.title or "",
        job.description or "",
        " ".join(job_analysis.responsibilities),
        " ".join(job_analysis.required_skills),
        " ".join(job_analysis.technologies),
    ])

    # ---------------------------------------
    # 5. SEMANTIC MATCH
    # ---------------------------------------

    semantic_score = calculate_semantic_match(
        resume_text,
        job_text,
    )

    # ---------------------------------------
    # 6. OVERALL SCORE
    # ---------------------------------------

    overall_score = calculate_overall_score(
        skill_score,
        experience_score,
        semantic_score,
    )

    # ---------------------------------------
    # 7. RETURN EVERYTHING
    # ---------------------------------------

    return {
        "job_id": job.job_id,
        "job_title": job.title,
        "company": job.company,

        "overall_score": overall_score,

        "skill_score": skill_score,
        "experience_score": experience_score,
        "semantic_score": semantic_score,

        "matched_skills": matched,
        "missing_skills": missing,

        # NEW
        "skill_gap": skill_gap,
    }