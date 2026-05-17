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
