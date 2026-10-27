from pydantic import BaseModel, Field


class JobAnalysis(BaseModel):
    job_id: str = Field(
        default="",
        description="Unique identifier of the job"
    )

    title: str = Field(
        description="Job title"
    )

    company: str | None = Field(
        default=None,
        description="Company offering the job"
    )

    required_skills: list[str] = Field(
        default_factory=list,
        description="Skills explicitly required for the job"
    )

    preferred_skills: list[str] = Field(
        default_factory=list,
        description="Skills listed as preferred or nice-to-have"
    )

    experience_requirements: list[str] = Field(
        default_factory=list,
        description="Required or preferred experience"
    )

    education_requirements: list[str] = Field(
        default_factory=list,
        description="Education or degree requirements"
    )

    responsibilities: list[str] = Field(
        default_factory=list,
        description="Main responsibilities of the role"
    )

    technologies: list[str] = Field(
        default_factory=list,
        description="Tools, frameworks, libraries, platforms, and technologies"
    )

    key_requirements: list[str] = Field(
        default_factory=list,
        description="Most important requirements for the role"
    )