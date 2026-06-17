"""
GAP-12-008: Tests for RequestDurationMiddleware.

Validates:
  - X-Response-Time-Ms header presence on every response.
  - Slow-request WARNING log when duration exceeds threshold.
  - No warning for fast requests.
  - Excluded paths (health, metrics, SSE) skip slow alerting.
  - Prometheus histogram observation when available.
"""
import asyncio
import logging
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient

from fastapi import FastAPI


# ---------------------------------------------------------------------------
# Helpers — build a minimal FastAPI app with the middleware
# ---------------------------------------------------------------------------

def _build_app(*, delay_s: float = 0.0) -> FastAPI:
    """Create a tiny FastAPI app with RequestDurationMiddleware mounted."""
    from app.middleware.request_duration import RequestDurationMiddleware

    test_app = FastAPI()
    test_app.add_middleware(RequestDurationMiddleware)

    @test_app.get("/fast")
    async def fast_endpoint():
        return {"ok": True}

    @test_app.get("/slow")
    async def slow_endpoint():
        await asyncio.sleep(delay_s)
        return {"ok": True}

    @test_app.get("/health")
    async def health_endpoint():
        await asyncio.sleep(delay_s)
        return {"status": "ok"}

    @test_app.get("/metrics")
    async def metrics_endpoint():
        await asyncio.sleep(delay_s)
        return {"metrics": []}

    @test_app.get("/api/v1/lia-assistant/sse/chat")
    async def sse_endpoint():
        await asyncio.sleep(delay_s)
        return {"stream": True}

    return test_app


# ---------------------------------------------------------------------------
# Test: header always present
# ---------------------------------------------------------------------------

class TestResponseTimeHeader:
    def test_adds_response_time_header(self):
        app = _build_app()
        client = TestClient(app)
        resp = client.get("/fast")
        assert resp.status_code == 200
        header_val = resp.headers.get("X-Response-Time-Ms")
        assert header_val is not None, "X-Response-Time-Ms header must be present"
        # Must be a non-negative number
        assert float(header_val) >= 0

    def test_header_on_404(self):
        app = _build_app()
        client = TestClient(app)
        resp = client.get("/nonexistent")
        assert resp.status_code == 404
        assert "X-Response-Time-Ms" in resp.headers


# ---------------------------------------------------------------------------
# Test: slow-request alerting
# ---------------------------------------------------------------------------

class TestSlowRequestAlerting:
    @patch("app.middleware.request_duration.SLOW_REQUEST_THRESHOLD_MS", 10)
    def test_slow_request_logs_warning(self, caplog):
        app = _build_app(delay_s=0.05)  # 50ms >> 10ms threshold
        client = TestClient(app)
        with caplog.at_level(logging.WARNING, logger="lia.slow_request"):
            resp = client.get("/slow")
        assert resp.status_code == 200
        slow_logs = [r for r in caplog.records if "Slow request" in r.getMessage()]
        assert len(slow_logs) >= 1, "Expected a WARNING log for slow request"
        record = slow_logs[0]
        assert record.levelno == logging.WARNING
        assert "/slow" in record.getMessage()

    @patch("app.middleware.request_duration.SLOW_REQUEST_THRESHOLD_MS", 60_000)
    def test_fast_request_no_warning(self, caplog):
        app = _build_app()
        client = TestClient(app)
        with caplog.at_level(logging.WARNING, logger="lia.slow_request"):
            resp = client.get("/fast")
        assert resp.status_code == 200
        slow_logs = [r for r in caplog.records if "Slow request" in r.getMessage()]
        assert len(slow_logs) == 0, "Fast request should NOT trigger slow warning"

    @patch("app.middleware.request_duration.SLOW_REQUEST_THRESHOLD_MS", 0)
    def test_excluded_health_no_warning(self, caplog):
        """Health endpoint should never trigger slow alert even if over threshold."""
        app = _build_app(delay_s=0.01)
        client = TestClient(app)
        with caplog.at_level(logging.WARNING, logger="lia.slow_request"):
            resp = client.get("/health")
        assert resp.status_code == 200
        slow_logs = [r for r in caplog.records if "Slow request" in r.getMessage()]
        assert len(slow_logs) == 0

    @patch("app.middleware.request_duration.SLOW_REQUEST_THRESHOLD_MS", 0)
    def test_excluded_metrics_no_warning(self, caplog):
        """Metrics endpoint should never trigger slow alert."""
        app = _build_app(delay_s=0.01)
        client = TestClient(app)
        with caplog.at_level(logging.WARNING, logger="lia.slow_request"):
            resp = client.get("/metrics")
        assert resp.status_code == 200
        slow_logs = [r for r in caplog.records if "Slow request" in r.getMessage()]
        assert len(slow_logs) == 0

    @patch("app.middleware.request_duration.SLOW_REQUEST_THRESHOLD_MS", 0)
    def test_excluded_sse_no_warning(self, caplog):
        """SSE streaming endpoint should never trigger slow alert."""
        app = _build_app(delay_s=0.01)
        client = TestClient(app)
        with caplog.at_level(logging.WARNING, logger="lia.slow_request"):
            resp = client.get("/api/v1/lia-assistant/sse/chat")
        assert resp.status_code == 200
        slow_logs = [r for r in caplog.records if "Slow request" in r.getMessage()]
        assert len(slow_logs) == 0


# ---------------------------------------------------------------------------
# Test: Prometheus histogram
# ---------------------------------------------------------------------------

class TestPrometheusHistogram:
    def test_histogram_observes_when_available(self):
        """When prometheus_client is installed, the histogram should be observed."""
        from app.middleware.request_duration import REQUEST_DURATION_HISTOGRAM

        if REQUEST_DURATION_HISTOGRAM is None:
            pytest.skip("prometheus_client not installed")

        app = _build_app()
        client = TestClient(app)

        # Record initial sample count
        initial = REQUEST_DURATION_HISTOGRAM.labels(
            method="GET", status_code="200"
        )._sum._value

        resp = client.get("/fast")
        assert resp.status_code == 200

        updated = REQUEST_DURATION_HISTOGRAM.labels(
            method="GET", status_code="200"
        )._sum._value

        assert updated > initial, "Histogram sum should increase after a request"
