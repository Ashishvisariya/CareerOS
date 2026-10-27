"""
CareerOS — Adaptive AI Interview system.

Manages interview sessions: question generation, answer evaluation,
follow-up adaptation, and session persistence.

Uses Groq for:
  - Question generation (structured by role, type, difficulty)
  - Answer evaluation against a rubric
  - Follow-up question selection based on prior answers
  - Session summary generation

Evaluation scores are calculated from structured rubric dimensions.
Sessions are persisted to disk via core.persistence.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from core.llm import get_llm, invoke_with_retry
from core.persistence import (
    load_interview_session,
    save_interview_session,
    list_interview_sessions,
    delete_interview_session,
)

logger = logging.getLogger(__name__)

InterviewType = Literal["technical", "behavioral", "project-based", "mixed"]
Difficulty = Literal["entry", "mid", "senior"]


# ──────────────────────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────────────────────

class QuestionTurn(BaseModel):
    turn: int
    question: str
    answer: str = ""
    evaluation: dict = Field(default_factory=dict)
    follow_up_context: str = ""


class InterviewSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    job_id: str | None = None
    target_role: str
    interview_type: str = "technical"
    difficulty: str = "mid"
    max_questions: int = 5
    current_turn: int = 0
    status: str = "active"  # active | completed | abandoned
    turns: list[QuestionTurn] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ──────────────────────────────────────────────────────────────────────────────
# Prompts
# ──────────────────────────────────────────────────────────────────────────────

def _opening_question_prompt(
    target_role: str,
    interview_type: str,
    difficulty: str,
    candidate_skills: list[str],
) -> str:
    return f"""You are an expert technical interviewer for {target_role} positions.

Interview type: {interview_type}
Difficulty level: {difficulty}
Candidate's known skills: {', '.join(candidate_skills[:10]) or 'not specified'}

Generate a strong opening interview question appropriate for this role and type.
The question should:
- Be clearly worded and unambiguous
- Be answerable in 2-5 minutes
- Be relevant to {target_role} responsibilities
- Match the {difficulty} difficulty level

Return ONLY the question text, nothing else."""


def _evaluation_prompt(
    question: str,
    answer: str,
    target_role: str,
    interview_type: str,
) -> str:
    return f"""You are evaluating a candidate's interview answer for a {target_role} position.

QUESTION: {question}

CANDIDATE'S ANSWER: {answer}

Evaluate the answer on these dimensions (score each 0-10):
1. Technical correctness: Is the answer factually accurate?
2. Reasoning: Does the candidate explain their thinking?
3. Relevance: Does the answer address the question?
4. Clarity: Is the explanation clear and well-structured?
5. Practical application: Does the candidate relate to real-world use?

Then provide:
- STRENGTHS: What the candidate did well (2-3 specific points)
- GAPS: What could be improved (2-3 specific points)
- OVERALL_SCORE: A single integer 0-10

Format your response EXACTLY like this:
TECHNICAL: <score>
REASONING: <score>
RELEVANCE: <score>
CLARITY: <score>
PRACTICAL: <score>
STRENGTHS: <bullet points>
GAPS: <bullet points>
OVERALL_SCORE: <score>

Important:
- Base your evaluation only on the answer provided
- Do not consider communication accent or style
- Do not infer personality or hiring suitability from this answer alone
- This evaluation is for practice purposes only"""


def _followup_prompt(
    target_role: str,
    interview_type: str,
    difficulty: str,
    history: list[dict],
    last_evaluation: dict,
) -> str:
    history_text = "\n".join(
        f"Q{i+1}: {t['question']}\nA{i+1}: {t['answer'][:200]}..."
        for i, t in enumerate(history[-3:])
    )
    strengths = last_evaluation.get("strengths", "")
    gaps = last_evaluation.get("gaps", "")

    return f"""You are conducting an adaptive interview for a {target_role} position.

Interview type: {interview_type}, Difficulty: {difficulty}

Previous Q&A (last 3):
{history_text}

Last answer feedback:
Strengths: {strengths}
Gaps to probe: {gaps}

