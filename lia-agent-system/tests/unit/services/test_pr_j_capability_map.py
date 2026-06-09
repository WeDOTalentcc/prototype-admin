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
    """Wave 1 PR-Q2 + PR-Q3: close_job, generate_job_report, forecast, start_wsi_interview."""

    def test_wave1_intents_present(self):
        """sensor: todos os 9 intents Wave 0+1 estão declarados no capability_map."""
        caps = CapabilityMapService.load()
        wave1 = ["close_job", "generate_job_report", "forecast", "start_wsi_interview"]
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

    def test_start_wsi_interview_requires_job(self):
        reqs = CapabilityMapService.needs_entity("start_wsi_interview")
        assert any(r.type == "job" for r in reqs), (
            "start_wsi_interview deve exigir job_id — triagem WSI é por vaga."
        )

    def test_wave1_navigate_fallbacks_are_valid_paths(self):
        """Todos os navigate_fallback devem começar com /."""
        wave1 = ["close_job", "generate_job_report", "forecast", "start_wsi_interview"]
        for intent in wave1:
            cap = CapabilityMapService.get(intent)
            if cap and cap.navigate_fallback:
                assert cap.navigate_fallback.startswith("/"), (
                    f"navigate_fallback de {intent} deve ser path absoluto (começa com /)."
                )

    def test_total_intents_is_twelve(self):
        """sensor: capability_map deve ter pelo menos 22 intents após UC-P1-28 (7 Rail A ghosts adicionados)."""
        caps = CapabilityMapService.load()
        assert len(caps) >= 22, (
            f"capability_map.yaml deve ter ao menos 22 intents após UC-P1-28, "
            f"encontrado: {len(caps)}. "
            "Adicione a entrada ou remova se obsoleta."
        )


class TestCapabilityMapWave4Intents:
    """Sensor computacional: Wave 4 intents (send_offer + register_hire) corretamente mapeados."""

    def test_wave4_intents_present(self):
        caps = CapabilityMapService.load()
        assert "send_offer" in caps, "send_offer ausente do capability_map"
        assert "register_hire" in caps, "register_hire ausente do capability_map"

    def test_send_offer_not_chat_executable(self):
        """send_offer abre OfferReviewModal diretamente — sem detour de chat."""
        cap = CapabilityMapService.get("send_offer")
        assert cap is not None
        assert cap.chat_executable is False

    def test_send_offer_has_offer_review_modal(self):
        cap = CapabilityMapService.get("send_offer")
        assert cap is not None
        assert cap.modal_id == "offer_review"

    def test_send_offer_requires_candidate_entity(self):
        reqs = CapabilityMapService.needs_entity("send_offer")
        types = [r.type for r in reqs]
        assert "candidate" in types

    def test_register_hire_is_chat_executable(self):
        """register_hire é conversacional — LIA guia checklist pós-contratação."""
        cap = CapabilityMapService.get("register_hire")
        assert cap is not None
        assert cap.chat_executable is True

    def test_register_hire_requires_candidate_and_job(self):
        reqs = CapabilityMapService.needs_entity("register_hire")
        types = [r.type for r in reqs]
        assert "candidate" in types, "register_hire deve exigir entidade candidate"
        assert "job" in types, "register_hire deve exigir entidade job"

    def test_register_hire_has_navigate_fallback(self):
        cap = CapabilityMapService.get("register_hire")
        assert cap is not None
        assert cap.navigate_fallback is not None
        assert "contratacao" in cap.navigate_fallback or "visao" in cap.navigate_fallback


class TestCapabilityMapFaseB:
    """Fase B (2026-06-06): set curado de capabilities globais + HITL + navegação.

    open_ui é a tool UNIFICADA: capability com modal_id abre modal (display via
    host fetch id→objeto); sem modal_id mas com navigate_page navega pro surface
    (a ação/seleção-acoplada vive na página, com seu handler + confirmação = HITL
    preservado, sem duplicar a lógica de mutação no chat — CLAUDE.md single-source).
    """

    # Capabilities que ABREM MODAL (display-only via LiaEntityModalHost).
    READONLY_MODALS = [
        ("view_score", "general_score", "candidate"),
        ("view_bigfive", "big_five", "candidate"),
        ("generate_job_report", "job_report", "job"),
        # Fase 1D (2026-06-09): compare_jobs migrou de navigate_page para modal_id
        # (modal de comparação multi-vaga em overlay, sem navegar para outra página)
        ("compare_jobs", "job_compare", None),
    ]

    # Capabilities que NAVEGAM pro surface. (intent, navigate_page, destrutivo?)
    NAVIGATE_CAPS = [
        ("view_profile", "candidato_detalhe", False),
        ("close_job", "vaga_detalhe", True),
        ("change_job_status", "vaga_detalhe", True),
        ("assign_recruiter", "vaga_detalhe", True),
        ("job_insights", "vaga_detalhe", False),
        ("bulk_action", "funil_talentos", True),
        ("data_request", "funil_talentos", True),
        ("send_communication", "central_comunicacao", True),
    ]
    VALID_PAGES = {
        "candidato_detalhe", "vaga_detalhe", "vagas",
        "funil_talentos", "central_comunicacao", "trust",
    }

    def test_requires_confirmation_defaults_false(self):
        cap = CapabilityMapService.get("search_candidates")
        assert cap is not None
        assert cap.requires_confirmation is False

    def test_readonly_modals_present_and_direct(self):
        for intent, modal_id, ent in self.READONLY_MODALS:
            cap = CapabilityMapService.get(intent)
            assert cap is not None, f"capability '{intent}' ausente (Fase B)"
            assert cap.modal_id == modal_id, (
                f"'{intent}'.modal_id deve ser '{modal_id}', achou {cap.modal_id!r}"
            )
            assert cap.requires_confirmation is False
            if ent:
                types = [r.type for r in cap.entity_required]
                assert ent in types

    def test_navigate_caps_no_modal_have_page(self):
        """Acoplados a ação/seleção: SEM modal_id, COM navigate_page canonical.
        Re-implementar o handler no chat duplicaria a página (anti-pattern)."""
        for intent, page, _destructive in self.NAVIGATE_CAPS:
            cap = CapabilityMapService.get(intent)
            assert cap is not None, f"capability '{intent}' ausente"
            assert cap.modal_id is None, (
                f"'{intent}' é navigate-to-surface — NÃO deve ter modal_id"
            )
            assert cap.navigate_page == page, (
                f"'{intent}'.navigate_page deve ser '{page}', achou {cap.navigate_page!r}"
            )
            assert cap.navigate_page in self.VALID_PAGES

    def test_destructive_navigate_caps_keep_confirmation(self):
        """Destrutivos mantêm requires_confirmation=True (HITL na página)."""
        for intent, _page, destructive in self.NAVIGATE_CAPS:
            if destructive:
                assert CapabilityMapService.requires_confirmation(intent) is True, (
                    f"'{intent}' é destrutivo — requires_confirmation deve ser True"
                )

    def test_requires_confirmation_is_bool_everywhere(self):
        for intent, cap in CapabilityMapService.load().items():
            assert isinstance(cap.requires_confirmation, bool)

    def test_confirmation_helper_unknown_intent_false(self):
        assert CapabilityMapService.requires_confirmation("xyz_unknown") is False

    def test_view_profile_navigates_to_candidate_not_user_modal(self):
        """Perfil de CANDIDATO navega p/ a página (profile-modal é do usuário)."""
        cap = CapabilityMapService.get("view_profile")
        assert cap is not None
        assert cap.modal_id is None
        assert cap.navigate_page == "candidato_detalhe"
