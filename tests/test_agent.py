"""Tests for sibyl.agent — core prediction pipeline."""

import pytest

from sibyl.parser import normalize_event


class TestNormalizeEventPipeline:
    """Tests for event normalization in the pipeline."""

    def test_binary_event_structure(self, sample_event):
        """Should preserve binary event structure."""
        event = normalize_event(sample_event)
        assert len(event["outcomes"]) == 2
        assert "Yes" in event["outcomes"]
        assert "No" in event["outcomes"]

    def test_multi_outcome_structure(self, sample_multi_event):
        """Should preserve multi-outcome event structure."""
        event = normalize_event(sample_multi_event)
        assert len(event["outcomes"]) == 3
        assert "Democrat" in event["outcomes"]

    def test_category_preserved(self, sample_event):
        """Should preserve category from event data."""
        event = normalize_event(sample_event)
        assert event["category"] == "Sports"

    def test_missing_fields_default(self):
        """Should provide defaults for missing fields."""
        event = normalize_event({"title": "Test?"})
        assert event["event_ticker"] == "unknown"
        assert event["category"] == "Other"
        assert event["outcomes"] == ["Yes", "No"]


class TestModelRouting:
    """Tests for model routing logic."""

    def test_high_confidence_uses_mini(self):
        from sibyl.model_router import select_model
        model = select_model(market_confidence=0.90)
        assert "mini" in model.lower() or "gpt-4o" in model.lower()

    def test_low_confidence_uses_premium(self):
        from sibyl.model_router import select_model
        model = select_model(market_confidence=0.1, category="Geopolitics")
        assert "claude" in model.lower() or "sonnet" in model.lower()

    def test_medium_confidence_uses_flash(self):
        from sibyl.model_router import select_model
        model = select_model(market_confidence=0.5, category="Sports")
        assert "gemini" in model.lower() or "flash" in model.lower()


class TestCalibration:
    """Tests for calibration module."""

    def test_uncalibrated_passthrough(self):
        """Without a loaded model, raw probabilities pass through."""
        from sibyl.calibration import calibrate_probability
        assert calibrate_probability(0.7) == 0.7
        assert calibrate_probability(0.3) == 0.3

    def test_calibrate_predictions_passthrough(self):
        """Without model, dict probabilities pass through."""
        from sibyl.calibration import calibrate_predictions
        probs = {"Yes": 0.65, "No": 0.35}
        result = calibrate_predictions(probs)
        assert result == probs
