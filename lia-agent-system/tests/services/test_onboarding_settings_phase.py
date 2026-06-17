"""Tests for onboarding_settings_phase — P2-2 Sprint A.2."""
from __future__ import annotations

import pytest

from app.services.onboarding_settings_phase import (
    ActionType,
    HandlerAction,
    SettingsExtractionState,
    SettingsExtractionStatus,
    handle_extraction_result,
    handle_persist_success,
    handle_user_response,
    is_confirmation_no,
    is_confirmation_yes,
    is_skip_phrase,
    is_stop_phrase,
    render_confirmation_message,
    render_question_message,
    start_settings_extraction,
)
from app.services.onboarding_yaml_loader import load_config


@pytest.fixture(scope="module")
def config():
    return load_config()


class TestStartExtraction:
    def test_returns_status_in_intro_state(self, config):
        status, _ = start_settings_extraction(config)
        assert status.state == SettingsExtractionState.INTRO

    def test_action_is_send_message_with_greeting(self, config):
        _, action = start_settings_extraction(config)
        assert action.action_type == ActionType.SEND_MESSAGE
        assert action.message == config.persona_greeting
        assert len(action.message) > 0

    def test_initial_status_empty_answered(self, config):
        status, _ = start_settings_extraction(config)
        assert status.answered_fields == {}
        assert status.skipped_fields == set()
        assert status.pending_extraction == {}


class TestPhraseDetectors:
    def test_is_skip_phrase_pular(self):
        assert is_skip_phrase("pular")

    def test_is_skip_phrase_case_insensitive(self):
        assert is_skip_phrase("PULAR")
        assert is_skip_phrase("Pular")
        assert is_skip_phrase("  pular  ")

    def test_is_skip_phrase_skip_english(self):
        assert is_skip_phrase("skip")

    def test_is_stop_phrase_parar(self):
        assert is_stop_phrase("parar")

    def test_is_stop_phrase_chega(self):
        assert is_stop_phrase("chega por hoje")

    def test_is_confirmation_yes_sim(self):
        assert is_confirmation_yes("sim")

    def test_is_confirmation_yes_isso(self):
        assert is_confirmation_yes("isso")

    def test_is_confirmation_yes_pode_salvar(self):
        assert is_confirmation_yes("pode salvar")

    def test_is_confirmation_no_nao(self):
        assert is_confirmation_no("nao")
        assert is_confirmation_no("não")

    def test_is_confirmation_no_errado(self):
        assert is_confirmation_no("errado")

    def test_normal_message_not_skip_or_stop(self):
        msg = "Somos uma empresa de software com 200 funcionários"
        assert not is_skip_phrase(msg)
        assert not is_stop_phrase(msg)

    def test_yes_does_not_match_negation(self):
        # "não" alone should NOT trigger yes
        assert not is_confirmation_yes("não")
        assert not is_confirmation_yes("nao")

    def test_empty_message_no_match(self):
        assert not is_skip_phrase("")
        assert not is_stop_phrase("")
        assert not is_confirmation_yes("")
        assert not is_confirmation_no("")


class TestRenderMessages:
    def test_render_question_includes_question_text(self, config):
        block = config.blocks[0]
        target = block.fields[0]
        msg = render_question_message(block, target, 0, config)
        assert target.question.strip() in msg

    def test_render_question_shows_block_context(self, config):
        block = config.blocks[0]
        target = block.fields[0]
        msg = render_question_message(block, target, 0, config)
        assert block.title in msg
        assert "Bloco 1 de" in msg

    def test_render_question_includes_example_when_present(self, config):
        # Find a field with example
        for block in config.blocks:
            for f in block.fields:
                if f.example_response:
                    msg = render_question_message(block, f, 10, config)
                    assert f.example_response.strip() in msg
                    return
        pytest.skip("no field with example in YAML")

    def test_render_question_includes_progress(self, config):
        block = config.blocks[0]
        target = block.fields[0]
        msg = render_question_message(block, target, 42, config)
        assert "42%" in msg

    def test_render_confirmation_uses_template(self, config):
        msg = render_confirmation_message({"company_name": "WeDOTalent"}, config)
        # Template starts with "Anotei aqui:"
        assert "Anotei aqui" in msg
        assert "Posso salvar" in msg

    def test_render_confirmation_lists_fields(self, config):
        extracted = {"company_name": "Acme Corp", "industry": "Tech"}
        msg = render_confirmation_message(extracted, config)
        assert "company_name" in msg
        assert "Acme Corp" in msg
        assert "industry" in msg
        assert "Tech" in msg

    def test_render_confirmation_handles_list_value(self, config):
        msg = render_confirmation_message({"benefits": ["VR", "VA", "Plano"]}, config)
        assert "VR" in msg and "VA" in msg and "Plano" in msg


class TestHandleUserResponseIntro:
    def test_intro_to_asking_returns_first_question(self, config):
        status, _ = start_settings_extraction(config)
        status2, action = handle_user_response(status, "ola lia", config)
        assert status2.state == SettingsExtractionState.ASKING
        assert action.action_type == ActionType.SEND_MESSAGE
        assert action.target_field is not None


