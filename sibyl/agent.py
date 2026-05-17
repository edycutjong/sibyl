"""Sibyl — Core forecasting agent.

The full prediction pipeline:
  Parse → Classify → Retrieve → Anchor → Select Model → Reason → Calibrate → Format

This module provides:
  - predict(event) → dict : CLI-compatible entry point
  - predict_from_prompt(prompt) → dict : OpenAI-compatible entry point
"""

from __future__ import annotations

import logging
import time
from typing import Any

from sibyl.anchor import anchor_confidence, get_market_anchor
from sibyl.calibration import calibrate_predictions, load_calibration_model
from sibyl.classifier import classify_event
from sibyl.model_router import select_model
from sibyl.parser import normalize_event, parse_event_from_prompt
from sibyl.reasoning import reason
from sibyl.retrieval import format_context, retrieve_context

logger = logging.getLogger(__name__)

# ── Stats tracking ────────────────────────────────────────────

_prediction_stats: list[dict] = []


def get_prediction_stats() -> dict:
    """Return aggregate prediction statistics."""
    if not _prediction_stats:
        return {"total": 0, "avg_latency_ms": 0, "categories": {}}

    total = len(_prediction_stats)
    avg_latency = sum(s["latency_ms"] for s in _prediction_stats) / total

    categories: dict[str, int] = {}
    for s in _prediction_stats:
        cat = s.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    return {
        "total": total,
        "avg_latency_ms": round(avg_latency),
        "categories": categories,
    }


# ── Main prediction pipeline ─────────────────────────────────


async def predict(event: dict[str, Any]) -> dict[str, Any]:
    """Core prediction pipeline. CLI-compatible entry point.

    This is the function that `prophet forecast predict --local sibyl.agent`
    will call directly.

    Args:
        event: Raw event dict with at least 'title' and 'outcomes'

    Returns:
        Dict with EITHER:
          - {"p_yes": float, "rationale": str} for binary events
          - {"probabilities": list[dict], "rationale": str} for multi-outcome
    """
    start = time.monotonic()

    # Step 1: Normalize event
    event = normalize_event(event)
    title = event["title"]
    outcomes = event["outcomes"]
    logger.info("─── Predicting: %s ───", title[:80])

    # Step 2: Classify category
    category = await classify_event(
        title=title,
        description=event.get("description", ""),
        category_hint=event.get("category", ""),
    )
    logger.info("Category: %s", category)

    # Step 3: Retrieve context
    search_results = await retrieve_context(
        title=title,
        category=category,
        description=event.get("description", ""),
    )
    context = format_context(search_results)

    # Step 4: Get market anchor
    market_data = await get_market_anchor(
        event_ticker=event.get("event_ticker", "unknown"),
        title=title,
        outcomes=outcomes,
    )
    confidence = anchor_confidence(market_data)

    # Step 5: Select model based on confidence + category
    model = select_model(market_confidence=confidence, category=category)

    # Step 6: LLM reasoning
    result = await reason(
        event=event,
        context=context,
        market_data=market_data,
        model=model,
    )

    # Step 7: Calibrate probabilities
    calibrated = calibrate_predictions(result["probabilities"])

    # Step 8: Format response
    latency_ms = round((time.monotonic() - start) * 1000)
    logger.info("Prediction complete in %dms", latency_ms)

    # Track stats
    _prediction_stats.append({
        "title": title[:60],
        "category": category,
        "model": result.get("model", "unknown"),
        "latency_ms": latency_ms,
    })

    # Format based on outcome count
    is_binary = len(outcomes) == 2 and "Yes" in outcomes and "No" in outcomes

    if is_binary:
        p_yes = calibrated.get("Yes", 0.5)
        return {
            "p_yes": round(max(0.01, min(0.99, p_yes)), 4),
            "rationale": result.get("rationale", ""),
        }
    else:
        # Multi-outcome format: list of {market, probability}
        prob_list = [
            {"market": outcome, "probability": round(calibrated.get(outcome, 0.01), 4)}
            for outcome in outcomes
        ]
        return {
            "probabilities": prob_list,
            "rationale": result.get("rationale", ""),
        }


async def predict_from_prompt(prompt: str) -> dict[str, Any]:
    """Extract event from a chat prompt and run prediction.

    This is the entry point for the OpenAI-compatible /chat/completions endpoint.

    Args:
        prompt: User message content from the chat request

    Returns:
        Same format as predict()
    """
    event = parse_event_from_prompt(prompt)
    return await predict(event)


# ── Startup ────────────────────────────────────────────────────

def startup() -> None:
    """Initialize the agent (load calibration model, etc.)."""
    load_calibration_model()
    logger.info("Sibyl agent initialized")
