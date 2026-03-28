"""
Tests para map_intent_to_actionable() e INTENT_TO_ACTIONABLE expandido.

Garante que:
- Todos os 15 intents em ACTIONABLE_INTENTS são alcançáveis via map_intent_to_actionable
- Intents em PT são mapeados diretamente (fallback para ACTIONABLE_INTENTS)
- Intents em EN são traduzidos via INTENT_TO_ACTIONABLE
- Intents update_job roteiam via JOB_ACTION_MAP
- SKIP_ACTION_INTENTS retornam None
- Intents desconhecidos retornam None
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_map_fn():
    from app.api.v1.chat import map_intent_to_actionable
    return map_intent_to_actionable


def _get_actionable_intents():
    from app.orchestrator.action_executor import ACTIONABLE_INTENTS
    return ACTIONABLE_INTENTS


def _get_intent_to_actionable():
    from app.api.v1.chat import INTENT_TO_ACTIONABLE
    return INTENT_TO_ACTIONABLE


# ---------------------------------------------------------------------------
# Section 1: Todos os 15 intents em ACTIONABLE_INTENTS são alcançáveis
# ---------------------------------------------------------------------------

class TestAllActionableIntentsReachable:

    def test_all_pt_intents_reachable(self):
        """Cada chave em ACTIONABLE_INTENTS deve ser retornada por map_intent_to_actionable."""
        fn = _get_map_fn()
        actionable = _get_actionable_intents()

        for intent_key in actionable:
            result = fn(intent_key, {})
            assert result == intent_key, (
                f"Intent PT '{intent_key}' deve ser retornado diretamente, got: {result}"
            )

    def test_total_actionable_intents_count(self):
        """ACTIONABLE_INTENTS deve ter pelo menos 15 entradas."""
        actionable = _get_actionable_intents()
        assert len(actionable) >= 15, f"Esperado >= 15 intents, encontrado {len(actionable)}"


# ---------------------------------------------------------------------------
# Section 2: Mapeamento EN → PT
# ---------------------------------------------------------------------------

class TestEnglishIntentMapping:

    def test_move_candidate_en(self):
        fn = _get_map_fn()
        assert fn("move_candidate", {}) == "mover_candidato"

    def test_start_screening_en(self):
        fn = _get_map_fn()
        assert fn("start_screening", {}) == "iniciar_triagem"

    def test_reject_candidate_en(self):
        fn = _get_map_fn()
        assert fn("reject_candidate", {}) == "reprovar_candidato"

    def test_approve_candidate_en(self):
        fn = _get_map_fn()
        assert fn("approve_candidate", {}) == "aprovar_candidato"

    def test_send_email_en(self):
        fn = _get_map_fn()
        assert fn("send_email", {}) == "enviar_email"

    def test_send_message_en(self):
        fn = _get_map_fn()
        assert fn("send_message", {}) == "enviar_mensagem"

    def test_schedule_interview_en(self):
        fn = _get_map_fn()
        assert fn("schedule_interview", {}) == "agendar_entrevista"

    def test_trigger_screening_en(self):
        fn = _get_map_fn()
        assert fn("trigger_screening", {}) == "disparar_triagem"

    def test_analyze_profile_en(self):
        fn = _get_map_fn()
        assert fn("analyze_profile", {}) == "analisar_perfil"

    def test_detailed_analysis_en(self):
        fn = _get_map_fn()
        assert fn("detailed_analysis", {}) == "analise_detalhada"

    def test_pause_job_en(self):
        fn = _get_map_fn()
        assert fn("pause_job", {}) == "pausar_vaga"

    def test_close_job_en(self):
        fn = _get_map_fn()
        assert fn("close_job", {}) == "fechar_vaga"

    def test_duplicate_job_en(self):
        fn = _get_map_fn()
        assert fn("duplicate_job", {}) == "duplicar_vaga"

    def test_reopen_job_en(self):
        fn = _get_map_fn()
        assert fn("reopen_job", {}) == "reabrir_vaga"

    def test_update_candidate_status_en(self):
        fn = _get_map_fn()
        assert fn("update_candidate_status", {}) == "atualizar_status_candidato"

    def test_update_status_en(self):
        fn = _get_map_fn()
        assert fn("update_status", {}) == "atualizar_status_candidato"


# ---------------------------------------------------------------------------
# Section 3: Mapeamento PT direto (fallback ACTIONABLE_INTENTS)
# ---------------------------------------------------------------------------

class TestPortugueseIntentDirect:

    def test_mover_candidato_pt(self):
        fn = _get_map_fn()
        assert fn("mover_candidato", {}) == "mover_candidato"

    def test_enviar_email_pt(self):
        fn = _get_map_fn()
        assert fn("enviar_email", {}) == "enviar_email"

    def test_enviar_mensagem_pt(self):
        fn = _get_map_fn()
        assert fn("enviar_mensagem", {}) == "enviar_mensagem"

    def test_agendar_entrevista_pt(self):
        fn = _get_map_fn()
        assert fn("agendar_entrevista", {}) == "agendar_entrevista"

    def test_disparar_triagem_pt(self):
        fn = _get_map_fn()
        assert fn("disparar_triagem", {}) == "disparar_triagem"

    def test_iniciar_triagem_pt(self):
        fn = _get_map_fn()
        assert fn("iniciar_triagem", {}) == "iniciar_triagem"

    def test_analisar_perfil_pt(self):
        fn = _get_map_fn()
        assert fn("analisar_perfil", {}) == "analisar_perfil"

    def test_analise_detalhada_pt(self):
        fn = _get_map_fn()
        assert fn("analise_detalhada", {}) == "analise_detalhada"

    def test_reprovar_candidato_pt(self):
        fn = _get_map_fn()
        assert fn("reprovar_candidato", {}) == "reprovar_candidato"

    def test_aprovar_candidato_pt(self):
        fn = _get_map_fn()
        assert fn("aprovar_candidato", {}) == "aprovar_candidato"

    def test_atualizar_status_candidato_pt(self):
        fn = _get_map_fn()
        assert fn("atualizar_status_candidato", {}) == "atualizar_status_candidato"


# ---------------------------------------------------------------------------
# Section 4: update_job → JOB_ACTION_MAP
# ---------------------------------------------------------------------------

class TestUpdateJobMapping:

    def test_update_job_pausar(self):
        fn = _get_map_fn()
        assert fn("update_job", {"ação": "pausar"}) == "pausar_vaga"

    def test_update_job_fechar(self):
        fn = _get_map_fn()
        assert fn("update_job", {"acao": "fechar"}) == "fechar_vaga"

    def test_update_job_encerrar(self):
        fn = _get_map_fn()
        assert fn("update_job", {"action": "encerrar"}) == "fechar_vaga"

    def test_update_job_reabrir(self):
        fn = _get_map_fn()
        assert fn("update_job", {"ação": "reabrir"}) == "reabrir_vaga"

    def test_update_job_duplicar(self):
        fn = _get_map_fn()
        assert fn("update_job", {"ação": "duplicar"}) == "duplicar_vaga"

    def test_update_job_unknown_action_returns_none(self):
        fn = _get_map_fn()
        assert fn("update_job", {"ação": "desconhecido"}) is None

    def test_update_job_no_action_returns_none(self):
        fn = _get_map_fn()
        assert fn("update_job", {}) is None


# ---------------------------------------------------------------------------
# Section 5: SKIP_ACTION_INTENTS retornam None
# ---------------------------------------------------------------------------

class TestSkipIntents:

    def test_create_job_skipped(self):
        fn = _get_map_fn()
        assert fn("create_job", {}) is None

    def test_greeting_skipped(self):
        fn = _get_map_fn()
        assert fn("greeting", {}) is None

    def test_general_question_skipped(self):
        fn = _get_map_fn()
        assert fn("general_question", {}) is None

    def test_search_candidates_skipped(self):
        fn = _get_map_fn()
        assert fn("search_candidates", {}) is None

    def test_unknown_skipped(self):
        fn = _get_map_fn()
        assert fn("unknown", {}) is None


# ---------------------------------------------------------------------------
# Section 6: Intents desconhecidos
# ---------------------------------------------------------------------------

class TestUnknownIntents:

    def test_completely_unknown_returns_none(self):
        fn = _get_map_fn()
        assert fn("xpto_nao_existe", {}) is None

    def test_empty_string_returns_none(self):
        fn = _get_map_fn()
        assert fn("", {}) is None
