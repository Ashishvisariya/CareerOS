from pathlib import Path
from schemas.job import JobPosting
from jobs.storage import save_job


def test_save_job():
    job = JobPosting(
        job_id="test-123",
        title="Machine Learning Engineer",
        company="Test Company",
        location="India",
        description="Machine learning engineer role",
        url="https://example.com/job",
        posted_date="2026-09-14",
        source="adzuna",
        raw_data={
            "id": "test-123",
            "title": "Machine Learning Engineer"
        }
    )

    file_path = save_job(job)

    assert Path(file_path).exists()

    print(f"Test passed: {file_path}")


if __name__ == "__main__":
    test_save_job()