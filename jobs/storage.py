import json
from pathlib import Path

from schemas.job import JobPosting


def save_job(job: JobPosting):
    folder_name = (
        job.title
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    folder = Path("data/raw_jobs") / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    file_path = folder / f"{job.job_id}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            job.model_dump(),
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(f"Saved: {file_path}")

    return file_path