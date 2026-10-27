from pydantic import BaseModel, Field


class JobMatch(BaseModel):
    job_id: str
    candidate_name: str
    job_title: str
    company: str | None = None

    overall_score: float = Field(
        description="Overall job match score from 0 to 100"
    )

    skill_score: float = Field(
        description="Skill match score from 0 to 100"
    )

    experience_score: float | None = Field(
        default=None,
        description="Experience match score from 0 to 100, or None if experience requirements not specified"
    )

    semantic_score: float = Field(
        description="Semantic similarity score from 0 to 100"
    )

    matched_skills: list[str] = Field(
        default_factory=list
    )

    missing_skills: list[str] = Field(
        default_factory=list
    )

    explanation: str