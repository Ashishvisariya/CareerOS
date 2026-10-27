import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from jobs.api_client import fetch_jobs



def main():
    api_url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

    print("Fetching jobs...\n")

    data = fetch_jobs(
        api_url,
        query="machine learning engineer",
    )

    print("Jobs received:", len(data.get("results", [])))

    if not data.get("results"):
        print("No results returned.")
        return

    job = data["results"][0]

    print("\n" + "=" * 60)
    print("TITLE")
    print("=" * 60)
    print(job.get("title"))

    print("\n" + "=" * 60)
    print("DESCRIPTION LENGTH")
    print("=" * 60)
    print(len(job.get("description", "")))

    print("\n" + "=" * 60)
    print("DESCRIPTION")
    print("=" * 60)
    print(job.get("description"))

    print("\n" + "=" * 60)
    print("URL")
    print("=" * 60)
    print(job.get("redirect_url"))


if __name__ == "__main__":
    main()