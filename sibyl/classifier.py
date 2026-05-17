"""Sibyl — Category classifier.

Classifies events into domain categories for targeted retrieval.
Uses GPT-4o-mini with few-shot examples, with keyword-based fallback.
"""

from __future__ import annotations

import logging
import re

import litellm

from sibyl.cache import cache_key, get_cached, set_cached
from sibyl.config import get_settings

logger = logging.getLogger(__name__)

CATEGORIES = ["Sports", "Geopolitics", "Economics", "Science/Tech", "Pop Culture", "Other"]

# ── Keyword-based fallback classifier ─────────────────────────
_KEYWORD_MAP: dict[str, list[str]] = {
    "Sports": [
        "nba", "nfl", "mlb", "nhl", "soccer", "football", "basketball", "baseball",
        "hockey", "tennis", "golf", "ufc", "mma", "boxing", "olympics", "world cup",
        "playoffs", "championship", "game", "match", "season", "team", "player",
        "coach", "score", "win", "beat", "defeat", "standings", "draft", "mvp",
        "super bowl", "world series", "stanley cup", "premier league", "la liga",
    ],
    "Geopolitics": [
        "election", "president", "congress", "senate", "vote", "policy", "war",
        "conflict", "sanctions", "nato", "un", "treaty", "diplomatic", "government",
        "minister", "parliament", "referendum", "military", "geopolit", "summit",
        "ceasefire", "tariff", "trade war", "border", "invasion", "coup",
    ],
    "Economics": [
        "fed", "interest rate", "inflation", "cpi", "gdp", "unemployment", "jobs",
        "economy", "recession", "stock", "market", "dow", "s&p", "nasdaq", "oil",
        "gas", "commodity", "treasury", "bond", "yield", "fomc", "bls", "housing",
        "mortgage", "bitcoin", "crypto", "ethereum", "currency", "forex",
    ],
    "Science/Tech": [
        "ai", "artificial intelligence", "spacex", "nasa", "launch", "climate",
        "vaccine", "fda", "drug", "trial", "research", "breakthrough", "quantum",
        "robot", "autonomous", "tech", "apple", "google", "microsoft", "openai",
        "model", "chip", "semiconductor", "fusion", "gene", "crispr", "mars",
    ],
    "Pop Culture": [
        "oscar", "grammy", "emmy", "movie", "film", "album", "song", "celebrity",
        "award", "show", "streaming", "netflix", "disney", "tiktok", "viral",
        "reality tv", "bachelor", "survivor", "concert", "tour", "box office",
    ],
}


def classify_by_keywords(title: str, description: str = "") -> str:
    """Fast keyword-based classification (no API call)."""
    text = f"{title} {description}".lower()
    scores: dict[str, int] = {cat: 0 for cat in CATEGORIES}

    for category, keywords in _KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text:
                scores[category] += 1

    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best if scores[best] > 0 else "Other"


_FEW_SHOT_EXAMPLES = """Classify the event into exactly one category.

Categories: Sports, Geopolitics, Economics, Science/Tech, Pop Culture, Other

Examples:
- "Will the Lakers beat the Celtics in Game 5?" → Sports
- "Will Russia withdraw from occupied territories by December?" → Geopolitics
- "Will the Fed raise interest rates at the June FOMC meeting?" → Economics
- "Will SpaceX successfully land Starship on its next attempt?" → Science/Tech
- "Will Taylor Swift's album break first-week streaming records?" → Pop Culture
- "Will it rain in San Francisco tomorrow?" → Other

Now classify this event. Return ONLY the category name, nothing else."""


async def classify_event(
    title: str,
    description: str = "",
    category_hint: str = "",
) -> str:
    """Classify an event into a domain category.

    Args:
        title: Event title/question
        description: Optional description
        category_hint: Optional pre-assigned category from the event data

    Returns:
        Category string from CATEGORIES
    """
    # If the event already has a valid category, trust it
    if category_hint and category_hint in CATEGORIES:
        return category_hint

    # Check cache
    ck = cache_key("classify", {"title": title})
    cached = get_cached(ck)
    if cached:
        return cached

    settings = get_settings()

    # Try LLM classification
    if settings.openai_api_key:
        try:
            response = await litellm.acompletion(
                model=settings.model_classifier,
                messages=[
                    {"role": "system", "content": _FEW_SHOT_EXAMPLES},
                    {"role": "user", "content": f"Event: \"{title}\"\nDescription: \"{description}\""},
                ],
                max_tokens=20,
                temperature=0.0,
            )
            result = response.choices[0].message.content.strip()

            # Validate the result
            for cat in CATEGORIES:
                if cat.lower() in result.lower():
                    set_cached(ck, cat, ttl=3600)
                    logger.info("Classified '%s' → %s (LLM)", title[:60], cat)
                    return cat

        except Exception as _err:
            logger.warning("LLM classification failed, falling back: %s", _err)

    # Fallback to keyword-based
    result = classify_by_keywords(title, description)
    set_cached(ck, result, ttl=3600)
    logger.info("Classified '%s' → %s (keywords)", title[:60], result)
    return result
