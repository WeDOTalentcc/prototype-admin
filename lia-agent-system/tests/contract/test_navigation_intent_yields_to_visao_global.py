"""
Sensor: CR-4 veto — "Visão Global" queries are delegated to the federated
agent (open_ui with tab-aware capabilities) instead of being matched by
the keyword NavigationIntentDetector to the wrong page.

Bug: Paulo 2026-06-15. "visao global de talentos" matched "talentos" (w=0.2)
in the Funil de Talentos group and navigated to the wrong page. "me leve
para Visão Global — aba Candidatos" failed because the detector cannot
address tabs.

Fix: CR-4 veto in navigation_intent.py yields to the federated agent's
open_ui(capability='ir_para_visao_global_candidatos') which knows tabs.
"""

import pytest
from app.orchestrator.context.navigation_intent import detect_navigation_intent


class TestVisaoGlobalVeto:
    """CR-4: visao global queries must NOT resolve to any page — federated agent handles them."""

    @pytest.mark.parametrize("message", [
        "visão global de talentos",
        "visao global de talentos",
        "qual é a pagina de visao global de talentos",
        "me leve para Visão Global",
        "me leve para visao global",
        "me leva pra visão global — aba Candidatos",
        "me leve para Visão Global — aba Candidatos",
        "abra a visão global aba vagas",
        "ir para visão global",
        "pipeline overview",
        "quero ver a visão global",
        "overview de recrutamento",
    ])
    def test_visao_global_queries_yield_to_federated_agent(self, message: str):
        result = detect_navigation_intent(message)
        assert result.page is None, (
            f"CR-4 veto failed: '{message}' resolved to page='{result.page}' "
            f"(pattern='{result.matched_pattern}'). Expected None — visao global "
            f"must be handled by federated agent open_ui, not keyword detector."
        )
        assert result.matched_pattern == "cr4_visao_global_veto"


class TestNonVisaoGlobalUnaffected:
    """CR-4 must NOT interfere with existing navigation patterns."""

    def test_funil_de_talentos_still_works(self):
        result = detect_navigation_intent("me leva pro funil de talentos")
        assert result.page == "Funil de Talentos"

    def test_buscar_candidato_still_works(self):
        result = detect_navigation_intent("buscar candidato")
        assert result.page == "Funil de Talentos"

    def test_vagas_still_works(self):
        result = detect_navigation_intent("me leva pra vagas")
        assert result.page == "Vagas"

    def test_configuracoes_still_works(self):
        result = detect_navigation_intent("abra configurações")
        assert result.page == "Configurações"

    def test_recrutar_pattern_works(self):
        result = detect_navigation_intent("me leva pra recrutar")
        assert result.page == "Recrutar"

    def test_painel_de_controle_still_works(self):
        result = detect_navigation_intent("abra o painel de controle")
        assert result.page == "Painel de Controle"


class TestNavigateRouteRecrutar:
    """navigation_routes.py must recognize /recrutar as valid."""

    def test_recrutar_route_valid(self):
        from app.shared.navigation_routes import validate_navigate_route
        assert validate_navigate_route("/recrutar") == "/recrutar"

    def test_recrutar_route_with_locale(self):
        from app.shared.navigation_routes import validate_navigate_route
        assert validate_navigate_route("/pt/recrutar") == "/pt/recrutar"

    def test_recrutar_route_with_query(self):
        from app.shared.navigation_routes import validate_navigate_route
        assert validate_navigate_route("/recrutar?view=candidatos") == "/recrutar?view=candidatos"
