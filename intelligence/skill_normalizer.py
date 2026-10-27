"""
CareerOS — Skill normalization layer.

Provides canonical skill names, alias resolution, and category tagging.
Uses a deterministic alias dictionary; no LLM required for normalization.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Alias map: lower-stripped alias → canonical display name
# ---------------------------------------------------------------------------
_ALIASES: dict[str, str] = {
    # Python ecosystem
    "python3": "Python",
    "python 3": "Python",
    "py": "Python",
    "sklearn": "Scikit-learn",
    "scikit learn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "sk-learn": "Scikit-learn",
    # Deep learning
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    "keras": "Keras",
    # ML
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "reinforcement learning": "Reinforcement Learning",
    "rl": "Reinforcement Learning",
    # NLP / LLM
    "nlp": "NLP",
    "natural language processing": "NLP",
    "llm": "LLMs",
    "llms": "LLMs",
    "large language models": "LLMs",
    "large language model": "LLMs",
    "generative ai": "Generative AI",
    "gen ai": "Generative AI",
    "genai": "Generative AI",
    # CV
    "cv": "Computer Vision",
    "computer vision": "Computer Vision",
    "opencv": "OpenCV",
    "open cv": "OpenCV",
    # RAG / Agents
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
    "langchain": "LangChain",
    "lang chain": "LangChain",
    "langgraph": "LangGraph",
    "lang graph": "LangGraph",
    "mcp": "MCP",
    "model context protocol": "MCP",
    # Data
    "numpy": "NumPy",
    "np": "NumPy",
    "pandas": "Pandas",
    "pd": "Pandas",
    "matplotlib": "Matplotlib",
    "seaborn": "Seaborn",
    "plotly": "Plotly",
    # Frameworks / infra
    "fastapi": "FastAPI",
    "fast api": "FastAPI",
    "streamlit": "Streamlit",
    "flask": "Flask",
    "django": "Django",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "google cloud": "GCP",
    "git": "Git",
    "github": "GitHub",
    "sql": "SQL",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    # Languages
    "c++": "C++",
    "cpp": "C++",
    "c#": "C#",
    "csharp": "C#",
    "java": "Java",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "r": "R",
    "matlab": "MATLAB",
    # General
    "oop": "OOP",
    "object oriented programming": "OOP",
    "data structures": "Data Structures",
    "algorithms": "Algorithms",
    "api": "API Development",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "restful": "REST APIs",
    "microservices": "Microservices",
    "ci/cd": "CI/CD",
    "agile": "Agile",
    "scrum": "Scrum",
    "linux": "Linux",
    "bash": "Bash",
    "shell": "Shell Scripting",
}

# ---------------------------------------------------------------------------
# Skill → category mapping (canonical name → category)
# ---------------------------------------------------------------------------
_CATEGORIES: dict[str, str] = {
    "Python": "Programming Languages",
    "C++": "Programming Languages",
    "Java": "Programming Languages",
    "JavaScript": "Programming Languages",
    "TypeScript": "Programming Languages",
    "Go": "Programming Languages",
    "Rust": "Programming Languages",
    "R": "Programming Languages",
    "MATLAB": "Programming Languages",
    "Machine Learning": "AI/ML",
    "Deep Learning": "AI/ML",
    "NLP": "AI/ML",
    "Computer Vision": "AI/ML",
    "LLMs": "AI/ML",
    "Generative AI": "AI/ML",
    "RAG": "AI/ML",
    "Reinforcement Learning": "AI/ML",
    "PyTorch": "AI/ML Frameworks",
    "TensorFlow": "AI/ML Frameworks",
    "Keras": "AI/ML Frameworks",
    "Scikit-learn": "AI/ML Frameworks",
    "LangChain": "AI/ML Frameworks",
    "LangGraph": "AI/ML Frameworks",
    "NumPy": "Data Science",
    "Pandas": "Data Science",
    "Matplotlib": "Data Science",
    "Seaborn": "Data Science",
    "Plotly": "Data Science",
    "FastAPI": "Web Frameworks",
    "Streamlit": "Web Frameworks",
    "Flask": "Web Frameworks",
    "Django": "Web Frameworks",
    "Docker": "DevOps/Infrastructure",
    "Kubernetes": "DevOps/Infrastructure",
    "AWS": "Cloud",
    "Azure": "Cloud",
    "GCP": "Cloud",
    "Git": "Tools",
    "GitHub": "Tools",
    "SQL": "Databases",
    "PostgreSQL": "Databases",
    "MySQL": "Databases",
    "MongoDB": "Databases",
    "Redis": "Databases",
    "OOP": "Software Engineering",
    "Data Structures": "Software Engineering",
    "Algorithms": "Software Engineering",
    "REST APIs": "Software Engineering",
    "Microservices": "Software Engineering",
    "CI/CD": "DevOps/Infrastructure",
    "Agile": "Soft Skills",
    "Scrum": "Soft Skills",
    "Linux": "Tools",
    "Bash": "Tools",
    "MCP": "AI/ML Frameworks",
    "OpenCV": "AI/ML Frameworks",
}


def normalize_skill(skill: str) -> str:
    """
    Normalize a raw skill string to a canonical display name.

    Resolution order:
    1. Alias dictionary (deterministic, exact match after lower-strip)
    2. Original (title-cased) if no alias found
    """
    if not skill or not str(skill).strip():
        return ""
    key = " ".join(str(skill).lower().strip().split())
    return _ALIASES.get(key, skill.strip())


def get_skill_category(canonical_skill: str) -> str:
    """Return the category for a canonical skill name, or 'Other'."""
    return _CATEGORIES.get(canonical_skill, "Other")


def normalize_skill_list(skills: list[str]) -> list[str]:
    """
    Normalize a list of raw skill strings, deduplicating by canonical name.
    Preserves insertion order of first occurrence.
    """
    seen: set[str] = set()
    result: list[str] = []
    for s in skills:
        canonical = normalize_skill(s)
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


def categorize_skills(skills: list[str]) -> dict[str, list[str]]:
    """
    Group a list of canonical skills by category.

    Returns a dict mapping category → list of skills in that category.
    """
    categories: dict[str, list[str]] = {}
    for skill in skills:
        cat = get_skill_category(skill)
        categories.setdefault(cat, []).append(skill)
    return categories
