"""
Unit tests for DataCollectionVoicePlugin (Voz Fase 2).

Validates the 4-method VoiceCorePlugin contract for the data-collection flow
that "lights up" the previously-dead voice_collection_script.py.

SSH note: heavy deps (orchestrator / lia_models registry) are mocked or simply
not imported at module top. The plugin imports voice_collection_script lazily
INSIDE its hooks, so these tests patch that module path. The real
``normalize_field_value`` / ``build_collection_script`` are pure (no I/O) so
TEST 2/3 use the real functions; TEST 4 patches ``normalize_field_value`` to
assert the plugin routes through it.
"""
from __future__ import annotations

import sys
import types
from dataclasses import dataclass

import pytest

# ── Lightweight stub for the VoiceScreeningSession (avoid heavy orchestrator import)
@dataclass
class _FakeSession:
    session_id: str = "sess-1"
    candidate_id: str = "cand-1"
    company_id: str = "co-1"
    job_id: str | None = None
    job_title: str = "Coleta de dados"
    metadata: dict | None = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def _make_plugin(fields, completed=None):
    from app.domains.voice.plugins.data_collection_voice_plugin import (
        DataCollectionVoicePlugin,
    )

    return DataCollectionVoicePlugin(fields=fields, completed_names=completed or [])


# ── TEST 1 — plugin_name identity (and NOT wsi_screening) ──────────────────
@pytest.mark.asyncio
async def test_plugin_name_is_data_collection_not_wsi():
    plugin = _make_plugin([])
    assert plugin.plugin_name == "data_collection"
    # Fase 0.5 gate keys off == "wsi_screening"; this must NOT match.
    assert plugin.plugin_name != "wsi_screening"


# ── TEST 2 — on_session_initiated builds field list; portal-only separated ──
@pytest.mark.asyncio
async def test_on_session_initiated_separates_portal_only():
    # 2 voice-collectable (text, cpf) + 1 portal-only (file).
    fields = [
        {"name": "full_name", "label": "seu nome completo", "field_type": "text", "is_required": True},
        {"name": "cpf", "label": "seu CPF", "field_type": "cpf", "is_required": True},
        {"name": "id_doc", "label": "documento de identidade", "field_type": "file", "is_required": True},
    ]
    plugin = _make_plugin(fields)
    session = _FakeSession()

    await plugin.on_session_initiated(session, db=None)

    voice_names = [p.name for p in plugin._voice_prompts]
    assert voice_names == ["full_name", "cpf"]
    assert plugin._portal_only_names == ["id_doc"]
    # Telemetry mirrored to session metadata.
    assert session.metadata["plugin_name"] == "data_collection"
    assert session.metadata["data_collection_voice_fields"] == ["full_name", "cpf"]
    assert session.metadata["data_collection_portal_fields"] == ["id_doc"]


# ── TEST 3 — get_next_question returns each prompt in order, then None ──────
@pytest.mark.asyncio
async def test_get_next_question_sequential_then_none():
    fields = [
        {"name": "full_name", "label": "seu nome completo", "field_type": "text", "is_required": True},
        {"name": "email", "label": "seu e-mail", "field_type": "email", "is_required": True},
    ]
    plugin = _make_plugin(fields)
    session = _FakeSession()
    await plugin.on_session_initiated(session, db=None)

    q1 = await plugin.get_next_question(session, db=None)
    q2 = await plugin.get_next_question(session, db=None)
    q3 = await plugin.get_next_question(session, db=None)

    assert q1 is not None and "nome completo" in q1
    assert q2 is not None and "e-mail" in q2
    assert q3 is None  # exhausted → core wraps up


# ── TEST 4 — finalize extracts + normalizes; unextractable → needs_followup ─
@pytest.mark.asyncio
async def test_on_session_finalized_extracts_and_marks_followup(monkeypatch):
    fields = [
        {"name": "full_name", "label": "seu nome completo", "field_type": "text", "is_required": True},
        {"name": "cpf", "label": "seu CPF", "field_type": "cpf", "is_required": True},
        {"name": "email", "label": "seu e-mail", "field_type": "email", "is_required": True},
    ]
    plugin = _make_plugin(fields)
    session = _FakeSession()
    await plugin.on_session_initiated(session, db=None)

    # Patch normalize_field_value to assert the plugin routes through it.
    from app.domains.communication.services import voice_collection_script as vcs

    NV = vcs.NormalizedValue

    calls: list[tuple[str, str]] = []

    def _fake_normalize(field_type, raw):
        calls.append((field_type, raw))
        if field_type == "text":
            return NV("Maria Silva", True, None)
        if field_type == "cpf":
            return NV(None, False, "cpf_invalid_length")  # invalid → followup
        return NV(raw, True, None)

    monkeypatch.setattr(vcs, "normalize_field_value", _fake_normalize)

    # Transcript: full_name + cpf answered; email NOT answered (only 2 cand turns).
    transcript = [
        {"role": "assistant", "text": "Poderia me informar seu nome completo?"},
        {"role": "candidate", "text": "Maria Silva"},
        {"role": "assistant", "text": "Poderia me informar seu CPF?"},
        {"role": "candidate", "text": "doze"},
    ]

    result = await plugin.on_session_finalized(session, db=None, transcript=transcript)

    assert result["strategy"] == "data_collection"
    # full_name extracted + normalized (valid).
    assert result["collected"]["full_name"]["value"] == "Maria Silva"
    assert result["collected"]["full_name"]["valid"] is True
    # cpf invalid → marked needs_followup, value NOT faked.
    assert "cpf" in result["needs_followup"]
    assert result["collected"]["cpf"]["value"] is None
    assert result["collected"]["cpf"]["valid"] is False
    # email had NO candidate utterance → needs_followup, NOT faked.
    assert "email" in result["needs_followup"]
    assert "email" not in result["collected"]
    # normalize_field_value was actually called for the answered fields.
    assert ("text", "Maria Silva") in calls
    assert ("cpf", "doze") in calls
