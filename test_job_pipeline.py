from jobs.api_client import fetch_jobs, process_jobs


API_URL = "https://api.adzuna.com/v1/api/jobs/in/search/1"


print("Fetching jobs...")

data = fetch_jobs(
    API_URL,
    query="machine learning engineer",
)

print("Jobs received:", len(data.get("results", [])))

jobs = process_jobs(data)

print("\nSuccessfully saved:", len(jobs))