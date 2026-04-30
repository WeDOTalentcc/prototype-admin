"""Unit tests for app.shared.providers.llm_retry.

Covers:
- _is_transient_llm_error predicate (status_code + class name paths)
- llm_transient_retry decorator integration: retries on transient, not on permanent
- Re-raises after exhausting attempts (circuit breaker must see final failure)
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.shared.providers.llm_retry import _TRANSIENT_CLASS_NAMES, _is_transient_llm_error, llm_transient_retry


# ---------------------------------------------------------------------------
# _is_transient_llm_error predicate
# ---------------------------------------------------------------------------

class TestIsTransientLLMError:
    """Unit tests for the provider-agnostic transient error predicate."""

    def _exc_with_status(self, status: int) -> Exception:
        e = Exception("test")
        e.status_code = status  # type: ignore[attr-defined]
        return e

    def test_429_is_transient(self):
        assert _is_transient_llm_error(self._exc_with_status(429)) is True

    def test_500_is_transient(self):
        assert _is_transient_llm_error(self._exc_with_status(500)) is True

    def test_503_is_transient(self):
        assert _is_transient_llm_error(self._exc_with_status(503)) is True

    def test_529_is_transient(self):
        assert _is_transient_llm_error(self._exc_with_status(529)) is True

    def test_200_is_not_transient(self):
        assert _is_transient_llm_error(self._exc_with_status(200)) is False

    def test_400_is_not_transient(self):
        # 4xx (except 429) -> permanent client error, do not retry
        assert _is_transient_llm_error(self._exc_with_status(400)) is False

    def test_401_is_not_transient(self):
        assert _is_transient_llm_error(self._exc_with_status(401)) is False

    def test_404_is_not_transient(self):
        assert _is_transient_llm_error(self._exc_with_status(404)) is False

    def test_class_name_rate_limit_error(self):
        class RateLimitError(Exception):
            pass
        assert _is_transient_llm_error(RateLimitError("quota")) is True

    def test_class_name_internal_server_error(self):
        class InternalServerError(Exception):
            pass
        assert _is_transient_llm_error(InternalServerError("oops")) is True

    def test_class_name_api_connection_error(self):
        class APIConnectionError(Exception):
            pass
        assert _is_transient_llm_error(APIConnectionError("conn")) is True

    def test_class_name_overloaded_error(self):
        class OverloadedError(Exception):
            pass
        assert _is_transient_llm_error(OverloadedError("load")) is True

    def test_class_name_timeout(self):
        class Timeout(Exception):
            pass
        assert _is_transient_llm_error(Timeout("timed out")) is True

    def test_class_name_value_error_is_not_transient(self):
        # ValueError is permanent -- do not retry
        assert _is_transient_llm_error(ValueError("bad input")) is False

    def test_class_name_runtime_error_is_not_transient(self):
        assert _is_transient_llm_error(RuntimeError("crash")) is False

    def test_status_via_status_attribute(self):
        """SDK uses .status instead of .status_code."""
        e = Exception("test")
        e.status = 429  # type: ignore[attr-defined]
        assert _is_transient_llm_error(e) is True

    def test_status_via_http_status_attribute(self):
        """SDK uses .http_status."""
        e = Exception("test")
        e.http_status = 503  # type: ignore[attr-defined]
        assert _is_transient_llm_error(e) is True

    def test_status_code_takes_precedence_over_class_name(self):
        """If status_code is 200 but class name is RateLimitError, not transient."""
        class RateLimitError(Exception):
            pass
        e = RateLimitError("confused")
        e.status_code = 200  # type: ignore[attr-defined]
        # status_code=200 -> not transient (status_code path is checked first)
        assert _is_transient_llm_error(e) is False

    def test_non_integer_status_falls_back_to_class_name(self):
        """If status_code is malformed, fall back to class-name check."""
        class RateLimitError(Exception):
            pass
        e = RateLimitError("garbled status")
        e.status_code = "not-a-number"  # type: ignore[attr-defined]
        # status parse fails -> fall back to class name -> transient
        assert _is_transient_llm_error(e) is True

    def test_all_known_transient_class_names_covered(self):
        """Every name in _TRANSIENT_CLASS_NAMES must be detected."""
        for name in _TRANSIENT_CLASS_NAMES:
            exc_cls = type(name, (Exception,), {})
            assert _is_transient_llm_error(exc_cls("x")) is True, (
                f"{name} should be detected as transient"
            )


# ---------------------------------------------------------------------------
# llm_transient_retry decorator
# ---------------------------------------------------------------------------

class TestLLMTransientRetry:
    """Integration tests for the retry decorator with async functions."""

    @pytest.mark.asyncio
    async def test_no_retry_on_success(self):
        """Successful call is only called once."""
        call_count = 0

        @llm_transient_retry
        async def _call():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await _call()
        assert result == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_transient_then_succeeds(self):
        """Retries twice on transient error then returns success."""
        call_count = 0

        class RateLimitError(Exception):
            pass

        @llm_transient_retry
        async def _call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitError("429")
            return "recovered"

        # Patch wait to avoid sleeping in tests
        with patch("tenacity.wait_exponential.__call__", return_value=0):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await _call()

        assert result == "recovered"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_reraises_after_exhausting_attempts(self):
        """After 3 failed attempts, the original exception is re-raised."""
        call_count = 0

        class InternalServerError(Exception):
            pass

        @llm_transient_retry
        async def _call():
            nonlocal call_count
            call_count += 1
            raise InternalServerError("500 always")

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(InternalServerError, match="500 always"):
                await _call()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """Permanent errors (ValueError, 401) are raised immediately, no retry."""
        call_count = 0

        @llm_transient_retry
        async def _call():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad schema")

        with pytest.raises(ValueError, match="bad schema"):
            await _call()

        # Called exactly once -- no retry
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_on_401_permanent(self):
        """HTTP 401 auth errors must not be retried."""
        call_count = 0

        @llm_transient_retry
        async def _call():
            nonlocal call_count
            call_count += 1
            e = Exception("unauthorized")
            e.status_code = 401  # type: ignore[attr-defined]
            raise e

        with pytest.raises(Exception, match="unauthorized"):
            await _call()

        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_status_code_429(self):
        """Exception with status_code=429 triggers retry."""
        call_count = 0

        @llm_transient_retry
        async def _call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                e = Exception("rate limited")
                e.status_code = 429  # type: ignore[attr-defined]
                raise e
            return "ok"

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await _call()

        assert result == "ok"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_on_status_code_503(self):
        """Exception with status_code=503 triggers retry."""
        call_count = 0

        @llm_transient_retry
        async def _call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                e = Exception("service unavailable")
                e.status_code = 503  # type: ignore[attr-defined]
                raise e
            return "ok"

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await _call()

        assert result == "ok"
        assert call_count == 2
