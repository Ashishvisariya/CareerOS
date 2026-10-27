import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from schemas.resume import ResumeAnalysis


# Load CareerOS/.env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def create_resume_analyzer():

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in CareerOS/.env"
        )

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0,
    )

    structured_llm = llm.with_structured_output(
        ResumeAnalysis
    )

    return structured_llm


def analyze_resume(resume_text: str):

    analyzer = create_resume_analyzer()

    prompt = f"""
Analyze the following resume.

Extract the candidate's:

- Name
- Skills
- Work experience
- Projects
- Education
- Strengths

Do not invent information.
Only use information present in the resume.

Resume:
{resume_text}
"""

    result = analyzer.invoke(prompt)

    return result