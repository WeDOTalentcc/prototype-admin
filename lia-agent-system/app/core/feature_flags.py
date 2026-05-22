"""
Lightweight feature-flag accessor for runtime hot paths.

Sprint 3.5 (W4-1 V2): Created to gate ``channel="voice"`` in
``CustomAgentRuntime.invoke``. The canonical DB-backed implementation lives
in ``app.shared.governance.feature_flag_service.FeatureFlagService`` and
requires an ``AsyncSession``; pulling a session inside every runtime invoke
is wasteful for a boolean gate that flips per-tenant rollout.

This module provides:

* ``is_enabled(flag_key, company_id=None)`` — sync function for fast-path
  checks. Resolution order:
    1. Environment override:
         - ``FEATURE_FLAG_<flag_key.upper()>`` (global, e.g.
           ``FEATURE_FLAG_VOICE_SCREENING_V2_ENABLED=1``)
         - ``FEATURE_FLAG_<flag_key.upper()>__<company_id>`` (per tenant)
       Values ``1``/``true``/``yes``/``on`` are truthy.
    2. Default value from ``FeatureFlagService.DEFAULT_FLAGS``.

* ``is_enabled_async(flag_key, db, company_id=None)`` — async helper that
  delegates to the canonical DB-backed ``FeatureFlagService`` when callers
  already hold an AsyncSession.

Per-tenant rollouts with ``rollout_percentage`` continue to live in the DB.
Use the env-var form for sandbox/CI/explicit tenant overrides.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_TRUTHY = frozenset({"1", "true", "yes", "on", "enabled"})


def _env_truthy(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in _TRUTHY


def is_enabled(flag_key: str, company_id: str | None = None) -> bool:
    """Synchronous feature flag check (env var + default fallback).

    Args:
        flag_key: canonical flag name (must exist in
            ``FeatureFlagService.DEFAULT_FLAGS``).
        company_id: optional tenant uuid for per-tenant override via
            ``FEATURE_FLAG_<KEY>__<company_id>`` env var.

    Returns:
        Bool gate. Logs warning for unknown flags but returns ``False`` to
        fail closed.
    """
    flag_upper = flag_key.upper()

    # Per-tenant env override (highest priority)
    if company_id:
        tenant_var = f"FEATURE_FLAG_{flag_upper}__{company_id}"
        tenant_val = os.environ.get(tenant_var)
        if tenant_val is not None:
            return _env_truthy(tenant_val)

    # Global env override
    global_var = f"FEATURE_FLAG_{flag_upper}"
    global_val = os.environ.get(global_var)
    if global_val is not None:
        return _env_truthy(global_val)

    # Default from canonical DEFAULT_FLAGS
    try:
        from app.shared.governance.feature_flag_service import FeatureFlagService
        meta: dict[str, Any] = FeatureFlagService.DEFAULT_FLAGS.get(flag_key, {})
        if not meta:
            logger.warning(
                "[feature_flags] unknown flag %r — defaulting to False",
                flag_key,
            )
            return False
        return bool(meta.get("default", False))
    except Exception as exc:
        logger.warning(
            "[feature_flags] DEFAULT_FLAGS lookup failed for %r: %s",
            flag_key, exc,
        )
        return False


async def is_enabled_async(
    flag_key: str,
    db: Any,
    company_id: str | None = None,
) -> bool:
    """Async wrapper delegating to canonical FeatureFlagService.

    Use this when the caller already holds an AsyncSession (e.g. inside an
    HTTP handler). For fast paths without a session, call ``is_enabled``.
    """
    try:
        from app.shared.governance.feature_flag_service import FeatureFlagService
        service = FeatureFlagService()
        return await service.is_enabled(db, flag_key, company_id)
    except Exception as exc:
        logger.warning(
            "[feature_flags] async lookup failed for %r: %s — falling back",
            flag_key, exc,
        )
        return is_enabled(flag_key, company_id)
