from jobs.api_client import fetch_jobs, process_jobs


ADZUNA_URL = (
    "https://api.adzuna.com/v1/api/jobs/in/search/1"
)


def fetch_and_store_jobs(
    query: str = "machine learning engineer"
):
    data = fetch_jobs(
        api_url=ADZUNA_URL,
        query=query,
    )

    jobs = process_jobs(data)

    return jobs