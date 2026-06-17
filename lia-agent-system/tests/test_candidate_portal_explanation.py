"""Tests: /api/v1/candidate/decisions/explain — EU AI Act Art. 86 + LGPD Art. 20.

Valida:
  - Token válido → 200 com payload sanitizado
  - Token inválido → 401
  - Rate limit excedido → 429
  - Nenhum campo proibido no response (wsi_score, lia_score, confidence, weights)
  - Anti-IDOR: company_id sempre derivado do token
  - Art. 86 notice presente em toda resposta
"""
import os
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


# Fixture: TestClient deve ser construído no conftest ou setup do projeto.
# Aqui assumimos que o `app` (FastAPI) é importável e o endpoint já registrado.


FORBIDDEN_FIELDS = {
    "wsi_score", "lia_score", "wsi_final_score", "match_percentage",
    "red_flags", "confidence", "score", "factors_weights",
    "calibration_weights_used", "calibration_weights",
    "recruiter_notes", "rejection_code",
}


def _assert_no_forbidden_fields(obj) -> None:
    """Recursively assert no forbidden field appears in the response body."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            assert key not in FORBIDDEN_FIELDS, (
                f"Forbidden field '{key}' exposed to candidate: {value}"
            )
            _assert_no_forbidden_fields(value)
    elif isinstance(obj, list):
        for item in obj:
            _assert_no_forbidden_fields(item)


@pytest.fixture
def valid_token_payload():
    return {
        "candidate_id": "cand_123",
        "vacancy_id": "vac_456",
        "company_id": "comp_789",
    }


@pytest.fixture
def mock_audit_logs():
    """Simulate AuditLog rows with ALL fields — endpoint should sanitize."""
    from datetime import UTC, datetime

    class FakeLog:
        def __init__(self, decision_type, with_fairness_flags=False):
            self.decision_type = decision_type
            self.created_at = datetime.now(UTC)
            self.criteria_used = ["Python experience", "5+ years backend"]
            self.criteria_ignored = [
                "Idade", "Gênero", "Etnia/raça", "Estado civil",
            ]
            self.reasoning = ["High match on technical skills"]
            self.fairness_flags = ["implicit_age_bias"] if with_fairness_flags else []
            self.human_reviewed_at = None
            # Forbidden fields that MUST NOT leak:
            self.score = 87.5
            self.confidence = 0.92
            self.wsi_score = 85

    return [
        FakeLog("cv_screening"),
        FakeLog("pipeline_transition", with_fairness_flags=True),
    ]


class TestCandidatePortalExplanation:
    """Contract tests for /api/v1/candidate/decisions/explain."""

    def test_invalid_token_returns_401(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get(
            "/api/v1/candidate/decisions/explain",
            params={"candidate_token": "invalid.jwt.token"},
        )
        assert response.status_code == 401

    @patch(
        "app.domains.candidate_self_service.services.candidate_status_service.CandidateStatusService.validate_token",
        new_callable=AsyncMock,
    )
    @patch(
        "app.domains.candidate_self_service.services.candidate_status_service.CandidateStatusService.check_rate_limit",
        new_callable=AsyncMock,
    )
    def test_rate_limit_exceeded_returns_429(
        self, mock_rate, mock_validate, valid_token_payload
    ):
        from fastapi.testclient import TestClient
        from app.main import app

        mock_validate.return_value = valid_token_payload
        mock_rate.return_value = {"allowed": False, "remaining_hour": 0, "remaining_day": 0}

        client = TestClient(app)
        response = client.get(
            "/api/v1/candidate/decisions/explain",
            params={"candidate_token": "valid.jwt"},
        )
        assert response.status_code == 429

    @patch(
        "app.domains.candidate_self_service.tools.explain_candidate_decision._explain_candidate_decision",
        new_callable=AsyncMock,
    )
    @patch(
        "app.domains.candidate_self_service.services.candidate_status_service.CandidateStatusService.check_rate_limit",
        new_callable=AsyncMock,
    )
    @patch(
        "app.domains.candidate_self_service.services.candidate_status_service.CandidateStatusService.validate_token",
        new_callable=AsyncMock,
    )
    def test_valid_request_returns_sanitized_response(
        self, mock_validate, mock_rate, mock_tool, valid_token_payload
    ):
        from fastapi.testclient import TestClient
        from app.main import app

        mock_validate.return_value = valid_token_payload
        mock_rate.return_value = {"allowed": True, "remaining_hour": 9, "remaining_day": 29}
        mock_tool.return_value = {
            "success": True,
            "data": {
                "decisions": [
                    {
                        "decision_type": "cv_screening",
                        "timestamp": "2026-04-23T10:00:00+00:00",
                        "criteria_evaluated": ["Python experience"],
                        "criteria_ignored": ["Idade", "Gênero"],
                        "reasoning_summary": "Análise baseada em 1 critério(s) objetivo(s).",
                        "fairness_check": "passed",
                        "human_reviewed": False,
                    }
                ],
                "transparency_note": "Critérios ignorados: Idade, Gênero, ...",
                "art_86_notice": "De acordo com o EU AI Act (Art. 86)...",
                "total_decisions": 1,
            },
        }

        client = TestClient(app)
        response = client.get(
            "/api/v1/candidate/decisions/explain",
            params={"candidate_token": "valid.jwt", "vacancy_id": "vac_456"},
        )
        assert response.status_code == 200
        body = response.json()

        # Anti-IDOR: company_id never echoed in response
        assert "company_id" not in str(body)

        # No forbidden fields anywhere
        _assert_no_forbidden_fields(body)

        # Art. 86 notice present
        assert "Art. 86" in str(body) or "art_86_notice" in str(body)

    def test_sanitize_function_removes_forbidden_fields(self):
        from app.domains.candidate_self_service.tools.explain_candidate_decision import (
            _sanitize_decision,
        )
        from datetime import UTC, datetime

        raw = {
            "decision_type": "cv_screening",
            "created_at": datetime.now(UTC),
            "criteria_used": ["Python"],
            "criteria_ignored": ["Idade"],
            "reasoning": ["Good fit"],
            "fairness_flags": [],
            "human_reviewed_at": None,
            # Forbidden:
            "wsi_score": 87,
            "confidence": 0.9,
            "score": 85,
            "lia_score": 82,
        }
        out = _sanitize_decision(raw)

        for forbidden in FORBIDDEN_FIELDS:
            assert forbidden not in out, f"Forbidden '{forbidden}' leaked: {out}"

        assert out["criteria_evaluated"] == ["Python"]
        assert out["criteria_ignored"] == ["Idade"]
        assert out["fairness_check"] == "passed"
