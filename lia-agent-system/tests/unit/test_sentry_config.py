"""UC-P1-05: Sentry sample rate is env-aware (30% prod / 100% staging)."""
import sys

import pytest


def _init_sentry_with_env(monkeypatch, app_env, explicit_rate=None):
    """Call init_sentry with a fake DSN and given APP_ENV."""
    monkeypatch.setenv('APP_ENV', app_env)
    if explicit_rate is not None:
        monkeypatch.setenv('SENTRY_TRACES_SAMPLE_RATE', str(explicit_rate))
    else:
        monkeypatch.delenv('SENTRY_TRACES_SAMPLE_RATE', raising=False)

    captured = {}

    fake_sentry = type(sys)('sentry_sdk')

    def fake_init(**kwargs):
        captured.update(kwargs)

    fake_sentry.init = fake_init

    fake_fastapi_int = type(sys)('sentry_sdk.integrations.fastapi')
    fake_fastapi_int.FastApiIntegration = lambda **kw: None
    fake_starlette_int = type(sys)('sentry_sdk.integrations.starlette')
    fake_starlette_int.StarletteIntegration = lambda **kw: None

    monkeypatch.setitem(sys.modules, 'sentry_sdk', fake_sentry)
    monkeypatch.setitem(sys.modules, 'sentry_sdk.integrations', type(sys)('sentry_sdk.integrations'))
    monkeypatch.setitem(sys.modules, 'sentry_sdk.integrations.fastapi', fake_fastapi_int)
    monkeypatch.setitem(sys.modules, 'sentry_sdk.integrations.starlette', fake_starlette_int)

    # Use monkeypatch.delitem so that app.core.sentry is restored after the test,
    # preventing contamination of subsequent tests that imported from app.core.sentry.
    for key in list(sys.modules):
        if key == 'app.core.sentry' or key.startswith('app.core.sentry.'):
            monkeypatch.delitem(sys.modules, key, raising=False)

    import app.core.sentry as sentry_mod
    sentry_mod.init_sentry(dsn='https://fake@sentry.example.com/1')
    return captured


def test_staging_rate_is_1(monkeypatch):
    """APP_ENV=staging -> traces_sample_rate = 1.0 by default."""
    captured = _init_sentry_with_env(monkeypatch, 'staging')
    assert captured.get('traces_sample_rate') == 1.0, (
        f"Expected 1.0 for staging, got {captured.get('traces_sample_rate')}"
    )


def test_test_rate_is_1(monkeypatch):
    """APP_ENV=test -> traces_sample_rate = 1.0 by default."""
    captured = _init_sentry_with_env(monkeypatch, 'test')
    assert captured.get('traces_sample_rate') == 1.0


def test_production_rate_is_03(monkeypatch):
    """APP_ENV=production -> traces_sample_rate = 0.3 by default."""
    captured = _init_sentry_with_env(monkeypatch, 'production')
    assert captured.get('traces_sample_rate') == 0.3, (
        f"Expected 0.3 for production, got {captured.get('traces_sample_rate')}"
    )


def test_development_rate_is_03(monkeypatch):
    """APP_ENV=development -> traces_sample_rate = 0.3 (not old 0.1 default)."""
    captured = _init_sentry_with_env(monkeypatch, 'development')
    assert captured.get('traces_sample_rate') == 0.3


def test_explicit_override_wins(monkeypatch):
    """Explicit SENTRY_TRACES_SAMPLE_RATE env var overrides auto-detected default."""
    captured = _init_sentry_with_env(monkeypatch, 'staging', explicit_rate=0.5)
    assert captured.get('traces_sample_rate') == 0.5
