"""
Pipeline Policy API.

Endpoints:
- GET /pipeline-policy/{company_id}/validate-transition — Check if transition is allowed
- GET /pipeline-policy/{company_id}/templates — Get available pipeline templates
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.policy_middleware import get_policy_for_company
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.shared.pipeline_rules import is_offer_stage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline-policy", tags=["pipeline-policy"])


@router.get("/{company_id}/validate-transition", response_model=None)
# TODO(phase2): extract to repository — pipeline policy management
async def validate_transition(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    candidate_id: str = Query(...),
    target_stage: str = Query(...),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Validate whether a pipeline transition is allowed based on company policy.
    
    Returns warnings (informational) and blockers (must resolve before proceeding).
    """
    policy = await get_policy_for_company(company_id, db)
    pipeline_rules = policy.get("pipeline_rules", {})
    
    warnings: list[str] = []
    blockers: list[str] = []
    metadata: dict[str, Any] = {}
    
    _is_offer_stage = is_offer_stage(target_stage)
    
    if _is_offer_stage:
        min_interviews = pipeline_rules.get("min_interviews_before_offer", 2)
        
        # Onda 4.2d-P0-17 (2026-05-23): cross-tenant guard — filter por company_id.
        # Antes vazava interview_count de candidatos de outras empresas
        # (info disclosure: indica estagio do pipeline).
        interview_count = 0
        try:
            from app.models.interview import Interview
            result = await db.execute(
                select(func.count(Interview.id)).where(
                    Interview.candidate_id == candidate_id,
                    Interview.company_id == company_id,
                    Interview.status.in_(["completed", "done", "realizada"]),
                )
            )
            interview_count = result.scalar() or 0
        except Exception as e:
            logger.warning(f"Could not count interviews for {candidate_id}: {e}")
            try:
                from app.domains.interview_scheduling.models.interview import Interview as DomainInterview
                result = await db.execute(
                    select(func.count(DomainInterview.id)).where(
                        DomainInterview.candidate_id == candidate_id,
                        DomainInterview.company_id == company_id,
                        DomainInterview.status.in_(["completed", "done", "realizada"]),
                    )
                )
                interview_count = result.scalar() or 0
            except Exception:
                pass
        
        metadata["interview_count"] = interview_count
        metadata["min_interviews_required"] = min_interviews
        
        if interview_count < min_interviews:
            warnings.append(
                f"Política da empresa exige pelo menos {min_interviews} entrevistas "
                f"antes da proposta. Este candidato teve {interview_count}."
            )
        
        manager_approval = pipeline_rules.get("manager_approval_for_offer", True)
        if manager_approval:
            metadata["requires_manager_approval"] = True
            metadata["suggested_sub_status"] = "Aguardando aprovação do gestor"
            warnings.append(
                "Política da empresa exige aprovação do gestor antes de emitir proposta."
            )
    
    max_days = pipeline_rules.get("max_days_in_stage", {})
    if isinstance(max_days, dict) and target_stage.lower() in max_days:
        metadata["sla_days"] = max_days[target_stage.lower()]
    
    return {
        "allowed": len(blockers) == 0,
        "warnings": warnings,
        "blockers": blockers,
        "metadata": metadata,
        "policy_applied": policy.get("id") is not None,
    }


@router.get("/{company_id}/templates", response_model=None)
async def get_pipeline_templates(
    company_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))) -> dict[str, Any]:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get available pipeline templates for a company.
    
    Returns company-specific templates from policy + system defaults.
    """
    policy = await get_policy_for_company(company_id, db)
    
    company_templates = policy.get("pipeline_templates", [])
    
    system_templates = [
        {
            "id": "standard",
            "name": "Processo Padrão",
            "description": "Fluxo padrão de recrutamento",
            "stages": [
                {"name": "Triagem", "order": 1, "sla_days": 5},
                {"name": "Entrevista RH", "order": 2, "sla_days": 7},
                {"name": "Entrevista Técnica", "order": 3, "sla_days": 7},
                {"name": "Proposta", "order": 4, "sla_days": 5},
            ],
        },
        {
            "id": "technical",
            "name": "Processo Técnico",
            "description": "Fluxo com avaliação técnica aprofundada",
            "stages": [
                {"name": "Triagem", "order": 1, "sla_days": 3},
                {"name": "Teste Técnico", "order": 2, "sla_days": 5},
                {"name": "Entrevista Técnica", "order": 3, "sla_days": 7},
                {"name": "Entrevista Cultural", "order": 4, "sla_days": 5},
                {"name": "Proposta", "order": 5, "sla_days": 5},
            ],
        },
        {
            "id": "operational",
            "name": "Processo Operacional",
            "description": "Fluxo simplificado para vagas operacionais",
            "stages": [
                {"name": "Triagem", "order": 1, "sla_days": 3},
                {"name": "Entrevista", "order": 2, "sla_days": 5},
                {"name": "Proposta", "order": 3, "sla_days": 3},
            ],
        },
        {
            "id": "executive",
            "name": "Processo Executivo",
            "description": "Fluxo completo para posições de liderança",
            "stages": [
                {"name": "Triagem", "order": 1, "sla_days": 5},
                {"name": "Entrevista RH", "order": 2, "sla_days": 7},
                {"name": "Case / Apresentação", "order": 3, "sla_days": 10},
                {"name": "Entrevista Diretoria", "order": 4, "sla_days": 7},
                {"name": "Referências", "order": 5, "sla_days": 5},
                {"name": "Proposta", "order": 6, "sla_days": 5},
            ],
        },
    ]
    
    return {
        "company_templates": company_templates,
        "system_templates": system_templates,
        "policy_applied": policy.get("id") is not None,
    }

reorder_collection_before_item(router)
