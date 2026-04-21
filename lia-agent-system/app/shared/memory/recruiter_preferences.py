"""Onda 3.5 Init III MVP (2026-04-21) — Episodic memory layer via
conversation_summaries.user_preferences JSON column.

Stores recruiter-level preferences learned across conversations:
  - preferred_top_n: int (e.g. recruiter always asks top-5 not top-10)
  - last_filters: dict (most recent search filters applied)
  - favored_stages: list[str] (pipeline stages recruiter focuses on)
  - communication_channel: str (email vs whatsapp preference)

Does NOT store raw PII (candidate names, CPFs, etc.) — only structured
preferences. PII guard at set_preference validates via pii_masking regexes.

Integration (future Init III.B): ConversationState hydrates from this
store at conv start; write-back on key recruiter actions.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_EPISODIC_MEMORY_ENABLED = os.environ.get(
    "LIA_EPISODIC_MEMORY_ENABLED", "true"
).lower() == "true"


# Allowed keys for recruiter preferences — schema guard. Extending this list
# requires reviewing LGPD implications (each new key = data retention policy).
_ALLOWED_KEYS: frozenset[str] = frozenset({
    "preferred_top_n",
    "last_filters",
    "favored_stages",
    "communication_channel",
    "locale_preference",
    "briefing_style",  # "short" | "detailed"
    "last_seen_at",
})


def _contains_pii(value: Any) -> bool:
    """Guard: refuse to store values containing likely PII patterns."""
    from app.shared.pii_masking import (
        CPF_PATTERN, EMAIL_PATTERN, PHONE_BR_PATTERN,
    )
    serialized = str(value)
    for pattern in (CPF_PATTERN, EMAIL_PATTERN, PHONE_BR_PATTERN):
        if pattern.search(serialized):
            return True
    return False


def set_preference(
    current_preferences: dict[str, Any] | None,
    key: str,
    value: Any,
) -> dict[str, Any]:
    """Set a single preference. Returns updated dict (immutable-style).

    - Rejects keys not in _ALLOWED_KEYS (schema guard)
    - Rejects values containing PII (LGPD defense)
    - Preserves existing preferences

    Args:
        current_preferences: existing user_preferences dict (or None)
        key: preference key (must be in _ALLOWED_KEYS)
        value: preference value (scalar / list / dict without PII)

    Returns:
        New preferences dict with the key set.

    Raises:
        ValueError: on schema or PII violation.
    """
    if not _EPISODIC_MEMORY_ENABLED:
        return current_preferences or {}

    if key not in _ALLOWED_KEYS:
        raise ValueError(
            f"Init III MVP: key {key!r} not in allowed schema. "
            f"Allowed: {sorted(_ALLOWED_KEYS)}"
        )

    if _contains_pii(value):
        logger.warning(
            "[LIA-MEMSET] blocked PII in preference key=%s (LGPD guard)",
            key,
        )
        raise ValueError(
            f"Init III MVP: value for {key!r} contains PII pattern — "
            f"refusing to store per LGPD policy"
        )

    updated = dict(current_preferences or {})
    updated[key] = value
    logger.info(
        "[LIA-MEMSET] preference set key=%s type=%s",
        key, type(value).__name__,
    )
    return updated


def get_preference(
    preferences: dict[str, Any] | None,
    key: str,
    default: Any = None,
) -> Any:
    """Get a single preference, return default if missing or disabled."""
    if not _EPISODIC_MEMORY_ENABLED or not preferences:
        return default
    return preferences.get(key, default)


def list_allowed_keys() -> list[str]:
    """Return the list of allowed preference keys (schema introspection)."""
    return sorted(_ALLOWED_KEYS)
