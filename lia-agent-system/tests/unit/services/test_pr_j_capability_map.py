"""
PR-J — CapabilityMapService tests (TDD RED → GREEN).

harness-engineering sensor computacional:
Valida contrato do capability_map.yaml. CI quebra se qualquer intent
ficar sem fallback — evita que o usuário fique stranded sem caminho.
"""
import pytest
from app.shared.services.capability_map_service import CapabilityMapService


class TestCapabilityMapLoads:
    def test_load_returns_non_empty_dict(self):
        caps = CapabilityMapService.load()
        assert isinstance(caps, dict)
        assert len(caps) >= 5, "capability_map deve ter ao menos 5 intents do Rail A"

    def test_all_five_rail_a_intents_present(self):
        caps = CapabilityMapService.load()
        required = [
            "add_candidate",
            "search_candidates",
            "move_candidate",
            "reschedule_interview",
            "compare_candidates",
        ]
        for intent in required:
            assert intent in caps, (
                f"Intent '{intent}' ausente de capability_map.yaml. "
                "Adicione a entrada antes de registrar o card no Rail A."
            )

    def test_every_intent_has_navigate_or_modal(self):
        """Sensor: nenhum intent pode deixar o usuário sem saída."""
        for intent, cap in CapabilityMapService.load().items():
            assert cap.navigate_fallback is not None or cap.modal_id is not None, (
                f"capability_map.yaml: intent '{intent}' não tem navigate_fallback nem modal_id. "
                "Adicione ao menos um para que o usuário tenha caminho quando a LIA não conseguir executar."
            )

    def test_chat_executable_is_bool(self):
        for intent, cap in CapabilityMapService.load().items():
            assert isinstance(cap.chat_executable, bool), (
                f"capability_map.yaml: '{intent}'.chat_executable deve ser bool (true/false), "
                f"encontrado: {type(cap.chat_executable).__name__}"
            )


class TestCapabilityGet:
    def test_add_candidate_not_chat_executable(self):
        cap = CapabilityMapService.get("add_candidate")
        assert cap is not None
        assert cap.chat_executable is False, (
            "add_candidate deve ter chat_executable=false — "
            "modal com 3 abas é melhor UX que loop de 5 perguntas no chat."
        )

    def test_add_candidate_has_modal_id(self):
        cap = CapabilityMapService.get("add_candidate")
        assert cap is not None
        assert cap.modal_id == "add_candidate"

    def test_move_candidate_is_chat_executable(self):
        cap = CapabilityMapService.get("move_candidate")
        assert cap is not None
        assert cap.chat_executable is True

    def test_move_candidate_has_entity_requirements(self):
        reqs = CapabilityMapService.needs_entity("move_candidate")
        types = [r.type for r in reqs]
        assert "candidate" in types, "move_candidate requer candidate_id"

    def test_reschedule_requires_candidate(self):
        reqs = CapabilityMapService.needs_entity("reschedule_interview")
        assert any(r.type == "candidate" for r in reqs)

    def test_compare_requires_job(self):
        reqs = CapabilityMapService.needs_entity("compare_candidates")
        assert any(r.type == "job" for r in reqs)

    def test_unknown_intent_returns_none(self):
        assert CapabilityMapService.get("nonexistent_xyz_intent") is None

    def test_unknown_intent_is_chat_executable_default_true(self):
        assert CapabilityMapService.is_chat_executable("unknown_xyz") is True

    def test_non_chat_executable_always_has_fallback(self):
        for intent, cap in CapabilityMapService.load().items():
            if not cap.chat_executable:
                assert cap.modal_id is not None or cap.navigate_fallback is not None, (
                    f"'{intent}' não é chat-executable mas não tem modal_id nem navigate_fallback."
                )


class TestCapabilityMapWave1Intents:
    """Wave 1 PR-Q2 + PR-Q3: close_job, generate_job_report, forecast, start_wsi_flow."""

    def test_wave1_intents_present(self):
        """sensor: todos os 9 intents Wave 0+1 estão declarados no capability_map."""
        caps = CapabilityMapService.load()
        wave1 = ["close_job", "generate_job_report", "forecast", "start_wsi_flow"]
        for intent in wave1:
            assert intent in caps, (
                f"Intent {intent} ausente do capability_map.yaml. "
                "Wave 1 PR-Q2/PR-Q3 requer essas entradas para entity resolution dos cards."
            )

    def test_close_job_requires_job_entity(self):
        reqs = CapabilityMapService.needs_entity("close_job")
        assert any(r.type == "job" for r in reqs), (
            "close_job deve exigir job_id para evitar dead-end (qual vaga encerrar?)."
        )

    def test_generate_job_report_requires_job_entity(self):
        reqs = CapabilityMapService.needs_entity("generate_job_report")
        assert any(r.type == "job" for r in reqs)

    def test_forecast_has_no_entity_required(self):
        """forecast é tenant-wide — não precisa de job específico."""
        reqs = CapabilityMapService.needs_entity("forecast")
        assert reqs == [], (
            "forecast não deve exigir entidade — é previsão do pipeline todo do tenant."
        )

    def test_start_wsi_flow_requires_job(self):
        reqs = CapabilityMapService.needs_entity("start_wsi_flow")
        assert any(r.type == "job" for r in reqs), (
            "start_wsi_flow deve exigir job_id — triagem WSI é por vaga."
        )

    def test_wave1_navigate_fallbacks_are_valid_paths(self):
        """Todos os navigate_fallback devem começar com /."""
        wave1 = ["close_job", "generate_job_report", "forecast", "start_wsi_flow"]
        for intent in wave1:
            cap = CapabilityMapService.get(intent)
            if cap and cap.navigate_fallback:
                assert cap.navigate_fallback.startswith("/"), (
                    f"navigate_fallback de {intent} deve ser path absoluto (começa com /)."
                )

    def test_total_intents_is_nine(self):
        """sensor: capability_map deve ter exatamente 9 intents após Wave 1."""
        caps = CapabilityMapService.load()
        assert len(caps) == 9, (
            f"capability_map.yaml deve ter 9 intents após Wave 1, "
            f"encontrado: {len(caps)}. "
            "Adicione a entrada ou remova se obsoleta."
        )
