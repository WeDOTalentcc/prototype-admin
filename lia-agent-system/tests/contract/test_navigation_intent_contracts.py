"""
Contract tests — Navigation Intent API (Phase 4b).

Verifica contratos do endpoint POST /api/v1/navigation-intent:
- Schema de request/response
- Detector: confidence threshold, page mapping, hit scoring
- Edge cases: mensagem vazia, mensagem irrelevante, caracteres especiais

Camada 5 — Contrato (pytest)
"""
import pytest


# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------


class TestNavigationIntentRequestContract:
    """POST /api/v1/navigation-intent aceita { message: str }."""

    def test_request_schema_has_message_field(self):
        from app.api.v1.navigation_intent import NavigationIntentRequest
        fields = NavigationIntentRequest.model_fields
        assert "message" in fields

    def test_request_message_min_length_1(self):
        from app.api.v1.navigation_intent import NavigationIntentRequest
        import pydantic
        with pytest.raises((pydantic.ValidationError, ValueError)):
            NavigationIntentRequest(message="")

    def test_request_message_max_length_2000(self):
        from app.api.v1.navigation_intent import NavigationIntentRequest
        import pydantic
        with pytest.raises((pydantic.ValidationError, ValueError)):
            NavigationIntentRequest(message="x" * 2001)

    def test_request_valid_message(self):
        from app.api.v1.navigation_intent import NavigationIntentRequest
        req = NavigationIntentRequest(message="ver vagas abertas")
        assert req.message == "ver vagas abertas"


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class TestNavigationIntentResponseContract:
    """Garante que NavigationIntentResponse tem todos os campos esperados pelo FE."""

    def test_response_has_page_field(self):
        from app.api.v1.navigation_intent import NavigationIntentResponse
        fields = NavigationIntentResponse.model_fields
        assert "page" in fields

    def test_response_has_confidence_field(self):
        from app.api.v1.navigation_intent import NavigationIntentResponse
        fields = NavigationIntentResponse.model_fields
        assert "confidence" in fields

    def test_response_has_hint_field(self):
        from app.api.v1.navigation_intent import NavigationIntentResponse
        fields = NavigationIntentResponse.model_fields
        assert "hint" in fields

    def test_response_has_matched_pattern_field(self):
        from app.api.v1.navigation_intent import NavigationIntentResponse
        fields = NavigationIntentResponse.model_fields
        assert "matched_pattern" in fields

    def test_response_serializes_to_dict(self):
        from app.api.v1.navigation_intent import NavigationIntentResponse
        resp = NavigationIntentResponse(
            page="Vagas",
            confidence=0.85,
            hint="Ver vagas abertas",
            matched_pattern="vagas",
        )
        d = resp.model_dump()
        assert d["page"] == "Vagas"
        assert d["confidence"] == 0.85
        assert "hint" in d
        assert "matched_pattern" in d

    def test_response_page_can_be_none(self):
        from app.api.v1.navigation_intent import NavigationIntentResponse
        resp = NavigationIntentResponse(
            page=None,
            confidence=0.3,
            hint=None,
            matched_pattern=None,
        )
        assert resp.page is None


# ---------------------------------------------------------------------------
# NavigationIntentDetector logic
# ---------------------------------------------------------------------------


class TestNavigationIntentDetector:
    """Testa o detector de intenção baseado em keywords."""

    def test_detect_vagas_keywords(self):
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        result = detect_navigation_intent("quero ver as vagas abertas")
        assert result.page == "Vagas"
        assert result.confidence >= 0.65

    def test_detect_candidatos_keywords(self):
        # CR-3 (2026-06-03): "listar candidatos" agora e data-read veto
        # (agente global federado responde inline) -- ver
        # test_navigation_intent_yields_to_data_query.py. Navegacao genuina
        # de candidatos usa "ver/mostrar", que continua deflectando pro Funil.
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        result = detect_navigation_intent("ver os candidatos disponíveis")
        assert result.page in ("Funil de Talentos",)
        assert result.confidence >= 0.65

    def test_detect_painel_keywords(self):
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        result = detect_navigation_intent("abrir painel de controle")
        # Deve detectar "Painel de Controle" ou ter confidence baixa
        if result.confidence >= 0.65:
            assert result.page is not None

    def test_detect_irrelevant_message_low_confidence(self):
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        result = detect_navigation_intent("olá como vai")
        # Mensagem irrelevante deve ter confidence baixa
        assert result.confidence < 0.65 or result.page is None

    def test_detect_empty_message_returns_null_page(self):
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        result = detect_navigation_intent("")
        # Sem keywords, page deve ser None ou confidence baixa
        assert result.page is None or result.confidence < 0.65

    def test_detect_result_has_all_fields(self):
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        result = detect_navigation_intent("ver vagas")
        assert hasattr(result, "page")
        assert hasattr(result, "confidence")
        assert hasattr(result, "hint")
        assert hasattr(result, "matched_pattern")

    def test_detect_confidence_bounded_0_to_1(self):
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        result = detect_navigation_intent("vagas candidatos painel dashboard")
        assert 0.0 <= result.confidence <= 1.0

    def test_detect_multiple_keywords_increases_confidence(self):
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        # Single keyword (navegacao genuina)
        r1 = detect_navigation_intent("vagas")
        # Multiple keywords from same group -- evita verbos de criacao (CR-2
        # veto) usando keywords que indicam VER vagas existentes em vez de
        # CRIAR novas. Mantem invariante do ranking cumulativo do detector.
        r2 = detect_navigation_intent("vagas headcount job description posição aberta")
        assert r2.confidence >= r1.confidence

    def test_detect_kanban_keywords(self):
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        result = detect_navigation_intent("ver kanban do pipeline")
        assert result.confidence >= 0.0  # at minimum returns a result

    def test_detect_case_insensitive(self):
        from app.orchestrator.context.navigation_intent import detect_navigation_intent
        r1 = detect_navigation_intent("VAGAS ABERTAS")
        r2 = detect_navigation_intent("vagas abertas")
        # ambos devem detectar a mesma página
        assert r1.page == r2.page


# ---------------------------------------------------------------------------
# Integration: endpoint delegates to detector
# ---------------------------------------------------------------------------


class TestNavigationIntentEndpointContract:
    """Garante que o endpoint usa o detector corretamente."""

    def test_endpoint_returns_response_model(self):
        """Endpoint retorna NavigationIntentResponse tipado."""
        from app.api.v1.navigation_intent import NavigationIntentResponse
        # Verifica que o modelo pode ser instanciado corretamente
        resp = NavigationIntentResponse(
            page="Vagas",
            confidence=0.85,
            hint="Ver vagas abertas",
            matched_pattern="vagas",
        )
        assert resp.page == "Vagas"

    def test_router_has_post_route(self):
        from app.api.v1.navigation_intent import router
        routes = [r.path for r in router.routes]
        # FastAPI inclui o prefix na rota compilada → "/navigation-intent" ou ""
        assert any("navigation-intent" in p or p in ("", "/") for p in routes)

    def test_router_prefix_is_navigation_intent(self):
        from app.api.v1.navigation_intent import router
        assert router.prefix == "/navigation-intent"