Generate the next interview question that:
1. Builds on the conversation so far
2. Probes the identified gaps if significant
3. Maintains appropriate difficulty ({difficulty})
4. Is a different question type from the last one when possible
5. Is clearly worded and answerable in 2-5 minutes

Return ONLY the question text."""


def _summary_prompt(session_dict: dict) -> str:
    turns_text = "\n".join(
        f"Q{t['turn']}: {t['question']}\n"
        f"Score: {t['evaluation'].get('overall_score', 'N/A')}/10\n"
        f"Strengths: {t['evaluation'].get('strengths', '')}\n"
        f"Gaps: {t['evaluation'].get('gaps', '')}"
        for t in session_dict.get("turns", [])
        if t.get("answer")
    )

    return f"""Summarize this {session_dict['target_role']} practice interview session.

Session data:
{turns_text}

Provide:
1. OVERALL_STRENGTHS: Key skills/knowledge the candidate demonstrated (3-4 points)
2. IMPROVEMENT_AREAS: Specific areas to practice more (3-4 points)
3. NEXT_STEPS: Concrete recommendations for preparation (3-4 actionable items)
4. SESSION_SCORE: Average score across all questions (calculate it)

Format:
OVERALL_STRENGTHS: <points>
IMPROVEMENT_AREAS: <points>
NEXT_STEPS: <points>
SESSION_SCORE: <number>

