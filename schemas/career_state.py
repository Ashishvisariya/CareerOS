from pydantic import BaseModel, Field


class JobSkillGapResult(BaseModel):
    job_id: str
    job_title: str
    company: str | None = None
    matched_required: list[str] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)
    matched_preferred: list[str] = Field(default_factory=list)
    missing_preferred: list[str] = Field(default_factory=list)
    required_skill_coverage: float | None = None
    preferred_skill_coverage: float | None = None


class MarketSkillStat(BaseModel):
    skill: str
    job_count: int
    demand_percentage: float
    candidate_has_skill: bool
    missing_count: int


class CareerState(BaseModel):
    candidate_name: str | None = None

    # Candidate profile
    current_skills: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    target_roles: list[str] = Field(default_factory=list)

    # Local job dataset analysis (Session 10)
    jobs_analyzed: int = 0
    job_skill_gaps: list[JobSkillGapResult] = Field(default_factory=list)
    market_skill_stats: list[MarketSkillStat] = Field(default_factory=list)
    frequently_required_skills: list[str] = Field(default_factory=list)
    common_candidate_skills: list[str] = Field(default_factory=list)
    recurring_skill_gaps: list[str] = Field(default_factory=list)
    market_skill_coverage: float | None = Field(
        default=None,
        description="Percentage of unique skills required across the dataset that the candidate possesses"
    )

    # Backwards compatibility fields
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    skill_coverage: float = Field(
        default=0.0,
        description="Single-job or primary target required skill coverage"
    )

    career_stage: str = "exploring"
    summary: str = ""