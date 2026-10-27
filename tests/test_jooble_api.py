import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from jobs.jooble_client import fetch_jooble_jobs


def main():
    print("Fetching Jooble jobs...\n")

    data = fetch_jooble_jobs(
        query="machine learning engineer",
        location="India",
    )

    jobs = data.get("jobs", [])

    print("Jobs received:", len(jobs))

    if not jobs:
        print("No jobs returned.")
        print(data)
        return

    job = jobs[0]

    print("\n" + "=" * 60)
    print("TITLE")
    print("=" * 60)
    print(job.get("title"))

    print("\n" + "=" * 60)
    print("COMPANY")
    print("=" * 60)
    print(job.get("company"))

    print("\n" + "=" * 60)
    print("LOCATION")
    print("=" * 60)
    print(job.get("location"))

    description = job.get("snippet", "")

    print("\n" + "=" * 60)
    print("DESCRIPTION LENGTH")
    print("=" * 60)
    print(len(description))

    print("\n" + "=" * 60)
    print("DESCRIPTION")
    print("=" * 60)
    print(description)

    print("\n" + "=" * 60)
    print("LINK")
    print("=" * 60)
    print(job.get("link"))


if __name__ == "__main__":
    main()