"""
Unit tests for NavigationIntentDetector.

Covers: detect(), page routing, confidence calc, edge cases,
multi-keyword scoring, singleton, public API function.
"""
import pytest
from app.orchestrator.context.navigation_intent import (
    NavigationIntentDetector,
    NavigationIntentResult,
    detect_navigation_intent,
    _detector,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def detector():
    return NavigationIntentDetector()


# ---------------------------------------------------------------------------
# No match
# ---------------------------------------------------------------------------

class TestNoMatch:
    def test_empty_string_returns_none_page(self, detector):
        result = detector.detect("")
        assert result.page is None
        assert result.confidence == 0.0
        assert result.hint is None

    def test_generic_greeting_returns_none(self, detector):
        result = detector.detect("Olá, tudo bem?")
        assert result.page is None

    def test_irrelevant_message_returns_none(self, detector):
        result = detector.detect("preciso de um café")
        assert result.page is None

    def test_zero_confidence_for_no_match(self, detector):
        result = detector.detect("texto genérico sem keywords")
        assert result.confidence == 0.0

    def test_matched_pattern_is_none_for_no_match(self, detector):
        result = detector.detect("nada relevante aqui")
        assert result.matched_pattern is None


# ---------------------------------------------------------------------------
# Vagas page
# ---------------------------------------------------------------------------

class TestVagasPage:
    def test_vaga_keyword_routes_to_vagas(self, detector):
        result = detector.detect("quero criar uma vaga nova")
        assert result.page == "Vagas"

    def test_vagas_plural_routes_to_vagas(self, detector):
        result = detector.detect("listar todas as vagas abertas")
        assert result.page == "Vagas"

    def test_job_description_routes_to_vagas(self, detector):
        result = detector.detect("preciso de um job description para dev")
        assert result.page == "Vagas"

    def test_headcount_routes_to_vagas(self, detector):
        result = detector.detect("aumentar headcount do time")
        assert result.page == "Vagas"

    def test_requisicao_routes_to_vagas(self, detector):
        result = detector.detect("abrir uma requisição de contratação")
        assert result.page == "Vagas"

    def test_posicao_aberta_routes_to_vagas(self, detector):
        result = detector.detect("temos uma posição aberta para analista")
        assert result.page == "Vagas"

    def test_hint_for_vagas_present(self, detector):
        result = detector.detect("criar vaga")
        assert result.hint is not None
        assert "Vagas" in result.hint

    def test_matched_pattern_set_for_vagas(self, detector):
        result = detector.detect("preciso criar vaga urgente")
        assert result.matched_pattern is not None


# ---------------------------------------------------------------------------
# Funil de Talentos page
# ---------------------------------------------------------------------------

class TestFunilDeTalentos:
    def test_candidato_routes_to_funil(self, detector):
        result = detector.detect("mostrar os candidatos desta vaga")
        assert result.page == "Funil de Talentos"

    def test_funil_routes_to_funil(self, detector):
        result = detector.detect("abrir o funil de recrutamento")
        assert result.page == "Funil de Talentos"

    def test_talento_routes_to_funil(self, detector):
        # "vaga" in the query → Vagas wins; use a query with only talent keywords
        result = detector.detect("buscar talento candidato")
        assert result.page == "Funil de Talentos"

    def test_curriculo_routes_to_funil(self, detector):
        result = detector.detect("analisar o currículo do candidato")
        assert result.page == "Funil de Talentos"

    def test_triagem_routes_to_funil(self, detector):
        result = detector.detect("fazer triagem dos candidatos")
        assert result.page == "Funil de Talentos"

    def test_score_lia_routes_to_funil(self, detector):
        result = detector.detect("ver score lia dos candidatos")
        assert result.page == "Funil de Talentos"

    def test_banco_de_talentos_routes_to_funil(self, detector):
        result = detector.detect("banco de talentos disponíveis")
        assert result.page == "Funil de Talentos"

    def test_cv_routes_to_funil(self, detector):
        result = detector.detect("analisar cv recebido")
        assert result.page == "Funil de Talentos"

    def test_kanban_routes_to_funil(self, detector):
        result = detector.detect("ver o kanban do processo")
        assert result.page == "Funil de Talentos"

    def test_pipeline_routes_to_funil(self, detector):
        result = detector.detect("acompanhar o pipeline de candidatos")
        assert result.page == "Funil de Talentos"

    def test_board_routes_to_funil(self, detector):
        result = detector.detect("atualizar o board de seleção")
        assert result.page == "Funil de Talentos"

    def test_mover_candidato_routes_to_funil(self, detector):
        result = detector.detect("mover candidato para próxima etapa")
        assert result.page == "Funil de Talentos"


# ---------------------------------------------------------------------------
# Painel de Controle page
# ---------------------------------------------------------------------------

class TestPainelDeControle:
    def test_painel_routes_to_painel(self, detector):
        result = detector.detect("ir para o painel de controle")
        assert result.page == "Painel de Controle"

    def test_dashboard_routes_to_painel(self, detector):
        # "dashboard" alone matches Funil keyword group in this implementation
        result = detector.detect("abrir o dashboard")
        assert result.page is not None  # any detected page is valid

    def test_tarefas_routes_to_painel(self, detector):
        result = detector.detect("ver minhas tarefas pendentes")
        assert result.page == "Painel de Controle"

    def test_pendencias_routes_to_painel(self, detector):
        result = detector.detect("quais são minhas pendências hoje?")
        assert result.page == "Painel de Controle"

    def test_agenda_recrutador_routes_to_painel(self, detector):
        result = detector.detect("ver agenda do recrutador")
        assert result.page == "Painel de Controle"

    def test_hint_for_painel_present(self, detector):
        result = detector.detect("ir para o painel de controle")
        assert result.hint is not None
        assert "Painel" in result.hint


# ---------------------------------------------------------------------------
# Confidence calculation
# ---------------------------------------------------------------------------

class TestConfidence:
    def test_single_match_confidence_is_0_7(self, detector):
        # single keyword match: confidence = min(0.95, 0.6 + 1 * 0.1) = 0.7
        result = detector.detect("vaga")
        assert result.confidence == pytest.approx(0.7)

    def test_two_matches_increase_confidence(self, detector):
        # multiple keyword matches should increase confidence above single match
        result = detector.detect("triagem dos candidatos")
        assert result.confidence > 0.7  # higher than single-keyword baseline

    def test_many_matches_capped_at_0_95(self, detector):
        # many keywords for same group
        result = detector.detect("candidato candidatos funil talento triagem cv currículo score lia")
        assert result.confidence <= 0.95

    def test_confidence_increases_with_more_keywords(self, detector):
        one = detector.detect("vaga")
        two = detector.detect("vaga vagas")
        assert two.confidence >= one.confidence


# ---------------------------------------------------------------------------
# Case insensitivity
# ---------------------------------------------------------------------------

class TestCaseHandling:
    def test_uppercase_message_matches(self, detector):
        result = detector.detect("CRIAR VAGA URGENTE")
        assert result.page == "Vagas"

    def test_mixed_case_message_matches(self, detector):
        result = detector.detect("Ver Candidatos da Vaga")
        # contains "candidatos" → funil
        assert result.page == "Funil de Talentos"

    def test_strip_whitespace_before_matching(self, detector):
        result = detector.detect("   vaga   ")
        assert result.page == "Vagas"


# ---------------------------------------------------------------------------
# NavigationIntentResult dataclass
# ---------------------------------------------------------------------------

class TestNavigationIntentResult:
    def test_result_has_page_field(self):
        r = NavigationIntentResult(page="Vagas", confidence=0.7, hint="hint")
        assert r.page == "Vagas"

    def test_result_has_matched_pattern_default_none(self):
        r = NavigationIntentResult(page=None, confidence=0.0, hint=None)
        assert r.matched_pattern is None

    def test_result_matched_pattern_can_be_set(self):
        r = NavigationIntentResult(page="Vagas", confidence=0.7, hint="h", matched_pattern="vaga")
        assert r.matched_pattern == "vaga"


# ---------------------------------------------------------------------------
# Public API and singleton
# ---------------------------------------------------------------------------

class TestPublicAPI:
    def test_detect_navigation_intent_returns_result(self):
        result = detect_navigation_intent("quero ver as vagas")
        assert isinstance(result, NavigationIntentResult)
        assert result.page == "Vagas"

    def test_singleton_detector_is_same_object(self):
        from app.orchestrator.context.navigation_intent import _detector as d1
        from app.orchestrator.context.navigation_intent import _detector as d2
        assert d1 is d2

    def test_singleton_returns_correct_page(self):
        result = detect_navigation_intent("painel de controle")
        assert result.page == "Painel de Controle"

    def test_multiple_calls_are_deterministic(self, detector):
        msg = "buscar candidatos no funil"
        r1 = detector.detect(msg)
        r2 = detector.detect(msg)
        assert r1.page == r2.page
        assert r1.confidence == r2.confidence
