"""
Protected Attributes Registry — single source of truth.

Loads from config/protected_attributes.yaml and exposes as importable constants.

Usage:
    from app.shared.compliance.protected_attributes import (
        PROTECTED_ATTRIBUTE_IDS,
        PROTECTED_DB_FIELDS,
        BIAS_AUDIT_DIMENSIONS,
        get_attribute,
        get_all_aliases,
    )
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

# Canonical path: app/config/protected_attributes.yaml
# This file lives at app/shared/compliance/, so go up two levels to reach app/,
# then into app/config/. Single canonical assignment — DO NOT add a second
# `_CONFIG_PATH = ...` reassignment (caused the ADR-031 v2 bug 2026-05-06,
# where `app/shared/config/...` resolved to a non-existent path and made
# FairnessGuard run fail-OPEN since Mar 2026).
_CONFIG_PATH = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "config", "protected_attributes.yaml"
    )
)


@lru_cache(maxsize=1)
def _load_config() -> dict:
    """Load and cache the YAML config.

    Behavior:
      - Returns the parsed dict on success.
      - Logs LOUD error + Sentry breadcrumb on failure, then returns {}
        for backward compat (callers must check `is_registry_loaded()`
        before relying on populated constants).

    Fail-closed enforcement is delegated to FairnessGuard / startup
    sanity check (`is_registry_loaded()`) so tests can still import this
    module without requiring the YAML.
    """
    try:
        import yaml
        with open(_CONFIG_PATH) as f:
            data = yaml.safe_load(f) or {}
        if not data or not data.get("attributes"):
            logger.error(
                "[ProtectedAttributes] YAML loaded but EMPTY at %s — "
                "FairnessGuard would fail-open. LGPD compliance gap.",
                _CONFIG_PATH,
            )
        else:
            logger.info(
                "[ProtectedAttributes] loaded %d attributes from %s",
                len(data.get("attributes", [])), _CONFIG_PATH,
            )
        return data
    except FileNotFoundError as exc:
        logger.error(
            "[ProtectedAttributes] YAML NOT FOUND at %s — FairnessGuard will run "
            "XXfail-OPEN (LGPD gap). Verify path resolver.XX",
            _CONFIG_PATH, exc_info=True,
        )
        _emit_sentry_breadcrumb("yaml_not_found", str(exc))
        return {}
    except Exception as exc:
        logger.error(
            "[ProtectedAttributes] Failed to load YAML at %s: %s",
            _CONFIG_PATH, exc, exc_info=True,
        )
        _emit_sentry_breadcrumb("yaml_parse_error", str(exc))
        return {}


def _emit_sentry_breadcrumb(category: str, msg: str) -> None:
    """Best-effort Sentry breadcrumb for compliance observability (ADR-031 §5)."""
    try:
        import sentry_sdk
        sentry_sdk.add_breadcrumb(
            category=f"compliance.protected_attributes.{category}",
            message=msg,
            level="error",
        )
    except Exception:
        # T-04 Tipo C: Sentry breadcrumb is best-effort observability;
        # never break compliance flow if sentry_sdk import/send fails.
        logger.debug(
            "[protected_attributes] sentry breadcrumb failed (best-effort)",
            exc_info=True,
        )


def is_registry_loaded() -> bool:
    """Returns True iff the YAML loaded with at least one protected attribute.

    Use at startup or before relying on PROTECTED_ATTRIBUTE_IDS / FairnessGuard
    enforcement. Fail-closed callers (`assert is_registry_loaded()`) prevent
    silent LGPD compliance gaps.
    """
    cfg = _load_config()
    return bool(cfg) and bool(cfg.get("attributes"))


def get_all_attributes() -> list[dict[str, Any]]:
    """Return the full list of protected attribute definitions."""
    return _load_config().get("attributes", [])


def get_attribute(attr_id: str) -> dict[str, Any] | None:
    """Look up a single attribute by ID."""
    for attr in get_all_attributes():
        if attr["id"] == attr_id:
            return attr
    return None


def get_all_aliases(lang: str = "both") -> set[str]:
    """Return all known aliases (PT, EN, or both) as a flat set."""
    aliases: set[str] = set()
    for attr in get_all_attributes():
        if lang in ("pt", "both"):
            aliases.update(attr.get("aliases_pt", []))
        if lang in ("en", "both"):
            aliases.update(attr.get("aliases_en", []))
    return aliases


# ---------------------------------------------------------------------------
# Pre-computed constants for fast access
# ---------------------------------------------------------------------------

def _compute_ids() -> frozenset[str]:
    return frozenset(a["id"] for a in get_all_attributes())


def _compute_db_fields() -> frozenset[str]:
    fields: set[str] = set()
    for attr in get_all_attributes():
        fields.update(attr.get("db_fields", []))
    return frozenset(fields)


def _compute_bias_audit_dimensions() -> dict[str, str]:
    """Return {attribute_id: dimension_name} for attributes with bias_audit_enabled."""
    return {
        a["id"]: a["bias_audit_dimension"]
        for a in get_all_attributes()
        if a.get("bias_audit_enabled") and a.get("bias_audit_dimension")
    }


def _compute_learning_protected_fields() -> frozenset[str]:
    """Return all DB field names + aliases that must never generate learning patterns."""
    fields: set[str] = set()
    for attr in get_all_attributes():
        fields.update(attr.get("db_fields", []))
        fields.update(attr.get("aliases_pt", []))
        fields.update(attr.get("aliases_en", []))
    return frozenset(fields)


# Lazy-initialized module-level constants
PROTECTED_ATTRIBUTE_IDS: frozenset[str] = _compute_ids()
PROTECTED_DB_FIELDS: frozenset[str] = _compute_db_fields()
BIAS_AUDIT_DIMENSIONS: dict[str, str] = _compute_bias_audit_dimensions()
LEARNING_PROTECTED_FIELDS: frozenset[str] = _compute_learning_protected_fields()
