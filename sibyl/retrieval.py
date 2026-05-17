"""Sibyl — Web search retrieval.

Category-aware search using Exa or Brave APIs.
Falls back gracefully to empty context on failure.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from sibyl.cache import cache_key, get_cached, set_cached
from sibyl.config import get_settings

logger = logging.getLogger(__name__)


# ── Category-specific query templates ────────────────────────

_QUERY_TEMPLATES: dict[str, str] = {
    "Sports": "{title} latest odds stats injury report predictions",
    "Geopolitics": "{title} latest news analysis expert opinion",
    "Economics": "{title} forecast data economic indicator consensus",
    "Science/Tech": "{title} latest research news breakthrough update",
    "Pop Culture": "{title} predictions trends news update",
    "Other": "{title} latest information analysis",
}


def build_search_query(title: str, category: str) -> str:
    """Build a category-aware search query from the event title."""
    template = _QUERY_TEMPLATES.get(category, _QUERY_TEMPLATES["Other"])
    # Clean the title — remove "Will" prefix, question marks
    clean_title = title.strip().removeprefix("Will ").rstrip("?").strip()
    return template.format(title=clean_title)


async def search_exa(query: str, api_key: str, limit: int = 3) -> list[dict[str, Any]]:
    """Search using the Exa API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://api.exa.ai/search",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "query": query,
                "num_results": limit,
                "use_autoprompt": True,
                "type": "neural",
                "contents": {"text": {"max_characters": 1000}},
            },
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", [])[:limit]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "text": item.get("text", "")[:1000],
            "source": "exa",
        })
    return results


async def search_brave(query: str, api_key: str, limit: int = 3) -> list[dict[str, Any]]:
    """Search using the Brave Search API."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": api_key},
            params={"q": query, "count": limit},
        )
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("web", {}).get("results", [])[:limit]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "text": item.get("description", "")[:1000],
            "source": "brave",
        })
    return results


async def retrieve_context(
    title: str,
    category: str,
    description: str = "",
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Retrieve relevant context for an event.

    Uses category-aware query building and searches via Exa or Brave.
    Returns empty list on failure (agent continues with LLM-only).

    Args:
        title: Event title/question
        category: Classified category
        description: Optional event description
        limit: Max results to return

    Returns:
        List of search result dicts with title, url, text, source
    """
    # Check cache
    ck = cache_key("search", {"title": title, "category": category})
    cached = get_cached(ck)
    if cached:
        logger.debug("Search cache hit for '%s'", title[:60])
        return cached

    query = build_search_query(title, category)
    settings = get_settings()
    results: list[dict[str, Any]] = []

    # Try Exa first (best for news/events)
    if settings.exa_api_key:
        try:
            results = await search_exa(query, settings.exa_api_key, limit)
            if results:
                logger.info("Retrieved %d results from Exa for '%s'", len(results), title[:60])
                set_cached(ck, results, ttl=300)
                return results
        except Exception as _err:
            logger.warning("Exa search failed: %s", _err)

    # Try Brave as fallback
    if settings.brave_api_key:
        try:
            results = await search_brave(query, settings.brave_api_key, limit)
            if results:
                logger.info("Retrieved %d results from Brave for '%s'", len(results), title[:60])
                set_cached(ck, results, ttl=300)
                return results
        except Exception as _err:
            logger.warning("Brave search failed: %s", _err)

    # Graceful fallback — agent will proceed with LLM-only
    logger.info("No search results for '%s' — proceeding without context", title[:60])
    return []


def format_context(results: list[dict[str, Any]], max_tokens: int = 3000) -> str:
    """Format search results into a context string for the LLM prompt.

    Args:
        results: List of search result dicts
        max_tokens: Approximate character limit (1 token ≈ 4 chars)

    Returns:
        Formatted context string
    """
    if not results:
        return "No external context available."

    parts: list[str] = []
    char_limit = max_tokens * 4
    current_chars = 0

    for i, r in enumerate(results, 1):
        snippet = f"[Source {i}] {r['title']}\n{r['text']}\nURL: {r['url']}\n"
        if current_chars + len(snippet) > char_limit:
            break
        parts.append(snippet)
        current_chars += len(snippet)

    return "\n---\n".join(parts)
