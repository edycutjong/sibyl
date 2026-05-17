from unittest.mock import MagicMock

import pytest

from sibyl import model_router
from sibyl.model_router import get_cost_stats, get_total_cost, log_cost, select_model


@pytest.fixture(autouse=True)
def reset_cost_log():
    model_router._cost_log = []
    yield
    model_router._cost_log = []


def test_select_model_high_confidence(mocker):
    mock_settings = MagicMock()
    mock_settings.high_confidence_threshold = 0.8
    mock_settings.model_high_confidence = "cheap-model"
    mocker.patch("sibyl.model_router.get_settings", return_value=mock_settings)

    assert select_model(0.85, "Sports") == "cheap-model"
    assert select_model(0.80, "Sports") == "cheap-model"


def test_select_model_low_confidence_complex(mocker):
    mock_settings = MagicMock()
    mock_settings.high_confidence_threshold = 0.8
    mock_settings.low_confidence_threshold = 0.6
    mock_settings.model_low_confidence = "expensive-model"
    mocker.patch("sibyl.model_router.get_settings", return_value=mock_settings)

    # 1.0 - 0.6 = 0.4
    assert select_model(0.3, "Geopolitics") == "expensive-model"
    assert select_model(0.4, "Economics") == "expensive-model"


def test_select_model_low_confidence_simple(mocker):
    mock_settings = MagicMock()
    mock_settings.high_confidence_threshold = 0.8
    mock_settings.low_confidence_threshold = 0.6
    mock_settings.model_medium_confidence = "medium-model"
    mocker.patch("sibyl.model_router.get_settings", return_value=mock_settings)

    assert select_model(0.3, "Sports") == "medium-model"


def test_select_model_medium_confidence(mocker):
    mock_settings = MagicMock()
    mock_settings.high_confidence_threshold = 0.8
    mock_settings.low_confidence_threshold = 0.6
    mock_settings.model_medium_confidence = "medium-model"
    mocker.patch("sibyl.model_router.get_settings", return_value=mock_settings)

    # Between 0.4 and 0.8
    assert select_model(0.5, "Sports") == "medium-model"
    assert select_model(0.5, "Geopolitics") == "medium-model"


def test_log_cost():
    # Known model
    cost1 = log_cost("gpt-4o-mini", 1000, 1000)
    assert cost1 == round((1000 * 0.15 + 1000 * 0.60) / 1000000, 6)

    # Unknown model (fallback rates)
    cost2 = log_cost("unknown", 1000, 1000)
    assert cost2 == round((1000 * 1.0 + 1000 * 3.0) / 1000000, 6)


def test_get_total_cost():
    log_cost("unknown", 1000000, 0)  # cost 1.0
    log_cost("unknown", 0, 1000000)  # cost 3.0
    assert get_total_cost() == 4.0


def test_get_cost_stats():
    # Empty
    assert get_cost_stats() == {"total_usd": 0.0, "predictions": 0, "avg_cost": 0.0}

    # With data
    log_cost("unknown", 1000000, 0)  # cost 1.0
    log_cost("unknown", 0, 1000000)  # cost 3.0
    stats = get_cost_stats()

    assert stats["total_usd"] == 4.0
    assert stats["predictions"] == 2
    assert stats["avg_cost"] == 2.0
    assert stats["by_model"] == {}
