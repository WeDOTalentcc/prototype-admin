"""i18n helper for wizard node messages — PR-18 F-4.1 (2026-05-26).

Loads PT-BR strings from app/prompts/job_creation/messages.yaml.

Usage::

    from app.domains.job_creation.helpers.i18n import msg

    text = msg("handoff.job_ready")
    text = msg("eligibility.questions_configured", count=3)
    text = msg("calibration.complete", approved_count=2, threshold=3)

Design principles:
- Single source of truth: all user-facing wizard strings live in messages.yaml.
- Fail-open: ``msg()`` returns the key itself when not found so the wizard
  never crashes due to a missing translation key.
- Cached: YAML is loaded once per process via ``lru_cache``.
- No fallback suppression: missing keys are logged as WARNING so they are
  auditable without silently returning empty strings.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# Path: lia-agent-system/app/prompts/job_creation/messages.yaml
# Resolved relative to THIS file: helpers/ → job_creation/ → domains/ → app/ → prompts/
_MESSAGES_FILE = (
    Path(__file__).resolve()
    .parent  # helpers/
    .parent  # job_creation/
    .parent  # domains/
    .parent  # app/
    / "prompts"
    / "job_creation"
    / "messages.yaml"
)


@lru_cache(maxsize=1)
def _load_messages() -> dict:
    """Load and cache messages from YAML (loaded once per process)."""
    if not _MESSAGES_FILE.exists():
        logger.warning(
            "i18n messages file not found at %s — all msg() calls will return keys",
            _MESSAGES_FILE,
        )
        return {}
    try:
        with open(_MESSAGES_FILE, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        logger.debug("i18n loaded %d top-level namespaces from %s", len(data), _MESSAGES_FILE)
        return data
    except Exception as exc:  # noqa: BLE001
        logger.error("i18n failed to load %s: %s", _MESSAGES_FILE, exc)
        return {}


def msg(key: str, **kwargs: Any) -> str:
    """Return a wizard message string by dotted key, with optional substitution.

    Args:
        key: Dotted key like ``"handoff.job_ready"`` or
             ``"eligibility.questions_configured"``.
        **kwargs: Named substitution args for ``{var}`` placeholders in the
                  message template.

    Returns:
        Formatted message string.  Falls back to ``key`` itself if the key
        is not found or the YAML file is unavailable (fail-open, never raises).

    Examples::

        >>> msg("handoff.job_ready")
        'Vaga pronta! Vou levar você para a página da vaga'

        >>> msg("eligibility.questions_configured", count=3)
        'Configurei 3 pergunta(s) eliminatória(s) para a triagem inicial.'

        >>> msg("missing.key")
        'missing.key'   # fail-open: returns key
    """
    messages = _load_messages()
    parts = key.split(".")
    value: Any = messages
    for part in parts:
        if not isinstance(value, dict):
            logger.warning(
                "i18n key %r not found — stopped at %r (parent is not a dict)",
                key,
                part,
            )
            return key
        value = value.get(part)
        if value is None:
            logger.warning("i18n key %r not found in messages.yaml", key)
            return key

    if not isinstance(value, str):
        logger.warning("i18n key %r resolved to %r, expected str — returning key", key, type(value).__name__)
        return key

    if not kwargs:
        return value

    try:
        return value.format(**kwargs)
    except (KeyError, IndexError) as exc:
        logger.warning(
            "i18n key %r format error (%s) — returning unformatted template",
            key,
            exc,
        )
        return value
