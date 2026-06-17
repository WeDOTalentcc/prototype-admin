"""
TDD — Gap E: DataCollectionVoicePlugin wording per-tenant (ai_persona).

Validates that:
1. CONSENT_QUESTION is a hardcoded LGPD literal (NEVER parameterized — Art. 7/9
   mentions WeDOTalent as legal data controller; this cannot be tenant-variable).
2. Recording notice defaults to "LIA" before persona is loaded.
3. _build_recording_notice(ai_name) returns a notice that includes the AI name.
4. on_session_initiated loads ai_persona and updates _ai_name / _ai_tone /
   _recording_notice_text when company_id is present.
5. _format_prompt adapts phrasing to the tenant's ai_tone (amigavel/casual → informal;
   formal/formal_amigavel → polite; profissional → default).

SSH-safe: only imports the plugin (lightweight chain — VoiceCorePlugin ABC, no
orchestrator/lia_models). ai_persona_service is pre-mocked via sys.modules so
the lazy import in on_session_initiated NEVER triggers the real SQLAlchemy chain.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


# ── Minimal session stub (SSH-safe, no orchestrator import) ────────────────
@dataclass
class _FakeSession:
    session_id: str = "sess-e"
    candidate_id: str = "cand-e"
    company_id: str = "co-e"
    job_id: str | None = None
    metadata: dict = field(default_factory=dict)
    transcript_segments: list | None = None


def _make_plugin(fields=None, require_verbal_consent=False):
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )
    return DataCollectionVoicePlugin(
        fields=fields or [],
        require_verbal_consent=require_verbal_consent,
    )


# ── TEST 1 — CONSENT_QUESTION is LGPD literal (no format interpolation) ────
def test_consent_question_is_lgpd_literal():
    """LGPD Art.7/9 sensor: consent text must never be parameterized.

    WeDOTalent is the legal data controller; the tenant's AI persona name
    must NOT appear in the consent question. This test acts as a regression
    guard — if CONSENT_QUESTION ever becomes an f-string or contains
    {ai_name} / {name}, this test will fail.
    """
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )
    cq = DataCollectionVoicePlugin.CONSENT_QUESTION
    # Must NOT contain format-string placeholders.
    assert "{" not in cq and "}" not in cq, (
        "LGPD violation: CONSENT_QUESTION must not contain format placeholders. "
        "WeDOTalent is the legal data controller and this text must be a "
        "hardcoded literal (LGPD Art. 7/9). Do NOT parameterize with ai_name."
    )
    # Must explicitly mention LGPD.
    assert "LGPD" in cq, "CONSENT_QUESTION must reference LGPD (Art. 7/9 compliance)."
    # Must not be empty.
    assert len(cq) > 20


# ── TEST 2 — Recording notice default before persona is loaded ──────────────
def test_recording_notice_default_contains_platform_default():
    """Before on_session_initiated runs, _recording_notice_text defaults to the
    class RECORDING_NOTICE (which is the generic platform default).
    The _ai_name defaults to 'LIA' (DEFAULT_AI_NAME canonical).
    """
    plugin = _make_plugin()
    # Class constant is still the platform default.
    assert "gravada" in DataCollectionVoicePlugin_RECORDING_NOTICE(plugin)
    # Instance default name is LIA.
    assert plugin._ai_name == "LIA"
    assert plugin._ai_tone == "profissional"

    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )
    # _recording_notice_text matches class constant before persona load.
    assert plugin._recording_notice_text == DataCollectionVoicePlugin.RECORDING_NOTICE


def DataCollectionVoicePlugin_RECORDING_NOTICE(plugin):
    """Helper to read class RECORDING_NOTICE without reaching into class."""
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )
    return DataCollectionVoicePlugin.RECORDING_NOTICE


# ── TEST 3 — _build_recording_notice includes AI name ──────────────────────
def test_build_recording_notice_includes_ai_name():
    """_build_recording_notice(ai_name) returns notice that includes the
    AI's name and retains LGPD informational content (recording mention)."""
    plugin = _make_plugin()
    notice = plugin._build_recording_notice("Sofia")
    assert "Sofia" in notice
    assert "gravada" in notice  # LGPD core content retained


