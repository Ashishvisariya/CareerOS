import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from schemas.job_analysis import JobAnalysis


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)


def create_job_analyzer():
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )

    structured_llm = llm.with_structured_output(
        JobAnalysis
    )

    return structured_llm


def analyze_job(job):
    analyzer = create_job_analyzer()

    prompt = f"""
Analyze this job posting using ONLY the information provided.

Do not invent skills, experience, education, technologies,
or requirements that are not explicitly supported by the text.

Extract:

1. Job title
2. Required skills
3. Preferred skills
4. Experience requirements
5. Education requirements
6. Responsibilities
7. Technologies
8. Key requirements

For key_requirements, include the most important requirements
or qualifications that are explicitly stated in the provided text.
If no explicit requirements are present, return an empty list.

Job Title:
{job.title}

Company:
{job.company}

Location:
{job.location}

Description:
{job.description}
"""

    result = analyzer.invoke(prompt)

    return result