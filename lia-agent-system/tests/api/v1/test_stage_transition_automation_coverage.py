"""
Coverage tests for app/api/v1/stage_transition_automation.py — Task #930.

Cobre os endpoints exercidos pelo menu Configurações (subset funcional):
- POST /predict-substatus              (happy + 500 quando service falha)
- GET  /substatus-options/{stage}      (rejected, offer_declined, default)
- POST /bulk-predict-substatus         (happy + isolamento por candidato no fallback)
- POST /bulk-predict-substatus-from-db (sem db retorna fallback per-id)

Endpoints adicionais do router (POST /generate-message, POST /regenerate-for-substatus,
POST /get-actions, POST /bulk-generate-messages) NÃO são alvo desta task — são consumidos
por fluxos fora do menu Configurações (workflow de transição em runtime, não setup).

Endpoints não exigem autenticação na implementação atual; testes focam
em comportamento funcional (happy/erro) + isolamento por candidato/stage.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.stage_transition_automation import get_db_session, router


CAND_A = "cand-a-1"
CAND_B = "cand-b-2"


@pytest.fixture
def app() -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1/automation")
    return application


def _candidate_payload(cid: str = CAND_A) -> dict:
    return {
        "id": cid,
        "name": f"Cand {cid}",
        "email": f"{cid}@test.example",
        "wsi_score": {"overall": 7.5, "technical": 8.0},
        "interview_notes": [],
    }


# ----------------- /predict-substatus -----------------

class TestPredictSubstatus:
    def test_happy_returns_predicted_substatus(self, app: FastAPI):
        with patch(
            "app.api.v1.stage_transition_automation.stage_transition_service.predict_substatus",
            new=AsyncMock(return_value={
                "predicted_substatus": "needs_more_experience",
                "confidence": 0.87,
                "reasoning": "Below seniority bar",
                "alternatives": [],
            }),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post(
                "/api/v1/automation/predict-substatus",
                json={
                    "candidate_context": _candidate_payload(),
                    "from_stage": "interview",
                    "to_stage": "rejected",
                },
            )
        assert r.status_code == 200
        body = r.json()
        assert body["predicted_substatus"] == "needs_more_experience"
        assert body["confidence"] == 0.87

    def test_service_exception_returns_500(self, app: FastAPI):
        with patch(
            "app.api.v1.stage_transition_automation.stage_transition_service.predict_substatus",
            new=AsyncMock(side_effect=RuntimeError("LLM down")),
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post(
                "/api/v1/automation/predict-substatus",
                json={
                    "candidate_context": _candidate_payload(),
                    "from_stage": "interview",
                    "to_stage": "rejected",
                },
            )
        assert r.status_code == 500


# ----------------- /substatus-options/{stage} -----------------

class TestSubstatusOptions:
    """Task #936 — endurecidos após a correção do bug de import.
    O endpoint agora resolve OFFER_DECLINE_REASONS / REJECTION_REASONS /
    SUB_STATUSES a partir de lia_models.recruitment_stages e responde 200
    para qualquer stage (motivos conhecidos viram lista populada,
    desconhecidos viram lista vazia)."""

    def test_rejected_returns_options(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/automation/substatus-options/rejected")
        assert r.status_code == 200
        body = r.json()
        assert body["stage"] == "rejected"
        options = body["options"]
        assert isinstance(options, list) and len(options) > 0
        first = options[0]
        assert {"code", "display_name", "category"}.issubset(first.keys())

    def test_offer_declined_returns_options(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/automation/substatus-options/offer_declined")
        assert r.status_code == 200
        body = r.json()
        assert body["stage"] == "offer_declined"
        options = body["options"]
        assert isinstance(options, list) and len(options) > 0
        first = options[0]
        assert {"code", "display_name"}.issubset(first.keys())

    def test_unknown_stage_returns_empty_options(self, app: FastAPI):
        client = TestClient(app, raise_server_exceptions=False)
        r = client.get("/api/v1/automation/substatus-options/__unknown_stage__")
        assert r.status_code == 200
        assert r.json()["options"] == []


# ----------------- /bulk-predict-substatus -----------------

class TestBulkPredictSubstatus:
    def test_per_candidate_predictions_returned(self, app: FastAPI, monkeypatch):
        monkeypatch.setenv("ENABLE_LLM_SUBSTATUS_PREDICTION", "true")

        async def _fake_predict(candidate_context, from_stage, to_stage):
            cid = candidate_context["id"]
            return {
                "predicted_substatus": f"sub_{cid}",
                "confidence": 0.5,
                "reasoning": f"reason for {cid}",
            }

        with patch(
            "app.api.v1.stage_transition_automation.stage_transition_service.predict_substatus",
            new=_fake_predict,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post(
                "/api/v1/automation/bulk-predict-substatus",
                json={
                    "candidates": [_candidate_payload(CAND_A), _candidate_payload(CAND_B)],
                    "from_stage": "interview",
                    "to_stage": "rejected",
                },
            )
        assert r.status_code == 200
        preds = r.json()["predictions"]
        # Each candidate's prediction is isolated — not mixed with the other's.
        assert {p["candidate_id"] for p in preds} == {CAND_A, CAND_B}
        assert {p["predicted_substatus"] for p in preds} == {f"sub_{CAND_A}", f"sub_{CAND_B}"}

    def test_per_candidate_failure_falls_back_per_candidate(self, app: FastAPI, monkeypatch):
        monkeypatch.setenv("ENABLE_LLM_SUBSTATUS_PREDICTION", "true")

        async def _fake_predict(candidate_context, from_stage, to_stage):
            if candidate_context["id"] == CAND_A:
                raise RuntimeError("downstream failure")
            return {
                "predicted_substatus": "ok_substatus",
                "confidence": 0.9,
                "reasoning": "fine",
            }

        with patch(
            "app.api.v1.stage_transition_automation.stage_transition_service.predict_substatus",
            new=_fake_predict,
        ):
            client = TestClient(app, raise_server_exceptions=False)
            r = client.post(
                "/api/v1/automation/bulk-predict-substatus",
                json={
                    "candidates": [_candidate_payload(CAND_A), _candidate_payload(CAND_B)],
                    "from_stage": "interview",
                    "to_stage": "rejected",
                },
            )
        assert r.status_code == 200
        preds = {p["candidate_id"]: p for p in r.json()["predictions"]}
        # Failure on A → fallback. Success on B → ok. Each isolated.
        assert preds[CAND_A]["predicted_substatus"] == "profile_not_aligned"
        assert preds[CAND_A]["confidence"] == 0.0
        assert preds[CAND_B]["predicted_substatus"] == "ok_substatus"


# ----------------- /bulk-predict-substatus-from-db -----------------

class TestBulkPredictFromDb:
    def test_no_db_returns_fallback_per_id(self, app: FastAPI):
        # Override get_db_session to yield None — simulating db unavailable.
        async def _no_db():
            yield None

        app.dependency_overrides[get_db_session] = _no_db
        client = TestClient(app, raise_server_exceptions=False)
        r = client.post(
            "/api/v1/automation/bulk-predict-substatus-from-db",
            json={
                "vacancy_candidate_ids": ["vc-1", "vc-2", "vc-3"],
                "from_stage": "interview",
                "to_stage": "rejected",
            },
        )
        assert r.status_code == 200
        body = r.json()
        assert body["data_source"] == "fallback"
        assert {p["vacancy_candidate_id"] for p in body["predictions"]} == {"vc-1", "vc-2", "vc-3"}
        assert all(p["predicted_substatus"] == "profile_not_aligned" for p in body["predictions"])
