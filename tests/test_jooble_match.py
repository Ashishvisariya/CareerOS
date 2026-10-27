import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from jobs.jooble_client import fetch_jooble_jobs
from ingestion.loaders import load_resume
from intelligence.resume_analyzer import analyze_resume
from intelligence.job_analyzer import analyze_job
from schemas.job import JobPosting
from matching.matcher import match_job


def main():
    # ==============================
    # 1. RESUME
    # ==============================

    resume_folder = Path("data/resumes")

    resume_files = [
        file
        for file in resume_folder.iterdir()
        if file.is_file()
        and file.suffix.lower() in [".pdf", ".png", ".jpg", ".jpeg"]
    ]

    if not resume_files:
        raise FileNotFoundError("No resume found")

    resume_file = resume_files[0]

    print("Resume:", resume_file)

    documents = load_resume(str(resume_file))

    resume_text = "\n".join(
        document.page_content
        for document in documents
    )

    print("\nAnalyzing resume...")

    resume_analysis = analyze_resume(resume_text)

    print("Resume analysis complete.")


    # ==============================
    # 2. JOOBLE JOB
    # ==============================

    print("\nFetching jobs from Jooble...")

    data = fetch_jooble_jobs(
        query="machine learning engineer",
        location="India"
    )

    jobs = data.get("jobs", [])

    print("Jobs received:", len(jobs))

    if not jobs:
        raise ValueError("No Jooble jobs found")


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


    # ==============================
    # 3. JOB ANALYSIS
    # ==============================

    print("\nAnalyzing job...")

    job_analysis = analyze_job(job)

    print("Job analysis complete.")


    # ==============================
    # 4. MATCH
    # ==============================

    print("\nCalculating match...")

    result = match_job(
        candidate_skills=resume_analysis.skills,
        candidate_experience=resume_analysis.experience,
        resume_text=resume_text,
        job_analysis=job_analysis,
        job=job,
    )


    # ==============================
    # 5. RESULT
    # ==============================

    print("\n" + "=" * 60)
    print("CAREEROS JOB MATCH")
    print("=" * 60)

    print("\nCandidate:")
    print(resume_analysis.name)

    print("\nJob:")
    print(result["job_title"])

    print("\nCompany:")
    print(result["company"])

    print("\nOverall Match:")
    print(f'{result["overall_score"]}%')

    print("\nSkill Match:")
    print(f'{result["skill_score"]}%')

    print("\nExperience Match:")
    print(f'{result["experience_score"]}%')

    print("\nSemantic Match:")
    print(f'{result["semantic_score"]}%')

    print("\nMatched Skills:")

    for skill in result["matched_skills"]:
        print("[x]", skill)

    print("\nMissing Skills:")

    for skill in result["missing_skills"]:
        print("[-]", skill)
        
    print("\n" + "=" * 60)
    print("SKILL GAP ANALYSIS")
    print("=" * 60)

    skill_gap = result["skill_gap"]

    print("\nMatched Required Skills:")

    for skill in skill_gap["matched_required"]:
        print("[x]", skill)

    print("\nMissing Required Skills:")

    for skill in skill_gap["missing_required"]:
        print("[-]", skill)

    print("\nMatched Preferred Skills:")

    for skill in skill_gap["matched_preferred"]:
        print("[x]", skill)

    print("\nMissing Preferred Skills:")

    for skill in skill_gap["missing_preferred"]:
        print("[-]", skill)

    print("\nRequired Skill Coverage:")
    print(f'{skill_gap["required_skill_coverage"]}%')

    print("\nPreferred Skill Coverage:")
    print(f'{skill_gap["preferred_skill_coverage"]}%')


if __name__ == "__main__":
    main()