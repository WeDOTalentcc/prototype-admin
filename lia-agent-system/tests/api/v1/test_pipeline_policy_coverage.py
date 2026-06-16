"""
Coverage tests for app/api/v1/pipeline_policy.py — Task #930.

Cobre:
- happy: GET /pipeline-policy/{company_id}/templates devolve system_templates.
- erro: GET /pipeline-policy/{company_id}/validate-transition para offer com poucas
        entrevistas devolve warning (mas allowed=True, pois é warning e não blocker).
- isolamento: company_id é repassado a get_policy_for_company; tenants distintos
        recebem políticas distintas.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.pipeline_policy import router
from app.core.database import get_db


COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    application.dependency_overrides[get_db] = lambda: MagicMock()
    return application


class TestPipelinePolicyTemplates:
    def test_happy_returns_system_and_company_templates(self, app: FastAPI):
        with patch(
            "app.api.v1.pipeline_policy.get_policy_for_company",
            new=AsyncMock(return_value={
                "id": "policy-A",
                "pipeline_templates": [{"id": "custom", "name": "Custom"}],
                "pipeline_rules": {},
            }),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get(f"/api/v1/pipeline-policy/{COMPANY_A}/templates")
        assert r.status_code == 200
        body = r.json()
        # System defaults always present
        ids = {t["id"] for t in body["system_templates"]}
        assert {"standard", "technical", "operational", "executive"} <= ids
        assert body["company_templates"] == [{"id": "custom", "name": "Custom"}]
        assert body["policy_applied"] is True


class TestPipelinePolicyValidateTransition:
    def test_offer_with_few_interviews_emits_warning(self, app: FastAPI):
        # mock get_policy_for_company to require min 2 interviews
        # mock db.execute to count 0 interviews → triggers warning
        async def _exec(*a, **k):
            res = MagicMock()
            res.scalar = MagicMock(return_value=0)
            return res

        db_mock = MagicMock()
        db_mock.execute = _exec
        app.dependency_overrides[get_db] = lambda: db_mock

        with patch(
            "app.api.v1.pipeline_policy.get_policy_for_company",
            new=AsyncMock(return_value={
                "id": "policy-A",
                "pipeline_rules": {
                    "min_interviews_before_offer": 2,
                    "manager_approval_for_offer": True,
                },
            }),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.get(
                f"/api/v1/pipeline-policy/{COMPANY_A}/validate-transition",
                params={"candidate_id": "cand-1", "target_stage": "proposta"},
            )
        assert r.status_code == 200
        body = r.json()
        # warning is emitted because 0 < 2 interviews; manager_approval also emits warning
        assert body["allowed"] is True  # no blockers, only warnings
        assert any("entrevistas" in w.lower() for w in body["warnings"])
        assert any("aprovação do gestor" in w.lower() for w in body["warnings"])
        assert body["metadata"]["interview_count"] == 0
        assert body["metadata"]["min_interviews_required"] == 2


class TestPipelinePolicyIsolation:
    def test_get_policy_for_company_called_with_provided_company_id(self, app: FastAPI):
        captured: list[str] = []

        async def _spy(company_id, db):
            captured.append(company_id)
            return {"id": company_id, "pipeline_templates": [], "pipeline_rules": {}}

        with patch(
            "app.api.v1.pipeline_policy.get_policy_for_company",
            new=_spy,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r1 = client.get(f"/api/v1/pipeline-policy/{COMPANY_A}/templates")
            r2 = client.get(f"/api/v1/pipeline-policy/{COMPANY_B}/templates")

        assert r1.status_code == 200
        assert r2.status_code == 200
        # Each request resolved its own company's policy — no shared state
        assert captured == [COMPANY_A, COMPANY_B]
        assert r1.json()["company_templates"] == []
        assert r2.json()["company_templates"] == []
