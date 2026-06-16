"""
Canonical webhook signature verification (HMAC-SHA256).

Provides a simple, reusable helper for verifying HMAC-SHA256 webhook signatures
from external providers (ATS platforms, interview tools, test platforms, etc.).

This module handles the SYMMETRIC HMAC verification step only. For the full
per-tenant ownership validation pipeline (per-tenant secrets, cross-tenant
ownership check, audit trail, Prometheus metrics), use webhook_ownership.py.

Usage::

    from app.shared.security.webhook_verification import (
        verify_webhook_signature,
        require_webhook_signature,
    )

    # Manual check
    if not verify_webhook_signature(raw_body, signature, secret, platform="gupy"):
        raise HTTPException(401, "Invalid webhook signature")

    # Or use the FastAPI dependency
    @router.post("/webhooks/{provider}")
    async def handle(request: Request, _=Depends(require_webhook_signature("ATS"))):
        ...

See also:
    - webhook_ownership.py — full per-tenant HMAC + ownership + audit.
    - external_webhooks.py — consumer for ATS/interview/test/document webhooks.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
from typing import Callable

from fastapi import Header, HTTPException, Request

logger = logging.getLogger(__name__)


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
    *,
    platform: str = "unknown",
) -> bool:
    """Verify HMAC-SHA256 webhook signature with constant-time comparison.

    Args:
        payload: Raw request body bytes (HMAC input).
        signature: Signature from the provider header. May be prefixed with
            sha256= (stripped automatically).
        secret: Webhook secret (shared with the provider).
        platform: Provider name for structured logging on failure.

    Returns:
        True if signature is valid, False otherwise. Never raises
        for invalid input — returns False and logs.
    """
    if not secret:
        logger.warning(
            "[WEBHOOK] No secret configured for %s — rejecting for security",
            platform,
        )
        return False

    if not signature:
        logger.warning(
            "[WEBHOOK] Missing signature header for %s — rejecting",
            platform,
        )
        return False

    try:
        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()
        # Strip common prefix formats
        clean_sig = signature
        if clean_sig.startswith("sha256="):
            clean_sig = clean_sig[len("sha256="):]
        return hmac.compare_digest(expected, clean_sig)
    except Exception as e:
        logger.error(
            "[WEBHOOK] Signature verification error for %s: %s",
            platform,
            e,
        )
        return False


def require_webhook_signature(
    platform: str,
    *,
    secret_env_var: str | None = None,
    header_name: str = "X-Webhook-Signature",
    legacy_bearer_env_var: str | None = None,
) -> Callable:
    """FastAPI dependency factory for webhook signature verification.

    Creates a dependency that:
    1. Reads the raw body and the signature header.
    2. Verifies HMAC-SHA256 against the configured secret.
    3. (Migration) If legacy_bearer_env_var is set and no HMAC signature
       is present, falls back to bearer token verification with a deprecation
       warning. This allows a gradual migration from bearer to HMAC.

    Args:
        platform: Provider name for logging and secret env var resolution.
        secret_env_var: Env var name holding the HMAC secret.
            Defaults to {PLATFORM}_WEBHOOK_SECRET.
        header_name: HTTP header carrying the HMAC signature.
        legacy_bearer_env_var: If set, accept Authorization: Bearer <token>
            as a fallback during migration. Logs a deprecation warning.

    Returns:
        An async FastAPI dependency.
    """
    _env_var = secret_env_var or f"{platform.upper()}_WEBHOOK_SECRET"

    async def _dependency(request: Request) -> None:
        raw_body = await request.body()
        signature = request.headers.get(header_name)
        secret = os.getenv(_env_var, "")

        # Path 1: HMAC signature present → verify
        if signature:
            if not secret:
                logger.error(
                    "[WEBHOOK] %s: %s not configured — cannot verify HMAC. "
                    "Configure the env var to enable this endpoint.",
                    platform,
                    _env_var,
                )
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"Webhook endpoint temporarily unavailable: "
                        f"{_env_var} not configured on server."
                    ),
                )
            if not verify_webhook_signature(raw_body, signature, secret, platform=platform):
                logger.warning(
                    "[WEBHOOK] %s: HMAC signature invalid — 401",
                    platform,
                )
                raise HTTPException(
                    status_code=401,
                    detail="Invalid webhook signature",
                )
            return  # HMAC verified OK

        # Path 2: No HMAC signature — try legacy bearer fallback
        if legacy_bearer_env_var:
            bearer_secret = os.getenv(legacy_bearer_env_var, "")
            auth_header = request.headers.get("Authorization", "")
            token = auth_header.removeprefix("Bearer ").strip()

            if not bearer_secret:
                logger.error(
                    "[WEBHOOK] %s: neither %s (HMAC) nor %s (bearer) configured "
                    "— rejecting.",
                    platform,
                    _env_var,
                    legacy_bearer_env_var,
                )
                raise HTTPException(
                    status_code=503,
                    detail="Webhook endpoint temporarily unavailable: no secrets configured.",
                )
            if token and secrets.compare_digest(token, bearer_secret):
                logger.warning(
                    "[WEBHOOK] %s: legacy bearer token accepted — DEPRECATED. "
                    "Migrate provider to HMAC-SHA256 via %s header. "
                    "Task #1147.",
                    platform,
                    header_name,
                )
                return  # Bearer fallback OK (deprecated)
            # Bearer present but invalid
            if token:
                logger.warning(
                    "[WEBHOOK] %s: bearer token invalid — 401",
                    platform,
                )
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Authorization bearer token",
                )

        # Path 3: No signature, no bearer → reject
        logger.warning(
            "[WEBHOOK] %s: no %s header and no Authorization bearer — 401",
            platform,
            header_name,
        )
        raise HTTPException(
            status_code=401,
            detail=f"Missing {header_name} header",
        )

    return _dependency
