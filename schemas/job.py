from typing import Any

from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    job_id: str
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
    posted_date: str | None = None
    source: str
    raw_data: dict[str, Any] = Field(default_factory=dict)