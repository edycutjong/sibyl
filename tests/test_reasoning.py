from unittest.mock import MagicMock

import pytest

from sibyl.reasoning import (
    _build_user_prompt,
    _fallback_prediction,
    _normalize_probabilities,
    reason,
)


def test_build_user_prompt():
    event = {
        "title": "Will it rain tomorrow?",
        "outcomes": ["Yes", "No"],
        "description": "Rain in London",
        "rules": "According to metoffice",
        "close_time": "2026-06-01",
    }
    context = "News says 90% chance of rain."
    market_data = {"found": True, "prices": {"Yes": 0.8, "No": 0.2}, "source": "test_anchor"}

    prompt = _build_user_prompt(event, context, market_data)

    assert "Will it rain tomorrow?" in prompt
    assert "Rain in London" in prompt
    assert "According to metoffice" in prompt
    assert "2026-06-01" in prompt
    assert "0.8" in prompt
    assert "test_anchor" in prompt
    assert "News says 90% chance of rain." in prompt


def test_build_user_prompt_minimal():
    event = {"title": "Will it rain tomorrow?"}
    prompt = _build_user_prompt(event, "", {"found": False})

    assert "Will it rain tomorrow?" in prompt
    assert "No market prices available" in prompt


def test_normalize_probabilities():
    # Clamp test
    probs1 = {"Yes": 1.5, "No": -0.5}
    norm1 = _normalize_probabilities(probs1, ["Yes", "No"])
    assert norm1 == {"Yes": 0.99, "No": 0.01}

    # Re-normalize test
    probs2 = {"Yes": 0.5, "No": 0.5, "Maybe": 0.5}
    norm2 = _normalize_probabilities(probs2, ["Yes", "No", "Maybe"])
    assert norm2 == {"Yes": 0.3333, "No": 0.3333, "Maybe": 0.3333}

    # Fill missing test
    probs3 = {"Yes": 0.9}
    norm3 = _normalize_probabilities(probs3, ["Yes", "No"])
    # 0.9 + 0.01 = 0.91 -> renormalize
    assert norm3["No"] > 0
    assert norm3["Yes"] + norm3["No"] == pytest.approx(1.0)


def test_fallback_prediction():
    event = {"outcomes": ["A", "B", "C"]}
    fallback = _fallback_prediction(event)

    assert fallback["model"] == "fallback"
    assert fallback["confidence"] == "low"
    assert fallback["probabilities"] == {"A": 0.3333, "B": 0.3333, "C": 0.3333}


@pytest.mark.asyncio
async def test_reason_success(mocker):
    # Mock Litellm
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"probabilities": {"Yes": 0.7, "No": 0.3}, "rationale": "Test", "confidence": "high"}'
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=10)

    mocker.patch("sibyl.reasoning.litellm.acompletion", return_value=mock_response)
    mocker.patch("sibyl.reasoning.log_cost")

    result = await reason({"title": "test"}, "context", {"found": False}, "test-model")

    assert result["probabilities"] == {"Yes": 0.7, "No": 0.3}
    assert result["rationale"] == "Test"
    assert result["confidence"] == "high"
    assert result["model"] == "test-model"


@pytest.mark.asyncio
async def test_reason_list_format(mocker):
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = '{"probabilities": [{"market": "Yes", "probability": 0.7}, {"market": "No", "probability": 0.3}]}'
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_response.usage = None

    mocker.patch("sibyl.reasoning.litellm.acompletion", return_value=mock_response)

    result = await reason({"title": "test"}, "context", {"found": False}, "test-model")
    assert result["probabilities"] == {"Yes": 0.7, "No": 0.3}


@pytest.mark.asyncio
async def test_reason_json_error(mocker, caplog):
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = 'Invalid JSON'
    mock_response.choices = [MagicMock(message=mock_message)]

    mocker.patch("sibyl.reasoning.litellm.acompletion", return_value=mock_response)

    result = await reason({"title": "test"}, "context", {"found": False}, "test-model")
    assert result["model"] == "fallback"
    assert "Failed to parse LLM JSON response" in caplog.text


@pytest.mark.asyncio
async def test_reason_markdown_strip(mocker):
    mock_response = MagicMock()
    mock_message = MagicMock()
    # Test stripping ``` without json
    mock_message.content = '```\n{"probabilities": {"Yes": 0.8, "No": 0.2}}\n```'
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_response.usage = None

    mocker.patch("sibyl.reasoning.litellm.acompletion", return_value=mock_response)

    result = await reason({"title": "test"}, "context", {"found": False}, "test-model")
    assert result["probabilities"] == {"Yes": 0.8, "No": 0.2}



@pytest.mark.asyncio
async def test_reason_exception(mocker, caplog):
    mocker.patch("sibyl.reasoning.litellm.acompletion", side_effect=Exception("API Error"))

    result = await reason({"title": "test"}, "context", {"found": False}, "test-model")
    assert result["model"] == "fallback"
    assert "LLM reasoning failed: API Error" in caplog.text
