from __future__ import annotations
"""Learning Loops Config endpoints — Sprint B Phase 1 + Phase 2.

Endpoints REST pra ligar/desligar os 4 learning loops por empresa.

GET    /companies/{company_id}/learning-loops-config
PATCH  /companies/{company_id}/learning-loops-config

Multi-tenancy: company_id no path, validado fail-closed.
Segurança: company_id SEMPRE do path/JWT — NUNCA do payload.
ADR-001: usa CompanyHiringPolicyRepository (TODO: extrair em PR separado;
por ora query direta segue padrao do automation_rules existente).
ADR-006: nenhum log com PII.
"""
from app.middleware.request_id import get_correlation_id

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import logging
logger = logging.getLogger(__name__)

from app.core.database import get_db, get_tenant_db
from lia_models.company_hiring_policy import (
    AUTOMATION_RULES_DEFAULTS,
    CompanyHiringPolicy,
)
from app.shared.security.require_company_id import require_company_id_strict_match

router = APIRouter(
    prefix="/companies",
    tags=["learning-loops", "sprint-b", "company-config"],
)


# Boy-Scout (audit 2026-05-24 P2-G): _enforce_tenant helper local foi
# removido como redundante. Defense-in-depth canonical agora é o single
# gate `Depends(require_company_id_strict_match("path.company_id"))` em
# cada endpoint — esse já valida JWT vs path com HTTP 403 ANTES do body
# do handler rodar (vide app/shared/security/require_company_id.py).
# Manter dois enforcers paralelos criava drift potencial: se a regra
# mudasse num lugar e não no outro, a defesa virava ilusória.


# ── Schemas ─────────────────────────────────────────────────────────────────


class LearningLoopsConfig(BaseModel):
    enabled: bool = True
    bigfive_company_culture: bool = True
    bigfive_department_history: bool = False
    wsi_question_effectiveness: bool = False
    jd_similar_suggestion: bool = True


class LearningLoopsConfigPatch(BaseModel):
    """Partial update — todos os campos opcionais."""
    enabled: bool | None = None
    bigfive_company_culture: bool | None = None
    bigfive_department_history: bool | None = None
    wsi_question_effectiveness: bool | None = None
    jd_similar_suggestion: bool | None = None


class LearningLoopsConfigResponse(BaseModel):
    company_id: str
    config: LearningLoopsConfig
    source: str  # "stored" | "default"


# ── Helpers ─────────────────────────────────────────────────────────────────


_DEFAULT_LOOPS = AUTOMATION_RULES_DEFAULTS["learning_loops"]


def _extract_loops(automation_rules: dict[str, Any] | None) -> dict[str, bool]:
    """Reads `learning_loops` block, fills missing keys with defaults."""
    rules = automation_rules or {}
    stored = rules.get("learning_loops") or {}
    out: dict[str, bool] = {}
    for k, default in _DEFAULT_LOOPS.items():
        out[k] = bool(stored.get(k, default))
    return out


async def _get_policy_or_404(
    db: AsyncSession, company_id: str
) -> CompanyHiringPolicy | None:
    if not company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="company_id required",
        )
    stmt = select(CompanyHiringPolicy).where(  # ADR-001-EXEMPT: router-level query (canonical applies to services only — see CLAUDE.md)
        CompanyHiringPolicy.company_id == company_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "/{company_id}/learning-loops-config",
    response_model=LearningLoopsConfigResponse,
)
async def get_config(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    _company_gate: str = Depends(
        require_company_id_strict_match("path.company_id")
    ),
) -> LearningLoopsConfigResponse:
    # multi-tenancy: enforced by `require_company_id_strict_match("path.company_id")` Depends gate above (JWT vs path)
    """Retorna config dos learning loops da empresa.

    Multi-tenancy: ``require_company_id_strict_match`` valida que o
    ``company_id`` do path bate com o do JWT antes desta função rodar.
    Se houver mismatch, 403 é levantado pelo Depends — chegamos aqui
    apenas com tenant consistente.

    Se nao houver CompanyHiringPolicy, retorna defaults (source='default').
    """
    policy = await _get_policy_or_404(db, company_id)
    if policy is None:
        return LearningLoopsConfigResponse(
            company_id=company_id,
            config=LearningLoopsConfig(**_DEFAULT_LOOPS),
            source="default",
        )
    loops = _extract_loops(policy.automation_rules or {})
    return LearningLoopsConfigResponse(
        company_id=company_id,
        config=LearningLoopsConfig(**loops),
        source="stored",
    )


