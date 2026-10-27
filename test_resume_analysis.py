from pathlib import Path

from ingestion.loaders import load_resume
from intelligence.resume_analyzer import analyze_resume


def main():

    resume_folder = Path("data/resumes")

    supported_extensions = [
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
    ]

    resume_files = [
        file
        for file in resume_folder.iterdir()
        if file.is_file()
        and file.suffix.lower() in supported_extensions
    ]

    if not resume_files:
        raise FileNotFoundError(
            "No resume found in data/resumes"
        )

    resume_file = resume_files[0]

    print(f"Loading resume: {resume_file}\n")

    documents = load_resume(
        str(resume_file)
    )

    resume_text = "\n".join(
        document.page_content
        for document in documents
    )

    print("Analyzing resume...\n")

    result = analyze_resume(resume_text)

    print("RESUME INTELLIGENCE")
    print("=" * 60)

    print("\nName:")
    print(result.name)

    print("\nSkills:")
    for skill in result.skills:
        print(f"- {skill}")

    print("\nExperience:")
    for experience in result.experience:
        print(f"- {experience}")

    print("\nProjects:")
    for project in result.projects:
        print(f"- {project}")

    print("\nEducation:")
    for education in result.education:
        print(f"- {education}")

    print("\nStrengths:")
    for strength in result.strengths:
        print(f"- {strength}")


if __name__ == "__main__":
    main()
