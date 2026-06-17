"""Cryptographic watermarking for AI-generated responses (UC-P3-04).

Embeds a verifiable HMAC-SHA256 signature in AI responses to prove provenance.
The token is metadata-only (appended or stored alongside the response).

Multi-tenancy: company_id is part of the signing payload so tokens from
one tenant cannot be verified against another tenant's responses.

TODO(ml-team, ISSUE-P3-04, 2026-09-01): Implement full semantic watermarking
(e.g., Kirchenbauer et al. 2023) for in-weights / token-distribution detection.
Current approach requires the full response text to verify (metadata watermark).

Environment variables:
    WATERMARK_SECRET: Signing secret (required in production). A default
                      fallback is provided for local dev only — change it.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_WINDOW_SECONDS = 300  # 5-minute rolling window for replay tolerance
_SIG_LENGTH = 16       # Characters taken from the hex digest


def _secret() -> bytes:
    """Read signing secret from env; warn if using the insecure default."""
    raw = os.getenv("WATERMARK_SECRET", "lia-default-secret-change-me")
    return raw.encode()


def _build_payload(response_text: str, company_id: str, model: str, timestamp: int) -> bytes:
    """Canonical payload for HMAC signing.

    Uses first 100 chars of response to keep payload short while still
    binding the token to the specific response content.
    """
    excerpt = response_text[:100]
    return f"{company_id}:{model}:{timestamp}:{excerpt}".encode()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_watermark(response_text: str, company_id: str, model: str) -> str:
    """Generate a watermark token for an AI response.

    Args:
        response_text: The full LLM response text.
        company_id: Tenant identifier (scopes the token to this tenant).
        model: Model name/ID that generated the response.

    Returns:
        A 16-character hex token derived from HMAC-SHA256.
    """
    timestamp = int(time.time()) // _WINDOW_SECONDS
    payload = _build_payload(response_text, company_id, model, timestamp)
    sig = hmac.new(_secret(), payload, hashlib.sha256).hexdigest()[:_SIG_LENGTH]
    return sig


def verify_watermark(
    response_text: str,
    company_id: str,
    model: str,
    token: str,
) -> bool:
    """Verify a watermark token.

    Checks the current 5-minute window and the immediately preceding window
    to allow for clock drift / request latency.

    Args:
        response_text: The full LLM response text to verify.
        company_id: Tenant identifier used during generation.
        model: Model name/ID used during generation.
        token: The watermark token to verify.

    Returns:
        True if the token is valid for either the current or previous window.
    """
    current_window = int(time.time()) // _WINDOW_SECONDS
    for delta in [0, 1]:
        timestamp = current_window - delta
        payload = _build_payload(response_text, company_id, model, timestamp)
        expected = hmac.new(_secret(), payload, hashlib.sha256).hexdigest()[:_SIG_LENGTH]
        if hmac.compare_digest(expected, token):
            return True
    return False
