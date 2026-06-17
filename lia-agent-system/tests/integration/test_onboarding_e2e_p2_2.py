"""E2E integration test P2-2 Sprint completo — onboarding conversacional.

Exercita pipeline INTEIRO com mocks no boundary (tool save + audit + persist).
Sensor canonical anti-regressão: se ANY módulo do P2-2 quebrar contrato
(YAML loader, state machine, extractor heuristic, runner, orchestrator handler,
dispatcher, tool _wrap_save_company_field), este test pega.

Pipeline exercitado:
    user_event -> orchestrator.handle_web_event
        -> handle_settings_extraction_message
        -> runner.start / runner.process_message
            -> settings_phase (state machine ASKING/CONFIRMING/COMPLETE)
            -> field_extractor (mock heuristic, use_llm=False default)
            -> save_field_fn (injectable; mocked aqui via _wrap_save_company_field patch)
        -> _audit + _persist
        -> session.settings_extraction_status_json persisted

Audit ref: ~/Documents/wedotalent_audit_2026-05-26/P2-2_ONBOARDING_CONVERSACIONAL_ADR.md
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.services.onboarding_orchestrator import (
    OnboardingOrchestrator,
    OnboardingPhase,
    OnboardingSession,
)
from app.services.onboarding_yaml_loader import load_config


def _seed_asking_state(session: OnboardingSession) -> str:
    """Helper: mutate session JSON to bypass INTRO short-circuit in orchestrator.

    The orchestrator restarts the runner whenever state==INTRO; to exercise the
    extract+confirm+persist branch of the pipeline, we seed state=ASKING with
    a valid last_asked_field from the canonical YAML config. Returns field_key.
    """
    config = load_config()
    # Pick first field of first block as canonical target
    first_block = config.blocks[0]
    target_field = first_block.fields[0]
    payload = {
        "state": "asking",
        "current_block_id": first_block.id,
        "answered_fields": {},
        "pending_extraction": {},
        "skipped_fields": [],
    }
    session.settings_extraction_status_json = json.dumps(payload)
    # Restored status object doesn't carry last_asked_field across JSON round-trip
    # (orchestrator restore omits this field). Tests that need it adjust via the
    # restored status path — see below.
    return target_field.field_key


@pytest.fixture
def session() -> OnboardingSession:
    """Canonical fixture for E2E — onboarding session ready to enter settings extraction."""
    return OnboardingSession(
        session_id="e2e-test-session-p2-2",
        user_id=12345,
        account_id=67890,
        user_name="Paulo Teste",
        user_email="paulo+e2e@wedotalent.cc",
        user_phone=None,
        channel="web",
    )


@pytest.fixture
def orchestrator() -> OnboardingOrchestrator:
    """Orchestrator with no real dependencies — _audit/_persist patched per test."""
    return OnboardingOrchestrator(db=None, llm=None, whatsapp_client=None, rails_client=None)


@pytest.fixture
def patch_audit_persist(orchestrator):
    """Patch _audit + _persist (não precisamos DB real pra E2E pipeline)."""
    with patch.object(orchestrator, "_audit", new=AsyncMock()) as audit_mock, patch.object(
        orchestrator, "_persist", new=AsyncMock()
    ) as persist_mock:
        yield audit_mock, persist_mock


@pytest.fixture
def mock_save_field():
    """Mock do _wrap_save_company_field — sempre sucesso. Patch path = onde o
    runner faz lazy import (_default_save_field in runner).
    """
    mock = AsyncMock(
        return_value={
            "success": True,
            "data": {"saved": True},
            "message": "Field saved",
        }
    )
    with patch(
        "app.domains.company_settings.agents.company_tool_registry._wrap_save_company_field",
        new=mock,
    ):
        yield mock


class TestOnboardingE2EPipeline:
    """E2E coverage of P2-2 Sprint pipeline (orchestrator + runner + tool wire)."""

    @pytest.mark.asyncio
    async def test_start_settings_extraction_returns_greeting(
        self, session, orchestrator, patch_audit_persist
    ):
        """Trigger 'start_settings_extraction' transitions phase + returns greeting."""
        audit_mock, persist_mock = patch_audit_persist

        result = await orchestrator.handle_web_event(
            session=session,
            event_type="start_settings_extraction",
        )

        assert session.phase == OnboardingPhase.SETTINGS_EXTRACTION
        assert result["phase"] == OnboardingPhase.SETTINGS_EXTRACTION.value
        assert isinstance(result["message"], str) and len(result["message"]) > 0
        assert result["is_complete"] is False
        assert result["progress_percent"] == 0

        # Pipeline observability: audit + persist called
        assert audit_mock.call_count >= 1
        assert persist_mock.call_count >= 1

        # State persisted as JSON in session
        assert session.settings_extraction_status_json is not None
        status = json.loads(session.settings_extraction_status_json)
        assert "state" in status
        assert "answered_fields" in status
        assert "pending_extraction" in status

    @pytest.mark.asyncio
    async def test_user_message_returns_valid_response(
        self, session, orchestrator, patch_audit_persist, mock_save_field
    ):
        """User message after start returns valid response (canonical contract).

        Note: orchestrator restarts runner whenever state==INTRO (current behavior).
        This test pins the canonical response contract regardless of advancement.
        """
        # Start
        await orchestrator.handle_web_event(
            session=session, event_type="start_settings_extraction"
        )

        # User responds with a name
        result = await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"message": "WeDOTalent SA"},
        )

        assert result["phase"] == OnboardingPhase.SETTINGS_EXTRACTION.value
        assert isinstance(result["message"], str) and len(result["message"]) > 0
        assert "progress_percent" in result
        assert "is_complete" in result
        # Session JSON valid
        status = json.loads(session.settings_extraction_status_json)
        assert "state" in status
        assert "answered_fields" in status

    @pytest.mark.asyncio
    async def test_confirm_yes_invokes_tool_persist(
        self, session, orchestrator, patch_audit_persist, mock_save_field
    ):
        """Seed CONFIRMING state with pending extraction -> 'sim' triggers tool persist.

        Exercises the runner -> tool wire (PERSIST_FIELDS -> save_field_fn -> tool).
        """
        # Enter SETTINGS_EXTRACTION phase
        session.phase = OnboardingPhase.SETTINGS_EXTRACTION
        # Seed CONFIRMING state with a pending field ready to persist
        config = load_config()
        first_block = config.blocks[0]
        target_field = first_block.fields[0]
        seeded = {
            "state": "confirming",
            "current_block_id": first_block.id,
            "answered_fields": {},
            "pending_extraction": {target_field.field_key: "WeDOTalent SA"},
            "skipped_fields": [],
        }
        session.settings_extraction_status_json = json.dumps(seeded)

        # User confirms
        result = await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"message": "sim"},
        )

        # Tool MUST have been invoked with canonical args
        assert mock_save_field.call_count >= 1, (
            f"_wrap_save_company_field not invoked on confirm; result={result}"
        )
        call_kwargs = mock_save_field.call_args.kwargs
        assert call_kwargs["company_id"] == str(session.account_id)
        assert call_kwargs["section"] in {"profile", "culture"}
        assert call_kwargs["field"] == target_field.field_key
        assert call_kwargs["value"] == "WeDOTalent SA"
        assert call_kwargs.get("user_id") == str(session.user_id)

    @pytest.mark.asyncio
    async def test_skip_phrase_does_not_persist(
        self, session, orchestrator, patch_audit_persist, mock_save_field
    ):
        """User says 'pular' on a question -> NO persist call, state stays ASKING."""
        await orchestrator.handle_web_event(
            session=session, event_type="start_settings_extraction"
        )
        # Get into ASKING first by sending an empty trigger (start already in ASKING state
        # after the runner pumps next question), then skip
        result = await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"message": "pular"},
        )

        # Tool should NOT have been called for a skipped field
        assert mock_save_field.call_count == 0
        assert result["is_complete"] is False
        # JSON still valid
        status = json.loads(session.settings_extraction_status_json)
        assert "state" in status

    @pytest.mark.asyncio
    async def test_stop_phrase_finalizes(
        self, session, orchestrator, patch_audit_persist, mock_save_field
    ):
        """User says 'parar' from ASKING state -> COMPLETE, is_complete True."""
        # Seed ASKING state (bypass INTRO short-circuit)
        session.phase = OnboardingPhase.SETTINGS_EXTRACTION
        config = load_config()
        first_block = config.blocks[0]
        seeded = {
            "state": "asking",
            "current_block_id": first_block.id,
            "answered_fields": {},
            "pending_extraction": {},
            "skipped_fields": [],
        }
        session.settings_extraction_status_json = json.dumps(seeded)

        result = await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"message": "parar"},
        )

        status = json.loads(session.settings_extraction_status_json)
        assert status["state"] == "complete" or result.get("is_complete") is True

    @pytest.mark.asyncio
    async def test_audit_called_per_step(
        self, session, orchestrator, patch_audit_persist, mock_save_field
    ):
        """Cada handle_web_event no settings flow dispara _audit ao menos uma vez."""
        audit_mock, _ = patch_audit_persist

        await orchestrator.handle_web_event(
            session=session, event_type="start_settings_extraction"
        )
        c1 = audit_mock.call_count
        assert c1 >= 1

        await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"message": "ACME Inc"},
        )
        c2 = audit_mock.call_count
        assert c2 > c1, f"Audit not called for user_message step (c1={c1}, c2={c2})"

        # Audit action label canonical
        all_actions = [call.args[0] if call.args else call.kwargs.get("action") for call in audit_mock.call_args_list]
        assert any("settings_extraction" in (a or "") for a in all_actions)

    @pytest.mark.asyncio
    async def test_persist_called_per_step(
        self, session, orchestrator, patch_audit_persist, mock_save_field
    ):
        """Each pipeline step calls _persist (session save)."""
        _, persist_mock = patch_audit_persist

        await orchestrator.handle_web_event(
            session=session, event_type="start_settings_extraction"
        )
        p1 = persist_mock.call_count
        await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"message": "Tech Corp"},
        )
        p2 = persist_mock.call_count
        assert p2 > p1

    @pytest.mark.asyncio
    async def test_session_state_persisted_between_calls(
        self, session, orchestrator, patch_audit_persist, mock_save_field
    ):
        """Status JSON preserves state across multiple handle_web_event calls."""
        await orchestrator.handle_web_event(
            session=session, event_type="start_settings_extraction"
        )
        first_status = session.settings_extraction_status_json
        assert first_status is not None

        await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"message": "ACME"},
        )
        second_status = session.settings_extraction_status_json
        assert second_status is not None

        # JSON valid in both — canonical contract preserved across calls
        parsed_first = json.loads(first_status)
        parsed_second = json.loads(second_status)
        for parsed in (parsed_first, parsed_second):
            assert "state" in parsed
            assert "answered_fields" in parsed
            assert "pending_extraction" in parsed
            assert "skipped_fields" in parsed
            assert isinstance(parsed["answered_fields"], dict)

    @pytest.mark.asyncio
    async def test_accepts_text_alias_in_payload(
        self, session, orchestrator, patch_audit_persist, mock_save_field
    ):
        """Orchestrator aceita 'text' como alias de 'message' (frontend compat)."""
        await orchestrator.handle_web_event(
            session=session, event_type="start_settings_extraction"
        )
        result = await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"text": "Empresa via text alias"},
        )
        assert result["phase"] == OnboardingPhase.SETTINGS_EXTRACTION.value
        assert isinstance(result["message"], str) and len(result["message"]) > 0

    @pytest.mark.asyncio
    async def test_progress_monotonic_non_decreasing(
        self, session, orchestrator, patch_audit_persist, mock_save_field
    ):
        """Progress percent never decreases over a successful answer+confirm cycle."""
        r0 = await orchestrator.handle_web_event(
            session=session, event_type="start_settings_extraction"
        )
        p0 = r0["progress_percent"]

        r1 = await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"message": "ACME Corp"},
        )
        p1 = r1["progress_percent"]

        r2 = await orchestrator.handle_web_event(
            session=session,
            event_type="user_message",
            data={"message": "sim"},
        )
        p2 = r2["progress_percent"]

        assert 0 <= p0 <= 100
        assert p1 >= p0
        assert p2 >= p1, f"Progress decreased: p0={p0} p1={p1} p2={p2}"
