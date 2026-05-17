"""Tests for sibyl.classifier — event category classification."""

from sibyl.classifier import CATEGORIES, classify_by_keywords


class TestKeywordClassifier:
    """Tests for keyword-based fallback classifier."""

    def test_sports_classification(self):
        """Should classify NBA game as Sports."""
        result = classify_by_keywords("Will the Lakers beat the Celtics in Game 5?")
        assert result == "Sports"

    def test_geopolitics_classification(self):
        """Should classify election question as Geopolitics."""
        result = classify_by_keywords("Will the president sign the trade treaty?")
        assert result == "Geopolitics"

    def test_economics_classification(self):
        """Should classify Fed question as Economics."""
        result = classify_by_keywords("Will the Fed raise interest rates?")
        assert result == "Economics"

    def test_science_classification(self):
        """Should classify SpaceX question as Science/Tech."""
        result = classify_by_keywords("Will SpaceX launch Starship successfully?")
        assert result == "Science/Tech"

    def test_pop_culture_classification(self):
        """Should classify Oscar question as Pop Culture."""
        result = classify_by_keywords("Will the movie win the Oscar for best picture?")
        assert result == "Pop Culture"

    def test_unknown_defaults_to_other(self):
        """Should return Other for unrecognizable events."""
        result = classify_by_keywords("Will the color of the sky be purple tomorrow?")
        assert result == "Other"

    def test_description_helps_classification(self):
        """Should use description to improve classification."""
        result = classify_by_keywords(
            "Who will win?",
            description="NBA playoffs basketball championship game",
        )
        assert result == "Sports"


class TestCategories:
    """Test category constants."""

    def test_all_categories_present(self):
        """Should have all 6 categories."""
        assert len(CATEGORIES) == 6
        assert "Sports" in CATEGORIES
        assert "Other" in CATEGORIES

import pytest

from sibyl.classifier import classify_event
from sibyl.config import Settings


@pytest.mark.asyncio
class TestClassifyEvent:
    """Tests for async classify_event function."""

    async def test_uses_category_hint(self):
        """Should bypass all logic if hint is a valid category."""
        res = await classify_event("Will it rain?", category_hint="Sports")
        assert res == "Sports"

    async def test_uses_cache(self, mocker):
        """Should return cached result if available."""
        mocker.patch("sibyl.classifier.get_cached", return_value="Geopolitics")
        res = await classify_event("Some event")
        assert res == "Geopolitics"

    async def test_uses_llm_success(self, mocker):
        """Should call LLM and cache result if valid."""
        mocker.patch("sibyl.classifier.get_cached", return_value=None)
        set_cached_mock = mocker.patch("sibyl.classifier.set_cached")

        settings_mock = mocker.patch("sibyl.classifier.get_settings")
        settings_mock.return_value = Settings(openai_api_key="fake", model_classifier="gpt-4o-mini")

        class MockMessage:
            content = "Sports"
        class MockChoice:
            message = MockMessage()
        class MockResponse:
            choices = [MockChoice()]

        mocker.patch("litellm.acompletion", return_value=MockResponse())
        res = await classify_event("NBA Finals")
        assert res == "Sports"
        set_cached_mock.assert_called_once()

    async def test_llm_failure_fallback(self, mocker):
        """Should fallback to keywords if LLM fails."""
        mocker.patch("sibyl.classifier.get_cached", return_value=None)
        mocker.patch("sibyl.classifier.set_cached")

        settings_mock = mocker.patch("sibyl.classifier.get_settings")
        settings_mock.return_value = Settings(openai_api_key="fake")

        mocker.patch("litellm.acompletion", side_effect=Exception("API down"))
        # Event has 'election' keyword
        res = await classify_event("election in 2024")
        assert res == "Geopolitics"

    async def test_no_api_key_fallback(self, mocker):
        """Should bypass LLM if no API key is configured."""
        mocker.patch("sibyl.classifier.get_cached", return_value=None)
        mocker.patch("sibyl.classifier.set_cached")

        settings_mock = mocker.patch("sibyl.classifier.get_settings")
        settings_mock.return_value = Settings(openai_api_key="")

        res = await classify_event("NBA Finals")
        assert res == "Sports"