Note: This is a practice session summary for self-improvement only."""


# ──────────────────────────────────────────────────────────────────────────────
# Parsing helpers
# ──────────────────────────────────────────────────────────────────────────────

def _parse_evaluation(text: str) -> dict:
    """Parse structured evaluation text into a dict."""
    result: dict[str, Any] = {
        "technical": 0, "reasoning": 0, "relevance": 0,
        "clarity": 0, "practical": 0,
        "strengths": "", "gaps": "", "overall_score": 0,
    }
    for line in text.splitlines():
        for key in ["TECHNICAL", "REASONING", "RELEVANCE", "CLARITY", "PRACTICAL", "OVERALL_SCORE"]:
            if line.startswith(f"{key}:"):
                try:
                    result[key.lower()] = int(line.split(":", 1)[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
        if line.startswith("STRENGTHS:"):
            result["strengths"] = line.split(":", 1)[1].strip()
        elif line.startswith("GAPS:"):
            result["gaps"] = line.split(":", 1)[1].strip()
    return result


def _parse_summary(text: str) -> dict:
    result: dict[str, Any] = {
        "overall_strengths": "", "improvement_areas": "",
        "next_steps": "", "session_score": 0.0,
    }
    for line in text.splitlines():
        if line.startswith("OVERALL_STRENGTHS:"):
            result["overall_strengths"] = line.split(":", 1)[1].strip()
        elif line.startswith("IMPROVEMENT_AREAS:"):
            result["improvement_areas"] = line.split(":", 1)[1].strip()
        elif line.startswith("NEXT_STEPS:"):
            result["next_steps"] = line.split(":", 1)[1].strip()
        elif line.startswith("SESSION_SCORE:"):
            try:
                result["session_score"] = float(line.split(":", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def create_session(
    target_role: str,
    interview_type: InterviewType = "technical",
    difficulty: Difficulty = "mid",
    max_questions: int = 5,
    candidate_skills: list[str] | None = None,
    job_id: str | None = None,
) -> dict:
    """
    Create a new interview session and generate the first question.

    Returns the session dict with session_id and first question populated.
    """
    candidate_skills = candidate_skills or []

    llm = get_llm(temperature=0.5, max_tokens=400)
    prompt = _opening_question_prompt(target_role, interview_type, difficulty, candidate_skills)

    try:
        response = invoke_with_retry(llm, prompt)
        question = response.content if hasattr(response, "content") else str(response)
        question = question.strip()
    except Exception as exc:
        logger.error("Failed to generate opening question: %s", exc)
        raise RuntimeError(f"Could not generate interview question: {exc}") from exc

    session = InterviewSession(
        target_role=target_role,
        interview_type=interview_type,
        difficulty=difficulty,
        max_questions=max_questions,
        job_id=job_id,
        current_turn=1,
    )
    session.turns.append(QuestionTurn(turn=1, question=question))

    session_dict = session.model_dump()
    save_interview_session(session_dict)
    logger.info("Created interview session %s for %s", session.session_id, target_role)
    return session_dict


def submit_answer(session_id: str, answer: str) -> dict:
    """
    Submit an answer for the current question, evaluate it, and generate the next question.

    Returns the updated session dict.
    """
    session_dict = load_interview_session(session_id)
    if not session_dict:
        raise ValueError(f"Session not found: {session_id}")

    if session_dict.get("status") != "active":
        raise ValueError(f"Session {session_id} is not active (status: {session_dict.get('status')})")

    turns = session_dict.get("turns", [])
    if not turns:
        raise ValueError(f"Session {session_id} has no questions")

    # Find the unanswered turn
    current_turn_idx = None
    for i, t in enumerate(turns):
        if not t.get("answer"):
            current_turn_idx = i
            break

    if current_turn_idx is None:
        raise ValueError(f"No unanswered question found in session {session_id}")

    current_q = turns[current_turn_idx]["question"]

    # Evaluate answer
    llm = get_llm(temperature=0.0, max_tokens=600)
    eval_prompt = _evaluation_prompt(
        current_q, answer,
        session_dict["target_role"],
        session_dict["interview_type"],
    )
    try:
        eval_response = invoke_with_retry(llm, eval_prompt)
        eval_text = eval_response.content if hasattr(eval_response, "content") else str(eval_response)
        evaluation = _parse_evaluation(eval_text)
    except Exception as exc:
        logger.warning("Evaluation failed: %s", exc)
        evaluation = {"error": str(exc), "overall_score": 0}

    turns[current_turn_idx]["answer"] = answer
    turns[current_turn_idx]["evaluation"] = evaluation

    current_turn_number = session_dict.get("current_turn", 1)
    max_questions = session_dict.get("max_questions", 5)

    # Check if session complete
    if current_turn_number >= max_questions:
        session_dict["status"] = "completed"
        session_dict["turns"] = turns
        # Generate summary
        try:
            llm_sum = get_llm(temperature=0.3, max_tokens=600)
            sum_prompt = _summary_prompt(session_dict)
            sum_response = invoke_with_retry(llm_sum, sum_prompt)
            sum_text = sum_response.content if hasattr(sum_response, "content") else str(sum_response)
            session_dict["summary"] = _parse_summary(sum_text)
        except Exception as exc:
            logger.warning("Summary generation failed: %s", exc)
            session_dict["summary"] = {"error": str(exc)}
    else:
        # Generate follow-up question
        history = [
            {"question": t["question"], "answer": t.get("answer", "")}
            for t in turns if t.get("answer")
        ]
        fu_prompt = _followup_prompt(
            session_dict["target_role"],
            session_dict["interview_type"],
            session_dict["difficulty"],
            history,
            evaluation,
        )
        try:
            fu_response = invoke_with_retry(llm, fu_prompt)
            next_question = fu_response.content if hasattr(fu_response, "content") else str(fu_response)
            next_question = next_question.strip()
        except Exception as exc:
            logger.error("Follow-up generation failed: %s", exc)
            raise RuntimeError(f"Could not generate follow-up question: {exc}") from exc

        next_turn = current_turn_number + 1
        turns.append({"turn": next_turn, "question": next_question, "answer": "", "evaluation": {}})
        session_dict["current_turn"] = next_turn
        session_dict["turns"] = turns

    save_interview_session(session_dict)
    return session_dict


def get_session(session_id: str) -> dict | None:
    """Return a session dict by ID."""
    return load_interview_session(session_id)


def get_all_sessions() -> list[dict]:
    """Return all persisted interview sessions."""
    return list_interview_sessions()


def delete_session(session_id: str) -> bool:
    """Delete a session. Returns True if found and deleted."""
    return delete_interview_session(session_id)
