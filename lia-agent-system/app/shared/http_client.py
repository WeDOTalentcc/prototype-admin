"""Canonical HTTP client factory with unified timeouts (GAP-08-007).

All external HTTP calls in lia-agent-system SHOULD use this factory so that
timeouts are configured consistently and can be tuned via env vars.

Existing callers that already use httpx.AsyncClient(timeout=N) should
be migrated here gradually — start with callers that pass no timeout at all.

Usage::

    from app.shared.http_client import get_http_client

    async with get_http_client("twilio") as client:
        resp = await client.post(url, ...)

    # Or with a one-off override:
    async with get_http_client("default", follow_redirects=True) as client:
        resp = await client.get(url)
"""
from __future__ import annotations

import os
import httpx

# ---------------------------------------------------------------------------
# Env-var overrides (seconds; float for sub-second precision)
# ---------------------------------------------------------------------------
_CONNECT = float(os.getenv("HTTP_CONNECT_TIMEOUT", "10"))
_READ = float(os.getenv("HTTP_READ_TIMEOUT", "30"))
_WRITE = float(os.getenv("HTTP_WRITE_TIMEOUT", "10"))
_POOL = float(os.getenv("HTTP_POOL_TIMEOUT", "5"))

# ---------------------------------------------------------------------------
# Vendor-specific timeout presets
# ---------------------------------------------------------------------------
# fmt: off
VENDOR_TIMEOUTS: dict[str, httpx.Timeout] = {
    # Google APIs (Calendar, Drive, Workspace)
    "google":    httpx.Timeout(connect=10, read=30, write=10, pool=5),
    # Microsoft Graph / Azure AD
    "microsoft": httpx.Timeout(connect=10, read=30, write=10, pool=5),
    # Twilio (WhatsApp, Voice) — low-latency service, tighter timeout
    "twilio":    httpx.Timeout(connect=5,  read=15, write=5,  pool=5),
    # Resend transactional email
    "resend":    httpx.Timeout(connect=5,  read=15, write=5,  pool=5),
    # Mailgun transactional email
    "mailgun":   httpx.Timeout(connect=5,  read=15, write=5,  pool=5),
    # Apify web scraping (slower by nature)
    "apify":     httpx.Timeout(connect=10, read=60, write=10, pool=5),
    # GitHub REST API
    "github":    httpx.Timeout(connect=10, read=30, write=10, pool=5),
    # ATS integrations (Greenhouse, Lever, etc.)
    "ats":       httpx.Timeout(connect=10, read=30, write=10, pool=5),
    # WorkOS auth
    "workos":    httpx.Timeout(connect=5,  read=10, write=5,  pool=5),
    # Generic fallback — respects env-var overrides
    "default":   httpx.Timeout(connect=_CONNECT, read=_READ, write=_WRITE, pool=_POOL),
}
# fmt: on


def get_http_timeout(vendor: str = "default") -> httpx.Timeout:
    """Return the httpx.Timeout for *vendor*, falling back to "default"."""
    return VENDOR_TIMEOUTS.get(vendor, VENDOR_TIMEOUTS["default"])


def get_http_client(vendor: str = "default", **kwargs) -> httpx.AsyncClient:
    """Return an ``httpx.AsyncClient`` pre-configured with vendor timeouts.

    The client is suitable for use as an async context manager::

        async with get_http_client("twilio") as client:
            resp = await client.post(url, ...)

    Args:
        vendor: Key in :data:`VENDOR_TIMEOUTS` (e.g. ``"google"``, ``"twilio"``).
                Unknown keys fall back to ``"default"``.
        **kwargs: Forwarded verbatim to ``httpx.AsyncClient``.  If you pass
                  ``timeout`` yourself it will override the vendor preset.

    Returns:
        A new ``httpx.AsyncClient`` instance.  The caller is responsible for
        closing it (use as a context manager or call ``await client.aclose()``).
    """
    timeout = VENDOR_TIMEOUTS.get(vendor, VENDOR_TIMEOUTS["default"])
    # Allow explicit caller override via kwarg
    kwargs.setdefault("timeout", timeout)
    return httpx.AsyncClient(**kwargs)
