import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Base directory for job requirements, resolved relative to repository root
BASE_DIR = Path(__file__).resolve().parent.parent
JOB_DIR = BASE_DIR / "data" / "job_requirements"


def validate_job_data(data: Any, file_name: str) -> dict[str, Any]:
    """
    Validate that the loaded JSON data conforms to the expected job requirement structure.
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid structure in '{file_name}': expected JSON object, got {type(data).__name__}"
        )

    # Validate essential fields
    job_id = data.get("job_id")
    if not job_id or not isinstance(job_id, str):
        raise ValueError(
            f"Missing or invalid 'job_id' in job file '{file_name}'"
        )

    title = data.get("title")
    if not title or not isinstance(title, str):
        raise ValueError(
            f"Missing or invalid 'title' in job file '{file_name}'"
        )

    # Normalize list fields to lists
    for list_field in [
        "required_skills",
        "preferred_skills",
        "experience_requirements",
        "education_requirements",
        "responsibilities",
        "technologies",
        "key_requirements",
    ]:
        val = data.get(list_field)
        if val is None:
            data[list_field] = []
        elif not isinstance(val, list):
            raise ValueError(
                f"Field '{list_field}' in '{file_name}' must be a list, got {type(val).__name__}"
            )

    return data


def load_local_jobs(
    directory_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """
    Load and validate all local job requirement JSON files from the specified directory.
    Supports recursive discovery to locate files in subdirectories (e.g., job_requirements/).
    """
    if directory_path is None:
        target_dir = JOB_DIR
    else:
        target_dir = Path(directory_path).resolve()

    if not target_dir.exists():
        raise FileNotFoundError(
            f"Job requirements directory does not exist: {target_dir}"
        )

    # Discover all JSON files (direct or nested)
    json_files = sorted(list(target_dir.rglob("*.json")))

    if not json_files:
        logger.warning(
            "No JSON job requirement files found in directory: %s", target_dir
        )
        return []

    jobs: list[dict[str, Any]] = []

    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Malformed JSON in file '{file_path.name}': {exc}"
            ) from exc
        except Exception as exc:
            raise ValueError(
                f"Failed to read file '{file_path.name}': {exc}"
            ) from exc

        validated_job = validate_job_data(raw_data, file_path.name)
        jobs.append(validated_job)

    logger.info("Loaded and validated %d local job files from %s", len(jobs), target_dir)
    return jobs