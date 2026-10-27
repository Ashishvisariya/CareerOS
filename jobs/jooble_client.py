import os
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


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