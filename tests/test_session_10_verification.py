import json
import tempfile
from pathlib import Path
import pytest

from jobs.local_job_loader import load_local_jobs, validate_job_data
from matching.skill_gap import calculate_skill_gap, normalize_skill
from matching.matcher import calculate_skill_match, calculate_experience_match, calculate_overall_score
from career.state import (
    build_career_state,
    aggregate_market_skills,
    calculate_job_skill_gaps,
    determine_career_stage,
)
from schemas.career_state import CareerState, JobSkillGapResult, MarketSkillStat
from schemas.resume import ResumeAnalysis
from schemas.skill_gap import SkillGap


# =====================================================================
# 1. Loading multiple local JSON job files
# =====================================================================
def test_load_multiple_local_jobs():
    """Verify loading real curated jobs from data/job_requirements."""
    jobs = load_local_jobs()
    assert len(jobs) == 13, f"Expected 13 curated jobs, found {len(jobs)}"
    for job in jobs:
        assert "job_id" in job and isinstance(job["job_id"], str)
        assert "title" in job and isinstance(job["title"], str)
        assert "required_skills" in job and isinstance(job["required_skills"], list)
        assert "preferred_skills" in job and isinstance(job["preferred_skills"], list)


# =====================================================================
# 2. Missing or empty job directory
# =====================================================================
def test_missing_job_directory(tmp_path):
    """Missing directory should raise FileNotFoundError."""
    missing_dir = tmp_path / "non_existent_folder"
    with pytest.raises(FileNotFoundError, match="does not exist"):
        load_local_jobs(missing_dir)


def test_empty_job_directory(tmp_path):
    """Empty directory should return empty list gracefully."""
    empty_dir = tmp_path / "empty_jobs"
    empty_dir.mkdir()
    jobs = load_local_jobs(empty_dir)
    assert jobs == []


