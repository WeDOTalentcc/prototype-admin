"""
GAP-11-023 — Sentry custom fingerprinting / error grouping.

Tests verify that _add_fingerprint and _normalize_path produce
stable, predictable fingerprints so similar errors land in the
same Sentry issue.

All tests are pure-Python (no Sentry SDK required).
"""
import sys
import os

# Make the libs/config importable without installing the package
_SENTRY_MOD_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "libs", "config"
)
if _SENTRY_MOD_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(_SENTRY_MOD_DIR))

from lia_config.sentry import _normalize_path, _add_fingerprint  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hint(exc):
    return {"exc_info": (type(exc), exc, None)}


def _make_event(url=""):
    return {"request": {"url": url}} if url else {}


# ---------------------------------------------------------------------------
# _normalize_path
# ---------------------------------------------------------------------------

def test_uuids_normalized_in_path():
    path = "/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/candidates"
    result = _normalize_path(path)
    assert "{uuid}" in result
    assert "550e8400" not in result


def test_numeric_ids_normalized_in_path():
    path = "/api/v1/candidates/42/profile"
    result = _normalize_path(path)
    assert "/{id}" in result
    assert "/42" not in result


def test_static_path_unchanged():
    path = "/api/v1/health"
    assert _normalize_path(path) == path


# ---------------------------------------------------------------------------
# _add_fingerprint — LIAError
# ---------------------------------------------------------------------------

def test_lia_error_gets_lia_error_fingerprint():
    """LIAError (and subclasses) must get ["lia-error", ClassName]."""
    try:
        from app.shared.errors import LIAError
    except ImportError:
        # Simulate with a dummy hierarchy when app not on path
        class LIAError(Exception):
            pass

    exc = LIAError("something broke")
    event = _add_fingerprint(_make_event(), _make_hint(exc))
    assert event.get("fingerprint") == ["lia-error", "LIAError"], event.get("fingerprint")


def test_lia_error_subclass_fingerprint():
    """LIAError subclass should use the subclass name."""
    try:
        from app.shared.errors import LIAAgentError
        exc = LIAAgentError("agent down")
    except ImportError:
        class LIAError(Exception):
            pass
        class LIAAgentError(LIAError):
            pass
        exc = LIAAgentError("agent down")

    event = _add_fingerprint(_make_event(), _make_hint(exc))
    fp = event.get("fingerprint")
    assert fp is not None and fp[0] == "lia-error", fp
    assert "Error" in fp[1], fp


# ---------------------------------------------------------------------------
# _add_fingerprint — HTTPException
# ---------------------------------------------------------------------------

def test_http_exception_gets_status_path_fingerprint():
    """HTTPException fingerprint must include status code and normalized path."""
    try:
        from fastapi import HTTPException
    except ImportError:
        class HTTPException(Exception):
            def __init__(self, status_code, detail=""):
                self.status_code = status_code
                self.detail = detail
                super().__init__(detail)

    exc = HTTPException(status_code=422, detail="Validation error")
    event = _add_fingerprint({"request": {"url": "/api/v1/jobs"}}, _make_hint(exc))
    fp = event.get("fingerprint")
    assert fp is not None, "Expected fingerprint"
    assert fp[0] == "http", fp
    assert fp[1] == "422", fp
    assert "/api/v1/jobs" in fp[2], fp


def test_http_exception_uuid_in_url_normalized():
    """UUIDs in the request URL must be replaced by {uuid} in the fingerprint."""
    try:
        from fastapi import HTTPException
    except ImportError:
        class HTTPException(Exception):
            def __init__(self, status_code, detail=""):
                self.status_code = status_code
                self.detail = detail
                super().__init__(detail)

    exc = HTTPException(status_code=404, detail="Not found")
    url = "https://api.example.com/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/candidates"
    event = _add_fingerprint({"request": {"url": url}}, _make_hint(exc))
    fp = event.get("fingerprint")
    assert fp is not None
    assert "{uuid}" in fp[2], fp
    assert "550e8400" not in fp[2], fp


# ---------------------------------------------------------------------------
# _add_fingerprint — DB errors
# ---------------------------------------------------------------------------

def test_db_error_grouped():
    """SQLAlchemy exceptions must get ['db-error', ExcClassName]."""
    # Simulate a SQLAlchemy exception by setting __module__
    class FakeOperationalError(Exception):
        pass

    exc = FakeOperationalError("connection refused")
    exc.__class__.__module__ = "sqlalchemy.exc"  # type: ignore[attr-defined]

    event = _add_fingerprint(_make_event(), _make_hint(exc))
    fp = event.get("fingerprint")
    assert fp == ["db-error", "FakeOperationalError"], fp


# ---------------------------------------------------------------------------
# _add_fingerprint — unknown errors keep default
# ---------------------------------------------------------------------------

def test_unknown_error_keeps_default():
    """Generic exceptions must NOT get a custom fingerprint (Sentry default)."""
    exc = RuntimeError("something unexpected")
    event = _add_fingerprint(_make_event(), _make_hint(exc))
    # No "fingerprint" key added for unknown exceptions
    assert "fingerprint" not in event, event.get("fingerprint")


def test_no_exc_info_returns_event_unchanged():
    """When hint has no exc_info, event is returned as-is."""
    event = {"foo": "bar"}
    result = _add_fingerprint(event, {})
    assert result == {"foo": "bar"}
