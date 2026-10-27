"""
CareerOS — Persistent state storage (JSON-based).

Loads and saves CareerState, roadmap missions, and interview sessions
to disk so progress persists across application restarts.

All paths are resolved via core.config.get_settings() — no CWD dependency.
"""
from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import get_settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON atomically (write temp → rename) to avoid corruption."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        shutil.move(str(tmp), str(path))
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _read_json(path: Path, default: Any = None) -> Any:
    """Read JSON from path, returning default if file doesn't exist or is corrupt."""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("Could not read %s: %s — returning default", path, exc)
        return default


# ──────────────────────────────────────────────────────────────────────────────
# Career State
# ──────────────────────────────────────────────────────────────────────────────

def load_career_state() -> dict:
    """Load persisted career state dict, or return empty dict."""
    settings = get_settings()
    return _read_json(settings.state_file, {})


def save_career_state(state_dict: dict) -> None:
    """Persist career state to disk with a timestamp."""
    settings = get_settings()
    state_dict["last_updated"] = datetime.now(timezone.utc).isoformat()
    _atomic_write(settings.state_file, state_dict)
    logger.info("Career state saved to %s", settings.state_file)


def clear_career_state() -> None:
    """Remove persisted career state file."""
    settings = get_settings()
    if settings.state_file.exists():
        settings.state_file.unlink()
        logger.info("Career state cleared")


# ──────────────────────────────────────────────────────────────────────────────
# Roadmap / Missions
# ──────────────────────────────────────────────────────────────────────────────

def load_roadmap() -> list[dict]:
    """Load persisted roadmap missions list."""
    settings = get_settings()
    data = _read_json(settings.roadmap_file, [])
    return data if isinstance(data, list) else []


def save_roadmap(missions: list[dict]) -> None:
    """Persist roadmap missions list to disk."""
    settings = get_settings()
    _atomic_write(settings.roadmap_file, missions)  # type: ignore[arg-type]


def update_mission_status(mission_id: str, status: str, notes: str = "") -> bool:
    """
    Update the status of a specific mission by ID.

    Returns True if the mission was found and updated.
    """
    missions = load_roadmap()
    for m in missions:
        if m.get("id") == mission_id:
            m["status"] = status
            if notes:
                m["notes"] = notes
            m["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_roadmap(missions)
            return True
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Interview Sessions
# ──────────────────────────────────────────────────────────────────────────────

def _session_path(session_id: str) -> Path:
    settings = get_settings()
    return settings.interviews_dir / f"{session_id}.json"


def load_interview_session(session_id: str) -> dict | None:
    """Load an interview session by ID, or None if not found."""
    path = _session_path(session_id)
    return _read_json(path)


def save_interview_session(session: dict) -> None:
    """Save an interview session to disk."""
    session_id = session.get("session_id") or session.get("id")
    if not session_id:
        raise ValueError("Interview session must have a 'session_id' field")
    session["updated_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write(_session_path(session_id), session)


def list_interview_sessions() -> list[dict]:
    """Return metadata for all saved interview sessions, newest first."""
    settings = get_settings()
    sessions = []
    for f in sorted(settings.interviews_dir.glob("*.json"), reverse=True):
        data = _read_json(f)
        if data:
            sessions.append(data)
    return sessions


def delete_interview_session(session_id: str) -> bool:
    """Delete a session file. Returns True if found and deleted."""
    path = _session_path(session_id)
    if path.exists():
        path.unlink()
        return True
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Resume metadata cache
# ──────────────────────────────────────────────────────────────────────────────

def _resume_meta_path() -> Path:
    settings = get_settings()
    return settings.data_dir / "resume_meta.json"


def load_resume_meta() -> dict:
    """Load cached resume analysis result."""
    return _read_json(_resume_meta_path(), {})


def save_resume_meta(analysis_dict: dict) -> None:
    """Cache resume analysis result to avoid repeated LLM calls."""
    analysis_dict["cached_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write(_resume_meta_path(), analysis_dict)


def clear_resume_meta() -> None:
    """Remove cached resume analysis (e.g. when a new resume is uploaded)."""
    p = _resume_meta_path()
    if p.exists():
        p.unlink()
