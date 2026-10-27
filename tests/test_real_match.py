import json
from pathlib import Path

from ingestion.loaders import load_resume
from intelligence.resume_analyzer import analyze_resume
from intelligence.job_analyzer import analyze_job
from schemas.job import JobPosting
from matching.matcher import match_job


def main():

    # ==========================================
    # 1. FIND RESUME
    # ==========================================

    resume_folder = Path("data/resumes")

    resume_files = [
        file
        for file in resume_folder.iterdir()
        if file.is_file()
        and file.suffix.lower() in [
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
        ]
    ]

    if not resume_files:
        raise FileNotFoundError(
            "No resume found in data/resumes"
        )

    resume_file = resume_files[0]

    print(f"Resume: {resume_file}")
    print("Loading resume...\n")

    documents = load_resume(
        str(resume_file)
    )

    resume_text = "\n".join(
        document.page_content
        for document in documents
    )

    # ==========================================
    # 2. ANALYZE RESUME
    # ==========================================

    print("Analyzing resume...\n")

    resume_analysis = analyze_resume(
        resume_text
    )

    print("Resume analysis complete.")

    print("\nCandidate:", resume_analysis.name)

    print("\nSkills:")
    for skill in resume_analysis.skills:
        print(f"- {skill}")

    # ==========================================
    # 3. FIND JOB
    # ==========================================

    job_files = list(
        Path("data/raw_jobs").rglob("*.json")
    )

    if not job_files:
        raise FileNotFoundError(
            "No job JSON files found in data/raw_jobs"
        )

    job_file = job_files[0]

    print(f"\nJob: {job_file}")

    with open(
        job_file,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    job = JobPosting.model_validate(data)

    # ==========================================
    # 4. ANALYZE JOB
    # ==========================================

    print("\nAnalyzing job...\n")

    job_analysis = analyze_job(job)

    print("Job analysis complete.")

    print("\nJob Title:")
    print(job_analysis.title)

    print("\nRequired Skills:")
    for skill in job_analysis.required_skills:
        print(f"- {skill}")

    # ==========================================
    # 5. MATCH
    # ==========================================

    print("\nCalculating match...\n")

    result = match_job(
        candidate_skills=resume_analysis.skills,
        candidate_experience=resume_analysis.experience,
        resume_text=resume_text,
        job_analysis=job_analysis,
        job=job,
    )

    # ==========================================
    # 6. DISPLAY RESULT
    # ==========================================

    print("\n")
    print("=" * 60)
    print("JOB MATCH RESULT")
    print("=" * 60)

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
        print(f"✓ {skill}")

    print("\nMissing Skills:")
    for skill in result["missing_skills"]:
        print(f"✗ {skill}")


if __name__ == "__main__":
    main()