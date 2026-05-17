"""Tests for sibyl.agent — core prediction pipeline."""


from sibyl.agent import (
    _prediction_stats,
    get_prediction_stats,
    predict,
    startup,
)
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

    def test_medium_confidence_uses_default(self):
        from sibyl.model_router import select_model
        model = select_model(market_confidence=0.5, category="Sports")
        assert "mini" in model.lower() or "gpt-4o" in model.lower()


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


class TestAgentPipeline:
    """Tests for the main agent pipeline."""

    async def test_predict_binary(self, mocker):
        """Should return p_yes format for binary event."""
        # Clear stats
        _prediction_stats.clear()

        mocker.patch("sibyl.agent.classify_event", return_value="Sports")
        mocker.patch("sibyl.agent.retrieve_context", return_value=[])
        mocker.patch("sibyl.agent.get_market_anchor", return_value={"market": 0.6})
        mocker.patch("sibyl.agent.reason", return_value={
            "probabilities": {"Yes": 0.7, "No": 0.3},
            "rationale": "It's likely.",
            "model": "gpt-4o-mini"
        })

        event = {"title": "Will it happen?", "outcomes": ["Yes", "No"]}
        res = await predict(event)

        assert "probabilities" in res
        assert len(res["probabilities"]) == 2
        assert res["probabilities"][0]["market"] == "Yes"
        assert res["probabilities"][0]["probability"] == 0.7
        assert res["rationale"] == "It's likely."

        stats = get_prediction_stats()
        assert stats["total"] == 1
        assert stats["categories"]["Sports"] == 1

    async def test_predict_multi(self, mocker):
        """Should return probabilities list for multi-outcome."""
        mocker.patch("sibyl.agent.classify_event", return_value="Geopolitics")
        mocker.patch("sibyl.agent.retrieve_context", return_value=[])
        mocker.patch("sibyl.agent.get_market_anchor", return_value={})
        mocker.patch("sibyl.agent.reason", return_value={
            "probabilities": {"A": 0.5, "B": 0.3, "C": 0.2},
            "rationale": "Maybe A.",
            "model": "claude-sonnet-4-20250514"
        })

        event = {"title": "Who will win?", "outcomes": ["A", "B", "C"]}
        res = await predict(event)

        assert "probabilities" in res
        assert len(res["probabilities"]) == 3
        assert res["probabilities"][0]["market"] == "A"
        assert res["probabilities"][0]["probability"] == 0.5



    def test_startup(self, mocker):
        """Should initialize agent."""
        mock_load = mocker.patch("sibyl.agent.load_calibration_model")
        startup()
        mock_load.assert_called_once()

    def test_empty_stats(self):
        """Should return 0s when no stats."""
        _prediction_stats.clear()
        stats = get_prediction_stats()
        assert stats["total"] == 0
