from unittest.mock import AsyncMock, MagicMock

import pytest

from sibyl.retrieval import (
    build_search_query,
    format_context,
    retrieve_context,
    search_brave,
    search_exa,
)


def test_build_search_query():
    # Category with template
    assert build_search_query("Will team A win?", "Sports") == "team A win latest odds stats injury report predictions"

    # Fallback category
    assert build_search_query("Unknown thing?", "Unknown") == "Unknown thing latest information analysis"


@pytest.mark.asyncio
async def test_search_exa(mocker):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "results": [
            {"title": "Title 1", "url": "http://1", "text": "Text 1"},
            {"title": "Title 2", "url": "http://2", "text": "Text 2"},
        ]
    }
    mock_resp.raise_for_status = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_resp)

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mocker.patch("sibyl.retrieval.httpx.AsyncClient", return_value=mock_client)

    results = await search_exa("query", "key", limit=1)

    assert len(results) == 1
    assert results[0] == {"title": "Title 1", "url": "http://1", "text": "Text 1", "source": "exa"}


@pytest.mark.asyncio
async def test_search_brave(mocker):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "web": {
            "results": [
                {"title": "Title 1", "url": "http://1", "description": "Desc 1"},
                {"title": "Title 2", "url": "http://2", "description": "Desc 2"},
            ]
        }
    }
    mock_resp.raise_for_status = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(return_value=mock_resp)

    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    mocker.patch("sibyl.retrieval.httpx.AsyncClient", return_value=mock_client)

    results = await search_brave("query", "key", limit=1)

    assert len(results) == 1
    assert results[0] == {"title": "Title 1", "url": "http://1", "text": "Desc 1", "source": "brave"}


@pytest.mark.asyncio
async def test_retrieve_context_cached(mocker):
    cached_results = [{"title": "Cached"}]
    mocker.patch("sibyl.retrieval.get_cached", return_value=cached_results)

    results = await retrieve_context("test", "Other")
    assert results == cached_results


@pytest.mark.asyncio
async def test_retrieve_context_exa_success(mocker):
    mocker.patch("sibyl.retrieval.get_cached", return_value=None)
    mock_set_cached = mocker.patch("sibyl.retrieval.set_cached")

    mock_settings = MagicMock()
    mock_settings.exa_api_key = "exa_key"
    mock_settings.brave_api_key = None
    mocker.patch("sibyl.retrieval.get_settings", return_value=mock_settings)

    mock_results = [{"title": "Exa result"}]
    mocker.patch("sibyl.retrieval.search_exa", return_value=mock_results)

    results = await retrieve_context("test", "Other")
    assert results == mock_results
    mock_set_cached.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_context_exa_fail_brave_success(mocker):
    mocker.patch("sibyl.retrieval.get_cached", return_value=None)
    mock_set_cached = mocker.patch("sibyl.retrieval.set_cached")

    mock_settings = MagicMock()
    mock_settings.exa_api_key = "exa_key"
    mock_settings.brave_api_key = "brave_key"
    mocker.patch("sibyl.retrieval.get_settings", return_value=mock_settings)

    mocker.patch("sibyl.retrieval.search_exa", side_effect=Exception("Exa failed"))
    mock_brave_results = [{"title": "Brave result"}]
    mocker.patch("sibyl.retrieval.search_brave", return_value=mock_brave_results)

    results = await retrieve_context("test", "Other")
    assert results == mock_brave_results
    mock_set_cached.assert_called_once()


@pytest.mark.asyncio
async def test_retrieve_context_all_fail(mocker):
    mocker.patch("sibyl.retrieval.get_cached", return_value=None)

    mock_settings = MagicMock()
    mock_settings.exa_api_key = "exa_key"
    mock_settings.brave_api_key = "brave_key"
    mocker.patch("sibyl.retrieval.get_settings", return_value=mock_settings)

    mocker.patch("sibyl.retrieval.search_exa", side_effect=Exception("Exa failed"))
    mocker.patch("sibyl.retrieval.search_brave", side_effect=Exception("Brave failed"))

    results = await retrieve_context("test", "Other")
    assert results == []


@pytest.mark.asyncio
async def test_retrieve_context_no_keys(mocker):
    mocker.patch("sibyl.retrieval.get_cached", return_value=None)

    mock_settings = MagicMock()
    mock_settings.exa_api_key = None
    mock_settings.brave_api_key = None
    mocker.patch("sibyl.retrieval.get_settings", return_value=mock_settings)

    results = await retrieve_context("test", "Other")
    assert results == []


def test_format_context():
    # Empty
    assert format_context([]) == "No external context available."

    # Single result
    results = [{"title": "T1", "url": "U1", "text": "Text1"}]
    formatted = format_context(results)
    assert "[Source 1] T1" in formatted
    assert "Text1" in formatted
    assert "URL: U1" in formatted

    # Token limit
    long_text = "a" * 15000  # Will exceed 3000 tokens * 4 = 12000 chars
    results2 = [{"title": "T1", "url": "U1", "text": long_text}]
    formatted2 = format_context(results2, max_tokens=100) # 400 chars limit
    assert formatted2 == "" # Since the single snippet is larger than the limit, it breaks immediately

    results3 = [
        {"title": "T1", "url": "U1", "text": "Short"},
        {"title": "T2", "url": "U2", "text": long_text},
    ]
    formatted3 = format_context(results3, max_tokens=100)
    assert "T1" in formatted3
    assert "T2" not in formatted3
