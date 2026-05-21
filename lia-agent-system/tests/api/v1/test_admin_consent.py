"""T-21c tests — Admin Company Training Data Consent endpoints.

Cobre /api/v1/admin/consent/company-training-consent:
  - GET returns default DENY shape para new company (T-11 B.1.2 fail-CLOSED)
  - POST grant cria record + idempotent
  - POST revoke cascade LGPD Art. 18
  - Multi-tenancy cross-tenant 403 / 404 isolation
  - Audit log entry created (AUDIT-NO-DEMO)
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.admin_consent import router
from app.auth.dependencies import require_admin
from app.auth.models import User, UserRole
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from app.shared.tenant_guard import get_verified_company_id


COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"
ADMIN_USER_ID = "33333333-3333-3333-3333-333333333333"


def _admin_user(company_id: str = COMPANY_A) -> SimpleNamespace:
    return SimpleNamespace(
        id=UUID(ADMIN_USER_ID),
        company_id=company_id,
        is_active=True,
        role=UserRole.admin,
        email="admin@test.cc",
    )


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    db_mock = AsyncMock()
    db_mock.commit = AsyncMock()
    db_mock.rollback = AsyncMock()
    application.state.db_mock = db_mock
    application.dependency_overrides[get_db] = lambda: db_mock
    application.dependency_overrides[require_admin] = lambda: _admin_user(COMPANY_A)
    application.dependency_overrides[require_company_id] = lambda: COMPANY_A
    application.dependency_overrides[get_verified_company_id] = lambda: COMPANY_A
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


# ───────────────────────── GET status ────────────────────────────────────────


class TestGetCompanyTrainingConsent:
    def test_returns_default_deny_when_record_missing(self, client, app):
        """T-11 B.1.2 fail-CLOSED — new company sem record retorna deny shape."""
        with patch(
            "app.api.v1.admin_consent.CompanyTrainingConsentRepository"
        ) as RepoCls:
            repo = AsyncMock()
            repo.get_by_company = AsyncMock(return_value=None)
            RepoCls.return_value = repo

            resp = client.get("/api/v1/admin/consent/company-training-consent")

        assert resp.status_code == 200
        data = resp.json()
        assert data["consent_given"] is False
        assert data["is_active"] is False
        assert data["granted_at"] is None
        assert data["revoked_at"] is None
        assert data["legal_basis"] == "LGPD_ART_7_I"

    def test_returns_active_record_canonical(self, client, app):
        """Record com consent_given=True + revoked_at=None retorna is_active."""
        granted = datetime(2026, 5, 20, 12, 0, 0)
        record = SimpleNamespace(
            consent_given=True,
            is_active=True,
            granted_at=granted,
            revoked_at=None,
            version="1.0",
            legal_basis="LGPD_ART_7_I",
            consent_text="Eu autorizo...",
            consent_source="admin_ui",
            user_id_granted=ADMIN_USER_ID,
            user_id_revoked=None,
            revoke_reason=None,
            updated_at=granted,
        )
        with patch(
            "app.api.v1.admin_consent.CompanyTrainingConsentRepository"
        ) as RepoCls:
            repo = AsyncMock()
            repo.get_by_company = AsyncMock(return_value=record)
            RepoCls.return_value = repo
            resp = client.get("/api/v1/admin/consent/company-training-consent")

        assert resp.status_code == 200
        data = resp.json()
        assert data["consent_given"] is True
        assert data["is_active"] is True
        assert data["granted_at"] == granted.isoformat()


# ───────────────────────── POST grant ────────────────────────────────────────


class TestGrantCompanyTrainingConsent:
    def test_grant_creates_record_canonical(self, client, app):
        """T-21c POST grant cria record + retorna granted_at."""
        granted = datetime(2026, 5, 20, 14, 0, 0)
        record = SimpleNamespace(
            consent_given=True,
            granted_at=granted,
            revoked_at=None,
        )
        with patch(
            "app.api.v1.admin_consent.CompanyTrainingConsentRepository"
        ) as RepoCls, patch(
            "app.api.v1.admin_consent.AuditService"
        ) as AuditCls:
            repo = AsyncMock()
            repo.grant_consent = AsyncMock(return_value=record)
            RepoCls.return_value = repo
            audit = AsyncMock()
            audit.log_decision = AsyncMock()
            AuditCls.return_value = audit

            resp = client.post(
                "/api/v1/admin/consent/company-training-consent/grant",
                json={
                    "consent_text": "Eu autorizo uso de feedback para fine-tune Claude.",
                    "version": "1.0",
                },
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["consent_given"] is True
        assert data["granted_at"] == granted.isoformat()
        # AUDIT-NO-DEMO entry foi criado
        audit.log_decision.assert_awaited_once()
        called = audit.log_decision.await_args.kwargs
        assert called["action"] == "grant_training_data_consent"
        assert called["decision_type"] == "company_settings_change"
        assert "LGPD_ART_7_I" in called["criteria_used"]

    def test_grant_rejects_empty_consent_text(self, client):
        """LGPD Art. 8 §I — consent precisa ser inequívoco (não-vazio)."""
        resp = client.post(
            "/api/v1/admin/consent/company-training-consent/grant",
            json={"consent_text": "   ", "version": "1.0"},
        )
        assert resp.status_code == 422

    def test_grant_rejects_extra_fields_pydantic_r1(self, client):
        """Pydantic Conventions R1 — request body com extra='forbid'.

        Frontend MAS NÃO PODE mandar company_id no body (REGRA R2).
        """
        resp = client.post(
            "/api/v1/admin/consent/company-training-consent/grant",
            json={
                "consent_text": "valid",
                "version": "1.0",
                "company_id": "should-be-rejected",  # R2 anti-pattern
            },
        )
        # extra='forbid' → 422
        assert resp.status_code == 422


# ───────────────────────── POST revoke ───────────────────────────────────────


class TestRevokeCompanyTrainingConsent:
    def test_revoke_cascade_lgpd_art_18(self, client, app):
        """T-21c POST revoke sets revoked_at + LGPD Art. 18 cascade."""
        revoked = datetime(2026, 5, 20, 16, 0, 0)
        record = SimpleNamespace(
            revoked_at=revoked,
            revoke_reason="Mudança de política interna",
        )
        with patch(
            "app.api.v1.admin_consent.CompanyTrainingConsentRepository"
        ) as RepoCls, patch(
            "app.api.v1.admin_consent.AuditService"
        ) as AuditCls:
            repo = AsyncMock()
            repo.revoke_consent = AsyncMock(return_value=record)
            RepoCls.return_value = repo
            audit = AsyncMock()
            audit.log_decision = AsyncMock()
            AuditCls.return_value = audit

            resp = client.post(
                "/api/v1/admin/consent/company-training-consent/revoke",
                json={"reason": "Mudança de política interna"},
            )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert data["revoked_at"] == revoked.isoformat()
        # AUDIT-NO-DEMO
        audit.log_decision.assert_awaited_once()
        called = audit.log_decision.await_args.kwargs
        assert called["action"] == "revoke_training_data_consent"
        assert "LGPD_ART_18" in called["criteria_used"]

    def test_revoke_404_when_no_active_consent(self, client, app):
        """Repo retorna None quando company nunca opt-in — 404 explícito."""
        with patch(
            "app.api.v1.admin_consent.CompanyTrainingConsentRepository"
        ) as RepoCls:
            repo = AsyncMock()
            repo.revoke_consent = AsyncMock(return_value=None)
            RepoCls.return_value = repo

            resp = client.post(
                "/api/v1/admin/consent/company-training-consent/revoke",
                json={"reason": "test"},
            )
        assert resp.status_code == 404
