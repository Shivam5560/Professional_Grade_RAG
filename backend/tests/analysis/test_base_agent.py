"""Tests for BaseAnalysisAgent, _extract_json, retry_with_backoff, compute_confidence."""

import json

import pytest

from app.analysis.base import (
    BaseAnalysisAgent,
    _extract_json,
    _fix_trailing_commas,
    retry_with_backoff,
)


class TestExtractJson:
    def test_plain_object(self):
        result = _extract_json('{"a": 1}')
        assert result == {"a": 1}

    def test_markdown_json_fence(self):
        result = _extract_json('```json\n{"a": 1}\n```')
        assert result == {"a": 1}

    def test_markdown_fence_no_lang(self):
        result = _extract_json('```\n{"a": 1}\n```')
        assert result == {"a": 1}

    def test_trailing_comma_in_object(self):
        result = _extract_json('{"a": 1,}')
        assert result == {"a": 1}

    def test_trailing_comma_in_array(self):
        result = _extract_json('[1, 2, 3,]')
        assert result == [1, 2, 3]

    def test_nested_objects(self):
        result = _extract_json('{"a": {"b": 2, "c": [3, 4]}}')
        assert result == {"a": {"b": 2, "c": [3, 4]}}

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Empty LLM response"):
            _extract_json("")

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _extract_json("not json at all")


class TestFixTrailingCommas:
    def test_object_trailing_comma(self):
        assert _fix_trailing_commas('{"a": 1,}') == '{"a": 1}'

    def test_array_trailing_comma(self):
        assert _fix_trailing_commas('[1, 2,]') == '[1, 2]'

    def test_no_trailing_commas(self):
        assert _fix_trailing_commas('{"a": 1}') == '{"a": 1}'

    def test_nested_trailing_commas(self):
        result = _fix_trailing_commas('{"a": [1,], "b": {"c": 2,}}')
        assert result == '{"a": [1], "b": {"c": 2}}'


class TestRetryWithBackoff:
    @pytest.mark.asyncio
    async def test_no_retry_on_success(self):
        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await retry_with_backoff(succeed, max_retries=3)
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_then_succeed(self):
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient")
            return "ok"

        result = await retry_with_backoff(fail_then_succeed, max_retries=3, base_delay=0.01)
        assert result == "ok"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhaust_retries(self):
        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("always down")

        with pytest.raises(ConnectionError):
            await retry_with_backoff(always_fail, max_retries=2, base_delay=0.01)
        assert call_count == 3  # initial + 2 retries

    @pytest.mark.asyncio
    async def test_no_retry_on_value_error(self):
        call_count = 0

        async def bad_request():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad input")

        with pytest.raises(ValueError):
            await retry_with_backoff(bad_request, max_retries=3)
        assert call_count == 1  # Non-retryable — no retry


class TestComputeConfidence:
    def test_high_findings_no_errors(self):
        score = BaseAnalysisAgent.compute_confidence(10, False, 1.0)
        assert 0.8 < score <= 0.95

    def test_few_findings_lower_confidence(self):
        score_high = BaseAnalysisAgent.compute_confidence(10, False, 1.0)
        score_low = BaseAnalysisAgent.compute_confidence(2, False, 1.0)
        assert score_low < score_high

    def test_errors_penalize_confidence(self):
        score_clean = BaseAnalysisAgent.compute_confidence(5, False, 1.0)
        score_err = BaseAnalysisAgent.compute_confidence(5, True, 1.0)
        assert score_err < score_clean

    def test_poor_quality_reduces_confidence(self):
        score_high = BaseAnalysisAgent.compute_confidence(5, False, 1.0)
        score_low = BaseAnalysisAgent.compute_confidence(5, False, 0.5)
        assert score_low < score_high

    def test_zero_findings_with_errors(self):
        score = BaseAnalysisAgent.compute_confidence(0, True, 0.5)
        assert score < 0.3
