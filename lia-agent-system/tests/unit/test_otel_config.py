"""UC-P1-04: OTEL startup warning when OTEL_EXPORTER_OTLP_ENDPOINT is not set."""
import logging
import sys

import pytest


def _reload_tracing(monkeypatch, endpoint_value):
    """Reload tracing module with a specific OTEL endpoint env var."""
    for key in list(sys.modules):
        if key == 'app.shared.tracing' or key.startswith('app.shared.tracing.'):
            del sys.modules[key]

    if endpoint_value:
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', endpoint_value)
    else:
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)

    import app.shared.tracing as tracing
    return tracing


def test_warning_emitted_when_endpoint_missing(monkeypatch, caplog):
    """No OTEL endpoint -> warning logged at module import time."""
    with caplog.at_level(logging.WARNING, logger='app.shared.tracing'):
        _reload_tracing(monkeypatch, '')
    warning_msgs = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any('OTEL_EXPORTER_OTLP_ENDPOINT not set' in m for m in warning_msgs), (
        f"Expected OTEL warning, got: {warning_msgs}"
    )


def test_no_warning_when_endpoint_set(monkeypatch, caplog):
    """OTEL endpoint set -> no 'not set' warning emitted."""
    with caplog.at_level(logging.WARNING, logger='app.shared.tracing'):
        _reload_tracing(monkeypatch, 'http://tempo:4318')
    otel_warnings = [
        r.message for r in caplog.records
        if r.levelno == logging.WARNING and 'OTEL_EXPORTER_OTLP_ENDPOINT not set' in r.message
    ]
    assert otel_warnings == [], f"Unexpected OTEL warning: {otel_warnings}"


def test_otlp_not_active_when_endpoint_missing(monkeypatch):
    """is_otlp_active() returns False when no endpoint is configured."""
    mod = _reload_tracing(monkeypatch, '')
    assert mod.is_otlp_active() is False