# ── TEST 4 — on_session_initiated loads persona, updates wording ─────────────
@pytest.mark.asyncio
async def test_on_session_initiated_loads_persona_and_updates_wording():
    """Persona service is called when company_id + db are present.
    After the call, _ai_name, _ai_tone, and _recording_notice_text are updated.
    The notice must NOT be the generic class RECORDING_NOTICE — it must
    include the tenant's AI name.
    """
    # Inject mock BEFORE on_session_initiated lazy-imports the module.
    mock_persona_module = MagicMock()
    mock_persona_module.get_ai_persona = AsyncMock(
        return_value={"name": "Sofia", "tone": "amigavel"}
    )
    _original = sys.modules.get("app.domains.persona.services.ai_persona_service")
    sys.modules["app.domains.persona.services.ai_persona_service"] = mock_persona_module

    try:
        plugin = _make_plugin()
        session = _FakeSession(company_id="co-tenant")
        await plugin.on_session_initiated(session, db=MagicMock())

        assert plugin._ai_name == "Sofia"
        assert plugin._ai_tone == "amigavel"
        assert "Sofia" in plugin._recording_notice_text

        from app.domains.voice.plugins.data_collection_voice_plugin import (
            DataCollectionVoicePlugin,
        )
        # Must NOT be the plain class constant anymore.
        assert plugin._recording_notice_text != DataCollectionVoicePlugin.RECORDING_NOTICE
    finally:
        if _original is not None:
            sys.modules["app.domains.persona.services.ai_persona_service"] = _original
        else:
            sys.modules.pop("app.domains.persona.services.ai_persona_service", None)


# ── TEST 5 — on_session_initiated persona load failure falls back gracefully ─
@pytest.mark.asyncio
async def test_on_session_initiated_persona_failure_keeps_defaults():
    """If ai_persona_service raises, plugin falls back to defaults (LIA /
    profissional / class RECORDING_NOTICE). Call must NOT break."""
    mock_persona_module = MagicMock()
    mock_persona_module.get_ai_persona = AsyncMock(side_effect=RuntimeError("db down"))
    _original = sys.modules.get("app.domains.persona.services.ai_persona_service")
    sys.modules["app.domains.persona.services.ai_persona_service"] = mock_persona_module

    try:
        plugin = _make_plugin()
        session = _FakeSession(company_id="co-err")
        # Must not raise.
        await plugin.on_session_initiated(session, db=MagicMock())

        # Defaults preserved.
        assert plugin._ai_name == "LIA"
        assert plugin._ai_tone == "profissional"
        from app.domains.voice.plugins.data_collection_voice_plugin import (
            DataCollectionVoicePlugin,
        )
        assert plugin._recording_notice_text == DataCollectionVoicePlugin.RECORDING_NOTICE
    finally:
        if _original is not None:
            sys.modules["app.domains.persona.services.ai_persona_service"] = _original
        else:
            sys.modules.pop("app.domains.persona.services.ai_persona_service", None)


# ── TEST 6 — _format_prompt adapts to tone ────────────────────────────────

@pytest.mark.parametrize("tone,expected_fragment", [
    ("amigavel", "Pode me contar"),
    ("casual", "Pode me contar"),
    ("formal", "gentileza"),
    ("formal_amigavel", "gentileza"),
    ("profissional", "Poderia me informar"),
    ("empatico", "Poderia me informar"),  # unknown tone → profissional default
])
def test_format_prompt_adapts_to_tone(tone, expected_fragment):
    """_format_prompt returns tone-appropriate phrasing for non-sensitive fields."""
    plugin = _make_plugin()
    plugin._ai_tone = tone
    prompt = SimpleNamespace(label="seu nome completo", name="full_name", sensitive=False)
    result = plugin._format_prompt(prompt)
    assert expected_fragment in result, (
        f"Tone '{tone}': expected '{expected_fragment}' in '{result}'"
    )


def test_format_prompt_sensitive_is_tone_independent():
    """Sensitive field prompt is unchanged regardless of tone (confirmation wording)."""
    plugin = _make_plugin()
    for tone in ("amigavel", "formal", "profissional"):
        plugin._ai_tone = tone
        prompt = SimpleNamespace(label="seu CPF", name="cpf", sensitive=True)
        result = plugin._format_prompt(prompt)
        assert "sensível" in result or "confirmar" in result, (
            f"Sensitive prompt unchanged for tone '{tone}'"
        )
