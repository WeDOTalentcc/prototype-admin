"""Tests for onboarding_settings_runner -- P2-2 Sprint A.4."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.services.onboarding_field_extractor import ExtractionResult
from app.services.onboarding_settings_phase import (
    SettingsExtractionState,
    SettingsExtractionStatus,
)
from app.services.onboarding_settings_runner import (
    RunnerResponse,
    _resolve_section_for_field,
    process_message,
    start,
)
from app.services.onboarding_yaml_loader import load_config


COMPANY_ID = "test-company-uuid"
USER_ID = "test-user-uuid"


def _ok_save() -> AsyncMock:
    """Mock save_field_fn that returns success."""
    return AsyncMock(return_value={"success": True, "data": {}, "message": "ok"})


def _fail_save(msg: str = "DB falhou") -> AsyncMock:
    return AsyncMock(return_value={"success": False, "message": msg})


# -------------------- start() --------------------


class TestStart:
    @pytest.mark.asyncio
    async def test_start_returns_greeting(self):
        resp = await start(COMPANY_ID)
        assert isinstance(resp, RunnerResponse)
        config = load_config()
        assert resp.user_message == config.persona_greeting
        assert len(resp.user_message) > 0

    @pytest.mark.asyncio
    async def test_start_initializes_status_intro(self):
        resp = await start(COMPANY_ID)
        assert resp.status.state == SettingsExtractionState.INTRO
        assert resp.is_complete is False
        assert resp.progress_percent == 0


# -------------------- process_message() --------------------


class TestProcessMessage:
    @pytest.mark.asyncio
    async def test_intro_to_first_question(self):
        """Em INTRO, qualquer msg avanca pra primeira pergunta (ASKING)."""
        start_resp = await start(COMPANY_ID)
        save = _ok_save()
        resp = await process_message(
            status=start_resp.status,
            user_message="vamos la",
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
        )
        assert resp.status.state == SettingsExtractionState.ASKING
        assert resp.status.last_asked_field is not None
        assert len(resp.user_message) > 0
        # Nada foi salvo ainda
        save.assert_not_called()
        assert resp.is_complete is False

    @pytest.mark.asyncio
    async def test_asking_normal_message_triggers_extract_and_confirm(self):
        """Resposta normal em ASKING -> extract (mock) -> CONFIRMING."""
        # Setup: simular state ASKING com um campo perguntado
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.ASKING,
            current_block_id=None,
            last_asked_field=None,
        )
        # Carregar primeiro field real do config pra ter target_field valido
        config = load_config()
        first_block = config.blocks[0]
        first_field = first_block.fields[0]
        status.current_block_id = first_block.id
        status.last_asked_field = first_field.field_key

        save = _ok_save()
        resp = await process_message(
            status=status,
            user_message="Somos uma empresa de tecnologia chamada Acme",
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
            use_llm=False,  # Sprint 1 BE-1: tests use mock heuristic; production uses use_llm=True
        )
        # Deve ter pedido extracao, recebido confirmation render
        assert resp.status.state == SettingsExtractionState.CONFIRMING
        assert len(resp.user_message) > 0
        save.assert_not_called()  # ainda nao persistiu

    @pytest.mark.asyncio
    async def test_asking_skip_phrase_moves_to_next(self):
        """skip phrase em ASKING -> marca skipped + avanca pra proxima pergunta."""
        config = load_config()
        first_block = config.blocks[0]
        first_field = first_block.fields[0]
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.ASKING,
            current_block_id=first_block.id,
            last_asked_field=first_field.field_key,
        )
        save = _ok_save()
        resp = await process_message(
            status=status,
            user_message="pular",
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
        )
        # Marcou skipped, mostrou proxima pergunta (ASKING) OU FINALIZE
        assert first_field.field_key in resp.status.skipped_fields
        save.assert_not_called()

    @pytest.mark.asyncio
    async def test_asking_stop_phrase_finalizes(self):
        """stop phrase termina o onboarding com FINALIZE."""
        config = load_config()
        first_block = config.blocks[0]
        first_field = first_block.fields[0]
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.ASKING,
            current_block_id=first_block.id,
            last_asked_field=first_field.field_key,
        )
        save = _ok_save()
        resp = await process_message(
            status=status,
            user_message="chega por hoje",
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
        )
        assert resp.is_complete is True
        assert resp.status.state == SettingsExtractionState.COMPLETE
        save.assert_not_called()

    @pytest.mark.asyncio
    async def test_confirming_yes_persists_and_asks_next(self):
        """Em CONFIRMING + yes -> persiste via save_field_fn + asks next."""
        config = load_config()
        first_block = config.blocks[0]
        first_field = first_block.fields[0]
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.CONFIRMING,
            current_block_id=first_block.id,
            last_asked_field=first_field.field_key,
            pending_extraction={first_field.field_key: "Acme Corp"},
        )
        save = _ok_save()
        resp = await process_message(
            status=status,
            user_message="sim",
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
        )
        # Save chamado uma vez com canonical kwargs
        save.assert_called_once()
        kwargs = save.call_args.kwargs
        assert kwargs["company_id"] == COMPANY_ID
        assert kwargs["field"] == first_field.field_key
        assert kwargs["value"] == "Acme Corp"
        assert kwargs["user_id"] == USER_ID
        # field movido pra answered
        assert first_field.field_key in resp.status.answered_fields
        # pending limpo
        assert resp.status.pending_extraction == {}

    @pytest.mark.asyncio
    async def test_confirming_no_re_asks(self):
        """Em CONFIRMING + no -> volta pra ASKING sem persistir."""
        config = load_config()
        first_block = config.blocks[0]
        first_field = first_block.fields[0]
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.CONFIRMING,
            current_block_id=first_block.id,
            last_asked_field=first_field.field_key,
            pending_extraction={first_field.field_key: "Errado"},
        )
        save = _ok_save()
        resp = await process_message(
            status=status,
            user_message="nao",
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
        )
        save.assert_not_called()
        assert resp.status.state == SettingsExtractionState.ASKING
        assert resp.status.pending_extraction == {}

    @pytest.mark.asyncio
    async def test_persist_failure_returns_error_message(self):
        """save_field_fn retorna success=False -> mensagem de erro user-friendly."""
        config = load_config()
        first_block = config.blocks[0]
        first_field = first_block.fields[0]
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.CONFIRMING,
            current_block_id=first_block.id,
            last_asked_field=first_field.field_key,
            pending_extraction={first_field.field_key: "Acme"},
        )
        save = _fail_save("Validation failed")
        resp = await process_message(
            status=status,
            user_message="sim",
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
        )
        save.assert_called_once()
        assert "problema" in resp.user_message.lower()
        assert "Validation failed" in resp.user_message
        # field NAO foi pra answered
        assert first_field.field_key not in resp.status.answered_fields

    @pytest.mark.asyncio
    async def test_extract_empty_message_returns_user_friendly_error(self):
        """Extractor falha (mensagem vazia) -> mensagem amigavel, mantem ASKING."""
        config = load_config()
        first_block = config.blocks[0]
        first_field = first_block.fields[0]
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.ASKING,
            current_block_id=first_block.id,
            last_asked_field=first_field.field_key,
        )
        save = _ok_save()
        resp = await process_message(
            status=status,
            user_message="   ",  # whitespace -> phase trata como ASKING normal,
            # extractor reject empty
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
            use_llm=False,  # Sprint 1 BE-1: tests use mock heuristic
        )
        # Extractor falhou -> resposta amigavel, state ASKING preservado
        assert resp.status.state == SettingsExtractionState.ASKING
        assert "nao consegui entender" in resp.user_message.lower()
        save.assert_not_called()

    @pytest.mark.asyncio
    async def test_progress_percent_updates_after_persist(self):
        """Apos persistir um field, progress_percent reflete answered count."""
        config = load_config()
        first_block = config.blocks[0]
        first_field = first_block.fields[0]
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.CONFIRMING,
            current_block_id=first_block.id,
            last_asked_field=first_field.field_key,
            pending_extraction={first_field.field_key: "Acme"},
        )
        save = _ok_save()
        resp = await process_message(
            status=status,
            user_message="sim",
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
        )
        assert resp.progress_percent > 0

    @pytest.mark.asyncio
    async def test_persist_unknown_field_reports_error(self):
        """pending_extraction com field_key invalido -> erro reportado."""
        config = load_config()
        first_block = config.blocks[0]
        first_field = first_block.fields[0]
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.CONFIRMING,
            current_block_id=first_block.id,
            last_asked_field=first_field.field_key,
            pending_extraction={"campo_que_nao_existe": "value"},
        )
        save = _ok_save()
        resp = await process_message(
            status=status,
            user_message="sim",
            company_id=COMPANY_ID,
            user_id=USER_ID,
            save_field_fn=save,
        )
        save.assert_not_called()
        assert "desconhecido" in resp.user_message.lower()


# -------------------- _resolve_section_for_field --------------------


class TestSectionResolution:
    def test_profile_fields_map_to_profile(self):
        assert _resolve_section_for_field("name") == "profile"
        assert _resolve_section_for_field("cnpj") == "profile"
        assert _resolve_section_for_field("website") == "profile"
        assert _resolve_section_for_field("industry") == "profile"

    def test_culture_fields_map_to_culture(self):
        assert _resolve_section_for_field("mission") == "culture"
        assert _resolve_section_for_field("vision") == "culture"
        assert _resolve_section_for_field("values") == "culture"
        assert _resolve_section_for_field("work_model") == "culture"
        assert _resolve_section_for_field("tech_stack") == "culture"

    def test_policy_fields_map_to_policy(self):
        """Sprint 1 BE-2: policy fields route correctly."""
        assert _resolve_section_for_field("auto_screening_enabled") == "policy"
        assert _resolve_section_for_field("manager_approval_for_offer") == "policy"
        assert _resolve_section_for_field("salary_screening_enabled") == "policy"
        assert _resolve_section_for_field("autonomy_level") == "policy"

    def test_workforce_fields_map_to_workforce(self):
        """Sprint 1 BE-2: workforce fields route correctly."""
        assert _resolve_section_for_field("hiring_volume") == "workforce"
        assert _resolve_section_for_field("job_types") == "workforce"
        assert _resolve_section_for_field("main_priority") == "workforce"
        assert _resolve_section_for_field("main_challenges") == "workforce"

    def test_lia_persona_fields_map_to_lia_persona(self):
        """Sprint 1 BE-2: lia_persona fields route correctly."""
        assert _resolve_section_for_field("ai_persona.name") == "lia_persona"
        assert _resolve_section_for_field("ai_persona.tone") == "lia_persona"

    def test_unknown_field_logs_warning_falls_back_to_profile(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING):
            section = _resolve_section_for_field("totally_unknown_field")
        assert section == "profile"
        assert any(
            "totally_unknown_field" in record.message
            for record in caplog.records
        )
