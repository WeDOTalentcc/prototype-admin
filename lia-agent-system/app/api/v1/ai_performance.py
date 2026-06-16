"""
AI Performance endpoints — T-19 Fase 6 dashboard canonical (Wave 2 Agent A).

Endpoints superficiais (sem lógica nova): consumem services canonical já existentes
(`ab_testing_service` + `BanditPosteriorRepository`) e expõem para o frontend
`AIPerformancePanel` em Governança.

Cobre:
- T-19 Fase 1 (FairnessGate) — exposto via promote-winner
- T-19 Fase 2 (BanditPosterior table) — exposto via /posteriors
- T-19 Fase 3 (Thompson integration) — exposto via promote-winner (use_thompson_sampling)
- T-19 Fase 4 (Bonferroni multi-arm) — exposto via promote-winner gate
- T-19 Fase 5 (Sequential testing / Pocock) — exposto via /check-early-stop

ADR-AB-001 + ADR-031-v3.

# AUDIT-NO-DEMO: T-19 dashboard governance (decisões sobre prompts/variants,
# não candidate decisions).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.learning.ab_testing_service import ab_testing_service as _service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-performance", tags=["ai-performance"])


# ---------------------------------------------------------------------------
# Request bodies (Pydantic R1 extra='forbid' via WeDoBaseModel; R2 no company_id)
# ---------------------------------------------------------------------------


class CheckEarlyStopBody(WeDoBaseModel):
    """Request body T-19 Fase 5 sequential testing (Pocock alpha-spending)."""

    look_number: int
    max_looks: int = 10
    alpha_total: float = 0.01
    futility_threshold: float = 0.001


class PromoteWinnerBody(WeDoBaseModel):
    """Request body T-19 Fase 3+4 promote winner com Bonferroni + FairnessGate."""

    use_thompson_sampling: bool = False
    thompson_threshold: float = 0.95


# ---------------------------------------------------------------------------
# GET /experiments — list active experiments
# ---------------------------------------------------------------------------


@router.get("/experiments", response_model=None)
async def list_experiments(
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    """Lista experiments ativos com snapshot de winner stats canonical."""
    active = await _service.list_active_tests(db, company_id=company_id)
    experiments: list[dict[str, Any]] = []

    for entry in active:
        test_name = entry.get("test_name")
        if not test_name:
            continue
        try:
            results = await _service.get_test_results(test_name, db)
        except Exception as exc:  # noqa: BLE001 — fail-soft per experiment
            logger.warning(
                "[ai-performance] get_test_results failed test=%s: %s",
                test_name, str(exc)[:200],
            )
            results = {}

        winner_info = results.get("winner") if isinstance(results, dict) else None
        sig = results.get("statistical_significance") if isinstance(results, dict) else None
        n_arms = (len(sig) + 1) if isinstance(sig, dict) else len(entry.get("variants", []))
        total_obs = results.get("total_observations") if isinstance(results, dict) else None

        experiments.append({
            "name": test_name,
            "variants": entry.get("variants", []),
            "current_winner": (winner_info or {}).get("variant"),
            "p_value": (winner_info or {}).get("p_value"),
            "n_arms": n_arms,
            "status": "active",
            "total_observations": total_obs,
            "created_at": entry.get("created_at"),
            "recommendation": results.get("recommendation") if isinstance(results, dict) else None,
        })

    return {"experiments": experiments}


# ---------------------------------------------------------------------------
# GET /experiments/{name}/posteriors — Thompson sampler posteriors
# ---------------------------------------------------------------------------


@router.get("/experiments/{test_name}/posteriors", response_model=None)
async def get_posteriors(
    test_name: str,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    """T-19 Fase 2: posteriors Bayesianos (α/β/expected/n_obs) por arm."""
    from app.shared.intelligence.ab_testing.bandit_posterior_repository import (
        BanditPosteriorRepository,
    )

    repo = BanditPosteriorRepository(db)
    # WT-2022 P1.4: SEM fallback global — se tenant nao tem posteriors retorna [].
    # Fallback global vazava posteriors de outros tenants (cross-tenant read).
    posteriors = await repo.get_all_for_test(test_name, company_id=company_id)

    payload: list[dict[str, Any]] = []
    for p in posteriors:
        alpha = float(getattr(p, "alpha", 1.0))
        beta = float(getattr(p, "beta", 1.0))
        total = alpha + beta
        expected = (alpha / total) if total > 0 else 0.5
        payload.append({
            "arm": getattr(p, "arm", None),
            "alpha": alpha,
            "beta": beta,
            "expected_value": round(expected, 6),
            "n_observations": int(getattr(p, "n_observations", 0) or 0),
        })

    return {"test_name": test_name, "posteriors": payload}


# ---------------------------------------------------------------------------
# POST /experiments/{name}/check-early-stop — T-19 Fase 5 Pocock sequential
# ---------------------------------------------------------------------------


@router.post("/experiments/{test_name}/check-early-stop", response_model=None)
async def check_early_stop(
    test_name: str,
    body: CheckEarlyStopBody,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    """T-19 Fase 5 canonical: sequential testing early stopping (Pocock alpha-spending)."""
    try:
        decision = await _service.check_early_stop(
            test_name,
            db,
            look_number=body.look_number,
            max_looks=body.max_looks,
            alpha_total=body.alpha_total,
            futility_threshold=body.futility_threshold,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return decision


# ---------------------------------------------------------------------------
# POST /experiments/{name}/promote-winner — T-19 Fase 3+4 com Bonferroni + FairnessGate
# ---------------------------------------------------------------------------


@router.post("/experiments/{test_name}/promote-winner", response_model=None)
async def promote_winner(
    test_name: str,
    body: PromoteWinnerBody,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    """T-19 auto_promote_winner canonical: Bonferroni multi-arm + FairnessGate L3."""
    result = await _service.auto_promote_winner(
        test_name,
        db,
        use_thompson_sampling=body.use_thompson_sampling,
        thompson_threshold=body.thompson_threshold,
        company_id=company_id,  # WT-2022 P1.3: tenant scoping
    )
    return result


# ---------------------------------------------------------------------------
# GET /experiments/{name}/history — past results/winners
# ---------------------------------------------------------------------------


@router.get("/experiments/{test_name}/history", response_model=None)
async def get_experiment_history(
    test_name: str,
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    """Histórico de resultados/winners por test_name.

    Backed por `get_test_results` canonical. Devolve estrutura plana com
    variants summary + significance + winner info para o frontend renderizar timeline.
    """
    results = await _service.get_test_results(test_name, db)

    if not isinstance(results, dict):
        return {"test_name": test_name, "history": []}

    winner_info = results.get("winner")
    sig_results = results.get("statistical_significance") or {}
    variants = results.get("variants") or {}

    history_entries: list[dict[str, Any]] = []
    if winner_info:
        history_entries.append({
            "kind": "current_winner_snapshot",
            "variant": winner_info.get("variant"),
            "p_value": winner_info.get("p_value"),
            "mean_diff": winner_info.get("mean_diff"),
            "metric": winner_info.get("metric"),
        })
    for variant_name, sig in sig_results.items():
        history_entries.append({
            "kind": "significance_comparison",
            "variant": variant_name,
            "p_value": sig.get("p_value"),
            "n_control": sig.get("n_control"),
            "n_variant": sig.get("n_variant"),
            "mean_diff": sig.get("mean_diff"),
        })

    return {
        "test_name": test_name,
        "winner": winner_info,
        "variants_summary": variants,
        "recommendation": results.get("recommendation"),
        "total_observations": results.get("total_observations"),
        "n_min": results.get("n_min"),
        "history": history_entries,
    }


# ---------------------------------------------------------------------------
# GET /dashboard/summary — KPIs canonical
# ---------------------------------------------------------------------------


@router.get("/dashboard/summary", response_model=None)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    """KPIs canonical agregados (active, promoted, blocked_by_fairness, total_obs)."""
    active = await _service.list_active_tests(db, company_id=company_id)
    active_count = len(active)
    total_observations = 0
    pending_fairness_gate = 0
    promoted_ready = 0

    for entry in active:
        test_name = entry.get("test_name")
        if not test_name:
            continue
        try:
            results = await _service.get_test_results(test_name, db)
        except Exception:  # noqa: BLE001
            continue

        if not isinstance(results, dict):
            continue

        total_observations += int(results.get("total_observations") or 0)
        winner = results.get("winner")
        if winner and winner.get("p_value") is not None:
            p_value = winner.get("p_value", 1.0)
            sig = results.get("statistical_significance") or {}
            n_arms = (len(sig) + 1) if isinstance(sig, dict) else 2
            alpha_adjusted = 0.01 / max(1, n_arms - 1)
            if p_value < alpha_adjusted:
                promoted_ready += 1
            else:
                pending_fairness_gate += 1

    return {
        "summary": {
            "active_count": active_count,
            "promoted_ready": promoted_ready,
            "pending_fairness_gate": pending_fairness_gate,
            "total_observations": total_observations,
        }
    }
