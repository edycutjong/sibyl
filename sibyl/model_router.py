"""Sibyl — Cost-tiered model selection.

Routes predictions to the cheapest suitable model based on
market confidence and question complexity.
"""

from __future__ import annotations

import logging

from sibyl.config import get_settings

logger = logging.getLogger(__name__)


def select_model(
    market_confidence: float,
    category: str = "Other",
) -> str:
    """Select the cheapest suitable LLM model for a prediction.

    Routing logic:
      - High confidence (market >85% or <15%): GPT-4o-mini (~$0.0001/q)
      - Medium confidence (15-85%): Gemini Flash (~$0.001/q)
      - Low confidence (40-60%, complex): Claude Sonnet 4 (~$0.005/q)

    Args:
        market_confidence: 0.0-1.0 (how confident the market is)
        category: Event category for complexity heuristics

    Returns:
        Model name string compatible with litellm
    """
    settings = get_settings()

    # High confidence — cheapest model is sufficient
    if market_confidence >= settings.high_confidence_threshold:
        model = settings.model_high_confidence
        tier = "high"

    # Low confidence — complex, ambiguous questions need best reasoning
    elif market_confidence <= (1.0 - settings.low_confidence_threshold):
        # Extra: Geopolitics and Economics tend to be nuanced
        if category in ("Geopolitics", "Economics"):
            model = settings.model_low_confidence
            tier = "low"
        else:
            model = settings.model_medium_confidence
            tier = "medium"

    # Medium confidence — balanced cost/quality
    else:
        model = settings.model_medium_confidence
        tier = "medium"

    logger.info(
        "Model selection: confidence=%.2f, category=%s → %s (%s tier)",
        market_confidence, category, model, tier,
    )
    return model


# ── Cost tracking ─────────────────────────────────────────────

_cost_log: list[dict] = []


def log_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Log the cost of a prediction and return estimated USD cost."""
    # Approximate costs per 1M tokens (input/output)
    cost_map = {
        "gpt-4o-mini": (0.15, 0.60),
        "gemini/gemini-2.5-flash-preview-05-20": (0.15, 0.60),
        "claude-sonnet-4-20250514": (3.00, 15.00),
    }

    input_rate, output_rate = cost_map.get(model, (1.0, 3.0))
    cost = (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000

    _cost_log.append({
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": round(cost, 6),
    })

    return round(cost, 6)


def get_total_cost() -> float:
    """Return total USD spent across all predictions."""
    return round(sum(e["cost_usd"] for e in _cost_log), 4)


def get_cost_stats() -> dict:
    """Return cost statistics."""
    if not _cost_log:
        return {"total_usd": 0.0, "predictions": 0, "avg_cost": 0.0}

    total = get_total_cost()
    return {
        "total_usd": total,
        "predictions": len(_cost_log),
        "avg_cost": round(total / len(_cost_log), 6),
        "by_model": {},
    }
