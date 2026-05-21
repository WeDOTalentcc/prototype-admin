"""
Coverage tests for app/api/v1/ai_transparency.py — Wave 1 Agent #1.

Cobre os 4 endpoints T-18 EU AI Act:
- GET  /api/v1/ai-transparency/explainability-statement
- GET  /api/v1/ai-transparency/automated-decisions
- POST /api/v1/ai-transparency/human-oversight/{decision_id}/override
- GET  /api/v1/ai-transparency/technical-documentation
"""
from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.ai_transparency import router
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id
from app.shared.tenant_guard import get_verified_company_id


COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"
DECISION_ID = "33333333-3333-3333-3333-333333333333"
CANDIDATE_ID = "44444444-4444-4444-4444-444444444444"
VACANCY_ID = "55555555-5555-5555-5555-555555555555"
REVIEWER_ID = "66666666-6666-6666-6666-666666666666"


def _user(company_id: str) -> MagicMock:
    u = MagicMock()
    u.id = uuid4()
    u.company_id = company_id
    u.is_active = True
    return u


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    db_mock = MagicMock()
    application.dependency_overrides[get_db] = lambda: db_mock
    application.dependency_overrides[get_current_user] = lambda: _user(COMPANY_A)
    application.dependency_overrides[require_company_id] = lambda: COMPANY_A
    application.dependency_overrides[get_verified_company_id] = lambda: COMPANY_A
    return application


# ───────────────────────── /explainability-statement ────────────────────────


class TestExplainabilityStatement:
    def test_returns_canonical_structure(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/ai-transparency/explainability-statement")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "sections" in body
        assert "last_updated" in body
        assert "version" in body
        assert "lawful_basis" in body
        assert body["annex_iii_category"] == "annex_iii_item_4_employment"
        assert body["company_id"] == COMPANY_A
        # Each section has title + content + examples
        assert len(body["sections"]) >= 4
        for section in body["sections"]:
            assert "title" in section
            assert "content" in section
            assert "examples" in section

    def test_protected_criteria_section_present(self, app: FastAPI):
        """REGRA: deve listar critérios protegidos explicitamente."""
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/ai-transparency/explainability-statement")
        assert r.status_code == 200
        body = r.json()
        titles = [s["title"] for s in body["sections"]]
        assert any("protegidos" in t.lower() or "não considera" in t.lower() for t in titles)


# ───────────────────────── /automated-decisions ─────────────────────────────


class TestAutomatedDecisions:
    def test_filters_by_candidate_id(self, app: FastAPI):
        # Mock the DB call to return empty result
        mock_db = MagicMock()
        count_result = MagicMock()
        count_result.scalar = MagicMock(return_value=0)
        list_result = MagicMock()
        list_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))

        mock_db.execute = AsyncMock(side_effect=[count_result, list_result])
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app, raise_server_exceptions=False)
        r = client.get(
            "/api/v1/ai-transparency/automated-decisions",
            params={"candidate_id": CANDIDATE_ID, "limit": 25, "offset": 0},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["decisions"] == []
        assert body["total"] == 0
        assert body["limit"] == 25
        assert body["offset"] == 0

    def test_invalid_candidate_id_returns_400(self, app: FastAPI):
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get(
            "/api/v1/ai-transparency/automated-decisions",
            params={"candidate_id": "not-a-uuid"},
        )
        assert r.status_code == 400


# ───────────────────────── /human-oversight override ────────────────────────


class TestHumanOversightOverride:
    def test_override_records_audit_entry(self, app: FastAPI):
        """REGRA: override deve criar audit_log canonical entry."""
        # Mock the decision row
        decision_row = MagicMock()
        decision_row.id = UUID(DECISION_ID)
        decision_row.company_id = UUID(COMPANY_A)
        decision_row.decision_type = "screening"
        decision_row.candidate_id = UUID(CANDIDATE_ID)
        decision_row.vacancy_id = UUID(VACANCY_ID)
        decision_row.ai_model_used = "claude-opus-4-7"
        decision_row.human_review_requested = False
        decision_row.human_review_completed_at = None

        mock_db = MagicMock()
        get_result = MagicMock()
        get_result.scalar_one_or_none = MagicMock(return_value=decision_row)
        mock_db.execute = AsyncMock(return_value=get_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        audit_mock = MagicMock()
        audit_mock.id = uuid4()

        with patch(
            "app.shared.compliance.audit_service.audit_service.log_decision",
            new=AsyncMock(return_value=audit_mock),
        ) as log_dec:
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post(
                f"/api/v1/ai-transparency/human-oversight/{DECISION_ID}/override",
                json={
                    "override_reason": "Avaliação humana mostra fit melhor que score IA",
                    "new_decision": "approved",
                    "reviewer_user_id": REVIEWER_ID,
                },
            )

        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert body["decision_id"] == DECISION_ID
        assert body["new_decision"] == "approved"
        assert body["audit_entry_id"] is not None
        log_dec.assert_called_once()

    def test_404_when_decision_not_in_tenant(self, app: FastAPI):
        mock_db = MagicMock()
        get_result = MagicMock()
        get_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=get_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            f"/api/v1/ai-transparency/human-oversight/{DECISION_ID}/override",
            json={
                "override_reason": "Razão de teste suficientemente longa",
                "new_decision": "rejected",
                "reviewer_user_id": REVIEWER_ID,
            },
        )
        assert r.status_code == 404

    def test_422_on_short_override_reason(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            f"/api/v1/ai-transparency/human-oversight/{DECISION_ID}/override",
            json={
                "override_reason": "curto",  # < 10 chars
                "new_decision": "approved",
                "reviewer_user_id": REVIEWER_ID,
            },
        )
        assert r.status_code == 422


# ───────────────────────── /technical-documentation ─────────────────────────


class TestTechnicalDocumentation:
    def test_returns_model_card_with_annex_iii_metadata(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/ai-transparency/technical-documentation")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "model_card" in body
        assert "training_data_summary" in body
        assert "intended_use" in body
        assert "limitations" in body
        assert "fairness_results" in body
        assert body["annex_iii_category"] == "annex_iii_item_4_employment"
        # ModelCard sections
        assert len(body["model_card"]) >= 5
        section_names = [s["name"] for s in body["model_card"]]
        assert "Model details" in section_names
        assert "Intended use" in section_names
        assert "Performance metrics" in section_names
        assert "Ethical considerations" in section_names
        assert "Caveats and limitations" in section_names

    def test_intended_use_contains_recruitment_scope(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/ai-transparency/technical-documentation")
        assert r.status_code == 200
        body = r.json()
        assert any("triagem" in u.lower() for u in body["intended_use"])

    def test_limitations_mention_lgpd_protected_attributes(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/ai-transparency/technical-documentation")
        body = r.json()
        text = " ".join(body["limitations"]).lower()
        assert "lgpd" in text or "protegidos" in text or "protected" in text
