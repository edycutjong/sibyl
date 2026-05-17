from unittest.mock import MagicMock

import pytest

from sibyl.reasoning import (
    _build_user_prompt,
    _extract_json,
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
    mock_message.content = 'Invalid JSON with no braces at all'
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_response.usage = None

    mocker.patch("sibyl.reasoning.litellm.acompletion", return_value=mock_response)

    result = await reason({"title": "test"}, "context", {"found": False}, "test-model")
    assert result["model"] == "fallback"
    assert "JSON extraction failed" in caplog.text


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


# ── _extract_json tests ─────────────────────────────────────

def test_extract_json_clean():
    assert _extract_json('{"a": 1}') == {"a": 1}


def test_extract_json_markdown_fences():
    assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert _extract_json('```\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_bad_markdown():
    # Strategy 1 matched but invalid JSON, should fall through and find valid JSON
    result = _extract_json('```json\n{bad_json}\n```\n{"A": 1}')
    assert result == {"A": 1}


def test_extract_json_prose_with_json():
    result = _extract_json('Some analysis text.\n{"probabilities": {"Yes": 0.7}}\nMore text')
    assert result == {"probabilities": {"Yes": 0.7}}


def test_extract_json_truncated():
    # Truncated rationale — should still extract probabilities
    result = _extract_json(
        '{"probabilities": {"A": 0.7, "B": 0.3}, "rationale": "trunc'
    )
    assert result is not None
    assert result["probabilities"] == {"A": 0.7, "B": 0.3}


def test_extract_json_no_json():
    assert _extract_json('Just plain text with no JSON at all') is None


def test_extract_json_nested_braces():
    result = _extract_json('{"a": {"b": 1}, "c": 2}')
    assert result == {"a": {"b": 1}, "c": 2}


# ── Retry logic tests ───────────────────────────────────────

@pytest.mark.asyncio
async def test_reason_retry_success(mocker):
    """First call returns bad JSON, retry returns good JSON."""
    bad_response = MagicMock()
    bad_msg = MagicMock()
    bad_msg.content = 'No JSON here at all'
    bad_response.choices = [MagicMock(message=bad_msg)]
    bad_response.usage = None

    good_response = MagicMock()
    good_msg = MagicMock()
    good_msg.content = '{"probabilities": {"Yes": 0.6, "No": 0.4}, "rationale": "Retry worked", "confidence": "medium"}'
    good_response.choices = [MagicMock(message=good_msg)]
    good_response.usage = None

    mocker.patch(
        "sibyl.reasoning.litellm.acompletion",
        side_effect=[bad_response, good_response],
    )

    result = await reason({"title": "test"}, "context", {"found": False}, "test-model")
    assert result["model"] == "test-model"
    assert result["probabilities"] == {"Yes": 0.6, "No": 0.4}
    assert result["rationale"] == "Retry worked"


def test_extract_json_balanced_braces_invalid_inner():
    """Strategy 3 finds balanced braces but inner JSON is invalid (line 117-118)."""
    # Looks like JSON structure but has invalid content between braces
    result = _extract_json("{not valid json content}")
    assert result is None


def test_extract_json_truncated_unfixable():
    """Strategy 5 tries to fix truncated JSON but result is still invalid (line 140-141)."""
    # Has a brace but completely malformed — can't be repaired
    result = _extract_json("{key without quotes: }")
    assert result is None


@pytest.mark.asyncio
async def test_reason_json_decode_error_in_extraction(mocker, caplog):
    """JSONDecodeError raised during processing triggers retry path (line 226-230, 235)."""
    mock_response = MagicMock()
    mock_msg = MagicMock()
    # Content has braces but _extract_json returns a result that triggers
    # JSONDecodeError when accessed — simulate via side_effect on json.loads
    mock_msg.content = '{"probabilities": {"Yes": 0.7, "No": 0.3}}'
    mock_response.choices = [MagicMock(message=mock_msg)]
    mock_response.usage = None

    # Make _extract_json return something, but then json parsing fails later
    # Actually: the JSONDecodeError path at line 225-230 can only be hit if
    # json.loads raises inside _extract_json which is already caught.
    # The easiest way: mock _extract_json to raise JSONDecodeError
    import json as json_mod
    mocker.patch("sibyl.reasoning.litellm.acompletion", return_value=mock_response)
    mocker.patch(
        "sibyl.reasoning._extract_json",
        side_effect=json_mod.JSONDecodeError("test", "", 0),
    )

    result = await reason({"title": "test"}, "context", {"found": False}, "test-model")
    assert result["model"] == "fallback"
