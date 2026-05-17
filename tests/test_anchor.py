import pytest

from sibyl.anchor import (
    _extract_prices,
    _fetch_kalshi_market,
    anchor_confidence,
    get_market_anchor,
    get_uniform_prior,
)


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


def test_extract_prices_binary():
    """Test price extraction for binary (yes/no) markets."""
    market_data = {"yes_price": 75, "no_price": 25}
    result = _extract_prices(market_data, ["Yes", "No"])
    assert result["Yes"] == 0.75
    assert result["No"] == 0.25


def test_extract_prices_low_price():
    """Test clamping at 0.01 minimum."""
    market_data = {"yes_price": 0}
    result = _extract_prices(market_data, ["Yes", "No"])
    assert result["Yes"] == 0.01
    assert result["No"] == pytest.approx(0.99, abs=0.001)


def test_extract_prices_high_price():
    """Test clamping at 0.99 maximum."""
    market_data = {"yes_price": 100}
    result = _extract_prices(market_data, ["Yes", "No"])
    assert result["Yes"] == 0.99
    assert result["No"] == pytest.approx(0.01, abs=0.001)


def test_extract_prices_last_price_fallback():
    """Test fallback to last_price when yes_price is None."""
    market_data = {"last_price": 60}
    result = _extract_prices(market_data, ["A", "B"])
    assert result["A"] == 0.6
    assert result["B"] == pytest.approx(0.4, abs=0.001)


def test_extract_prices_multi_outcome():
    """Test multi-outcome price distribution."""
    market_data = {"yes_price": 80}
    result = _extract_prices(market_data, ["A", "B", "C"])
    assert result["A"] == 0.8
    assert result["B"] == 0.1
    assert result["C"] == 0.1


def test_extract_prices_no_price_data():
    """Test fallback to uniform when no price fields are present."""
    market_data = {"status": "open", "volume": 1000}
    result = _extract_prices(market_data, ["Yes", "No"])
    assert result == {"Yes": 0.5, "No": 0.5}


@pytest.mark.asyncio
async def test_fetch_kalshi_market_success(mocker):
    """Test successful Kalshi API fetch."""
    mock_resp = mocker.MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"market": {"yes_price": 65, "no_price": 35}}

    mock_client = mocker.AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=False)

    mocker.patch("sibyl.anchor.httpx.AsyncClient", return_value=mock_client)

    result = await _fetch_kalshi_market("KXTEST-123")
    assert result == {"yes_price": 65, "no_price": 35}


@pytest.mark.asyncio
async def test_fetch_kalshi_market_404(mocker):
    """Test Kalshi API 404 returns None."""
    mock_resp = mocker.MagicMock()
    mock_resp.status_code = 404

    mock_client = mocker.AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=False)

    mocker.patch("sibyl.anchor.httpx.AsyncClient", return_value=mock_client)

    result = await _fetch_kalshi_market("KXTEST-NOTFOUND")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_kalshi_market_500(mocker):
    """Test Kalshi API 500 (other status code) returns None."""
    mock_resp = mocker.MagicMock()
    mock_resp.status_code = 500

    mock_client = mocker.AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=False)

    mocker.patch("sibyl.anchor.httpx.AsyncClient", return_value=mock_client)

    result = await _fetch_kalshi_market("KXTEST-500")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_kalshi_market_error(mocker):
    """Test Kalshi API network error returns None."""
    mock_client = mocker.AsyncMock()
    mock_client.get.side_effect = Exception("Connection refused")
    mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = mocker.AsyncMock(return_value=False)

    mocker.patch("sibyl.anchor.httpx.AsyncClient", return_value=mock_client)

    result = await _fetch_kalshi_market("KXTEST-ERR")
    assert result is None


@pytest.mark.asyncio
async def test_get_market_anchor_kalshi_success(mocker):
    """Test get_market_anchor with successful Kalshi lookup."""
    mocker.patch("sibyl.anchor.get_cached", return_value=None)
    mock_set_cached = mocker.patch("sibyl.anchor.set_cached")

    # Mock successful Kalshi fetch
    mocker.patch(
        "sibyl.anchor._fetch_kalshi_market",
        return_value={"yes_price": 70, "no_price": 30},
    )

    result = await get_market_anchor("KXTEST-123", "Test event", ["Yes", "No"])

    assert result["source"] == "kalshi"
    assert result["found"] is True
    assert result["prices"]["Yes"] == 0.7
    assert result["prices"]["No"] == pytest.approx(0.3, abs=0.001)

    mock_set_cached.assert_called_once()


@pytest.mark.asyncio
async def test_get_market_anchor_kalshi_fallback(mocker):
    """Test get_market_anchor falls back to uniform on Kalshi failure."""
    mocker.patch("sibyl.anchor.get_cached", return_value=None)
    mock_set_cached = mocker.patch("sibyl.anchor.set_cached")

    # Mock Kalshi failure
    mocker.patch("sibyl.anchor._fetch_kalshi_market", return_value=None)

    result = await get_market_anchor("KXTEST-FAIL", "Will something happen?", ["Yes", "No"])

    assert result["source"] == "uniform_prior"
    assert result["found"] is False
    assert result["prices"] == {"Yes": 0.5, "No": 0.5}

    mock_set_cached.assert_called_once()
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
