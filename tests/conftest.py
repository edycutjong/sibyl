"""Shared test fixtures for Sibyl."""

import pytest


@pytest.fixture
def sample_event() -> dict:
    """A standard binary sports event."""
    return {
        "event_ticker": "NBA-2026-FINALS",
        "market_ticker": "NBA-2026-FINALS-G5",
        "title": "Will the Lakers beat the Celtics in Game 5?",
        "category": "Sports",
        "outcomes": ["Yes", "No"],
        "description": "NBA Finals 2026 Game 5 prediction.",
        "close_time": "2026-06-15T00:00:00Z",
    }


@pytest.fixture
def sample_multi_event() -> dict:
    """A multi-outcome geopolitical event."""
    return {
        "event_ticker": "POTUS-2028",
        "market_ticker": "POTUS-2028-WINNER",
        "title": "Who will win the 2028 US Presidential Election?",
        "category": "Geopolitics",
        "outcomes": ["Democrat", "Republican", "Third Party"],
        "description": "2028 US Presidential Election winner prediction.",
        "close_time": "2028-11-05T00:00:00Z",
    }


@pytest.fixture
def sample_chat_prompt() -> str:
    """A sample OpenAI-format chat prompt with embedded event."""
    return '''Please predict the following event:
{
  "event_ticker": "FED-JUNE-2026",
  "market_ticker": "FED-JUNE-2026-HIKE",
  "title": "Will the Fed raise interest rates at the June 2026 FOMC meeting?",
  "category": "Economics",
  "outcomes": ["Yes", "No"],
  "close_time": "2026-06-15T00:00:00Z"
}'''
