import os
import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from ingestion.loaders import load_resume
from intelligence.resume_analyzer import analyze_resume
from career.state import build_career_state
from jobs.local_job_loader import load_local_jobs
from schemas.resume import ResumeAnalysis


def main():
    # -----------------------------
    # 1. Load Resume / Candidate Profile
    # -----------------------------
    resume_folder = Path("data/resumes")
    resume_analysis = None

    resume_files = [
        file
        for file in resume_folder.iterdir()
        if file.is_file()
        and file.suffix.lower() in [".pdf", ".png", ".jpg", ".jpeg"]
    ] if resume_folder.exists() else []

    api_key = os.getenv("GOOGLE_API_KEY")

    if resume_files and api_key:
        resume_file = resume_files[0]
        print(f"Loading resume: {resume_file}")
        try:
            documents = load_resume(str(resume_file))
            resume_text = "\n".join(
                document.page_content for document in documents
            )
            print("\nAnalyzing resume with Gemini...")
            resume_analysis = analyze_resume(resume_text)
            print("Resume analysis complete.")
        except Exception as e:
            print(f"Online resume analysis failed ({e}); using offline fallback profile.")

    if resume_analysis is None:
        print("Using structured candidate profile (offline mode)...")
        resume_analysis = ResumeAnalysis(
            name="Prince Kumar",
            skills=[
                "Python",
                "Machine Learning",
                "Deep Learning",
                "PyTorch",
                "TensorFlow",
                "Scikit-learn",
                "Data Analysis",
                "SQL",
                "Docker",
                "Git",
            ],
            experience=[
                "Machine Learning Intern: Developed predictive ML models with Scikit-learn and PyTorch",
                "Data Science Project: Built end-to-end classification pipeline with Docker and Python",
            ],
            projects=[
                "AI Image Classification system using PyTorch and CNNs",
                "Career intelligence search tool with Python and SQL",
            ],
            education=[
                "B.Tech in Computer Science and Engineering",
            ],
            strengths=[
                "Strong foundation in core ML and Python development",
                "Hands-on experience with deep learning frameworks",
            ],
        )

    # -----------------------------
    # 2. Load Local Jobs & Build Career State
    # -----------------------------
    print("\nLoading local job requirement dataset...")
    jobs = load_local_jobs()
    print(f"Loaded {len(jobs)} local job postings.")

    print("\nBuilding Career State...")
    career_state = build_career_state(
        resume_analysis=resume_analysis,
        target_roles=[
            "Machine Learning Engineer",
            "AI Engineer",
            "Data Scientist",
        ],
        jobs=jobs,
        frequency_threshold=0.40,
    )

    # -----------------------------
    # 3. Print State & Market Insights
    # -----------------------------
    print("\n" + "=" * 60)
    print("CAREER STATE - SESSION 10")
    print("=" * 60)

    print("\nCandidate:")
    print(career_state.candidate_name)

    print("\nCurrent Skills:")
    for skill in career_state.current_skills:
        print(f"  - {skill}")

    print("\nTarget Roles:")
    for role in career_state.target_roles:
        print(f"  - {role}")

    print("\nCareer Stage:")
    print(f"  {career_state.career_stage}")

    print("\nJobs Analyzed in Dataset:")
    print(f"  {career_state.jobs_analyzed}")

    print("\nCross-Dataset Market Skill Coverage:")
    if career_state.market_skill_coverage is not None:
        print(f"  {career_state.market_skill_coverage}%")
    else:
        print("  N/A")

    print("\nHigh-Demand Skills Candidate Already Possesses:")
    for skill in career_state.common_candidate_skills:
        print(f"  [x] {skill}")

    print("\nRecurring Market Skill Gaps (Demand >= 40%):")
    for skill in career_state.recurring_skill_gaps:
        print(f"  [-] {skill}")

    print("\nPer-Job Skill Gaps (Sample first 3 jobs):")
    for gap in career_state.job_skill_gaps[:3]:
        print(f"\n  Job: {gap.job_title} ({gap.company or 'Unknown'})")
        print(f"    Required Coverage: {gap.required_skill_coverage}%")
        print(f"    Preferred Coverage: {gap.preferred_skill_coverage if gap.preferred_skill_coverage is not None else 'N/A'}")
        print(f"    Matched Required: {', '.join(gap.matched_required[:4])}...")
        print(f"    Missing Required: {', '.join(gap.missing_required[:4])}...")

    print("\n" + "=" * 60)
    print("CAREER SUMMARY")
    print("=" * 60)
    print(career_state.summary)


if __name__ == "__main__":
    main()