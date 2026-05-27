"""
Digital Twins API — endpoints for creating, indexing, and using Digital Twins.

Apply to: lia-agent-system/app/api/v1/digital_twins.py
Register: app.include_router(digital_twins_router)
"""

import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from pydantic import BaseModel, Field
from typing import Optional
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digital-twins", tags=["Digital Twins"])


class CreateTwinRequest(WeDoBaseModel):
    twin_name: str = Field(..., min_length=3, max_length=256)
    sme_user_id: Optional[str] = None
    specialties: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    months_back: int = Field(default=12, ge=1, le=36)


class EvaluateRequest(WeDoBaseModel):
    candidate_profile: dict
    job_context: dict
    k: int = Field(default=5, ge=1, le=20)


class ManualDecisionRequest(WeDoBaseModel):
    decision: str = Field(..., pattern="^(approved|rejected|maybe)$")
    reasoning: str = Field(..., min_length=10, max_length=2000)
    candidate_snapshot: Optional[dict] = None
    job_snapshot: Optional[dict] = None


@router.post("")
async def create_twin(
    body: CreateTwinRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create a Digital Twin and optionally index ATS history.

    The twin captures the decision-making reasoning of a Subject Matter Expert.
    """
    from lia_models.digital_twin import DigitalTwin
    from app.services.quota_enforcement import enforce_quota

    # Multi-tenancy canonical (CLAUDE.md REGRA 6): company_id vem do JWT via
    # Depends(require_company_id). NUNCA fazer overwrite com current_user.get(...)
    # — current_user é dict cujo company_id NÃO passa por get_verified_company_id
    # e tem fallback literal "unknown" que vaza cross-tenant ou viola FK.
    # Fix harness audit 2026-05-23 — anti-pattern detectado em audit deep.
    await enforce_quota("digital_twins", company_id, db)

    twin = DigitalTwin(
        id=str(uuid.uuid4()),
        company_id=company_id,
        twin_name=body.twin_name,
        sme_user_id=body.sme_user_id,
        specialties=body.specialties,
        description=body.description,
        is_active=True,
    )
    db.add(twin)
    await db.commit()
    await db.refresh(twin)

    # Index ATS history. P0-4(c) audit 2026-05-21: anti-silent-fallback (REGRA 4 CLAUDE.md).
    # Antes: try/except: pass swallowava falha de indexação. Twin sempre criado vazio sem
    # erro visível → recruiter via "Avaliação maybe (confiança 0%)" e achava que era bug.
    # Agora: log explícito + retorna decisions_indexed=0 com flag indexing_failed=True
    # no response. Frontend pode mostrar warning "Sem histórico ATS — twin criado vazio".
    indexed = 0
    indexing_failed = False
    indexing_error = None
    try:
        from app.services.twin_knowledge_indexer import twin_knowledge_indexer
        indexed = await twin_knowledge_indexer.index_from_ats_history(
            twin_id=str(twin.id),
            company_id=company_id,
            months_back=body.months_back,
            db=db,
        )
    except Exception as idx_exc:
        indexing_failed = True
        indexing_error = str(idx_exc)[:200]
        logger.error(
            "[DigitalTwin] index_from_ats_history failed for twin=%s company=%s: %s",
            twin.id, company_id, idx_exc, exc_info=True,
        )

    # P0-3 chunk 2 audit 2026-05-21: twin creation trail (LGPD Art. 20 — automated decision tool created)
    try:
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=company_id,
            action="studio_twin_create",
            decision="created",
            reasoning=[
                f"Twin name: {body.twin_name}",
                f"Specialties: {', '.join(body.specialties)}",
                f"Months indexed: {body.months_back}",
                f"Decisions indexed: {indexed}",
                f"Indexing failed: {indexing_failed}",
            ],
            actor_user_id=str(current_user.id),
            target_id=str(twin.id),
            target_type="digital_twin",
        )
    except Exception:
        pass

    return {
        "twin_id": str(twin.id),
        "twin_name": twin.twin_name,
        "decisions_indexed": indexed,
        "status": "active",
        "indexing_failed": indexing_failed,  # P0-4(c) — true if ATS history indexing failed
        "indexing_error": indexing_error,     # human-readable error message if any
        "needs_manual_indexing": indexed == 0,  # UX hint: twin nasceu vazio
    }


@router.get("")
async def list_twins(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all Digital Twins for the current company."""
    from lia_models.digital_twin import DigitalTwin
    from sqlalchemy import select

    # Multi-tenancy canonical (CLAUDE.md REGRA 6): company_id vem do JWT via
    # Depends(require_company_id). Audit harness 2026-05-23 fixou create_twin;
    # list_twins tinha mesmo bug — read endpoint vulnerável a leak cross-tenant
    # se current_user dict tiver company_id diferente do JWT-canonical.
    result = await db.execute(
        select(DigitalTwin)
        .where(DigitalTwin.company_id == company_id)
        .order_by(DigitalTwin.created_at.desc())
    )
    twins = result.scalars().all()

    return {"twins": [
        {
            "id": str(t.id),
            "twin_name": t.twin_name,
            "specialties": t.specialties or [],
            "description": t.description,
            "decision_count": t.decision_count,
            "accuracy_pct": t.accuracy_pct,
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in twins
    ]}


@router.get("/{twin_id}")
async def get_twin(twin_id: str, db: AsyncSession = Depends(get_tenant_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get details of a specific Digital Twin."""
    from lia_models.digital_twin import DigitalTwin
    from sqlalchemy import select

    result = await db.execute(select(DigitalTwin).where(DigitalTwin.id == twin_id, DigitalTwin.company_id == company_id))
    twin = result.scalar_one_or_none()
    if not twin:
        raise HTTPException(404, "Twin not found")

    return {
        "id": str(twin.id),
        "twin_name": twin.twin_name,
        "specialties": twin.specialties or [],
        "description": twin.description,
        "decision_count": twin.decision_count,
        "accuracy_pct": twin.accuracy_pct,
        "is_active": twin.is_active,
        "sme_user_id": twin.sme_user_id,
    }


@router.post("/{twin_id}/index-audio")
async def index_audio(
    twin_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Upload and index an interview recording with the SME."""
    audio_bytes = await file.read()
    audio_format = file.content_type or "audio/mp4"

    from app.services.twin_knowledge_indexer import twin_knowledge_indexer
    result = await twin_knowledge_indexer.index_from_audio(
        twin_id=twin_id,
        audio_bytes=audio_bytes,
        audio_format=audio_format,
        db=db,
    )
    return result


@router.post("/{twin_id}/index-decision")
async def index_manual_decision(
    twin_id: str,
    body: ManualDecisionRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Manually index a single decision + reasoning."""
    from app.services.twin_knowledge_indexer import twin_knowledge_indexer
    result = await twin_knowledge_indexer.index_manual_decision(
        twin_id=twin_id,
        decision=body.decision,
        reasoning=body.reasoning,
        candidate_snapshot=body.candidate_snapshot,
        job_snapshot=body.job_snapshot,
        db=db,
    )
    return result


@router.post("/{twin_id}/evaluate")
async def evaluate_candidate(
    twin_id: str,
    body: EvaluateRequest,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Evaluate a candidate using the Digital Twin's reasoning.

    Returns score, decision, and reasoning in the SME's style,
    plus the supporting examples that informed the evaluation.
    """
    from app.services.twin_inference_service import twin_inference_service

    evaluation = await twin_inference_service.evaluate(
        twin_id=twin_id,
        candidate_profile=body.candidate_profile,
        job_context=body.job_context,
        k=body.k,
        db=db,
    )

    # P0-3 chunk 2 audit 2026-05-21: twin evaluation trail (LGPD Art. 20 — automated decision)
    try:
        from app.domains.agent_studio._audit_helper import studio_audit
        await studio_audit(
            company_id=company_id,
            action="studio_twin_evaluate",
            decision=evaluation.decision,
            reasoning=[
                f"Twin ID: {evaluation.twin_id}",
                f"Score: {evaluation.score}",
                f"Confidence: {evaluation.confidence}",
                f"Reasoning excerpt: {(evaluation.reasoning or '')[:200]}",
            ],
            target_id=str(evaluation.twin_id),
            target_type="digital_twin",
            score=evaluation.score,
            confidence=evaluation.confidence,
        )
    except Exception:
        pass

    return {
        "twin_id": evaluation.twin_id,
        "twin_name": evaluation.twin_name,
        "score": evaluation.score,
        "decision": evaluation.decision,
        "reasoning": evaluation.reasoning,
        "confidence": evaluation.confidence,
        # REGRA 4 anti-silent-fallback (audit 2026-05-27): propaga falha LLM explícita
        "evaluation_failed": evaluation.evaluation_failed,
        "failure_reason": evaluation.failure_reason,
        "needs_manual_review": evaluation.needs_manual_review,
        "supporting_examples": [
            {
                "decision": ex["decision"],
                "reasoning": ex["reasoning"][:200],
                "similarity": ex.get("similarity", 0),
            }
            for ex in evaluation.supporting_examples
        ],
    }
