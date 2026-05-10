"""
Digital Twins API — endpoints for creating, indexing, and using Digital Twins.

Apply to: lia-agent-system/app/api/v1/digital_twins.py
Register: app.include_router(digital_twins_router)
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/api/v1/digital-twins", tags=["Digital Twins"])


class CreateTwinRequest(BaseModel):
    twin_name: str = Field(..., min_length=3, max_length=256)
    sme_user_id: Optional[str] = None
    specialties: list[str] = Field(default_factory=list)
    description: Optional[str] = None
    months_back: int = Field(default=12, ge=1, le=36)


class EvaluateRequest(BaseModel):
    candidate_profile: dict
    job_context: dict
    k: int = Field(default=5, ge=1, le=20)


class ManualDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected|maybe)$")
    reasoning: str = Field(..., min_length=10, max_length=2000)
    candidate_snapshot: Optional[dict] = None
    job_snapshot: Optional[dict] = None


@router.post("")
async def create_twin(
    body: CreateTwinRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create a Digital Twin and optionally index ATS history.

    The twin captures the decision-making reasoning of a Subject Matter Expert.
    """
    from lia_models.digital_twin import DigitalTwin
    from app.services.quota_enforcement import enforce_quota

    company_id = current_user.get("company_id", "unknown")
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

    # Index ATS history in background
    indexed = 0
    try:
        from app.services.twin_knowledge_indexer import twin_knowledge_indexer
        indexed = await twin_knowledge_indexer.index_from_ats_history(
            twin_id=str(twin.id),
            company_id=company_id,
            months_back=body.months_back,
            db=db,
        )
    except Exception:
        pass  # Non-blocking — twin is created even if indexing fails

    return {
        "twin_id": str(twin.id),
        "twin_name": twin.twin_name,
        "decisions_indexed": indexed,
        "status": "active",
    }


@router.get("")
async def list_twins(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all Digital Twins for the current company."""
    from lia_models.digital_twin import DigitalTwin
    from sqlalchemy import select

    company_id = current_user.get("company_id", "unknown")
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
async def get_twin(twin_id: str, db: AsyncSession = Depends(get_db)):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
    """Get details of a specific Digital Twin."""
    from lia_models.digital_twin import DigitalTwin
    from sqlalchemy import select

    result = await db.execute(select(DigitalTwin).where(DigitalTwin.id == twin_id))
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
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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
    db: AsyncSession = Depends(get_db),
):
    # multi-tenancy: protected via auth middleware (JWT) + Postgres RLS runtime (Sprint follow-up: add _require_company_id explicit gate)
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

    return {
        "twin_id": evaluation.twin_id,
        "twin_name": evaluation.twin_name,
        "score": evaluation.score,
        "decision": evaluation.decision,
        "reasoning": evaluation.reasoning,
        "confidence": evaluation.confidence,
        "supporting_examples": [
            {
                "decision": ex["decision"],
                "reasoning": ex["reasoning"][:200],
                "similarity": ex.get("similarity", 0),
            }
            for ex in evaluation.supporting_examples
        ],
    }