class TestHandleUserResponseAsking:
    def _seed_asking(self, config) -> SettingsExtractionStatus:
        status, _ = start_settings_extraction(config)
        status, _ = handle_user_response(status, "vamos", config)
        return status

    def test_asking_with_skip_phrase_marks_skipped(self, config):
        status = self._seed_asking(config)
        asked = status.last_asked_field
        assert asked is not None
        status2, action = handle_user_response(status, "pular", config)
        assert asked in status2.skipped_fields
        # Avança pra próxima pergunta OR finaliza
        assert action.action_type in (ActionType.SEND_MESSAGE, ActionType.FINALIZE)

    def test_asking_with_stop_phrase_finalizes(self, config):
        status = self._seed_asking(config)
        status2, action = handle_user_response(status, "parar", config)
        assert status2.state == SettingsExtractionState.COMPLETE
        assert action.action_type == ActionType.FINALIZE

    def test_asking_with_normal_message_triggers_extract(self, config):
        status = self._seed_asking(config)
        status2, action = handle_user_response(
            status, "Somos a WeDOTalent, empresa de RH tech", config
        )
        assert action.action_type == ActionType.EXTRACT_FIELDS
        # Status state stays ASKING — caller will call handle_extraction_result
        assert status2.state == SettingsExtractionState.ASKING


class TestHandleUserResponseConfirming:
    def _seed_confirming(self, config) -> SettingsExtractionStatus:
        status, _ = start_settings_extraction(config)
        status, _ = handle_user_response(status, "vamos", config)
        # Move to CONFIRMING with pending extraction
        status, _ = handle_extraction_result(
            status, {"company_name": "WeDOTalent"}, 0.9, config
        )
        return status

    def test_confirming_yes_triggers_persist(self, config):
        status = self._seed_confirming(config)
        status2, action = handle_user_response(status, "sim", config)
        assert action.action_type == ActionType.PERSIST_FIELDS
        assert action.pending_extraction == {"company_name": "WeDOTalent"}

    def test_confirming_no_re_asks_question(self, config):
        status = self._seed_confirming(config)
        status2, action = handle_user_response(status, "errado", config)
        assert status2.state == SettingsExtractionState.ASKING
        assert status2.pending_extraction == {}
        assert action.action_type == ActionType.SEND_MESSAGE


class TestHandleExtractionResult:
    def test_transitions_to_confirming(self, config):
        status, _ = start_settings_extraction(config)
        status, _ = handle_user_response(status, "vamos", config)
        status2, _ = handle_extraction_result(
            status, {"company_name": "X"}, 0.9, config
        )
        assert status2.state == SettingsExtractionState.CONFIRMING

    def test_stores_pending_extraction(self, config):
        status, _ = start_settings_extraction(config)
        status, _ = handle_user_response(status, "vamos", config)
        status2, _ = handle_extraction_result(
            status, {"company_name": "X", "industry": "Y"}, 0.9, config
        )
        assert status2.pending_extraction == {"company_name": "X", "industry": "Y"}

    def test_action_is_confirm_extraction(self, config):
        status, _ = start_settings_extraction(config)
        status, _ = handle_user_response(status, "vamos", config)
        _, action = handle_extraction_result(
            status, {"company_name": "X"} , 0.9, config
        )
        assert action.action_type == ActionType.CONFIRM_EXTRACTION
        assert action.pending_extraction == {"company_name": "X"}


class TestHandlePersistSuccess:
    def test_copies_pending_to_answered(self, config):
        status, _ = start_settings_extraction(config)
        status, _ = handle_user_response(status, "vamos", config)
        status, _ = handle_extraction_result(
            status, {"company_name": "X"}, 0.9, config
        )
        status2, _ = handle_persist_success(status, {"company_name": "X"}, config)
        assert status2.answered_fields["company_name"] == "X"

    def test_clears_pending(self, config):
        status, _ = start_settings_extraction(config)
        status, _ = handle_user_response(status, "vamos", config)
        status, _ = handle_extraction_result(
            status, {"company_name": "X"}, 0.9, config
        )
        status2, _ = handle_persist_success(status, {"company_name": "X"}, config)
        assert status2.pending_extraction == {}

    def test_decides_next_question_when_below_threshold(self, config):
        # Single field persisted shouldn't hit threshold (need ~80%)
        status, _ = start_settings_extraction(config)
        status, _ = handle_user_response(status, "vamos", config)
        status, _ = handle_extraction_result(
            status, {"company_name": "X"}, 0.9, config
        )
        _, action = handle_persist_success(status, {"company_name": "X"}, config)
        assert action.action_type == ActionType.SEND_MESSAGE
        assert action.target_field is not None

    def test_finalizes_when_above_threshold(self, config):
        # Pre-populate answered with ALL fields → triggers finalize
        all_keys = {
            f.field_key for b in config.blocks for f in b.fields
        }
        status = SettingsExtractionStatus(
            state=SettingsExtractionState.CONFIRMING,
            answered_fields={k: "stub" for k in all_keys},
            pending_extraction={list(all_keys)[0]: "updated"},
        )
        _, action = handle_persist_success(
            status, {list(all_keys)[0]: "updated"}, config
        )
        assert action.action_type == ActionType.FINALIZE
