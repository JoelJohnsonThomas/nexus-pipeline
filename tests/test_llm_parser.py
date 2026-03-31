"""
Tests for the LLM output parser in LLMSummarizer.summarize().

These tests mock the Gemini API call so no network access or API key is needed.
They verify that the parser handles the three response formats Gemini can return:
  1. Raw JSON object
  2. Markdown-fenced JSON block (```json ... ```)
  3. Plain text (no valid JSON) — graceful fallback
"""
import json
from unittest.mock import MagicMock, patch

import pytest


def _make_summarizer(model_name="gemini-test"):
    """Build an LLMSummarizer with a mocked Gemini model."""
    mock_genai = MagicMock()
    mock_model_instance = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model_instance

    with patch("app.processing.llm_summarizer.genai", mock_genai):
        from app.processing.llm_summarizer import LLMSummarizer
        summarizer = LLMSummarizer.__new__(LLMSummarizer)
        summarizer.provider = "gemini"
        summarizer.model_name = model_name
        summarizer.model = mock_model_instance
        summarizer.SYSTEM_PROMPT = "You are a helpful assistant."

    return summarizer


class TestLLMOutputParser:

    def _call_summarize(self, summarizer, response_text: str):
        """Patch _call_gemini and invoke summarize()."""
        with patch.object(summarizer, "_call_gemini", return_value=response_text):
            return summarizer.summarize("Some article content here.", title="Test Title")

    def test_raw_json_response_is_parsed(self):
        """A plain JSON object in the response should be parsed correctly."""
        summarizer = _make_summarizer()
        payload = {"summary": "This is a summary.", "key_points": ["Point A", "Point B"]}
        result = self._call_summarize(summarizer, json.dumps(payload))

        assert result is not None
        assert result["summary"] == "This is a summary."
        assert result["key_points"] == ["Point A", "Point B"]
        assert result["model"] == "gemini-test"

    def test_markdown_fenced_json_is_parsed(self):
        """JSON wrapped in ```json ... ``` markdown blocks should be extracted and parsed."""
        summarizer = _make_summarizer()
        payload = {"summary": "Fenced summary.", "key_points": ["Fenced point"]}
        response = f"```json\n{json.dumps(payload)}\n```"
        result = self._call_summarize(summarizer, response)

        assert result is not None
        assert result["summary"] == "Fenced summary."
        assert result["key_points"] == ["Fenced point"]

    def test_plain_text_fallback(self):
        """A response with no JSON should be returned as a plain summary with empty key_points."""
        summarizer = _make_summarizer()
        plain_response = "This article is about machine learning trends."
        result = self._call_summarize(summarizer, plain_response)

        assert result is not None
        assert plain_response in result["summary"]
        assert result["key_points"] == []
        assert result["model"] == "gemini-test"

    def test_missing_key_points_defaults_to_empty_list(self):
        """A JSON response missing key_points should default to an empty list."""
        summarizer = _make_summarizer()
        payload = {"summary": "Just a summary, no key points."}
        result = self._call_summarize(summarizer, json.dumps(payload))

        assert result is not None
        assert result["key_points"] == []

    def test_missing_summary_falls_back_to_raw_text(self):
        """A JSON response missing 'summary' should use the raw response text as the summary."""
        summarizer = _make_summarizer()
        payload = {"key_points": ["Only key points, no summary"]}
        raw = json.dumps(payload)
        # The parser sets result['summary'] = response_text.strip() when 'summary' is missing
        result = self._call_summarize(summarizer, raw)

        assert result is not None
        assert result["summary"] is not None
        assert len(result["summary"]) > 0

    def test_api_failure_returns_none(self):
        """If the Gemini API call raises an exception, summarize() should return None."""
        summarizer = _make_summarizer()
        with patch.object(summarizer, "_call_gemini", side_effect=Exception("API error")):
            result = summarizer.summarize("Content.", title="Title")

        assert result is None
