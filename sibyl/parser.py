"""Sibyl — Event parser.

Extracts structured event data from either:
  A) Raw event JSON dict (from /predict endpoint)
  B) OpenAI chat prompt text with embedded event details (from /chat/completions)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def parse_event_from_prompt(prompt: str) -> dict[str, Any]:
    """Extract event data from a chat prompt string.

    The Prophet Arena sends event details embedded in the user message.
    We try multiple extraction strategies:
      1. JSON block in the prompt
      2. Key-value parsing from natural language
      3. Minimal fallback with just the title
    """
    # Strategy 1: Look for JSON block (```json ... ``` or raw {})
    json_match = re.search(r"```json?\s*\n?(.*?)\n?\s*```", prompt, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 2: Look for raw JSON object
    brace_match = re.search(r"\{[^{}]*\"(?:event_ticker|title|question)\"[^{}]*\}", prompt, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Try the entire prompt as JSON
    try:
        parsed = json.loads(prompt)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass

    # Strategy 4: Extract key fields from natural language
    event: dict[str, Any] = {}

    # Title / question
    title_match = re.search(
        r"(?:title|question|predict|forecast)[:\s]*[\"']?(.+?)[\"']?\s*(?:\n|$|outcomes|category)",
        prompt,
        re.IGNORECASE,
    )
    if title_match:
        event["title"] = title_match.group(1).strip().rstrip("?") + "?"
    else:
        # Use first line or first sentence as title
        first_line = prompt.strip().split("\n")[0].strip()
        event["title"] = first_line[:200]

    # Outcomes
    outcomes_match = re.search(
        r"outcomes?[:\s]*\[([^\]]+)\]", prompt, re.IGNORECASE
    )
    if outcomes_match:
        raw = outcomes_match.group(1)
        event["outcomes"] = [o.strip().strip("\"'") for o in raw.split(",")]
    else:
        # Default binary
        event["outcomes"] = ["Yes", "No"]

    # Category
    cat_match = re.search(r"category[:\s]*[\"']?(\w+)", prompt, re.IGNORECASE)
    if cat_match:
        event["category"] = cat_match.group(1)

    # Event ticker
    ticker_match = re.search(r"event_ticker[:\s]*[\"']?([A-Z0-9\-]+)", prompt, re.IGNORECASE)
    if ticker_match:
        event["event_ticker"] = ticker_match.group(1)

    # Market ticker
    market_match = re.search(r"market_ticker[:\s]*[\"']?([A-Z0-9\-]+)", prompt, re.IGNORECASE)
    if market_match:
        event["market_ticker"] = market_match.group(1)

    logger.debug("Parsed event from prompt: %s", event)
    return event


def normalize_event(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize an event dict to ensure all required fields exist."""
    return {
        "event_ticker": raw.get("event_ticker", raw.get("ticker", "unknown")),
        "market_ticker": raw.get("market_ticker", raw.get("event_ticker", "unknown")),
        "title": raw.get("title", raw.get("question", "Unknown event")),
        "category": raw.get("category", "Other"),
        "outcomes": raw.get("outcomes", ["Yes", "No"]),
        "description": raw.get("description", ""),
        "rules": raw.get("rules", ""),
        "close_time": raw.get("close_time", ""),
    }
