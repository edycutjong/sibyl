"""Tests for sibyl.parser — event extraction from prompts."""

from sibyl.parser import normalize_event, parse_event_from_prompt


class TestParseEventFromPrompt:
    """Tests for parse_event_from_prompt."""

    def test_json_block_extraction(self):
        """Should extract event from ```json``` code block."""
        prompt = '''Predict this:
```json
{"event_ticker": "TEST-1", "title": "Will it rain?", "outcomes": ["Yes", "No"]}
```'''
        event = parse_event_from_prompt(prompt)
        assert event["event_ticker"] == "TEST-1"
        assert event["title"] == "Will it rain?"

    def test_json_block_invalid_json(self):
        """Should fallback if json block contains invalid json."""
        prompt = '''Here is the event:
```json
{invalid: json}
```
title: "Valid title"
'''
        event = parse_event_from_prompt(prompt)
        assert event.get("title") == "Valid title?"

    def test_raw_json_extraction(self):
        """Should extract event from raw JSON in prompt."""
        prompt = 'Please forecast: {"event_ticker": "T1", "title": "Test?", "outcomes": ["Yes", "No"]}'
        event = parse_event_from_prompt(prompt)
        assert event["title"] == "Test?"

    def test_raw_json_invalid(self):
        """Should fallback if raw JSON is invalid."""
        prompt = 'Here is the event: {"event_ticker": "T1", invalid} \ntitle: "Valid title2"'
        event = parse_event_from_prompt(prompt)
        assert event.get("title") == "Valid title2?"

    def test_full_json_prompt(self):
        """Should handle prompt that is entirely JSON."""
        # This will be caught by Strategy 2
        prompt = '{"event_ticker": "T2", "title": "Will X happen?", "outcomes": ["Yes", "No"]}'
        event = parse_event_from_prompt(prompt)
        assert event["event_ticker"] == "T2"

        # This will bypass Strategy 2 and be caught by Strategy 3
        prompt_other = '{"other_key": "value"}'
        event_other = parse_event_from_prompt(prompt_other)
        assert event_other.get("other_key") == "value"

    def test_full_json_invalid_or_not_dict(self):
        """Should fallback if entire JSON is invalid or a list."""
        prompt_list = '["not a dict"]\ntitle: "List fallback"'
        event1 = parse_event_from_prompt(prompt_list)
        assert event1.get("title") == "List fallback?"

        prompt_invalid = '{"event_ticker": "T2"\ntitle: "Invalid fallback"'
        event2 = parse_event_from_prompt(prompt_invalid)
        assert event2.get("title") == "Invalid fallback?"

    def test_natural_language_fallback(self):
        """Should extract from natural language when no JSON found."""
        prompt = "Will the Lakers win the championship this year?"
        event = parse_event_from_prompt(prompt)
        assert "Lakers" in event.get("title", "")

    def test_natural_language_full_extraction(self):
        """Should extract title, outcomes, category, event_ticker, market_ticker from natural language."""
        prompt = '''
title: "Will OpenAI release GPT-5 in 2026?"
outcomes: ["Yes", "No", "Maybe"]
category: AI
event_ticker: OPENAI-2026
market_ticker: GPT5-MK
        '''
        event = parse_event_from_prompt(prompt)
        assert event["title"] == "Will OpenAI release GPT-5 in 2026?"
        assert event["outcomes"] == ["Yes", "No", "Maybe"]
        assert event["category"] == "AI"
        assert event["event_ticker"] == "OPENAI-2026"
        assert event["market_ticker"] == "GPT5-MK"

    def test_handles_empty_prompt(self):
        """Should not crash on empty prompt."""
        event = parse_event_from_prompt("")
        assert "title" in event or event == {}


class TestNormalizeEvent:
    """Tests for normalize_event."""

    def test_normalizes_complete_event(self):
        """Should pass through all fields."""
        raw = {
            "event_ticker": "A",
            "title": "Test?",
            "outcomes": ["Y", "N"],
            "category": "Sports",
        }
        result = normalize_event(raw)
        assert result["event_ticker"] == "A"
        assert result["title"] == "Test?"
        assert result["outcomes"] == ["Y", "N"]

    def test_normalizes_minimal_event(self):
        """Should fill defaults for missing fields."""
        raw = {"title": "Will it happen?"}
        result = normalize_event(raw)
        assert result["event_ticker"] == "unknown"
        assert result["outcomes"] == ["Yes", "No"]
        assert result["category"] == "Other"

    def test_uses_question_field(self):
        """Should fall back to 'question' if 'title' missing."""
        raw = {"question": "Is it going to rain?"}
        result = normalize_event(raw)
        assert result["title"] == "Is it going to rain?"
