"""Sibyl — Market price anchor.

Fetches real market prices from Kalshi's public API.
Falls back to uniform prior if no market data available.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from sibyl.cache import cache_key, get_cached, set_cached

logger = logging.getLogger(__name__)

# Kalshi public API (no auth required for market reads)
_KALSHI_API_BASE = "https://api.elections.kalshi.com/trade-api/v2"


def get_uniform_prior(outcomes: list[str]) -> dict[str, float]:
    """Return uniform probability distribution across outcomes."""
    n = len(outcomes) if outcomes else 2
    prob = round(1.0 / n, 4)
    return {outcome: prob for outcome in (outcomes or ["Yes", "No"])}


async def _fetch_kalshi_market(ticker: str) -> dict[str, Any] | None:
    """Fetch market data from Kalshi's public API.

    Returns market dict or None on failure.
    """
    url = f"{_KALSHI_API_BASE}/markets/{ticker}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("market", data)
            elif resp.status_code == 404:
                logger.debug("Kalshi market not found: %s", ticker)
                return None
            else:
                logger.warning("Kalshi API returned %d for %s", resp.status_code, ticker)
                return None
    except Exception as _err:
        logger.warning("Kalshi API request failed: %s", _err)
        return None


def _extract_prices(
    market_data: dict[str, Any],
    outcomes: list[str],
) -> dict[str, float]:
    """Extract outcome probabilities from Kalshi market data.

    Kalshi prices are in cents (0-100). Convert to probability (0.0-1.0).
    Binary markets have yes_price/no_price. Multi-outcome need different handling.
    """
    yes_price = market_data.get("yes_price")
    if yes_price is None:
        yes_price = market_data.get("last_price")
    no_price = market_data.get("no_price")

    if yes_price is not None:
        # Kalshi prices are in cents (1-99) → convert to probability
        p_yes = max(0.01, min(0.99, yes_price / 100.0))
        p_no = 1.0 - p_yes

        # Map to outcomes
        if len(outcomes) == 2:
            return {outcomes[0]: round(p_yes, 4), outcomes[1]: round(p_no, 4)}
        else:
            # For multi-outcome, distribute remaining probability uniformly
            prices = {outcomes[0]: round(p_yes, 4)}
            remaining = 1.0 - p_yes
            per_other = round(remaining / max(1, len(outcomes) - 1), 4)
            for outcome in outcomes[1:]:
                prices[outcome] = per_other
            return prices

    return get_uniform_prior(outcomes)


async def get_market_anchor(
    event_ticker: str,
    title: str,
    outcomes: list[str],
) -> dict[str, Any]:
    """Fetch market price for an event from Kalshi.

    Tries the Kalshi public API first, falls back to uniform prior
    if the market isn't found or the API is unreachable.

    Args:
        event_ticker: Kalshi-format event ticker (e.g., KXNBAGAME-26MAY15DETCLE)
        title: Event title (unused, for logging)
        outcomes: List of possible outcomes

    Returns:
        Dict with 'prices' (outcome→probability), 'source', 'found'
    """
    # Check cache
    ck = cache_key("anchor", event_ticker)
    cached = get_cached(ck)
    if cached:
        return cached

    # Try Kalshi API for real market prices
    market = await _fetch_kalshi_market(event_ticker)

    if market is not None:
        prices = _extract_prices(market, outcomes)
        result = {
            "prices": prices,
            "source": "kalshi",
            "found": True,
        }
        logger.info(
            "Market anchor for '%s': Kalshi prices %s",
            event_ticker,
            {k: f"{v:.2%}" for k, v in prices.items()},
        )
    else:
        # Graceful fallback — uniform prior
        result = {
            "prices": get_uniform_prior(outcomes),
            "source": "uniform_prior",
            "found": False,
        }
        logger.debug("Market anchor for '%s': uniform prior (Kalshi unavailable)", event_ticker)

    set_cached(ck, result, ttl=300)
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
