"""Sibyl — LLM reasoning engine.

Takes event data + retrieved context + market anchor and produces
calibrated probability predictions via structured LLM output.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

# Suppress noisy LiteLLM warnings (botocore, sagemaker)
os.environ.setdefault("LITELLM_LOG", "ERROR")
import litellm  # noqa: E402

litellm.suppress_debug_info = True

from sibyl.model_router import log_cost  # noqa: E402

logger = logging.getLogger(__name__)


_REASONING_SYSTEM_PROMPT = """You are Sibyl, an expert probabilistic forecasting agent. You estimate the probability of outcomes for prediction market events.

You will receive:
1. An event with a question and possible outcomes
2. Retrieved context from recent web searches
3. Market price data (if available)

Your task:
- Analyze ALL available evidence carefully
- Consider base rates, recent trends, and expert consensus
- Account for uncertainty — avoid extreme probabilities unless evidence is overwhelming
- Return calibrated probabilities that sum to 1.0

IMPORTANT RULES:
- Never return exactly 0.0 or 1.0 — use 0.01 minimum and 0.99 maximum
- For binary events (2 outcomes), probabilities must sum to 1.0
- For multi-outcome events, all probabilities must sum to 1.0
- Provide a clear, concise rationale (2-3 sentences)

Respond with ONLY a valid JSON object in this exact format:
{
  "probabilities": {"Outcome1": 0.65, "Outcome2": 0.35},
  "rationale": "Brief explanation of your reasoning based on the evidence.",
  "confidence": "high|medium|low"
}"""


def _build_user_prompt(
    event: dict[str, Any],
    context: str,
    market_data: dict[str, Any],
) -> str:
    """Build the user prompt for LLM reasoning."""
    outcomes_str = ", ".join(event.get("outcomes", ["Yes", "No"]))

    parts = [
        f"## Event\n**Question**: {event.get('title', 'Unknown')}\n**Outcomes**: {outcomes_str}",
    ]

    if event.get("description"):
        parts.append(f"**Description**: {event['description']}")

    if event.get("rules"):
        parts.append(f"**Resolution Rules**: {event['rules']}")

    if event.get("close_time"):
        parts.append(f"**Closes**: {event['close_time']}")

    # Market anchor
    if market_data.get("found"):
        prices_str = json.dumps(market_data["prices"], indent=2)
        parts.append(f"\n## Current Market Prices\n{prices_str}\nSource: {market_data['source']}")
    else:
        parts.append("\n## Market Data\nNo market prices available. Use your best judgment.")

    # Retrieved context
    parts.append(f"\n## Retrieved Context\n{context}")

    parts.append("\n## Task\nEstimate the probability of each outcome. Return ONLY a JSON object with 'probabilities', 'rationale', and 'confidence'.")

    return "\n".join(parts)


def _extract_json(content: str) -> dict[str, Any] | None:
    """Try multiple strategies to extract JSON from LLM output."""
    cleaned = content.strip()

    # Strategy 1: Extract from markdown code blocks if present anywhere
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 2: Strip markdown fences if they are at the edges
    stripped = re.sub(r"^```(?:json)?\s*", "", cleaned)
    stripped = re.sub(r"\s*```$", "", stripped)
    stripped = stripped.strip()

    # Strategy 3: Direct parse
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Strategy 4: Fix truncated JSON — close open strings and braces
    first_brace = stripped.find("{")
    if first_brace != -1:
        fragment = stripped[first_brace:]
        # Close any open string
        if fragment.count('"') % 2 != 0:
            fragment += '"'
        # Close open braces
        open_braces = fragment.count("{") - fragment.count("}")
        fragment += "}" * max(0, open_braces)
        try:
            return json.loads(fragment)
        except json.JSONDecodeError:
            pass

    # Strategy 5: Find outermost { ... } with balanced braces, searching all {
    start_idx = 0
    while True:
        brace_start = stripped.find("{", start_idx)
        if brace_start == -1:
            break

        depth = 0
        for i in range(brace_start, len(stripped)):
            if stripped[i] == "{":
                depth += 1
            elif stripped[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(stripped[brace_start : i + 1])
                    except json.JSONDecodeError:
                        break  # Not valid JSON at this brace_start, break inner loop
        start_idx = brace_start + 1

    # Strategy 6: Greedy regex (first { to last })
    last_brace = stripped.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(stripped[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    return None


async def reason(
    event: dict[str, Any],
    context: str,
    market_data: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    """Run LLM reasoning to produce probability predictions.

    Args:
        event: Normalized event dict
        context: Formatted context string from retrieval
        market_data: Market anchor data
        model: LLM model name (litellm format)

    Returns:
        Dict with 'probabilities' (outcome→float), 'rationale' (str), 'confidence' (str)
    """
    user_prompt = _build_user_prompt(event, context, market_data)

    for attempt in range(2):
        try:
            messages = [
                {"role": "system", "content": _REASONING_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]

            # On retry, add a stricter instruction
            if attempt > 0:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response was not valid JSON. "
                            "Respond with ONLY a raw JSON object — no markdown, no explanation, no code fences. "
                            "Start your response with { and end with }."
                        ),
                    }
                )
                logger.info("Retry %d with stricter JSON prompt", attempt)

            response = await litellm.acompletion(
                model=model,
                messages=messages,
                max_tokens=4096,
                temperature=0.2,
            )

            content = response.choices[0].message.content.strip()

            # Track cost
            usage = response.usage
            if usage:
                log_cost(model, usage.prompt_tokens, usage.completion_tokens)

            # Extract JSON with multiple strategies
            result = _extract_json(content)

            if result is None:
                if attempt == 0:
                    logger.warning("JSON extraction failed (attempt 1), retrying...")
                    logger.debug("Raw content: %s", content[:500])
                    continue
                else:
                    logger.error("JSON extraction failed after retry")
                    logger.error("Raw content: %s", content[:500])
                    return _fallback_prediction(event)

            # Validate and normalize probabilities
            probs = result.get("probabilities", {})
            if isinstance(probs, list):
                probs = {item["market"]: item["probability"] for item in probs}

            probs = _normalize_probabilities(probs, event.get("outcomes", ["Yes", "No"]))

            return {
                "probabilities": probs,
                "rationale": result.get("rationale", "No rationale provided."),
                "confidence": result.get("confidence", "medium"),
                "model": model,
            }

        except json.JSONDecodeError as _err:
            if attempt == 0:
                logger.warning("JSON parse error (attempt 1): %s", _err)
                continue
            logger.error("Failed to parse LLM JSON after retry: %s", _err)
            return _fallback_prediction(event)
        except Exception as _err:
            logger.error("LLM reasoning failed: %s", _err)
            return _fallback_prediction(event)

    return _fallback_prediction(event)  # pragma: no cover


def _normalize_probabilities(
    probs: dict[str, float],
    outcomes: list[str],
) -> dict[str, float]:
    """Ensure probabilities are valid and sum to 1.0.

    - Clamp to [0.01, 0.99]
    - Normalize to sum to 1.0
    - Fill missing outcomes
    """
    # Fill missing outcomes with small probability
    for outcome in outcomes:
        if outcome not in probs:
            probs[outcome] = 0.01

    # Clamp values
    for k in probs:
        probs[k] = max(0.01, min(0.99, float(probs[k])))

    # Normalize to sum to 1.0
    total = sum(probs.values())
    if total > 0 and abs(total - 1.0) > 0.001:
        probs = {k: round(v / total, 4) for k, v in probs.items()}

    return probs


def _fallback_prediction(event: dict[str, Any]) -> dict[str, Any]:
    """Return a safe fallback prediction when reasoning fails."""
    outcomes = event.get("outcomes", ["Yes", "No"])
    n = len(outcomes)
    uniform = round(1.0 / n, 4)
    return {
        "probabilities": {o: uniform for o in outcomes},
        "rationale": "Fallback: uniform distribution due to reasoning failure.",
        "confidence": "low",
        "model": "fallback",
    }