# =====================================================================
# 3. Invalid JSON handling
# =====================================================================
def test_malformed_json_handling(tmp_path):
    """Malformed JSON syntax raises ValueError with filename in message."""
    bad_file = tmp_path / "broken_job.json"
    bad_file.write_text('{ "job_id": "test", "title": "Dev", ', encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed JSON in file 'broken_job.json'"):
        load_local_jobs(tmp_path)


def test_invalid_structure_json(tmp_path):
    """JSON that is not a dictionary raises ValueError."""
    bad_file = tmp_path / "array_job.json"
    bad_file.write_text('["not", "an", "object"]', encoding="utf-8")
    with pytest.raises(ValueError, match="expected JSON object"):
        load_local_jobs(tmp_path)


# =====================================================================
# 4. Missing required_skills or preferred_skills
# =====================================================================
def test_missing_optional_skill_keys(tmp_path):
    """Jobs without required_skills or preferred_skills default to empty lists."""
    job_file = tmp_path / "minimal_job.json"
    job_file.write_text(
        json.dumps({"job_id": "min_001", "title": "Minimal Engineer"}),
        encoding="utf-8",
    )
    jobs = load_local_jobs(tmp_path)
    assert len(jobs) == 1
    assert jobs[0]["required_skills"] == []
    assert jobs[0]["preferred_skills"] == []


# =====================================================================
# 5. Case-insensitive skill normalization
# =====================================================================
def test_skill_normalization():
    """Verify whitespace stripping and case-insensitive normalization."""
    assert normalize_skill("  Python  ") == "python"
    assert normalize_skill("MACHINE   LEARNING") == "machine learning"
    assert normalize_skill("PyTorch") == "pytorch"


# =====================================================================
# 6. Duplicate skills within one job
# =====================================================================
def test_duplicate_skills_within_one_job():
    """Duplicate skills within a single job should count as 1 for market frequency."""
    jobs = [
        {
            "job_id": "job_1",
            "title": "Engineer 1",
            "required_skills": ["Python", "python", "PYTHON", "Docker"],
        },
        {
            "job_id": "job_2",
            "title": "Engineer 2",
            "required_skills": ["Python", "AWS"],
        },
    ]
    agg = aggregate_market_skills(jobs, candidate_skills=["Python"])
    stats_dict = {stat.skill.lower(): stat for stat in agg["market_skill_stats"]}
    # Python is in both jobs -> count should be 2, demand 100%
    assert stats_dict["python"].job_count == 2
    assert stats_dict["python"].demand_percentage == 100.0


# =====================================================================
# 7. Correct required-skill coverage
# =====================================================================
def test_required_skill_coverage():
    """Coverage matches actual proportion of required skills."""
    res_partial = calculate_skill_gap(
        candidate_skills=["Python", "PyTorch"],
        required_skills=["Python", "PyTorch", "Docker", "AWS"],
    )
    assert res_partial["required_skill_coverage"] == 50.0

    res_full = calculate_skill_gap(
        candidate_skills=["Python", "PyTorch"],
        required_skills=["Python", "PyTorch"],
    )
    assert res_full["required_skill_coverage"] == 100.0

    res_none = calculate_skill_gap(
        candidate_skills=["Java"],
        required_skills=["Python", "PyTorch"],
    )
    assert res_none["required_skill_coverage"] == 0.0


# =====================================================================
# 8. Preferred skills not specified (returns None, not 100%)
# =====================================================================
def test_preferred_skills_not_specified():
    """When preferred skills are empty, preferred_skill_coverage must be None, not 100%."""
    res = calculate_skill_gap(
        candidate_skills=["Python"],
        required_skills=["Python", "Docker"],
        preferred_skills=[],
    )
    assert res["preferred_skill_coverage"] is None
    assert res["matched_preferred"] == []
    assert res["missing_preferred"] == []

    # Also test when required skills are absent
    res_no_req = calculate_skill_gap(
        candidate_skills=["Python"],
        required_skills=[],
        preferred_skills=["Docker"],
    )
    assert res_no_req["required_skill_coverage"] is None

    # Schema allows None for both
    gap_model = SkillGap.model_validate(res)
    assert gap_model.preferred_skill_coverage is None


def test_experience_matcher_missing_requirements():
    """When experience requirements are absent, return None instead of phantom 100%."""
    score = calculate_experience_match(
        candidate_experience=["3 years ML experience"],
        job_requirements=[],
    )
    assert score is None

    # Overall score redistributes weights when experience score is None
    overall = calculate_overall_score(
        skill_score=80.0,
        experience_score=None,
        semantic_score=60.0,
    )
    # 80 * 0.625 + 60 * 0.375 = 50.0 + 22.5 = 72.5
    assert overall == 72.5


# =====================================================================
# 9. Multiple jobs with different skill requirements
# =====================================================================
def test_multiple_jobs_different_requirements():
    """Computes distinct skill gaps across heterogeneous jobs."""
    jobs = [
        {
            "job_id": "j1",
            "title": "ML Engineer",
            "company": "Corp A",
            "required_skills": ["Python", "PyTorch"],
            "preferred_skills": ["MLOps"],
        },
        {
            "job_id": "j2",
            "title": "Data Engineer",
            "company": "Corp B",
            "required_skills": ["SQL", "Spark"],
            "preferred_skills": [],
        },
    ]
    candidate = ["Python", "SQL"]
    gaps = calculate_job_skill_gaps(candidate, jobs)

    assert len(gaps) == 2
    assert gaps[0].job_id == "j1"
    assert gaps[0].required_skill_coverage == 50.0
    assert gaps[0].preferred_skill_coverage == 0.0

    assert gaps[1].job_id == "j2"
    assert gaps[1].required_skill_coverage == 50.0
    assert gaps[1].preferred_skill_coverage is None


# =====================================================================
# 10. Market skill frequency and recurring gaps
# =====================================================================
def test_market_skill_frequency_and_threshold():
    """Verify frequency aggregation and configurable recurring gap threshold."""
    jobs = [
        {"job_id": "1", "title": "J1", "required_skills": ["Python", "Docker"]},
        {"job_id": "2", "title": "J2", "required_skills": ["Python", "Docker"]},
        {"job_id": "3", "title": "J3", "required_skills": ["Python", "Kubernetes"]},
        {"job_id": "4", "title": "J4", "required_skills": ["AWS"]},
    ]
    # Total jobs: 4
    # Python: 3/4 = 75%
    # Docker: 2/4 = 50%
    # Kubernetes: 1/4 = 25%
    # AWS: 1/4 = 25%
    candidate_skills = ["Python"]

    agg_40 = aggregate_market_skills(jobs, candidate_skills=candidate_skills, frequency_threshold=0.40)
    # At 40% threshold: Python (75%) and Docker (50%) are frequent
    assert "Python" in agg_40["common_candidate_skills"]
    assert "Docker" in agg_40["recurring_skill_gaps"]
    assert "Kubernetes" not in agg_40["recurring_skill_gaps"]  # 25% < 40%

    # Custom threshold at 60%
    agg_60 = aggregate_market_skills(jobs, candidate_skills=candidate_skills, frequency_threshold=0.60)
    # Docker is 50%, so not in recurring gaps at 60%
    assert "Docker" not in agg_60["recurring_skill_gaps"]
    assert "Python" in agg_60["common_candidate_skills"]


# =====================================================================
# 11. Empty resume skill lists
# =====================================================================
def test_empty_resume_skills():
    """Candidate with zero skills handles market analysis gracefully without crashing."""
    jobs = [
        {"job_id": "1", "title": "J1", "required_skills": ["Python", "SQL"]},
    ]
    resume = ResumeAnalysis(name="Novice", skills=[])
    state = build_career_state(resume, jobs=jobs)
    assert state.jobs_analyzed == 1
    assert state.market_skill_coverage == 0.0
    assert state.common_candidate_skills == []
    assert "Python" in state.recurring_skill_gaps
    assert "SQL" in state.recurring_skill_gaps
    assert "Novice possesses 0 identified skills" in state.summary


# =====================================================================
# 12. Career State schema validation
# =====================================================================
def test_career_state_schema_validation():
    """Verify full CareerState validation, typing, and serialization."""
    gap_result = JobSkillGapResult(
        job_id="test_1",
        job_title="ML Engineer",
        company="TechCorp",
        matched_required=["Python"],
        missing_required=["Docker"],
        required_skill_coverage=50.0,
        preferred_skill_coverage=None,
    )
    stat = MarketSkillStat(
        skill="Python",
        job_count=10,
        demand_percentage=76.92,
        candidate_has_skill=True,
        missing_count=0,
    )
    state = CareerState(
        candidate_name="Alice",
        current_skills=["Python", "PyTorch"],
        jobs_analyzed=13,
        job_skill_gaps=[gap_result],
        market_skill_stats=[stat],
        frequently_required_skills=["Python"],
        common_candidate_skills=["Python"],
        recurring_skill_gaps=["Docker"],
        market_skill_coverage=45.5,
        career_stage="early-career",
        summary="Test summary.",
    )
    dumped = state.model_dump()
    assert dumped["candidate_name"] == "Alice"
    assert dumped["jobs_analyzed"] == 13
    assert dumped["job_skill_gaps"][0]["preferred_skill_coverage"] is None
    assert dumped["market_skill_stats"][0]["job_count"] == 10

    # Re-validate from dict
    restored = CareerState.model_validate(dumped)
    assert restored.candidate_name == "Alice"
    assert restored.market_skill_coverage == 45.5


# =====================================================================
# 13. End-to-end local dataset analysis without live API or LLM
# =====================================================================
def test_end_to_end_local_dataset_analysis_offline():
    """End-to-end Session 10 workflow using real local dataset completely offline."""
    jobs = load_local_jobs()
    assert len(jobs) == 13

    candidate = ResumeAnalysis(
        name="Prince Kumar",
        skills=[
            "Python",
            "PyTorch",
            "Machine Learning",
            "Deep Learning",
            "TensorFlow",
            "Scikit-learn",
            "Data Preprocessing",
            "Docker",
            "Git",
            "SQL",
        ],
        experience=["ML Intern at AI Labs", "Data Science researcher"],
        projects=["Image classifier with PyTorch"],
        education=["B.Tech Computer Science"],
        strengths=["Machine learning modeling", "Python programming"],
    )

    state = build_career_state(
        resume_analysis=candidate,
        target_roles=["AI Engineer", "ML Engineer"],
        jobs=jobs,
        frequency_threshold=0.40,
    )

    assert state.candidate_name == "Prince Kumar"
    assert state.jobs_analyzed == 13
    assert len(state.job_skill_gaps) == 13
    assert state.market_skill_coverage is not None
    assert state.market_skill_coverage > 0.0

    # Common skills that are in high demand in the dataset
    assert "Python" in state.common_candidate_skills or "Machine Learning" in state.common_candidate_skills
    # Summary contains candidate name and jobs analyzed
    assert "Prince Kumar" in state.summary
    assert "13 local job requirements" in state.summary
    assert state.career_stage == "early-career"
