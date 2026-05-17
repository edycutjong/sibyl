import pytest

from sibyl.anchor import anchor_confidence, get_market_anchor, get_uniform_prior


def test_get_uniform_prior():
    # Test with empty/None
    assert get_uniform_prior([]) == {"Yes": 0.5, "No": 0.5}
    assert get_uniform_prior(None) == {"Yes": 0.5, "No": 0.5}

    # Test with 2 outcomes
    assert get_uniform_prior(["A", "B"]) == {"A": 0.5, "B": 0.5}

    # Test with 3 outcomes
    assert get_uniform_prior(["A", "B", "C"]) == {"A": 0.3333, "B": 0.3333, "C": 0.3333}

    # Test with 1 outcome (edge case)
    assert get_uniform_prior(["A"]) == {"A": 1.0}


@pytest.mark.asyncio
async def test_get_market_anchor(mocker):
    # Mock the cache module to prevent interfering with real cache or other tests
    mocker.patch("sibyl.anchor.get_cached", return_value=None)
    mock_set_cached = mocker.patch("sibyl.anchor.set_cached")

    result = await get_market_anchor("EVT-123", "Will something happen?", ["Yes", "No"])

    assert result["source"] == "uniform_prior"
    assert result["found"] is False
    assert result["prices"] == {"Yes": 0.5, "No": 0.5}

    # Verify set_cached was called
    mock_set_cached.assert_called_once()
    assert mock_set_cached.call_args[0][0].startswith("anchor:")
    assert mock_set_cached.call_args[0][1] == result
    assert mock_set_cached.call_args[1]["ttl"] == 300


@pytest.mark.asyncio
async def test_get_market_anchor_cached(mocker):
    cached_result = {"source": "cache", "found": True, "prices": {"Yes": 0.8, "No": 0.2}}
    mocker.patch("sibyl.anchor.get_cached", return_value=cached_result)

    result = await get_market_anchor("EVT-123", "Test", [])
    assert result == cached_result


def test_anchor_confidence():
    # Test not found
    assert anchor_confidence({"found": False}) == 0.0
    assert anchor_confidence({}) == 0.0

    # Test found but empty prices
    assert anchor_confidence({"found": True, "prices": {}}) == 0.0

    # Test uniform prior (confidence 0)
    assert anchor_confidence({"found": True, "prices": {"A": 0.5, "B": 0.5}}) == 0.0

    # Test complete certainty (confidence 1)
    assert anchor_confidence({"found": True, "prices": {"A": 1.0, "B": 0.0}}) == 1.0

    # Test multi-outcome certainty
    assert anchor_confidence({"found": True, "prices": {"A": 0.8, "B": 0.1, "C": 0.1}}) == 0.7

    # Test multi-outcome uniform
    assert anchor_confidence({"found": True, "prices": {"A": 0.3333, "B": 0.3333, "C": 0.3333}}) == 0.0

    # Test single outcome
    assert anchor_confidence({"found": True, "prices": {"A": 1.0}}) == 0.0
