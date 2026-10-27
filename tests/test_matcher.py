import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from matching.matcher import (
    calculate_skill_match,
    calculate_experience_match,
    calculate_overall_score,
)


def main():
    print("Testing skill matching...\n")

    skill_score, matched, missing = calculate_skill_match(
        candidate_skills=[
            "Python",
            "SQL",
            "Docker",
            "LangChain",
        ],
        required_skills=[
            "Python",
            "SQL",
            "AWS",
            "Docker",
        ],
        preferred_skills=[
            "Kubernetes",
            "LangChain",
        ],
    )

    print("Skill Score:", skill_score)

    print("\nMatched Skills:")
    for skill in matched:
        print(f"- {skill}")

    print("\nMissing Skills:")
    for skill in missing:
        print(f"- {skill}")

    print("\nTesting experience matching...\n")

    experience_score = calculate_experience_match(
        candidate_experience=[
            "Built machine learning applications using Python",
            "Worked with SQL databases and Docker",
        ],
        job_requirements=[
            "Experience with Python",
            "Experience with Docker",
            "Experience with AWS",
        ],
    )

    print("Experience Score:", experience_score)

    print("\nTesting overall score...\n")

    overall_score = calculate_overall_score(
        skill_score=skill_score,
        experience_score=experience_score,
        semantic_score=80,
    )

    print("Overall Score:", overall_score)


if __name__ == "__main__":
    main()