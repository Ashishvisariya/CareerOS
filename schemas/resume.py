from pydantic import BaseModel, Field


class ResumeAnalysis(BaseModel):
    name: str | None = Field(
        default=None,
        description="Candidate's full name"
    )

    skills: list[str] = Field(
        default_factory=list,
        description="Technical and professional skills explicitly found in the resume"
    )

    experience: list[str] = Field(
        default_factory=list,
        description="Work experience explicitly found in the resume"
    )

    projects: list[str] = Field(
        default_factory=list,
        description="Projects explicitly found in the resume"
    )

    education: list[str] = Field(
        default_factory=list,
        description="Education and qualifications explicitly found in the resume"
    )

    strengths: list[str] = Field(
        default_factory=list,
        description="Candidate strengths supported by the resume"
    )