import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from schemas.job import JobPosting
from jobs.storage import save_job


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


def fetch_jobs(
    api_url: str,
    query: str = "machine learning engineer",
):
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        raise ValueError(
            "ADZUNA_APP_ID or ADZUNA_APP_KEY missing in .env"
        )

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "results_per_page": 10,
    }

    response = requests.get(
        api_url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def process_jobs(data):
    jobs = []

    for item in data.get("results", []):

        company = item.get("company") or {}
        location = item.get("location") or {}

        job = JobPosting(
            job_id=str(item.get("id")),
            title=item.get("title", "Unknown"),
            company=company.get("display_name"),
            location=location.get("display_name"),
            description=item.get("description"),
            url=item.get("redirect_url"),
            posted_date=item.get("created"),
            source="adzuna",
            raw_data=item,
        )

        save_job(job)
        jobs.append(job)

    return jobs

def fetch_jooble_jobs(
    query="machine learning engineer",
    location="India",
):
    api_key = os.getenv("JOOBLE_API_KEY")

    if not api_key:
        raise ValueError(
            "JOOBLE_API_KEY not found in CareerOS/.env"
        )

    url = f"https://jooble.org/api/{api_key}"

    payload = {
        "keywords": query,
        "location": location,
        "page": 1,
        "searchMode": 1,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()