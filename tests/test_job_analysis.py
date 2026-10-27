import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from jobs.jooble_client import fetch_jooble_jobs
from schemas.job import JobPosting
from intelligence.job_analyzer import analyze_job


def main():
    print("Fetching jobs from Jooble...\n")

    data = fetch_jooble_jobs(
        query="machine learning engineer",
        location="India",
    )

    jobs = data.get("jobs", [])

    print("Jobs received:", len(jobs))

    if not jobs:
        raise ValueError("No jobs returned from Jooble")


    item = jobs[0]

    job = JobPosting(
        job_id=str(item.get("id", "")),
        title=item.get("title", "Unknown"),
        company=item.get("company"),
        location=item.get("location"),
        description=item.get("snippet", ""),
        url=item.get("link"),
        posted_date=item.get("updated"),
        source="jooble",
        raw_data=item,
    )


    print("\n" + "=" * 60)
    print("JOB")
    print("=" * 60)

    print("\nTitle:")
    print(job.title)

    print("\nCompany:")
    print(job.company)

    print("\nLocation:")
    print(job.location)

    print("\nDescription Length:")
    print(len(job.description or ""))


    print("\nAnalyzing job...\n")

    analysis = analyze_job(job)


    print("=" * 60)
    print("JOB ANALYSIS")
    print("=" * 60)

    print("\nTitle:")
    print(analysis.title)

    print("\nRequired Skills:")
    for skill in analysis.required_skills:
        print(f"- {skill}")

    print("\nPreferred Skills:")
    for skill in analysis.preferred_skills:
        print(f"- {skill}")

    print("\nExperience Requirements:")
    for item in analysis.experience_requirements:
        print(f"- {item}")

    print("\nEducation Requirements:")
    for item in analysis.education_requirements:
        print(f"- {item}")

    print("\nResponsibilities:")
    for item in analysis.responsibilities:
        print(f"- {item}")

    print("\nTechnologies:")
    for item in analysis.technologies:
        print(f"- {item}")

    print("\nKey Requirements:")
    for item in analysis.key_requirements:
        print(f"- {item}")


if __name__ == "__main__":
    main()