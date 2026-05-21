"""
Coverage tests for app/api/v1/ai_performance.py — Wave 2 Agent A (T-19 Fase 6).

Cobre os 6 endpoints canonical:
- GET  /api/v1/ai-performance/experiments
- GET  /api/v1/ai-performance/experiments/{name}/posteriors
- POST /api/v1/ai-performance/experiments/{name}/check-early-stop
- POST /api/v1/ai-performance/experiments/{name}/promote-winner
- GET  /api/v1/ai-performance/experiments/{name}/history
- GET  /api/v1/ai-performance/dashboard/summary

+ Multi-tenancy (cross-tenant denied via require_company_id absent)
+ Pydantic R1 forbid (extra fields → 422)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.ai_performance import router
from app.core.database import get_db
from app.shared.security.require_company_id import require_company_id


COMPANY_A = "11111111-1111-1111-1111-111111111111"
COMPANY_B = "22222222-2222-2222-2222-222222222222"


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.execute = AsyncMock()
    return db


def _build_app(company_id: str = COMPANY_A) -> FastAPI:
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    db_mock = _mock_db()
    application.dependency_overrides[get_db] = lambda: db_mock
    application.dependency_overrides[require_company_id] = lambda: company_id
    return application


# ---------------------------------------------------------------------------
# GET /experiments
# ---------------------------------------------------------------------------


def test_list_experiments_returns_active_with_winner_stats() -> None:
    app = _build_app()
    client = TestClient(app)

    with patch(
        "app.api.v1.ai_performance._service.list_active_tests",
        new=AsyncMock(return_value=[
            {
                "test_name": "wsi_v1_vs_v2",
                "variants": [
                    {"variant_name": "control", "traffic_percentage": 50.0, "is_active": True},
                    {"variant_name": "variant_b", "traffic_percentage": 50.0, "is_active": True},
                ],
                "created_at": "2026-05-01T00:00:00",
            }
        ]),
    ), patch(
        "app.api.v1.ai_performance._service.get_test_results",
        new=AsyncMock(return_value={
            "test_name": "wsi_v1_vs_v2",
            "winner": {"variant": "variant_b", "p_value": 0.003},
            "statistical_significance": {"variant_b": {"p_value": 0.003, "n_control": 200, "n_variant": 200}},
            "total_observations": 400,
            "recommendation": "promote_winner",
        }),
    ):
        resp = client.get("/api/v1/ai-performance/experiments")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "experiments" in body
    assert len(body["experiments"]) == 1
    exp = body["experiments"][0]
    assert exp["name"] == "wsi_v1_vs_v2"
    assert exp["current_winner"] == "variant_b"
    assert exp["p_value"] == 0.003
    assert exp["n_arms"] == 2  # 1 sig comparison + control
    assert exp["status"] == "active"


# ---------------------------------------------------------------------------
# GET /experiments/{name}/posteriors
# ---------------------------------------------------------------------------


def test_get_posteriors_returns_alpha_beta_expected() -> None:
    app = _build_app()
    client = TestClient(app)

    posterior_row = MagicMock(arm="control", alpha=4.0, beta=2.0, n_observations=4)
    posterior_row_b = MagicMock(arm="variant_b", alpha=6.0, beta=2.0, n_observations=6)

    with patch(
        "app.shared.intelligence.ab_testing.bandit_posterior_repository.BanditPosteriorRepository.get_all_for_test",
        new=AsyncMock(side_effect=[[posterior_row, posterior_row_b], []]),
    ):
        resp = client.get("/api/v1/ai-performance/experiments/wsi_v1_vs_v2/posteriors")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["test_name"] == "wsi_v1_vs_v2"
    arms = {p["arm"]: p for p in body["posteriors"]}
    assert "control" in arms
    assert arms["control"]["alpha"] == 4.0
    assert arms["control"]["beta"] == 2.0
    # expected = α / (α+β) = 4/6 ≈ 0.6667
    assert abs(arms["control"]["expected_value"] - 0.666667) < 1e-4
    assert arms["variant_b"]["n_observations"] == 6


# ---------------------------------------------------------------------------
# POST /experiments/{name}/check-early-stop
# ---------------------------------------------------------------------------


def test_check_early_stop_continues() -> None:
    app = _build_app()
    client = TestClient(app)

    with patch(
        "app.api.v1.ai_performance._service.check_early_stop",
        new=AsyncMock(return_value={
            "action": "continue",
            "winner": None,
            "p_value": 0.04,
            "alpha_per_look": 0.001,
            "look_number": 3,
            "max_looks": 10,
            "reason": "continue: p=0.04000 not yet < α_per_look=0.00100 OR n=80 < 100 per variant",
        }),
    ):
        resp = client.post(
            "/api/v1/ai-performance/experiments/wsi_v1_vs_v2/check-early-stop",
            json={"look_number": 3, "max_looks": 10},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["action"] == "continue"
    assert body["look_number"] == 3


def test_check_early_stop_invalid_look_number_returns_400() -> None:
    app = _build_app()
    client = TestClient(app)

    with patch(
        "app.api.v1.ai_performance._service.check_early_stop",
        new=AsyncMock(side_effect=ValueError("look_number must be >= 1 (got 0)")),
    ):
        resp = client.post(
            "/api/v1/ai-performance/experiments/wsi_v1_vs_v2/check-early-stop",
            json={"look_number": 0, "max_looks": 10},
        )

    assert resp.status_code == 400
    assert "look_number" in resp.json().get("detail", "")


# ---------------------------------------------------------------------------
# POST /experiments/{name}/promote-winner
# ---------------------------------------------------------------------------


def test_promote_winner_frequentist_canonical() -> None:
    app = _build_app()
    client = TestClient(app)

    with patch(
        "app.api.v1.ai_performance._service.auto_promote_winner",
        new=AsyncMock(return_value={
            "promoted": True,
            "winner": "variant_b",
            "reason": "auto_promoted",
            "gate_used": "frequentist",
            "n_arms": 2,
            "alpha_adjusted": 0.01,
        }),
    ):
        resp = client.post(
            "/api/v1/ai-performance/experiments/wsi_v1_vs_v2/promote-winner",
            json={"use_thompson_sampling": False},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["promoted"] is True
    assert body["winner"] == "variant_b"
    assert body["gate_used"] == "frequentist"


def test_promote_winner_blocked_by_fairness_gate() -> None:
    """T-19 Fase 1 FairnessGate L3 canonical: bloqueia winner com viés."""
    app = _build_app()
    client = TestClient(app)

    with patch(
        "app.api.v1.ai_performance._service.auto_promote_winner",
        new=AsyncMock(return_value={
            "promoted": False,
            "winner": "variant_b",
            "reason": "fairness_gate_blocked: protected_class_term_detected",
            "fairness_violation": True,
        }),
    ):
        resp = client.post(
            "/api/v1/ai-performance/experiments/wsi_v1_vs_v2/promote-winner",
            json={"use_thompson_sampling": True, "thompson_threshold": 0.95},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["promoted"] is False
    assert body.get("fairness_violation") is True


# ---------------------------------------------------------------------------
# GET /experiments/{name}/history
# ---------------------------------------------------------------------------


def test_history_returns_winner_snapshot_and_significance() -> None:
    app = _build_app()
    client = TestClient(app)

    with patch(
        "app.api.v1.ai_performance._service.get_test_results",
        new=AsyncMock(return_value={
            "test_name": "wsi_v1_vs_v2",
            "winner": {"variant": "variant_b", "p_value": 0.002, "metric": "satisfaction"},
            "statistical_significance": {
                "variant_b": {"p_value": 0.002, "n_control": 150, "n_variant": 150, "mean_diff": 0.12},
            },
            "variants": {"control": {"metrics": {}}, "variant_b": {"metrics": {}}},
            "recommendation": "promote_winner",
            "total_observations": 300,
            "n_min": 100,
        }),
    ):
        resp = client.get("/api/v1/ai-performance/experiments/wsi_v1_vs_v2/history")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["test_name"] == "wsi_v1_vs_v2"
    assert body["winner"]["variant"] == "variant_b"
    history_kinds = [entry["kind"] for entry in body["history"]]
    assert "current_winner_snapshot" in history_kinds
    assert "significance_comparison" in history_kinds


# ---------------------------------------------------------------------------
# GET /dashboard/summary
# ---------------------------------------------------------------------------


def test_dashboard_summary_aggregates_kpis() -> None:
    app = _build_app()
    client = TestClient(app)

    with patch(
        "app.api.v1.ai_performance._service.list_active_tests",
        new=AsyncMock(return_value=[
            {"test_name": "wsi_v1_vs_v2", "variants": [{"variant_name": "control"}, {"variant_name": "v2"}]},
            {"test_name": "email_subject_a_vs_b", "variants": [{"variant_name": "control"}, {"variant_name": "b"}]},
        ]),
    ), patch(
        "app.api.v1.ai_performance._service.get_test_results",
        new=AsyncMock(side_effect=[
            {
                "winner": {"variant": "v2", "p_value": 0.003},
                "statistical_significance": {"v2": {}},
                "total_observations": 400,
            },
            {
                "winner": {"variant": "b", "p_value": 0.06},  # not significant
                "statistical_significance": {"b": {}},
                "total_observations": 200,
            },
        ]),
    ):
        resp = client.get("/api/v1/ai-performance/dashboard/summary")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    summary = body["summary"]
    assert summary["active_count"] == 2
    assert summary["promoted_ready"] == 1  # only wsi (p<0.01)
    assert summary["pending_fairness_gate"] == 1  # email (p=0.06 fails Bonferroni)
    assert summary["total_observations"] == 600


# ---------------------------------------------------------------------------
# Multi-tenancy + Pydantic conventions
# ---------------------------------------------------------------------------


def test_endpoints_require_company_id_dependency() -> None:
    """Sem dependency override de require_company_id → endpoint 401/403."""
    application = FastAPI()
    application.include_router(router, prefix="/api/v1")
    db_mock = _mock_db()
    application.dependency_overrides[get_db] = lambda: db_mock
    # Intencionalmente NÃO sobrescreve require_company_id

    client = TestClient(application)
    resp = client.get("/api/v1/ai-performance/experiments")
    # require_company_id retorna 401/403 quando JWT ausente em test client
    assert resp.status_code in (401, 403, 422)


def test_promote_winner_rejects_extra_field_pydantic_forbid() -> None:
    """Pydantic R1: WeDoBaseModel extra='forbid' canonical."""
    app = _build_app()
    client = TestClient(app)

    resp = client.post(
        "/api/v1/ai-performance/experiments/wsi_v1_vs_v2/promote-winner",
        json={"use_thompson_sampling": True, "company_id": "spoofed-tenant"},  # extra field
    )
    assert resp.status_code == 422
    detail = resp.json().get("detail", "")
    assert "extra" in str(detail).lower() or "forbid" in str(detail).lower()


def test_check_early_stop_rejects_extra_field_pydantic_forbid() -> None:
    """Pydantic R1: WeDoBaseModel extra='forbid' canonical."""
    app = _build_app()
    client = TestClient(app)

    resp = client.post(
        "/api/v1/ai-performance/experiments/wsi_v1_vs_v2/check-early-stop",
        json={"look_number": 1, "evil_field": "spoofed"},
    )
    assert resp.status_code == 422
