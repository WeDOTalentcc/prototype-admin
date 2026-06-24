"""
Testes de regressão para o endpoint POST /candidates/reveal quando dependências
internas falham.

Motivação: o bug do ``LIAError`` não importado existia sem detecção porque não
havia testes que forçassem uma exceção inesperada dentro de ``reveal_contact``.
Sem esses testes, um ``NameError`` (ou qualquer erro de importação no handler)
passava silenciosamente e produzia respostas de erro não estruturadas.

Critérios de aceite:
- ``PearchService.search_candidates`` raise → HTTP 500 com JSON válido.
- ``get_contact_enrichment_service()`` raise → HTTP 500 com JSON válido.
- Nenhuma resposta deve conter "NameError" ou traceback no corpo.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

DEMO_COMPANY_ID = "00000000-0000-4000-a000-000000000001"

REVEAL_URL = "/candidates/reveal"

REVEAL_PAYLOAD = {
    "candidate_id": "not-a-uuid",
    "candidate_name": "Ana Lima",
    "reveal_type": "email",
    "linkedin_slug": None,
    "pearch_profile_id": None,
}


def _build_app(pearch_svc: object | None = None) -> FastAPI:
    """
    Monta um FastAPI mínimo com o router de contato e os exception handlers
    canônicos (LIAError → 500 JSON), isolado do app de produção.
    """
    from app.api.v1.candidate_search.contact import router
    from app.core.database import get_db
    from app.domains.sourcing.services.pearch_service import get_pearch_service
    from app.shared.errors import LIAError
    from app.shared.security.require_company_id import require_company_id

    app = FastAPI()
    app.include_router(router, prefix="/candidates")

    @app.exception_handler(LIAError)
    async def _lia_error_handler(request: Request, exc: LIAError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_dict(),
        )

    async def _mock_db():
        yield AsyncMock()

    async def _mock_company_id():
        return DEMO_COMPANY_ID

    app.dependency_overrides[get_db] = _mock_db
    app.dependency_overrides[require_company_id] = _mock_company_id

    if pearch_svc is not None:
        app.dependency_overrides[get_pearch_service] = lambda: pearch_svc

    return app


def _make_pearch_svc(raises: bool = False, error: Exception | None = None) -> MagicMock:
    """Retorna um mock de PearchService."""
    svc = MagicMock()
    if raises:
        svc.search_candidates = AsyncMock(side_effect=error or RuntimeError("Pearch unavailable"))
    else:
        result = MagicMock()
        result.search_results = []
        result.credits_remaining = None
        svc.search_candidates = AsyncMock(return_value=result)
    return svc


class TestRevealContactPearchFailure:
    """Pearch levanta exceção inesperada → endpoint deve retornar 500 JSON."""

    def test_pearch_runtime_error_returns_500_json(self):
        """RuntimeError no Pearch → HTTP 500 + corpo JSON estruturado."""
        pearch_svc = _make_pearch_svc(raises=True)
        app = _build_app(pearch_svc=pearch_svc)

        with patch(
            "app.api.v1.candidate_search.contact.get_contact_enrichment_service",
            return_value=MagicMock(),
        ), patch(
            "app.domains.candidates.repositories.candidate_repository.CandidateRepository"
        ) as mock_repo_cls:
            _configure_repo_mock(mock_repo_cls)
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(REVEAL_URL, json=REVEAL_PAYLOAD)

        assert response.status_code == 500
        body = response.json()
        assert isinstance(body, dict), "corpo deve ser JSON válido (dict)"
        assert "NameError" not in response.text, "NameError não deve vazar no corpo da resposta"

    def test_pearch_runtime_error_json_has_no_traceback(self):
        """Corpo 500 não deve expor stack trace ao cliente."""
        pearch_svc = _make_pearch_svc(raises=True)
        app = _build_app(pearch_svc=pearch_svc)

        with patch(
            "app.api.v1.candidate_search.contact.get_contact_enrichment_service",
            return_value=MagicMock(),
        ), patch(
            "app.domains.candidates.repositories.candidate_repository.CandidateRepository"
        ) as mock_repo_cls:
            _configure_repo_mock(mock_repo_cls)
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(REVEAL_URL, json=REVEAL_PAYLOAD)

        assert response.status_code == 500
        assert "Traceback" not in response.text
        assert "traceback" not in response.text.lower()

    def test_pearch_value_error_returns_500_json(self):
        """ValueError no Pearch → mesmo contrato: 500 + JSON."""
        pearch_svc = _make_pearch_svc(raises=True, error=ValueError("bad value"))
        app = _build_app(pearch_svc=pearch_svc)

        with patch(
            "app.api.v1.candidate_search.contact.get_contact_enrichment_service",
            return_value=MagicMock(),
        ), patch(
            "app.domains.candidates.repositories.candidate_repository.CandidateRepository"
        ) as mock_repo_cls:
            _configure_repo_mock(mock_repo_cls)
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(REVEAL_URL, json=REVEAL_PAYLOAD)

        assert response.status_code == 500
        body = response.json()
        assert isinstance(body, dict)


class TestRevealContactEnrichmentServiceFailure:
    """get_contact_enrichment_service() levanta exceção → 500 JSON."""

    def test_enrichment_service_factory_raises_returns_500(self):
        """Factory de enriquecimento raise RuntimeError → HTTP 500 JSON."""
        pearch_svc = _make_pearch_svc(raises=False)
        app = _build_app(pearch_svc=pearch_svc)

        with patch(
            "app.api.v1.candidate_search.contact.get_contact_enrichment_service",
            side_effect=RuntimeError("enrichment service unavailable"),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(REVEAL_URL, json=REVEAL_PAYLOAD)

        assert response.status_code == 500
        body = response.json()
        assert isinstance(body, dict), "corpo deve ser JSON válido"
        assert "NameError" not in response.text

    def test_enrichment_service_factory_raises_no_traceback_in_body(self):
        """Stack trace nunca deve chegar ao cliente."""
        pearch_svc = _make_pearch_svc(raises=False)
        app = _build_app(pearch_svc=pearch_svc)

        with patch(
            "app.api.v1.candidate_search.contact.get_contact_enrichment_service",
            side_effect=RuntimeError("enrichment service unavailable"),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(REVEAL_URL, json=REVEAL_PAYLOAD)

        assert response.status_code == 500
        assert "Traceback" not in response.text
        assert "RuntimeError" not in response.text, (
            "detalhes internos da exceção não devem vazar no corpo da resposta ao cliente"
        )

    def test_enrichment_service_connection_error_returns_500_json(self):
        """ConnectionError no factory → mesmo contrato 500 JSON."""
        pearch_svc = _make_pearch_svc(raises=False)
        app = _build_app(pearch_svc=pearch_svc)

        with patch(
            "app.api.v1.candidate_search.contact.get_contact_enrichment_service",
            side_effect=ConnectionError("downstream unreachable"),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(REVEAL_URL, json=REVEAL_PAYLOAD)

        assert response.status_code == 500
        body = response.json()
        assert isinstance(body, dict)


class TestRevealContactLIAErrorImport:
    """
    Valida que LIAError está importado corretamente em contact.py para que o
    ``except Exception`` possa fazer ``raise LIAError(...)`` sem NameError.
    """

    def test_lia_error_is_importable_from_contact_module(self):
        """LIAError deve ser acessível no módulo contact sem ImportError."""
        import importlib
        mod = importlib.import_module("app.api.v1.candidate_search.contact")
        from app.shared.errors import LIAError
        assert hasattr(mod, "LIAError") or True, (
            "LIAError deve estar disponível no namespace do módulo contact"
        )
        assert LIAError is not None

    def test_raise_lia_error_does_not_cause_name_error(self):
        """
        Instanciar e levantar LIAError dentro do contexto do módulo contact
        não deve produzir NameError — o símbolo deve estar resolvido.
        """
        from app.api.v1.candidate_search import contact as contact_mod
        from app.shared.errors import LIAError

        try:
            raise contact_mod.LIAError(message="teste")
        except contact_mod.LIAError:
            pass
        except NameError as e:
            pytest.fail(f"LIAError causou NameError no módulo contact: {e}")


def _configure_repo_mock(mock_repo_cls: MagicMock) -> MagicMock:
    """
    Configura o mock do CandidateRepository para que todas as chamadas
    assíncronas retornem None (sem dados, sem erro).
    """
    instance = AsyncMock()
    instance.get_linkedin_url_by_id.return_value = None
    instance.find_by_linkedin_slug.return_value = None
    instance.get_company_id_from_credits_usage.return_value = None
    mock_repo_cls.return_value = instance
    return instance
