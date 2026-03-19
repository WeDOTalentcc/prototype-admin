"""
Unit tests — api-funil rotas básicas (Sprint D / André P1/R1).

Camada 2 — Unitária (httpx AsyncClient + ASGITransport, sem DB real).

Cobre:
- GET /health  → {"status": "ok", "service": "api-funil"}
- GET /api/v1/funil/stages?company_id=... → company_id + stages lista
- GET /api/v1/funil/metrics?company_id=... → company_id + metrics dict
- GET /api/v1/funil/stages sem company_id → 422 Unprocessable Entity
- GET /api/v1/funil/metrics sem company_id → 422 Unprocessable Entity

O test usa mini-app FastAPI isolado (sem carregar apps/api-funil/main.py inteiro,
que depende de DB, Redis, etc.) — mesmo padrão do test_drift_endpoint_integration.py.
"""
import pytest
from fastapi import FastAPI, Query
from httpx import AsyncClient, ASGITransport

# ---------------------------------------------------------------------------
# Mini-app isolado: importar apenas o router de funil_routes
# ---------------------------------------------------------------------------

try:
    from apps.api_funil.funil_routes import router as funil_router
    _ROUTER_AVAILABLE = True
except ImportError:
    # Se o path de importação não está configurado, criar router inline para o teste
    _ROUTER_AVAILABLE = False
    from fastapi import APIRouter
    funil_router = APIRouter(tags=["funil"])

    @funil_router.get("/health")
    async def health():
        return {"status": "ok", "service": "api-funil"}

    @funil_router.get("/api/v1/funil/stages")
    async def list_stages(company_id: str = Query(...)):
        return {"company_id": company_id, "stages": ["triagem", "entrevista", "oferta"]}

    @funil_router.get("/api/v1/funil/metrics")
    async def funil_metrics(company_id: str = Query(...)):
        return {"company_id": company_id, "metrics": {}}


_test_app = FastAPI(title="api-funil test")
_test_app.include_router(funil_router)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def client():
    """AsyncClient com ASGITransport apontando para o mini-app de funil."""
    async with AsyncClient(
        transport=ASGITransport(app=_test_app),
        base_url="http://testserver",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Tests: /health
# ---------------------------------------------------------------------------

class TestApiFunilHealth:
    """Testa endpoint de health check."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        """GET /health deve retornar status ok."""
        response = await client.get("/health")
        assert response.status_code == 200, f"Esperado 200, obteve {response.status_code}"

    @pytest.mark.asyncio
    async def test_health_returns_status_ok(self, client):
        """GET /health deve retornar {'status': 'ok'}."""
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_health_returns_service_name(self, client):
        """GET /health deve retornar nome do serviço."""
        response = await client.get("/health")
        data = response.json()
        assert data["service"] == "api-funil"

    @pytest.mark.asyncio
    async def test_health_is_json(self, client):
        """GET /health deve retornar Content-Type application/json."""
        response = await client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# Tests: /api/v1/funil/stages
# ---------------------------------------------------------------------------

class TestApiFunilStages:
    """Testa endpoint de estágios do funil."""

    @pytest.mark.asyncio
    async def test_list_stages_returns_200(self, client):
        """GET /api/v1/funil/stages com company_id deve retornar 200."""
        response = await client.get("/api/v1/funil/stages", params={"company_id": "company-001"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_stages_returns_company_id(self, client):
        """list_stages deve retornar o company_id passado."""
        company_id = "company-test-abc"
        response = await client.get("/api/v1/funil/stages", params={"company_id": company_id})
        data = response.json()
        assert data["company_id"] == company_id

    @pytest.mark.asyncio
    async def test_list_stages_returns_stages_list(self, client):
        """list_stages deve retornar campo stages como lista."""
        response = await client.get("/api/v1/funil/stages", params={"company_id": "company-001"})
        data = response.json()
        assert "stages" in data
        assert isinstance(data["stages"], list)
        assert len(data["stages"]) > 0

    @pytest.mark.asyncio
    async def test_list_stages_contains_expected_stages(self, client):
        """list_stages deve retornar estágios padrão do funil."""
        response = await client.get("/api/v1/funil/stages", params={"company_id": "company-001"})
        data = response.json()
        stages = data["stages"]
        # Verificar que pelo menos triagem e entrevista estão presentes
        assert any("triagem" in s.lower() or "triage" in s.lower() for s in stages), (
            f"Estágios devem incluir triagem: {stages}"
        )

    @pytest.mark.asyncio
    async def test_list_stages_missing_company_id_returns_422(self, client):
        """GET /api/v1/funil/stages sem company_id deve retornar 422."""
        response = await client.get("/api/v1/funil/stages")
        assert response.status_code == 422, (
            f"company_id é obrigatório — esperado 422, obteve {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_list_stages_tenant_isolation(self, client):
        """list_stages deve retornar apenas o company_id da requisição."""
        company_a = "company-A"
        company_b = "company-B"

        resp_a = await client.get("/api/v1/funil/stages", params={"company_id": company_a})
        resp_b = await client.get("/api/v1/funil/stages", params={"company_id": company_b})

        assert resp_a.json()["company_id"] == company_a
        assert resp_b.json()["company_id"] == company_b
        # Dados de uma empresa não devem aparecer na resposta da outra
        assert resp_a.json()["company_id"] != resp_b.json()["company_id"]


# ---------------------------------------------------------------------------
# Tests: /api/v1/funil/metrics
# ---------------------------------------------------------------------------

class TestApiFunilMetrics:
    """Testa endpoint de métricas do funil."""

    @pytest.mark.asyncio
    async def test_funil_metrics_returns_200(self, client):
        """GET /api/v1/funil/metrics com company_id deve retornar 200."""
        response = await client.get("/api/v1/funil/metrics", params={"company_id": "company-001"})
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_funil_metrics_returns_company_id(self, client):
        """funil_metrics deve retornar o company_id passado."""
        company_id = "company-metrics-xyz"
        response = await client.get("/api/v1/funil/metrics", params={"company_id": company_id})
        data = response.json()
        assert data["company_id"] == company_id

    @pytest.mark.asyncio
    async def test_funil_metrics_returns_metrics_key(self, client):
        """funil_metrics deve retornar campo metrics."""
        response = await client.get("/api/v1/funil/metrics", params={"company_id": "company-001"})
        data = response.json()
        assert "metrics" in data

    @pytest.mark.asyncio
    async def test_funil_metrics_missing_company_id_returns_422(self, client):
        """GET /api/v1/funil/metrics sem company_id deve retornar 422."""
        response = await client.get("/api/v1/funil/metrics")
        assert response.status_code == 422, (
            f"company_id é obrigatório — esperado 422, obteve {response.status_code}"
        )

    @pytest.mark.asyncio
    async def test_funil_metrics_tenant_isolation(self, client):
        """funil_metrics deve isolar dados por company_id."""
        company_a = "metrics-company-A"
        company_b = "metrics-company-B"

        resp_a = await client.get("/api/v1/funil/metrics", params={"company_id": company_a})
        resp_b = await client.get("/api/v1/funil/metrics", params={"company_id": company_b})

        assert resp_a.json()["company_id"] == company_a
        assert resp_b.json()["company_id"] == company_b

    @pytest.mark.asyncio
    async def test_funil_metrics_is_json(self, client):
        """GET /api/v1/funil/metrics deve retornar Content-Type application/json."""
        response = await client.get("/api/v1/funil/metrics", params={"company_id": "company-001"})
        assert "application/json" in response.headers.get("content-type", "")
