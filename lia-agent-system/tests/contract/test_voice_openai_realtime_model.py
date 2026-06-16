"""Contract test: OpenAI Realtime provider uses canonical (non-deprecated) model.

Pins the canonical model literal to ``gpt-realtime`` (GA since 2025-09-08).
The previous default ``gpt-4o-realtime-preview`` was DEPRECATED by OpenAI on
2026-05-12; any regression to that string would silently break production
voice sessions (404 / model_not_found) the next time the cache expires.

Companion sensor:
  ``scripts/check_realtime_uses_canonical_model.py`` (BLOCKING in CI) —
  detects the deprecated string literal anywhere under ``app/``.
"""
from __future__ import annotations


def test_canonical_model_is_gpt_realtime_not_deprecated_preview():
    """OPENAI_REALTIME_MODEL MUST be gpt-realtime, NOT the deprecated preview."""
    from app.shared.providers.voice_openai_realtime import OPENAI_REALTIME_MODEL

    assert OPENAI_REALTIME_MODEL == "gpt-realtime", (
        f"Canonical Realtime model regressed! Got {OPENAI_REALTIME_MODEL!r}; "
        "must be 'gpt-realtime' (GA). 'gpt-4o-realtime-preview' was "
        "DEPRECATED by OpenAI on 2026-05-12 and will 404 in production."
    )
    # Belt + suspenders: explicit deny-list of known-bad strings.
    assert "preview" not in OPENAI_REALTIME_MODEL.lower(), (
        "Realtime model contains 'preview' — preview models are temporary "
        "and get deprecated. Use the GA name."
    )


def test_canonical_model_constant_is_string():
    """Sanity: must be str, not Enum / settings lookup."""
    from app.shared.providers.voice_openai_realtime import OPENAI_REALTIME_MODEL

    assert isinstance(OPENAI_REALTIME_MODEL, str)
    assert OPENAI_REALTIME_MODEL.strip() == OPENAI_REALTIME_MODEL
