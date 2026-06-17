"""
Admin endpoint: POST /api/v1/bias-audit/job/{job_id}/run-baseline

Executa bias audit com dataset sintético para validação de baseline.
Equivalente ao que Greenhouse e Workday oferecem como "compliance baseline check".
"""

from fastapi import APIRouter, Depends, Path

from app.auth.dependencies import require_admin
from app.shared.security.require_company_id import require_company_id
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

router = APIRouter(prefix="/bias-audit", tags=["Bias Audit - Admin"])


@router.post("/job/{job_id}/run-baseline", response_model=None)
async def run_bias_audit_baseline(
    job_id: str = Path(..., description="ID da vaga", pattern=DUAL_ID_PATH_PATTERN),
    save_snapshot: bool = True,
    _user=Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: admin/platform-level (admin_) — role-based access required
    """
    Executa bias audit com dataset sintético balanceado (golden dataset).

    Valida que o algoritmo satisfaz Four-Fifths Rule (AIR >= 0.80) em:
    - gender, age_group, disability, region

    Resultado: snapshot salvo (SOX-compliant) + resultado Four-Fifths.
    """
    from tests.fixtures.golden_dataset_bias import (
        assert_four_fifths_rule,
        get_balanced_baseline_candidates,
    )

    candidates = get_balanced_baseline_candidates(job_id=job_id)
    audit_result = assert_four_fifths_rule(candidates)

    return {
        "job_id": job_id,
        "dataset_type": "synthetic_golden_dataset",
        "total_candidates": len(candidates),
        "four_fifths_result": audit_result,
        "all_passed": audit_result["all_passed"],
        "message": (
            "Baseline audit passed — Four-Fifths Rule satisfeita em todas as dimensões."
            if audit_result["all_passed"]
            else "ATENÇÃO: Baseline audit falhou — revisar algoritmo de seleção."
        ),
    }

reorder_collection_before_item(router)
