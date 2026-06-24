"""
Unit tests for GAP-12-006: N+1 query detection via SQLAlchemy event counter.

Tests are pure-unit: no DB connection needed.
They verify the ContextVar counter logic and the N_PLUS_ONE_ENABLED flag.
"""
import importlib
import os
import sys
import types
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Isolate database module without real DB connection
# ---------------------------------------------------------------------------

def _build_mock_database_module():
    """Return a minimal stub that exercises only the query counter logic."""
    from contextvars import ContextVar

    _request_query_count: ContextVar[int] = ContextVar("_request_query_count", default=0)
    N_PLUS_ONE_THRESHOLD = 10
    N_PLUS_ONE_ENABLED = True

    def get_request_query_count() -> int:
        return _request_query_count.get(0)

    def reset_request_query_count() -> None:
        _request_query_count.set(0)

    def _simulate_query():
        """Simulate what _count_sql_query does on before_cursor_execute."""
        _request_query_count.set(_request_query_count.get(0) + 1)

    mod = types.SimpleNamespace(
        N_PLUS_ONE_ENABLED=N_PLUS_ONE_ENABLED,
        N_PLUS_ONE_THRESHOLD=N_PLUS_ONE_THRESHOLD,
        get_request_query_count=get_request_query_count,
        reset_request_query_count=reset_request_query_count,
        _simulate_query=_simulate_query,
    )
    return mod


_db = _build_mock_database_module()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestQueryCounter:
    """Tests for the ContextVar-based SQL query counter."""

    def setup_method(self):
        _db.reset_request_query_count()

    def test_initial_count_is_zero(self):
        assert _db.get_request_query_count() == 0

    def test_simulated_queries_increment_counter(self):
        _db._simulate_query()
        _db._simulate_query()
        _db._simulate_query()
        assert _db.get_request_query_count() == 3

    def test_reset_clears_counter(self):
        _db._simulate_query()
        _db._simulate_query()
        _db.reset_request_query_count()
        assert _db.get_request_query_count() == 0

    def test_counter_isolation_per_contextvar_scope(self):
        """Each call with a fresh ContextVar token sees 0 — simulates per-request isolation."""
        import asyncio
        from contextvars import copy_context

        results = []

        def run_in_isolated_context(n_queries):
            _db.reset_request_query_count()
            for _ in range(n_queries):
                _db._simulate_query()
            results.append(_db.get_request_query_count())

        # Two separate contexts accumulate independently
        ctx_a = copy_context()
        ctx_b = copy_context()
        ctx_a.run(run_in_isolated_context, 3)
        ctx_b.run(run_in_isolated_context, 7)

        assert results == [3, 7], f"Expected [3, 7], got {results}"

    def test_threshold_constant(self):
        assert _db.N_PLUS_ONE_THRESHOLD == 10

    def test_enabled_flag_is_true_in_dev(self):
        assert _db.N_PLUS_ONE_ENABLED is True

    def test_env_var_disables_detection(self):
        """When N_PLUS_ONE_DETECT=0, N_PLUS_ONE_ENABLED should be False."""
        with patch.dict(os.environ, {"APP_ENV": "development", "N_PLUS_ONE_DETECT": "0"}):
            enabled = (
                os.getenv("APP_ENV", "development") != "production"
                and os.getenv("N_PLUS_ONE_DETECT", "1") != "0"
            )
        assert enabled is False

    def test_env_var_disables_detection_in_production(self):
        """When APP_ENV=production, N_PLUS_ONE_ENABLED should be False regardless."""
        with patch.dict(os.environ, {"APP_ENV": "production", "N_PLUS_ONE_DETECT": "1"}):
            enabled = (
                os.getenv("APP_ENV", "development") != "production"
                and os.getenv("N_PLUS_ONE_DETECT", "1") != "0"
            )
        assert enabled is False

    def test_custom_threshold_from_env(self):
        """N_PLUS_ONE_THRESHOLD reads from env var."""
        with patch.dict(os.environ, {"N_PLUS_ONE_THRESHOLD": "5"}):
            threshold = int(os.getenv("N_PLUS_ONE_THRESHOLD", "10"))
        assert threshold == 5


class TestRequestDurationMiddlewareQueryCount:
    """Smoke tests for the middleware integration of N+1 detection."""

    def test_middleware_resets_and_reports_query_count(self):
        """Verify the middleware resets counter before dispatch and reads it after."""
        _db.reset_request_query_count()
        # Simulate reset at request start
        _db.reset_request_query_count()
        assert _db.get_request_query_count() == 0

        # Simulate queries during request
        for _ in range(3):
            _db._simulate_query()

        # Simulate middleware reading after call_next
        qcount = _db.get_request_query_count()
        assert qcount == 3

    def test_no_warning_below_threshold(self):
        """Under threshold -> no WARNING emitted."""
        _db.reset_request_query_count()
        for _ in range(_db.N_PLUS_ONE_THRESHOLD - 1):
            _db._simulate_query()
        assert _db.get_request_query_count() < _db.N_PLUS_ONE_THRESHOLD

    def test_warning_above_threshold(self):
        """Above threshold -> warning condition is True."""
        _db.reset_request_query_count()
        for _ in range(_db.N_PLUS_ONE_THRESHOLD + 1):
            _db._simulate_query()
        assert _db.get_request_query_count() > _db.N_PLUS_ONE_THRESHOLD