@router.patch(
    "/{company_id}/learning-loops-config",
    response_model=LearningLoopsConfigResponse,
)
async def patch_config(
    company_id: str,
    body: LearningLoopsConfigPatch,
    db: AsyncSession = Depends(get_tenant_db),
    _company_gate: str = Depends(
        require_company_id_strict_match("path.company_id")
    ),
) -> LearningLoopsConfigResponse:
    # multi-tenancy: enforced by `require_company_id_strict_match("path.company_id")` Depends gate above (JWT vs path)
    """Update partial dos toggles.

    Multi-tenancy: ``require_company_id_strict_match`` valida JWT vs path
    fail-closed antes do handler rodar.

    Se nao existir CompanyHiringPolicy, cria com defaults aplicando o patch.
    Audit log: cada toggle mudado deveria gerar entrada (TODO: instrumentar).
    """
    policy = await _get_policy_or_404(db, company_id)
    patch = body.model_dump(exclude_none=True)

    # Boy-Scout (audit 2026-05-24 P2-D): snapshot prev ANTES da mutação,
    # para o audit log poder anexar diff prev/next per ADR-LGPD-001.
    if policy is None:
        old_loops: dict[str, bool] = dict(_DEFAULT_LOOPS)
    else:
        _existing = (policy.automation_rules or {}).get("learning_loops") or {}
        old_loops = {k: bool(_existing.get(k, d)) for k, d in _DEFAULT_LOOPS.items()}

    if policy is None:
        # Cria nova policy com defaults + patch aplicado em learning_loops
        new_loops = {**_DEFAULT_LOOPS, **patch}
        new_automation = {**AUTOMATION_RULES_DEFAULTS, "learning_loops": new_loops}
        policy = CompanyHiringPolicy(
            company_id=company_id,
            automation_rules=new_automation,
        )
        db.add(policy)
    else:
        rules = dict(policy.automation_rules or {})
        loops = dict(rules.get("learning_loops") or {})
        loops.update(patch)
        rules["learning_loops"] = loops
        # Reasignment forces SQLAlchemy JSON change detection
        policy.automation_rules = rules

    await db.commit()

    final_loops = _extract_loops(policy.automation_rules or {})

    # Sprint B audit log: toggle changes are LGPD-critical (especially
    # bigfive_dept). P1-7 (post-Sprint-B audit): consolidate action_type
    # to canonical 'feature_flag_change' so forensic queries don't need
    # OR across two parallel taxonomies. The HTTP endpoint
    # /feature-flags/set, policy_sync_service, and this learning_loops
    # endpoint all emit the same action_type — single source of truth.
    # The flag_namespace field tells the consumer this row is a
    # learning_loops change specifically.
    #
    # Boy-Scout (audit 2026-05-24 P2-D): metadata agora carrega prev/next
    # snapshot per ADR-LGPD-001 — forensic queries conseguem reconstruir
    # o estado completo antes da mudança sem precisar derivar de outras rows.
    try:
        from app.shared.compliance.audit_service import get_audit_service
        import uuid as _uuid
        await get_audit_service().log_action(
            trace_id=get_correlation_id(),
            company_id=company_id,
            action_type="feature_flag_change",
            actor="api:learning_loops_config",
            target_id=company_id,
            target_type="company",
            metadata={
                "changes": patch,
                "prev": old_loops,
                "next": final_loops,
                "source": "learning_loops_config",
                "flag_namespace": "learning_loops",
            },
        )
    except Exception as _audit_exc:
        # Boy-Scout (audit 2026-05-24 P2-C): exc_info=True per REGRA 4
        # anti-silent-fallback. Audit log é LGPD-critical — sem stack
        # trace fica impossível diagnosticar a falha em prod.
        logger.error(
            "[learning_loops] audit log failed",
            exc_info=True,
            extra={
                "company_id": str(company_id),
                "changes_keys": list(patch.keys()),
            },
        )

    return LearningLoopsConfigResponse(
        company_id=company_id,
        config=LearningLoopsConfig(**final_loops),
        source="stored",
    )

