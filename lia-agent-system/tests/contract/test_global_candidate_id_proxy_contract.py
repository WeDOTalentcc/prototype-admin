"""Contract test — candidato GLOBAL (pearch, id nao-UUID) nao pode gerar 422.

Pina os fixes de 2026-06-05 (handoff Funil de Talentos):
- #7: GET /api/v1/data-requests?candidate_id=<nao-UUID> -> 200 lista vazia,
      nunca 422 (candidate_id Query agora str|None; nao-UUID -> []).
      Antes do fix era candidate_id: UUID -> 422 p/ id global pearch.
- #3: GET /api/v1/experience-highlights/<pearch-slug> valida via
      CANDIDATE_OR_SOURCING_ID_PATTERN -> 404 (sem highlight), nunca 422.
      Antes era DUAL_ID_PATH_PATTERN -> 422 p/ slug pearch.

Raiz comum (handoff): candidato global recebe id sintetico NAO-UUID
(useCandidatesExecuteSearch.ts gera "search-<ts>-<rand>" ou slug pearch);
endpoints candidate-scoped que exigiam UUID respondiam 422.

Strategy: TestClient + app minimo + dependency_overrides (vide
test_agent_studio_voice_endpoints.py). Sem DB real:
- data_request: branch nao-UUID retorna [] ANTES de tocar o DB.
- experience_highlights: patch repo.get_valid_highlight -> None -> 404.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

COMPANY_ID = "11111111-1111-1111-1111-111111111111"

# ids reais nao-UUID gerados pelo FE p/ candidato global
PEARCH_IDS = ["search-1700000000-abc123", "paul-criswell-7583691"]


# ───────────────────────── #7 data-requests (Query str|None) ─────────────────

def _data_request_app() -> FastAPI:
    from app.api.v1 import data_request
    from app.core.database import get_db
    from app.shared.security.require_company_id import require_company_id

    app = FastAPI()
    app.include_router(data_request.router, prefix="/api/v1")

    async def _fake_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = _fake_db
    app.dependency_overrides[require_company_id] = lambda: COMPANY_ID
    return app


@pytest.mark.parametrize("cid", PEARCH_IDS)
def test_data_requests_non_uuid_candidate_returns_200_empty_not_422(cid):
    """#7: id global pearch -> 200 lista vazia (fail-soft), nunca 422."""
    client = TestClient(_data_request_app())
    resp = client.get(f"/api/v1/data-requests?candidate_id={cid}")
    assert resp.status_code == 200, (cid, resp.status_code, resp.text)
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_data_requests_uuid_candidate_not_rejected_at_validation():
    """Controle: candidate_id UUID valido nao e 422 (path normal preservado)."""
    from app.domains.communication.services import data_request_service as svc_mod
    with patch.object(
        svc_mod.data_request_service,
        "get_candidate_data_requests",
        AsyncMock(return_value=[]),
    ):
        client = TestClient(_data_request_app())
        resp = client.get(f"/api/v1/data-requests?candidate_id={uuid4()}")
    assert resp.status_code == 200, (resp.status_code, resp.text)


# ──────────────────── #3 experience-highlights (Path pattern) ────────────────

def _experience_highlights_app() -> FastAPI:
    from app.api.v1 import experience_highlights
    from app.auth.dependencies import get_current_user_or_demo
    from app.core.database import get_tenant_db
    from app.shared.security.require_company_id import require_company_id

    app = FastAPI()
    app.include_router(experience_highlights.router, prefix="/api/v1")

    async def _fake_db():
        yield MagicMock()

    user = SimpleNamespace(id=uuid4(), company_id=COMPANY_ID, role="admin")
    app.dependency_overrides[get_tenant_db] = _fake_db
    app.dependency_overrides[get_current_user_or_demo] = lambda: user
    app.dependency_overrides[require_company_id] = lambda: COMPANY_ID
    return app


@pytest.mark.parametrize("cid", PEARCH_IDS)
def test_experience_highlight_pearch_slug_not_422(cid):
    """#3: slug pearch passa o pattern -> 404 (sem highlight), nunca 422."""
    with patch(
        "app.api.v1.experience_highlights.ExperienceHighlightRepository.get_valid_highlight",
        AsyncMock(return_value=None),
    ):
        client = TestClient(_experience_highlights_app())
        resp = client.get(f"/api/v1/experience-highlights/{cid}")
    assert resp.status_code != 422, (cid, resp.status_code, resp.text)
    assert resp.status_code == 404, (cid, resp.status_code, resp.text)


def test_experience_highlight_garbage_id_still_422():
    """Controle positivo: id que NAO casa o pattern (comeca com '-') -> 422.

    Prova que o pattern afrouxou so p/ slug pearch, nao virou 'aceita tudo'.
    """
    client = TestClient(_experience_highlights_app())
    resp = client.get("/api/v1/experience-highlights/-invalid")
    assert resp.status_code == 422, (resp.status_code, resp.text)
