"""Agent API routes."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("/chat")
def agent_chat(request: ChatRequest):
    """Send a message to the Career Agent and receive a grounded response."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")
    try:
        from agents.career_agent import chat
        response = chat(
            user_message=request.message.strip(),
            history=request.history,
        )
        return {
            "status": "ok",
            "response": response,
            "message": request.message,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}")
