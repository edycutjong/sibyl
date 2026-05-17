"""Sibyl — Market price anchor.

Attempts to look up current market prices for events.
Falls back to uniform prior if no market data available.
"""

from __future__ import annotations

import logging
from typing import Any

from sibyl.cache import cache_key, get_cached, set_cached

logger = logging.getLogger(__name__)


def get_uniform_prior(outcomes: list[str]) -> dict[str, float]:
    """Return uniform probability distribution across outcomes."""
    n = len(outcomes) if outcomes else 2
    prob = round(1.0 / n, 4)
    return {outcome: prob for outcome in (outcomes or ["Yes", "No"])}


async def get_market_anchor(
    event_ticker: str,
    title: str,
    outcomes: list[str],
) -> dict[str, Any]:
    """Attempt to fetch market price for an event.

    Currently returns uniform prior — market lookup can be added later
    for Kalshi/Polymarket/Metaculus scraping.

    Args:
        event_ticker: Event identifier
        title: Event title for search
        outcomes: List of possible outcomes

    Returns:
        Dict with 'prices' (outcome→probability), 'source', 'found'
    """
    # Check cache
    ck = cache_key("anchor", event_ticker)
    cached = get_cached(ck)
    if cached:
        return cached

    # For MVP: use uniform prior
    # Future: add Kalshi/Polymarket API lookups here
    prior = get_uniform_prior(outcomes)

    result = {
        "prices": prior,
        "source": "uniform_prior",
        "found": False,
    }

    set_cached(ck, result, ttl=300)
    logger.debug("Market anchor for '%s': %s", event_ticker, result["source"])
    return result


def anchor_confidence(market_data: dict[str, Any]) -> float:
    """Determine confidence level from market data.

    Returns a float 0.0-1.0 indicating how far the market is from 50/50.
    High values = market is very confident (lean on market more).
    Low values = market is uncertain (rely on agent analysis more).
    """
    if not market_data.get("found"):
        return 0.0

    prices = market_data.get("prices", {})
    if not prices:
        return 0.0

    max_price = max(prices.values())
    # Distance from uniform (0.5 for binary)
    n = len(prices)
    uniform = 1.0 / n
    confidence = abs(max_price - uniform) / (1.0 - uniform) if uniform < 1.0 else 0.0
    return round(min(confidence, 1.0), 4)
