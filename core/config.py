"""
CareerOS — Centralized configuration.

Loads environment variables once and exposes them via a Settings singleton.
Uses pydantic-settings for validation and clear error messages.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve the repository root so env loading is path-independent on Windows
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _REPO_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM ───────────────────────────────────────────────────────────────
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile", alias="GROQ_MODEL"
    )

    # ── Embeddings ────────────────────────────────────────────────────────
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    embedding_model: str = Field(
        default="models/gemini-embedding-001", alias="EMBEDDING_MODEL"
    )

    # ── Job APIs ──────────────────────────────────────────────────────────
    adzuna_app_id: str = Field(default="", alias="ADZUNA_APP_ID")
    adzuna_app_key: str = Field(default="", alias="ADZUNA_APP_KEY")
    jooble_api_key: str = Field(default="", alias="JOOBLE_API_KEY")

    # ── Backend ───────────────────────────────────────────────────────────
    backend_url: str = Field(
        default="http://127.0.0.1:8000", alias="BACKEND_URL"
    )
    api_prefix: str = "/api/v1"

    # ── Storage paths ─────────────────────────────────────────────────────
    @property
    def repo_root(self) -> Path:
        return _REPO_ROOT

    @property
    def data_dir(self) -> Path:
        return _REPO_ROOT / "data"

    @property
    def chroma_dir(self) -> Path:
        return _REPO_ROOT / "chroma_db"

    @property
    def resumes_dir(self) -> Path:
        return _REPO_ROOT / "data" / "resumes"

    @property
    def job_requirements_dir(self) -> Path:
        return _REPO_ROOT / "data" / "job_requirements"

    @property
    def state_file(self) -> Path:
        return _REPO_ROOT / "data" / "career_state.json"

    @property
    def interviews_dir(self) -> Path:
        return _REPO_ROOT / "data" / "interviews"

    @property
    def roadmap_file(self) -> Path:
        return _REPO_ROOT / "data" / "roadmap.json"

    # ── Derived status helpers ────────────────────────────────────────────
    @property
    def groq_configured(self) -> bool:
        return bool(self.groq_api_key and not self.groq_api_key.startswith("your_"))

    @property
    def google_configured(self) -> bool:
        return bool(self.google_api_key and not self.google_api_key.startswith("your_"))

    @property
    def adzuna_configured(self) -> bool:
        return bool(self.adzuna_app_id and self.adzuna_app_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    s = Settings()
    # Ensure required data directories exist
    for d in (s.data_dir, s.resumes_dir, s.interviews_dir):
        d.mkdir(parents=True, exist_ok=True)
    return s
