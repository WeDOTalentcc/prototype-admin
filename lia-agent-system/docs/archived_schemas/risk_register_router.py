"""
Risk Register API Endpoints.

Provides endpoints for:
- Risk management (SOX, ISO 27001, BCB 498 compliance)
- Risk treatments
- Risk matrix and statistics
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import Optional, List
from datetime import datetime, date
import logging
from uuid import UUID

from app.core.database import get_db
from app.models.observability import RiskEntry, RiskTreatment
from app.shared.tenant_guard import get_verified_company_id
from app.schemas.risk_register import (
    RiskResponse, RiskListResponse, RiskCreate, RiskUpdate,
    RiskTreatmentResponse, RiskTreatmentCreate, RiskTreatmentUpdate,
    RiskMatrixResponse, RiskMatrixCell, RiskStats,
    RiskCategoryEnum, RiskStatusEnum, RiskLevelEnum
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risks", tags=["risk-register"])


def calculate_risk_level(likelihood: int, impact: int) -> str:
    """Calculate risk level based on likelihood and impact."""
    score = likelihood * impact
    if score <= 4:
        return "low"
    elif score <= 9:
        return "medium"
    elif score <= 16:
        return "high"
    else:
        return "critical"


def risk_entry_to_response(risk: RiskEntry, treatments: List[RiskTreatmentResponse] = None) -> dict:
    """Convert RiskEntry model to response dict format."""
    return {
        "id": str(risk.id),
        "company_id": str(risk.company_id),
        "title": risk.title,
        "description": risk.description,
        "category": risk.category,
        "status": risk.status,
        "likelihood": risk.likelihood,
        "impact": risk.impact,
        "risk_level": risk._calculate_risk_level() or calculate_risk_level(risk.likelihood, risk.impact),
        "risk_score": risk.inherent_risk_score or (risk.likelihood * risk.impact),
        "owner": risk.risk_owner,
        "owner_email": None,
        "identified_at": risk.created_at.isoformat() if risk.created_at else None,
        "last_assessed_at": risk.last_reviewed_at.isoformat() if risk.last_reviewed_at else None,
        "next_review_at": risk.review_date.isoformat() if risk.review_date else None,
        "controls": [str(c) for c in risk.controls_linked] if risk.controls_linked else [],
        "affected_processes": [],
        "compliance_frameworks": [],
        "created_at": risk.created_at.isoformat() if risk.created_at else None,
        "updated_at": risk.updated_at.isoformat() if risk.updated_at else None,
        "treatments": treatments or []
    }


def treatment_to_response(treatment: RiskTreatment) -> dict:
    """Convert RiskTreatment model to response dict format."""
    return {
        "id": str(treatment.id),
        "risk_id": str(treatment.risk_id),
        "treatment_type": treatment.treatment_type,
        "description": treatment.description,
        "responsible": treatment.responsible,
        "due_date": treatment.due_date.isoformat() if treatment.due_date else None,
        "status": treatment.status,
        "effectiveness": None,
        "notes": None,
        "created_at": treatment.created_at.isoformat() if treatment.created_at else None,
        "updated_at": treatment.updated_at.isoformat() if treatment.updated_at else None
    }


@router.get("/stats", response_model=RiskStats, summary="Get risk statistics")
async def get_risk_stats(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated risk statistics for the company."""
    try:
        company_uuid = UUID(company_id)
        
        risks_query = select(RiskEntry).where(RiskEntry.company_id == company_uuid)
        risks_result = await db.execute(risks_query)
        risks = risks_result.scalars().all()
        
        by_category = {}
        by_status = {}
        by_level = {}
        total_score = 0
        pending_reviews = 0
        
        for risk in risks:
            cat = risk.category or "unknown"
            by_category[cat] = by_category.get(cat, 0) + 1
            
            stat = risk.status or "unknown"
            by_status[stat] = by_status.get(stat, 0) + 1
            
            level = risk._calculate_risk_level() or "unknown"
            by_level[level] = by_level.get(level, 0) + 1
            
            total_score += risk.inherent_risk_score or 0
            
            if risk.review_date and risk.review_date < date.today():
                pending_reviews += 1
        
        treatments_query = select(RiskTreatment).where(
            and_(
                RiskTreatment.status.notin_(["completed", "cancelled"]),
                RiskTreatment.due_date < date.today()
            )
        )
        treatments_result = await db.execute(treatments_query)
        overdue_treatments = len(treatments_result.scalars().all())
        
        return RiskStats(
            total_risks=len(risks),
            by_category=by_category,
            by_status=by_status,
            by_level=by_level,
            overdue_treatments=overdue_treatments,
            pending_reviews=pending_reviews,
            average_risk_score=total_score / len(risks) if risks else 0.0
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting risk stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matrix", response_model=RiskMatrixResponse, summary="Get risk matrix")
async def get_risk_matrix(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get risk matrix showing count of risks by likelihood and impact."""
    try:
        company_uuid = UUID(company_id)
        
        query = select(RiskEntry).where(RiskEntry.company_id == company_uuid)
        result = await db.execute(query)
        risks = result.scalars().all()
        
        matrix_data = {}
        for risk in risks:
            key = (risk.likelihood or 1, risk.impact or 1)
            if key not in matrix_data:
                matrix_data[key] = {"count": 0, "risk_ids": []}
            matrix_data[key]["count"] += 1
            matrix_data[key]["risk_ids"].append(str(risk.id))
        
        matrix = []
        for (likelihood, impact), data in matrix_data.items():
            matrix.append(RiskMatrixCell(
                likelihood=likelihood,
                impact=impact,
                count=data["count"],
                risk_level=calculate_risk_level(likelihood, impact),
                risk_ids=data["risk_ids"]
            ))
        
        by_level = {}
        for risk in risks:
            level = risk._calculate_risk_level() or "unknown"
            by_level[level] = by_level.get(level, 0) + 1
        
        return RiskMatrixResponse(
            matrix=matrix,
            total_risks=len(risks),
            by_level=by_level
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting risk matrix: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=RiskListResponse, summary="List risks")
async def list_risks(
    category: Optional[str] = Query(None, description="Filter by category"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List risks with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [RiskEntry.company_id == company_uuid]
        
        if category:
            conditions.append(RiskEntry.category == category)
        if status_filter:
            conditions.append(RiskEntry.status == status_filter)
        
        query = select(RiskEntry).where(and_(*conditions))
        query = query.order_by(desc(RiskEntry.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        risks = result.scalars().all()
        
        count_query = select(func.count(RiskEntry.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        risk_responses = []
        for risk in risks:
            risk_data = risk_entry_to_response(risk, [])
            if risk_level and risk_data.get("risk_level") != risk_level:
                continue
            risk_responses.append(RiskResponse(**risk_data))
        
        return RiskListResponse(
            risks=risk_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing risks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{risk_id}", response_model=RiskResponse, summary="Get risk details")
async def get_risk(
    risk_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific risk with its treatments."""
    try:
        company_uuid = UUID(company_id)
        risk_uuid = UUID(risk_id)
        
        query = select(RiskEntry).where(
            and_(
                RiskEntry.id == risk_uuid,
                RiskEntry.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        risk = result.scalar_one_or_none()
        
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        treatments_query = select(RiskTreatment).where(RiskTreatment.risk_id == risk_uuid)
        treatments_result = await db.execute(treatments_query)
        treatments = treatments_result.scalars().all()
        
        treatment_responses = [RiskTreatmentResponse(**treatment_to_response(t)) for t in treatments]
        
        return RiskResponse(**risk_entry_to_response(risk, treatment_responses))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid risk ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=RiskResponse, status_code=status.HTTP_201_CREATED, summary="Create risk")
async def create_risk(
    data: RiskCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new risk."""
    try:
        company_uuid = UUID(company_id)
        risk_score = data.likelihood * data.impact
        
        risk = RiskEntry(
            company_id=company_uuid,
            risk_id=f"RISK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            category=data.category.value,
            title=data.title,
            description=data.description,
            likelihood=data.likelihood,
            impact=data.impact,
            inherent_risk_score=risk_score,
            residual_risk_score=risk_score,
            risk_owner=data.owner,
            risk_owner_id=None,
            mitigation_plan=None,
            mitigation_status=None,
            controls_linked=[],
            status="identified"
        )
        
        db.add(risk)
        await db.commit()
        await db.refresh(risk)
        
        logger.info(f"Created risk {risk.id} for company {company_id}")
        return RiskResponse(**risk_entry_to_response(risk, []))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{risk_id}", response_model=RiskResponse, summary="Update risk")
async def update_risk(
    risk_id: str,
    data: RiskUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing risk."""
    try:
        company_uuid = UUID(company_id)
        risk_uuid = UUID(risk_id)
        
        query = select(RiskEntry).where(
            and_(
                RiskEntry.id == risk_uuid,
                RiskEntry.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        risk = result.scalar_one_or_none()
        
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        if data.title is not None:
            risk.title = data.title
        if data.description is not None:
            risk.description = data.description
        if data.category is not None:
            risk.category = data.category.value
        if data.status is not None:
            risk.status = data.status.value
        if data.likelihood is not None:
            risk.likelihood = data.likelihood
        if data.impact is not None:
            risk.impact = data.impact
        if data.owner is not None:
            risk.risk_owner = data.owner
        if data.next_review_at is not None:
            risk.review_date = data.next_review_at
        
        risk.inherent_risk_score = risk.likelihood * risk.impact
        risk.last_reviewed_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(risk)
        
        treatments_query = select(RiskTreatment).where(RiskTreatment.risk_id == risk_uuid)
        treatments_result = await db.execute(treatments_query)
        treatments = treatments_result.scalars().all()
        treatment_responses = [RiskTreatmentResponse(**treatment_to_response(t)) for t in treatments]
        
        logger.info(f"Updated risk {risk_id} for company {company_id}")
        return RiskResponse(**risk_entry_to_response(risk, treatment_responses))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid risk ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating risk: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{risk_id}/treatments", response_model=RiskTreatmentResponse, status_code=status.HTTP_201_CREATED, summary="Add treatment")
async def add_treatment(
    risk_id: str,
    data: RiskTreatmentCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Add a treatment to a risk."""
    try:
        company_uuid = UUID(company_id)
        risk_uuid = UUID(risk_id)
        
        query = select(RiskEntry).where(
            and_(
                RiskEntry.id == risk_uuid,
                RiskEntry.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        risk = result.scalar_one_or_none()
        
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        treatment = RiskTreatment(
            risk_id=risk_uuid,
            treatment_type=data.treatment_type.value,
            description=data.description,
            responsible=data.responsible,
            due_date=data.due_date,
            status="planned",
            evidence_files=[]
        )
        
        db.add(treatment)
        
        if risk.status == "identified":
            risk.status = "assessed"
        
        await db.commit()
        await db.refresh(treatment)
        
        logger.info(f"Added treatment {treatment.id} to risk {risk_id}")
        return RiskTreatmentResponse(**treatment_to_response(treatment))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid risk ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding treatment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/treatments/{treatment_id}", response_model=RiskTreatmentResponse, summary="Update treatment")
async def update_treatment(
    treatment_id: str,
    data: RiskTreatmentUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a risk treatment."""
    try:
        company_uuid = UUID(company_id)
        treatment_uuid = UUID(treatment_id)
        
        query = select(RiskTreatment).where(RiskTreatment.id == treatment_uuid)
        result = await db.execute(query)
        treatment = result.scalar_one_or_none()
        
        if not treatment:
            raise HTTPException(status_code=404, detail="Treatment not found")
        
        risk_query = select(RiskEntry).where(
            and_(
                RiskEntry.id == treatment.risk_id,
                RiskEntry.company_id == company_uuid
            )
        )
        risk_result = await db.execute(risk_query)
        risk = risk_result.scalar_one_or_none()
        
        if not risk:
            raise HTTPException(status_code=404, detail="Treatment not found")
        
        if data.treatment_type is not None:
            treatment.treatment_type = data.treatment_type.value
        if data.description is not None:
            treatment.description = data.description
        if data.responsible is not None:
            treatment.responsible = data.responsible
        if data.due_date is not None:
            treatment.due_date = data.due_date
        if data.status is not None:
            treatment.status = data.status.value
        
        await db.commit()
        await db.refresh(treatment)
        
        if data.status and data.status.value == "completed":
            all_treatments_query = select(RiskTreatment).where(RiskTreatment.risk_id == treatment.risk_id)
            all_treatments_result = await db.execute(all_treatments_query)
            all_treatments = all_treatments_result.scalars().all()
            all_completed = all(t.status == "completed" for t in all_treatments)
            if all_completed and risk.status != "closed":
                risk.status = "treated"
                await db.commit()
        
        logger.info(f"Updated treatment {treatment_id}")
        return RiskTreatmentResponse(**treatment_to_response(treatment))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid treatment ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating treatment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
