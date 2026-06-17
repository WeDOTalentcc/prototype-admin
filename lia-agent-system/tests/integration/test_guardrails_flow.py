"""
Integração — Guardrails API (CRUD completo)

Testa o flow completo: criar → listar → atualizar → toggle → seed-defaults.
Usa mini-app isolado (sem app.main) + DB in-memory via mock.

Sprint X2 / I1 — K2 (15/03/2026)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from app.api.v1.guardrails import router as guardrails_router
from app.core.database import get_db

_test_app = FastAPI()
_test_app.include_router(guardrails_router, prefix="/api/v1")

COMPANY_ID = str(uuid4())
GUARDRAIL_ID = str(uuid4())

_mock_guardrail = MagicMock()
_mock_guardrail.id = GUARDRAIL_ID
_mock_guardrail.level = "primary"
_mock_guardrail.domain = None
_mock_guardrail.node = None
_mock_guardrail.tool = None
_mock_guardrail.rule = "Nunca discriminar por gênero ou raça."
_mock_guardrail.blocking_message = "Ação bloqueada por guardrail de equidade."
_mock_guardrail.is_active = True
_mock_guardrail.company_id = COMPANY_ID
_mock_guardrail.updated_by = "admin"
_mock_guardrail.updated_at = datetime.utcnow()


def _mock_db():
    db = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [_mock_guardrail]
    result.scalar_one_or_none.return_value = _mock_guardrail
    db.execute.return_value = result
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    return db


async def _mock_db_gen():
    yield _mock_db()


@pytest.mark.asyncio
async def test_list_guardrails_returns_200():
    """GET /guardrails deve retornar lista com campos corretos."""
    with patch("app.api.v1.guardrails.get_db", _mock_db_gen):
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/guardrails")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "id" in data[0]
    assert "rule" in data[0]
    assert "is_active" in data[0]


@pytest.mark.asyncio
async def test_list_guardrails_filter_by_domain():
    """GET /guardrails?domain=cv_screening deve filtrar corretamente."""
    with patch("app.api.v1.guardrails.get_db", _mock_db_gen):
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/guardrails?domain=cv_screening")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_guardrails_filter_by_company():
    """GET /guardrails?company_id= deve filtrar por tenant."""
    with patch("app.api.v1.guardrails.get_db", _mock_db_gen):
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/api/v1/guardrails?company_id={COMPANY_ID}")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_guardrail_by_id():
    """GET /guardrails/{id} deve retornar o guardrail correto."""
    _test_app.dependency_overrides[get_db] = _mock_db_gen
    try:
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/api/v1/guardrails/{GUARDRAIL_ID}")
    finally:
        _test_app.dependency_overrides.pop(get_db, None)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == GUARDRAIL_ID
    assert data["level"] == "primary"


@pytest.mark.asyncio
async def test_get_guardrail_not_found():
    """GET /guardrails/{id} inexistente deve retornar 404."""
    db = _mock_db()
    db.execute.return_value.scalar_one_or_none.return_value = None
    with patch("app.api.v1.guardrails.get_db", return_value=db):
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/api/v1/guardrails/{uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_guardrail_returns_201():
    """POST /guardrails deve criar e retornar 201."""
    with patch("app.api.v1.guardrails.GuardrailRepository") as mock_repo:
        mock_repo.upsert = AsyncMock(return_value=_mock_guardrail)
        with patch("app.api.v1.guardrails.get_db", _mock_db_gen):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/v1/guardrails", json={
                    "level": "primary",
                    "rule": "Nunca revelar dados pessoais sem autorização.",
                    "blocking_message": "Ação bloqueada.",
                    "updated_by": "admin",
                })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_update_guardrail_returns_200():
    """PUT /guardrails/{id} deve atualizar e retornar 200."""
    _test_app.dependency_overrides[get_db] = _mock_db_gen
    try:
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            resp = await client.put(f"/api/v1/guardrails/{GUARDRAIL_ID}", json={
                "rule": "Regra atualizada.",
                "updated_by": "admin",
            })
    finally:
        _test_app.dependency_overrides.pop(get_db, None)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_guardrail_not_found():
    """PUT /guardrails/{id} inexistente deve retornar 404."""
    db = _mock_db()
    db.execute.return_value.scalar_one_or_none.return_value = None
    with patch("app.api.v1.guardrails.get_db", return_value=db):
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            resp = await client.put(f"/api/v1/guardrails/{uuid4()}", json={
                "rule": "x", "updated_by": "admin",
            })
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_toggle_guardrail():
    """PATCH /guardrails/{id}/toggle deve mudar is_active."""
    with patch("app.api.v1.guardrails.GuardrailRepository") as mock_repo:
        toggled = MagicMock(**{**_mock_guardrail.__dict__, "is_active": False})
        toggled.id = GUARDRAIL_ID
        toggled.level = "primary"
        toggled.domain = None
        toggled.node = None
        toggled.tool = None
        toggled.rule = _mock_guardrail.rule
        toggled.blocking_message = _mock_guardrail.blocking_message
        toggled.is_active = False
        toggled.company_id = COMPANY_ID
        toggled.updated_by = "admin"
        toggled.updated_at = datetime.utcnow()
        mock_repo.toggle_active = AsyncMock(return_value=toggled)
        with patch("app.api.v1.guardrails.get_db", _mock_db_gen):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                resp = await client.patch(f"/api/v1/guardrails/{GUARDRAIL_ID}/toggle")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_toggle_guardrail_not_found():
    """PATCH /guardrails/{id}/toggle inexistente deve retornar 404."""
    with patch("app.api.v1.guardrails.GuardrailRepository") as mock_repo:
        mock_repo.toggle_active = AsyncMock(return_value=None)
        with patch("app.api.v1.guardrails.get_db", _mock_db_gen):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                resp = await client.patch(f"/api/v1/guardrails/{uuid4()}/toggle")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_guardrail_soft_delete():
    """DELETE /guardrails/{id} deve fazer soft-delete (204)."""
    with patch("app.api.v1.guardrails.GuardrailRepository") as mock_repo:
        mock_repo.soft_delete = AsyncMock(return_value=True)
        with patch("app.api.v1.guardrails.get_db", _mock_db_gen):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                resp = await client.delete(f"/api/v1/guardrails/{GUARDRAIL_ID}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_guardrail_not_found():
    """DELETE /guardrails/{id} inexistente deve retornar 404."""
    with patch("app.api.v1.guardrails.GuardrailRepository") as mock_repo:
        mock_repo.soft_delete = AsyncMock(return_value=False)
        with patch("app.api.v1.guardrails.get_db", _mock_db_gen):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                resp = await client.delete(f"/api/v1/guardrails/{uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_seed_defaults_creates_guardrails():
    """POST /guardrails/seed-defaults deve criar defaults idempotentemente."""
    db = _mock_db()
    # Simula que nenhum guardrail existe ainda
    db.execute.return_value.scalar_one_or_none.return_value = None

    with patch("app.api.v1.guardrails.GuardrailRepository") as mock_repo:
        mock_repo.upsert = AsyncMock(return_value=_mock_guardrail)
        with patch("app.api.v1.guardrails.get_db", return_value=db):
            async with AsyncClient(
                transport=ASGITransport(app=_test_app), base_url="http://test"
            ) as client:
                resp = await client.post("/api/v1/guardrails/seed-defaults")
    assert resp.status_code == 200
    data = resp.json()
    assert "created" in data
    assert "skipped" in data
    assert "total" in data
    assert data["total"] == 9  # 5 primários + 4 secundários


@pytest.mark.asyncio
async def test_seed_defaults_idempotent():
    """POST /guardrails/seed-defaults com guardrails já existentes deve retornar skipped."""
    # Simula todos já existindo
    db = _mock_db()
    db.execute.return_value.scalar_one_or_none.return_value = _mock_guardrail

    with patch("app.api.v1.guardrails.get_db", return_value=db):
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            resp = await client.post("/api/v1/guardrails/seed-defaults")
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"] == 9
    assert data["created"] == 0


@pytest.mark.asyncio
async def test_guardrail_response_has_required_fields():
    """Response de guardrail deve conter todos os campos do schema."""
    _test_app.dependency_overrides[get_db] = _mock_db_gen
    try:
        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test"
        ) as client:
            resp = await client.get(f"/api/v1/guardrails/{GUARDRAIL_ID}")
    finally:
        _test_app.dependency_overrides.pop(get_db, None)
    assert resp.status_code == 200
    data = resp.json()
    required_fields = {"id", "level", "rule", "blocking_message", "is_active", "updated_by"}
    assert required_fields.issubset(data.keys())
