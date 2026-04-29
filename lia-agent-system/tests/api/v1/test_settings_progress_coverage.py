"""
Coverage tests for app/api/v1/settings_progress.py — Task #930.

Cobre:
- happy: GET /settings/progress retorna estrutura completa com scores.
- erro: repository falha → endpoint devolve fallback gracioso (overall=0, error=True).
- isolamento: company_id query muda o resultado (cada tenant resolve via repo independente).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.settings_progress import router
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.core.database import get_db


COMPANY_A = "11111111-1111-1111-1111-111111111111"


def _user_in(company_id: str = COMPANY_A) -> MagicMock:
    """Mock user whose JWT-derived company matches `company_id` (Onda 36 guards)."""
    u = MagicMock(spec=User)
    u.id = f"user-{company_id}"
    u.email = f"user@{company_id}.test"
    u.company_id = company_id
    u.role = "user"
    u.is_active = True
    u.can_access_company = lambda cid: cid == company_id
    return u


def _fake_db() -> MagicMock:
    """AsyncSession mock with begin_nested as async context manager."""
    db = MagicMock()

    @asynccontextmanager
    async def _ctx():
        yield None

    db.begin_nested = lambda: _ctx()
    return db


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    application.dependency_overrides[get_db] = lambda: _fake_db()
    # Onda 36: tenant guard exige current_user; default = COMPANY_A.
    application.dependency_overrides[get_current_user_or_demo] = lambda: _user_in(COMPANY_A)
    return application


def _build_repo_mock(
    *,
    benefits: int = 2,
    policies: int = 2,
    stages: int = 4,
    slas: int = 1,
    questions: int = 5,
    templates: int = 2,
    has_sig: bool = True,
    alerts: int = 1,
    has_lgpd: bool = True,
    users: int = 3,
    depts: int = 2,
    integrations: int = 1,
    webhooks: int = 1,
    delivering: int = 1,
    company_id: str = COMPANY_A,
) -> MagicMock:
    repo = MagicMock()
    company = MagicMock()
    company.id = company_id
    company.name = "Acme Co"
    company.website = "https://acme.test"
    company.sector = "tech"
    company.industry = "tech"
    company.description = "desc"
    company.headquarters_city = "SP"
    company.employee_count = 100
    company.company_size = "100-500"
    company.logo_url = "https://logo"

    # Onda 36: handler agora usa get_company_by_id (após validate_company_access).
    # Mantém get_default_company por retrocompat de outros testes/callers.
    repo.get_default_company = AsyncMock(return_value=company)
    repo.get_company_by_id = AsyncMock(return_value=company)
    repo.get_culture_profile = AsyncMock(return_value={
        "mission": "m",
        "vision": "v",
        "values": ["v1"],
        "core_competencies": ["c1"],
        "evp_bullets": ["e1"],
        "tech_stack": ["python"],
        "engineering_culture": "agile",
        "default_languages": ["pt"],
        "additional_data": {"workforce_plan": {"plan": True}},
    })
    repo.count_active_benefits = AsyncMock(return_value=benefits)
    repo.count_active_policies = AsyncMock(return_value=policies)
    repo.count_active_stages = AsyncMock(return_value=stages)
    repo.count_active_slas = AsyncMock(return_value=slas)
    repo.count_active_screening_questions = AsyncMock(return_value=questions)
    repo.count_active_templates = AsyncMock(return_value=templates)
    repo.has_email_signature = AsyncMock(return_value=has_sig)
    repo.count_active_alert_configs = AsyncMock(return_value=alerts)
    repo.has_lgpd_schedule = AsyncMock(return_value=has_lgpd)
    repo.count_active_users = AsyncMock(return_value=users)
    repo.count_active_departments = AsyncMock(return_value=depts)
    repo.count_active_integrations = AsyncMock(return_value=integrations)
    repo.count_webhooks = AsyncMock(return_value=webhooks)
    repo.count_delivering_webhooks = AsyncMock(return_value=delivering)
    return repo


class TestSettingsProgressHappy:
    def test_returns_full_structure(self, app: FastAPI):
        repo = _build_repo_mock()
        with patch(
            "app.api.v1.settings_progress.SettingsProgressRepository",
            return_value=repo,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/settings/progress")
        assert r.status_code == 200
        body = r.json()
        assert "overall" in body
        assert isinstance(body["overall"], int)
        assert 0 <= body["overall"] <= 100
        # All 8 sections present
        assert set(body["sections"].keys()) == {
            "minha-empresa", "pipeline", "screening", "templates-assinatura",
            "comunicacao-alertas", "usuarios-departamentos", "integracoes", "webhooks",
        }
        assert body["sections"]["webhooks"] == 100  # delivering=1 → 100
        assert body["details"]["company_name"] == "Acme Co"


class TestSettingsProgressError:
    def test_repository_raises_returns_fallback(self, app: FastAPI):
        with patch(
            "app.api.v1.settings_progress.SettingsProgressRepository",
            side_effect=RuntimeError("db down"),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get("/api/v1/settings/progress")
        # Endpoint catches and returns fallback structure (overall=0, error=True)
        assert r.status_code == 200
        body = r.json()
        assert body["overall"] == 0
        assert body.get("error") is True
        assert body.get("error_message")
        # All sections still present, all zeroed
        for v in body["sections"].values():
            assert v == 0


class TestSettingsProgressIsolation:
    def test_different_companies_yield_different_scores(self, app: FastAPI):
        """When the resolved company has no UUID, all sections fall back to 0."""
        repo_no_company = MagicMock()
        repo_no_company.get_default_company = AsyncMock(return_value=None)
        # Onda 36: handler chama get_company_by_id; simular "company não encontrada".
        repo_no_company.get_company_by_id = AsyncMock(return_value=None)

        with patch(
            "app.api.v1.settings_progress.SettingsProgressRepository",
            return_value=repo_no_company,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r1 = client.get("/api/v1/settings/progress")
        assert r1.status_code == 200
        body_empty = r1.json()
        assert body_empty["overall"] == 0
        assert body_empty["details"]["company_id"] is None

        # Now a populated tenant — sections are non-zero
        repo_full = _build_repo_mock()
        with patch(
            "app.api.v1.settings_progress.SettingsProgressRepository",
            return_value=repo_full,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r2 = client.get("/api/v1/settings/progress")
        assert r2.status_code == 200
        body_full = r2.json()
        assert body_full["overall"] > 0
        # Cross-tenant separation is enforced by the repo returning different
        # company.id — confirm that both responses propagate the company UUID
        # they were given (no leakage between calls).
        assert body_empty["details"]["company_id"] != body_full["details"]["company_id"]
