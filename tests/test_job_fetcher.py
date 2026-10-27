from jobs.fetcher import fetch_and_store_jobs


def main():
    print("Fetching jobs from Adzuna...\n")

    jobs = fetch_and_store_jobs(
        query="machine learning engineer"
    )

    print(f"Fetched {len(jobs)} jobs\n")

    for job in jobs:
        print("-" * 60)
        print(f"ID: {job.job_id}")
        print(f"Title: {job.title}")
        print(f"Company: {job.company}")
        print(f"Location: {job.location}")
        print(f"Source: {job.source}")


if __name__ == "__main__":
    main()