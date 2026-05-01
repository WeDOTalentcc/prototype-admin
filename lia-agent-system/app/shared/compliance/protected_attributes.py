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

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "app", "config", "protected_attributes.yaml"
)
# Resolve relative to this file's location
_CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "config", "protected_attributes.yaml")
)


@lru_cache(maxsize=1)
def _load_config() -> dict:
    """Load and cache the YAML config. Returns empty dict on failure."""
    try:
        import yaml
        with open(_CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:
        logger.error("[ProtectedAttributes] Failed to load YAML: %s", exc)
        return {}


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
