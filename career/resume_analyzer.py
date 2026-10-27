"""
CareerOS — Resume analyzer (Groq-based).

Replaces the previous Gemini-chat-based analyzer with the centralized
Groq LLM factory while keeping the same public interface.
"""
from __future__ import annotations

import logging

from langchain_core.documents import Document

from core.llm import get_structured_llm, invoke_with_retry
from ingestion.pipeline import get_retriever
from retrieval.retriever import retrieve_resume_chunks
from schemas.resume import ResumeAnalysis

logger = logging.getLogger(__name__)

_EXTRACTION_QUERY = """
Extract the following information from the candidate's resume:
1. Candidate's full name
2. Technical and professional skills
3. Work experience and internships
4. Projects
5. Education
6. Strengths supported by the resume
Use only information contained in the resume. Do not invent information.
"""


def format_resume_context(documents: list[Document]) -> str:
    parts = []
    for i, doc in enumerate(documents, start=1):
        parts.append(f"--- RESUME CHUNK {i} ---\n{doc.page_content}")
    return "\n\n".join(parts)


def analyze_resume(retriever=None) -> ResumeAnalysis:
    """
    Analyze a resume using the Groq LLM and return a structured ResumeAnalysis.

    Parameters
    ----------
    retriever:
        An optional pre-built retriever. If None, the default resume
        Chroma collection is used.

    Raises
    ------
    ValueError
        When no resume chunks are found or the LLM returns invalid output.
    """
    if retriever is None:
        retriever = get_retriever()

    documents = retrieve_resume_chunks(retriever, _EXTRACTION_QUERY)

    if not documents:
        raise ValueError(
            "No resume chunks found. Please upload and ingest a resume first."
        )

    context = format_resume_context(documents)

    prompt = f"""You are an expert resume information extraction system.

IMPORTANT RULES:
- Use ONLY the information in the resume.
- Do NOT invent information.
- Do NOT guess the candidate's name.
- Do NOT create skills that are not present.
- Do NOT create experience, projects, or education that are not present.
- Strengths must be supported by evidence in the resume.
- If information is genuinely unavailable, use an empty list.
- Return the result using the ResumeAnalysis schema.

RESUME TEXT:

{context}
"""

    structured_llm = get_structured_llm(ResumeAnalysis)
    result = invoke_with_retry(structured_llm, prompt)

    if not isinstance(result, ResumeAnalysis):
        raise ValueError(
            f"LLM returned unexpected type: {type(result)}. Expected ResumeAnalysis."
        )

    logger.info(
        "Resume analyzed: name=%r, skills=%d, experience=%d",
        result.name,
        len(result.skills),
        len(result.experience),
    )
    return result