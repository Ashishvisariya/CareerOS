from pydantic import BaseModel, Field


class SkillGap(BaseModel):
    matched_required: list[str] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)

    matched_preferred: list[str] = Field(default_factory=list)
    missing_preferred: list[str] = Field(default_factory=list)

    required_skill_coverage: float | None = Field(
        default=None,
        description="Percentage of required skills matched, or None if no required skills specified"
    )

    preferred_skill_coverage: float | None = Field(
        default=None,
        description="Percentage of preferred skills matched, or None if no preferred skills specified"
    )