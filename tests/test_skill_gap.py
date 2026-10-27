import sys
from pathlib import Path

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

from matching.skill_gap import calculate_skill_gap


def main():
    candidate_skills = [
        "Python",
        "Machine Learning",
        "PyTorch",
        "Pandas",
    ]

    required_skills = [
        "Python",
        "Machine Learning",
        "PyTorch",
        "Docker",
        "AWS",
    ]

    preferred_skills = [
        "LangChain",
        "LangGraph",
        "Kubernetes",
    ]

    result = calculate_skill_gap(
        candidate_skills=candidate_skills,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )

    print("\n" + "=" * 60)
    print("SKILL GAP ANALYSIS")
    print("=" * 60)

    print("\nMatched Required Skills:")
    for skill in result["matched_required"]:
        print("[x]", skill)

    print("\nMissing Required Skills:")
    for skill in result["missing_required"]:
        print("[-]", skill)

    print("\nMatched Preferred Skills:")
    for skill in result["matched_preferred"]:
        print("[x]", skill)

    print("\nMissing Preferred Skills:")
    for skill in result["missing_preferred"]:
        print("[-]", skill)

    print("\nRequired Skill Coverage:")
    print(f'{result["required_skill_coverage"]}%')

    print("\nPreferred Skill Coverage:")
    print(f'{result["preferred_skill_coverage"]}%')


if __name__ == "__main__":
    main()