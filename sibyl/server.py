"""Sibyl — FastAPI server with dual endpoints.

Endpoints:
  POST /predict           — Prophet Arena prediction endpoint (accepts event JSON)
  GET  /health            — Uptime check
  GET  /stats             — Cost/latency monitoring
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sibyl.agent import get_prediction_stats, predict, startup
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

# Mount public directory for static assets
app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/")
async def root():
    """Serve the static pitch deck landing page."""
    return FileResponse("public/index.html")





# ── POST /predict ─────────────────────────────────────────────


@app.post("/predict")
async def predict_endpoint(
    request: PredictRequest,
    _token: str | None = Depends(verify_token),
) -> dict[str, Any]:
    """Prophet Arena prediction endpoint.

    Receives raw event JSON, returns prediction probabilities directly.
    """
    event = request.model_dump()

    # Support both "title" and "question" fields
    if not event.get("title") and event.get("question"):
        event["title"] = event["question"]

    if not event.get("title"):
        raise HTTPException(status_code=400, detail="Event must have a 'title' or 'question' field")

    result = await predict(event)
    return result


# ── POST /chat/completions ────────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]

@app.post("/chat/completions")
async def chat_completions(
    request: ChatRequest,
    _token: str | None = Depends(verify_token),
) -> dict[str, Any]:
    """OpenAI-compatible chat completions endpoint."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages list cannot be empty")

    prompt = request.messages[0].content
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt content cannot be empty")

    from sibyl.parser import normalize_event, parse_event_from_prompt

    raw_event = parse_event_from_prompt(prompt)
    event = normalize_event(raw_event)

    result = await predict(event)

    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": json.dumps(result)
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


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
