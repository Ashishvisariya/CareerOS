"""
CareerOS — Centralized LLM factory.

Provides a configured ChatGroq instance for all modules that need LLM
chat/completion. Separated from the embedding pipeline (Google Gemini).

Usage:
    from core.llm import get_llm, get_structured_llm

    llm = get_llm()
    structured = get_structured_llm(MyPydanticModel)
"""
from __future__ import annotations

import logging
import time
from typing import Any, Type, TypeVar

from langchain_groq import ChatGroq
from pydantic import BaseModel

from core.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Retry configuration for transient Groq failures
_MAX_RETRIES = 3
_RETRY_DELAY_S = 2.0


def get_llm(
    temperature: float = 0.0,
    max_tokens: int = 4096,
) -> ChatGroq:
    """
    Return a configured ChatGroq instance.

    Raises
    ------
    ValueError
        When GROQ_API_KEY is missing or looks like a placeholder.
    RuntimeError
        When the Groq model name is rejected by the API.
    """
    settings = get_settings()

    if not settings.groq_configured:
        raise ValueError(
            "GROQ_API_KEY is not configured. "
            "Add a valid key to your .env file as GROQ_API_KEY=<your-key>."
        )

    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_structured_llm(schema: Type[T], temperature: float = 0.0) -> Any:
    """
    Return a ChatGroq instance bound to produce structured output
    conforming to the given Pydantic model schema.

    Parameters
    ----------
    schema:
        A Pydantic BaseModel subclass defining the expected output shape.
    temperature:
        Sampling temperature (0 = deterministic).
    """
    llm = get_llm(temperature=temperature)
    return llm.with_structured_output(schema)


def invoke_with_retry(
    chain: Any,
    prompt: str,
    max_retries: int = _MAX_RETRIES,
    delay: float = _RETRY_DELAY_S,
) -> Any:
    """
    Invoke a LangChain chain with bounded retries for transient errors.

    Retries only on connection/timeout errors. Raises immediately on
    authentication failures (401/403) to avoid invalid-credential loops.
    """
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return chain.invoke(prompt)
        except Exception as exc:
            msg = str(exc).lower()

            # Do not retry auth failures
            if any(
                kw in msg
                for kw in ("401", "403", "authentication", "invalid api key", "unauthorized")
            ):
                logger.error("LLM authentication error — not retrying: %s", exc)
                raise

            last_exc = exc
            if attempt < max_retries:
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s — retrying in %.1fs",
                    attempt,
                    max_retries,
                    exc,
                    delay,
                )
                time.sleep(delay)
            else:
                logger.error(
                    "LLM call failed after %d attempts: %s", max_retries, exc
                )

    raise RuntimeError(
        f"LLM call failed after {max_retries} attempts."
    ) from last_exc
