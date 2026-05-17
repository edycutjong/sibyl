"""Sibyl — FastAPI server with dual endpoints.

Endpoints:
  POST /chat/completions  — OpenAI-compatible (Prophet Arena auto-eval)
  POST /predict           — CLI-compatible (prophet forecast predict --agent-url)
  GET  /health            — Uptime check
  GET  /stats             — Cost/latency monitoring
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from sibyl.agent import get_prediction_stats, predict, predict_from_prompt, startup
from sibyl.config import get_settings
from sibyl.model_router import get_cost_stats

logger = logging.getLogger(__name__)

# ── Auth ──────────────────────────────────────────────────────

security = HTTPBearer(auto_error=False)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """Verify Bearer token if configured. Returns token or None."""
    settings = get_settings()

    # If no token set, skip auth
    if not settings.bearer_token:
        return None

    if credentials is None or credentials.credentials != settings.bearer_token:
        raise HTTPException(status_code=401, detail="Invalid or missing Bearer token")

    return credentials.credentials


# ── Request/Response Models ───────────────────────────────────


class ChatMessage(BaseModel):
    role: str = "user"
    content: str = ""


class ChatRequest(BaseModel):
    model: str = "sibyl-v1"
    messages: list[ChatMessage] = []
    temperature: float = 0.2
    max_tokens: int = 500


class PredictRequest(BaseModel):
    event_ticker: str = "unknown"
    market_ticker: str = "unknown"
    title: str = ""
    question: str = ""
    category: str = "Other"
    outcomes: list[str] = ["Yes", "No"]
    description: str = ""
    rules: str = ""
    close_time: str = ""


# ── Lifespan ──────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    startup()
    logger.info("🔮 Sibyl forecasting agent started")
    yield
    logger.info("Sibyl shutting down")


# ── FastAPI App ───────────────────────────────────────────────

app = FastAPI(
    title="Sibyl",
    description="Retrieval-augmented forecasting agent for Prophet Arena",
    version="1.0.0",
    lifespan=lifespan,
)


# ── POST /chat/completions ────────────────────────────────────


@app.post("/chat/completions")
async def chat_completions(
    request: ChatRequest,
    _token: str | None = Depends(verify_token),
) -> dict[str, Any]:
    """OpenAI-compatible endpoint for Prophet Arena auto-evaluation.

    Receives a chat request with event details in the user message,
    returns an OpenAI-shaped response with prediction in content.
    """
    # Extract the user prompt
    prompt = ""
    for msg in request.messages:
        if msg.role == "user":
            prompt = msg.content
            break

    if not prompt:
        raise HTTPException(status_code=400, detail="No user message found in request")

    # Run prediction
    result = await predict_from_prompt(prompt)

    # Format as OpenAI-compatible response
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(result),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(json.dumps(result).split()),
            "total_tokens": len(prompt.split()) + len(json.dumps(result).split()),
        },
    }


# ── POST /predict ─────────────────────────────────────────────


@app.post("/predict")
async def predict_endpoint(
    request: PredictRequest,
    _token: str | None = Depends(verify_token),
) -> dict[str, Any]:
    """CLI-compatible endpoint for prophet forecast predict --agent-url.

    Receives raw event JSON, returns prediction directly.
    """
    event = request.model_dump()

    # Support both "title" and "question" fields
    if not event.get("title") and event.get("question"):
        event["title"] = event["question"]

    if not event.get("title"):
        raise HTTPException(status_code=400, detail="Event must have a 'title' or 'question' field")

    result = await predict(event)
    return result


# ── GET /health ───────────────────────────────────────────────


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint for uptime monitoring."""
    return {"status": "healthy", "agent": "sibyl", "version": "1.0.0"}


# ── GET /stats ────────────────────────────────────────────────


@app.get("/stats")
async def stats() -> dict[str, Any]:
    """Cost and performance statistics."""
    return {
        "predictions": get_prediction_stats(),
        "costs": get_cost_stats(),
    }
