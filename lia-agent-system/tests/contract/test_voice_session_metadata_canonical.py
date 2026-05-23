"""C.2 contract: VoiceScreeningSession.metadata canonical dataclass field.

Workstream C ticket 2 (2026-05-23).

Sprint 3.6 StudioVoicePlugin attached metadata to VoiceScreeningSession
via setattr (defensive — class lacked the field). That works in-memory
but does NOT survive the Redis JSONB round-trip via _session_to_state /
_state_to_session. This contract promotes `metadata` to a canonical
field with default empty dict + round-trip preservation.

Backward compat: legacy state dicts WITHOUT a 'metadata' key load as
empty dict, not error.
"""
from __future__ import annotations

from dataclasses import fields

import pytest

from app.domains.voice.services.voice_screening_orchestrator import (
    VoiceCoreOrchestrator,
    VoiceScreeningSession,
)


# ----------------------------------------------------------------------------
# Field declaration contract
# ----------------------------------------------------------------------------

class TestMetadataFieldDeclaration:
    def test_metadata_default_empty_dict(self):
        """C.2: VoiceScreeningSession(...).metadata defaults to {} (not None, not setattr-defensive)."""
        session = VoiceScreeningSession(
            session_id="s-1",
            candidate_id="c-1",
            candidate_name="Candidate",
            job_title="Vaga",
            company_id="company-1",
            phone_number="+5511999999999",
        )
        assert hasattr(session, "metadata"), (
            "C.2: VoiceScreeningSession must declare canonical `metadata` "
            "field (not rely on setattr defensiveness)."
        )
        assert session.metadata == {}, (
            f"C.2: default must be empty dict, got {session.metadata!r}"
        )

    def test_metadata_can_store_arbitrary_keys(self):
        """C.2: metadata is a mutable dict[str, Any] — arbitrary keys ok."""
        session = VoiceScreeningSession(
            session_id="s-2",
            candidate_id="c-2",
            candidate_name="Candidate",
            job_title="Vaga",
            company_id="company-1",
            phone_number="+5511999999999",
        )
        session.metadata["studio_agent_id"] = "agent-x"
        session.metadata["plugin_name"] = "studio_voice"
        session.metadata["custom_telemetry"] = {"nested": True}

        assert session.metadata["studio_agent_id"] == "agent-x"
        assert session.metadata["plugin_name"] == "studio_voice"
        assert session.metadata["custom_telemetry"] == {"nested": True}

    def test_metadata_field_in_dataclass_fields(self):
        """C.2: metadata is in dataclass fields() — survives introspection (Pydantic
        serialization, mypy, asdict)."""
        names = {f.name for f in fields(VoiceScreeningSession)}
        assert "metadata" in names, (
            f"C.2: 'metadata' missing from dataclass fields. Found: {sorted(names)}"
        )


# ----------------------------------------------------------------------------
# Round-trip serialization contract
# ----------------------------------------------------------------------------

class TestMetadataRoundTrip:
    def test_session_state_round_trip_preserves_metadata(self):
        """C.2: _session_to_state → _state_to_session preserves metadata content."""
        orch = VoiceCoreOrchestrator()
        original = VoiceScreeningSession(
            session_id="s-rt",
            candidate_id="c-rt",
            candidate_name="Round Trip",
            job_title="Engineer",
            company_id="company-rt",
            phone_number="+5511999999999",
        )
        original.metadata["studio_agent_id"] = "agent-xyz"
        original.metadata["plugin_name"] = "studio_voice"

        state = orch._session_to_state(original)
        assert "metadata" in state, (
            f"C.2: _session_to_state must export metadata key. Got keys: "
            f"{sorted(state.keys())}"
        )
        assert state["metadata"] == {
            "studio_agent_id": "agent-xyz",
            "plugin_name": "studio_voice",
        }

        reloaded = orch._state_to_session(state)
        assert reloaded.metadata == original.metadata

    def test_legacy_state_without_metadata_loads_with_empty(self):
        """C.2: legacy Redis state dict (pre-C.2 sessions) WITHOUT 'metadata' key
        loads with metadata={} (backward compat, no KeyError)."""
        orch = VoiceCoreOrchestrator()
        # Build a state dict that mimics a session stored before C.2 — no metadata key.
        legacy_state = {
            "session_id": "legacy-s",
            "candidate_id": "legacy-c",
            "candidate_name": "Legacy",
            "job_title": "Old Vaga",
            "company_id": "company-legacy",
            "phone_number": "+5511999990000",  # may be plain (not masked) in legacy
            "job_id": None,
            "call_sid": None,
            "status": "completed",
            "language": "pt-BR",
            "transcript_segments": [],
            "questions_asked": [],
            "started_at": None,
            "ended_at": None,
            "wsi_result": None,
            "error": None,
            "consent_verified": False,
            "job_context": None,
            "presentation_done": False,
            "voice_provider": "twilio",
            # NB: NO 'metadata' key.
        }

        reloaded = orch._state_to_session(legacy_state)
        assert reloaded.metadata == {}, (
            f"C.2: legacy state without metadata must load with empty dict, "
            f"got {reloaded.metadata!r}"
        )
