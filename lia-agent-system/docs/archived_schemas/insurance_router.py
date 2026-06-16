"""
Insurance Management API Endpoints for BCB 498/2025 compliance.

Provides endpoints for:
- Insurance Policies (cyber insurance)
- Coverages (data breach, ransomware, etc.)
- Documents (policy attachments)
- Claims/Sinistros
- Dashboard and Alerts
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc, or_
from typing import Optional, List
from datetime import datetime, date, timedelta
import logging
from uuid import UUID

from app.core.database import get_db
from app.shared.tenant_guard import get_verified_company_id
from app.models.observability import (
    InsurancePolicy, InsuranceCoverage, InsuranceDocument, InsuranceClaim,
    InsurancePolicyStatusEnum, InsuranceCoverageTypeEnum, InsuranceDocumentTypeEnum,
    InsuranceClaimStatusEnum
)
from app.schemas.insurance import (
    InsurancePolicyCreate, InsurancePolicyUpdate, InsurancePolicyResponse, InsurancePolicyListResponse,
    InsuranceCoverageCreate, InsuranceCoverageUpdate, InsuranceCoverageResponse,
    InsuranceDocumentCreate, InsuranceDocumentResponse,
    InsuranceClaimCreate, InsuranceClaimUpdate, InsuranceClaimResponse, InsuranceClaimListResponse,
    InsuranceDashboard, InsuranceAlert, InsuranceAlertListResponse, InsuranceCoverageChecklist,
    CoverageStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insurance", tags=["insurance"])

BCB_498_REQUIRED_COVERAGES = [
    "data_breach",
    "ransomware",
    "business_interruption",
    "regulatory_defense",
    "cyber_liability",
    "forensics",
    "notification_costs",
    "crisis_management"
]


@router.get("/dashboard", response_model=InsuranceDashboard, summary="Get insurance dashboard")
async def get_insurance_dashboard(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get insurance dashboard with active policy, coverages, gaps, and claims summary."""
    try:
        company_uuid = UUID(company_id)
        today = date.today()
        
        active_policy_query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.company_id == company_uuid,
                InsurancePolicy.status == "active",
                InsurancePolicy.coverage_start <= today,
                InsurancePolicy.coverage_end >= today
            )
        ).order_by(desc(InsurancePolicy.coverage_end)).limit(1)
        
        result = await db.execute(active_policy_query)
        active_policy = result.scalar_one_or_none()
        
        active_policy_response = None
        days_until_expiry = None
        total_coverage = None
        total_premium = None
        coverages_by_type = {}
        coverage_gaps = list(BCB_498_REQUIRED_COVERAGES)
        
        if active_policy:
            active_policy_response = InsurancePolicyResponse(**active_policy.to_dict())
            days_until_expiry = active_policy._days_until_expiry()
            total_coverage = float(active_policy.total_coverage_amount) if active_policy.total_coverage_amount else 0
            total_premium = float(active_policy.premium_amount) if active_policy.premium_amount else 0
            
            coverages_query = select(InsuranceCoverage).where(
                and_(
                    InsuranceCoverage.policy_id == active_policy.id,
                    InsuranceCoverage.is_included == True
                )
            )
            coverages_result = await db.execute(coverages_query)
            coverages = coverages_result.scalars().all()
            
            for cov in coverages:
                coverages_by_type[cov.coverage_type] = float(cov.coverage_limit) if cov.coverage_limit else 0
                if cov.coverage_type in coverage_gaps:
                    coverage_gaps.remove(cov.coverage_type)
        
        pending_claims_query = select(
            func.count(InsuranceClaim.id),
            func.sum(InsuranceClaim.claimed_amount)
        ).where(
            and_(
                InsuranceClaim.policy_id.in_(
                    select(InsurancePolicy.id).where(InsurancePolicy.company_id == company_uuid)
                ),
                InsuranceClaim.status.in_(["reported", "under_review"])
            )
        )
        pending_result = await db.execute(pending_claims_query)
        pending_count, pending_amount = pending_result.one()
        
        total_claims_query = select(
            func.count(InsuranceClaim.id),
            func.sum(InsuranceClaim.settled_amount)
        ).where(
            InsuranceClaim.policy_id.in_(
                select(InsurancePolicy.id).where(InsurancePolicy.company_id == company_uuid)
            )
        )
        total_result = await db.execute(total_claims_query)
        total_count, total_settled = total_result.one()
        
        covered_types = [ct for ct in BCB_498_REQUIRED_COVERAGES if ct not in coverage_gaps]
        compliance_status = InsuranceCoverageChecklist(
            coverages=[
                CoverageStatus(
                    coverage_type=ct,
                    covered=ct in covered_types,
                    coverage_limit=coverages_by_type.get(ct)
                ) for ct in BCB_498_REQUIRED_COVERAGES
            ],
            total_required=8,
            total_covered=len(covered_types),
            compliance_percentage=round(len(covered_types) / 8 * 100, 1)
        )
        
        return InsuranceDashboard(
            active_policy=active_policy_response,
            days_until_expiry=days_until_expiry,
            total_coverage_amount=total_coverage,
            total_premium=total_premium,
            coverages_by_type=coverages_by_type,
            coverage_gaps=coverage_gaps,
            pending_claims_count=pending_count or 0,
            pending_claims_amount=float(pending_amount) if pending_amount else None,
            total_claims_count=total_count or 0,
            total_settled_amount=float(total_settled) if total_settled else None,
            compliance_status=compliance_status
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting insurance dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", response_model=InsuranceAlertListResponse, summary="Get insurance alerts")
async def get_insurance_alerts(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get insurance alerts for renewal and compliance issues."""
    try:
        company_uuid = UUID(company_id)
        today = date.today()
        alerts: List[InsuranceAlert] = []
        
        expiring_query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.company_id == company_uuid,
                InsurancePolicy.status == "active",
                InsurancePolicy.coverage_end >= today,
                InsurancePolicy.coverage_end <= today + timedelta(days=90)
            )
        )
        result = await db.execute(expiring_query)
        expiring_policies = result.scalars().all()
        
        for policy in expiring_policies:
            days_left = (policy.coverage_end - today).days
            if days_left <= 30:
                severity = "critical"
            elif days_left <= 60:
                severity = "high"
            else:
                severity = "medium"
            
            alerts.append(InsuranceAlert(
                alert_type="renewal",
                severity=severity,
                message=f"Apólice {policy.policy_number} vence em {days_left} dias",
                policy_id=str(policy.id),
                policy_number=policy.policy_number,
                days_until_expiry=days_left,
                created_at=datetime.utcnow()
            ))
        
        active_policy_query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.company_id == company_uuid,
                InsurancePolicy.status == "active",
                InsurancePolicy.coverage_start <= today,
                InsurancePolicy.coverage_end >= today
            )
        ).limit(1)
        
        result = await db.execute(active_policy_query)
        active_policy = result.scalar_one_or_none()
        
        if active_policy:
            coverages_query = select(InsuranceCoverage.coverage_type).where(
                and_(
                    InsuranceCoverage.policy_id == active_policy.id,
                    InsuranceCoverage.is_included == True
                )
            )
            coverages_result = await db.execute(coverages_query)
            covered_types = [c[0] for c in coverages_result.all()]
            
            missing = [ct for ct in BCB_498_REQUIRED_COVERAGES if ct not in covered_types]
            
            if missing:
                alerts.append(InsuranceAlert(
                    alert_type="compliance",
                    severity="high" if len(missing) > 2 else "medium",
                    message=f"Faltam {len(missing)} coberturas exigidas pelo BCB 498/2025",
                    policy_id=str(active_policy.id),
                    policy_number=active_policy.policy_number,
                    missing_coverages=missing,
                    created_at=datetime.utcnow()
                ))
        else:
            alerts.append(InsuranceAlert(
                alert_type="compliance",
                severity="critical",
                message="Nenhuma apólice de seguro cibernético ativa encontrada",
                created_at=datetime.utcnow()
            ))
        
        return InsuranceAlertListResponse(alerts=alerts, total=len(alerts))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting insurance alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/coverage-checklist", response_model=InsuranceCoverageChecklist, summary="Get BCB 498 coverage checklist")
async def get_coverage_checklist(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get checklist of required BCB 498/2025 coverages with status."""
    try:
        company_uuid = UUID(company_id)
        today = date.today()
        
        active_policy_query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.company_id == company_uuid,
                InsurancePolicy.status == "active",
                InsurancePolicy.coverage_start <= today,
                InsurancePolicy.coverage_end >= today
            )
        ).limit(1)
        
        result = await db.execute(active_policy_query)
        active_policy = result.scalar_one_or_none()
        
        coverage_data: dict = {}
        
        if active_policy:
            coverages_query = select(InsuranceCoverage).where(
                and_(
                    InsuranceCoverage.policy_id == active_policy.id,
                    InsuranceCoverage.is_included == True
                )
            )
            coverages_result = await db.execute(coverages_query)
            coverages = coverages_result.scalars().all()
            
            for cov in coverages:
                coverage_data[cov.coverage_type] = {
                    "coverage_limit": float(cov.coverage_limit) if cov.coverage_limit else None,
                    "policy_id": str(active_policy.id)
                }
        
        checklist = [
            CoverageStatus(
                coverage_type=ct,
                covered=ct in coverage_data,
                coverage_limit=coverage_data.get(ct, {}).get("coverage_limit"),
                policy_id=coverage_data.get(ct, {}).get("policy_id")
            ) for ct in BCB_498_REQUIRED_COVERAGES
        ]
        
        total_covered = sum(1 for c in checklist if c.covered)
        
        return InsuranceCoverageChecklist(
            coverages=checklist,
            total_required=8,
            total_covered=total_covered,
            compliance_percentage=round(total_covered / 8 * 100, 1)
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting coverage checklist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies/", response_model=InsurancePolicyListResponse, summary="List insurance policies")
async def list_policies(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    insurer_name: Optional[str] = Query(None, description="Filter by insurer name"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List insurance policies with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [InsurancePolicy.company_id == company_uuid]
        
        if status_filter:
            conditions.append(InsurancePolicy.status == status_filter)
        if insurer_name:
            conditions.append(InsurancePolicy.insurer_name.ilike(f"%{insurer_name}%"))
        
        query = select(InsurancePolicy).where(and_(*conditions))
        query = query.order_by(desc(InsurancePolicy.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        policies = result.scalars().all()
        
        count_query = select(func.count(InsurancePolicy.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return InsurancePolicyListResponse(
            policies=[InsurancePolicyResponse(**p.to_dict()) for p in policies],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies/{policy_id}", response_model=InsurancePolicyResponse, summary="Get policy details")
async def get_policy(
    policy_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get policy details with coverages and documents."""
    try:
        company_uuid = UUID(company_id)
        policy_uuid = UUID(policy_id)
        
        query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.id == policy_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        coverages_query = select(InsuranceCoverage).where(InsuranceCoverage.policy_id == policy_uuid)
        coverages_result = await db.execute(coverages_query)
        coverages = coverages_result.scalars().all()
        
        docs_query = select(InsuranceDocument).where(InsuranceDocument.policy_id == policy_uuid)
        docs_result = await db.execute(docs_query)
        documents = docs_result.scalars().all()
        
        policy_data = policy.to_dict()
        policy_data["coverages"] = [InsuranceCoverageResponse(**c.to_dict()) for c in coverages]
        policy_data["documents"] = [InsuranceDocumentResponse(**d.to_dict()) for d in documents]
        
        return InsurancePolicyResponse(**policy_data)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/", response_model=InsurancePolicyResponse, status_code=status.HTTP_201_CREATED, summary="Create policy")
async def create_policy(
    data: InsurancePolicyCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new insurance policy."""
    try:
        company_uuid = UUID(company_id)
        
        policy = InsurancePolicy(
            company_id=company_uuid,
            policy_number=data.policy_number,
            insurer_name=data.insurer_name,
            insurer_cnpj=data.insurer_cnpj,
            broker_name=data.broker_name,
            broker_contact=data.broker_contact,
            coverage_start=data.coverage_start,
            coverage_end=data.coverage_end,
            total_coverage_amount=data.total_coverage_amount,
            currency=data.currency,
            premium_amount=data.premium_amount,
            deductible_amount=data.deductible_amount,
            status="active"
        )
        
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        
        logger.info(f"Created insurance policy {policy.policy_number} for company {company_id}")
        return InsurancePolicyResponse(**policy.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/policies/{policy_id}", response_model=InsurancePolicyResponse, summary="Update policy")
async def update_policy(
    policy_id: str,
    data: InsurancePolicyUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an insurance policy."""
    try:
        company_uuid = UUID(company_id)
        policy_uuid = UUID(policy_id)
        
        query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.id == policy_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        if data.policy_number is not None:
            policy.policy_number = data.policy_number
        if data.insurer_name is not None:
            policy.insurer_name = data.insurer_name
        if data.insurer_cnpj is not None:
            policy.insurer_cnpj = data.insurer_cnpj
        if data.broker_name is not None:
            policy.broker_name = data.broker_name
        if data.broker_contact is not None:
            policy.broker_contact = data.broker_contact
        if data.coverage_start is not None:
            policy.coverage_start = data.coverage_start
        if data.coverage_end is not None:
            policy.coverage_end = data.coverage_end
        if data.total_coverage_amount is not None:
            policy.total_coverage_amount = data.total_coverage_amount
        if data.currency is not None:
            policy.currency = data.currency
        if data.premium_amount is not None:
            policy.premium_amount = data.premium_amount
        if data.deductible_amount is not None:
            policy.deductible_amount = data.deductible_amount
        if data.status is not None:
            policy.status = data.status.value
        
        await db.commit()
        await db.refresh(policy)
        
        logger.info(f"Updated insurance policy {policy.policy_number}")
        return InsurancePolicyResponse(**policy.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Deactivate policy")
async def deactivate_policy(
    policy_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate (soft delete) an insurance policy."""
    try:
        company_uuid = UUID(company_id)
        policy_uuid = UUID(policy_id)
        
        query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.id == policy_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        policy.status = "cancelled"
        
        await db.commit()
        
        logger.info(f"Deactivated insurance policy {policy.policy_number}")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deactivating policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies/{policy_id}/coverages/", response_model=List[InsuranceCoverageResponse], summary="List policy coverages")
async def list_coverages(
    policy_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List coverages for a policy."""
    try:
        company_uuid = UUID(company_id)
        policy_uuid = UUID(policy_id)
        
        policy_query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.id == policy_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        policy_result = await db.execute(policy_query)
        if not policy_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Policy not found")
        
        query = select(InsuranceCoverage).where(InsuranceCoverage.policy_id == policy_uuid)
        result = await db.execute(query)
        coverages = result.scalars().all()
        
        return [InsuranceCoverageResponse(**c.to_dict()) for c in coverages]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing coverages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/{policy_id}/coverages/", response_model=InsuranceCoverageResponse, status_code=status.HTTP_201_CREATED, summary="Add coverage")
async def add_coverage(
    policy_id: str,
    data: InsuranceCoverageCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Add a coverage to a policy."""
    try:
        company_uuid = UUID(company_id)
        policy_uuid = UUID(policy_id)
        
        policy_query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.id == policy_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        policy_result = await db.execute(policy_query)
        if not policy_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Policy not found")
        
        coverage = InsuranceCoverage(
            policy_id=policy_uuid,
            coverage_type=data.coverage_type.value,
            description=data.description,
            coverage_limit=data.coverage_limit,
            sub_limit=data.sub_limit,
            deductible=data.deductible,
            is_included=data.is_included,
            exclusions=data.exclusions,
            notes=data.notes
        )
        
        db.add(coverage)
        await db.commit()
        await db.refresh(coverage)
        
        logger.info(f"Added coverage {data.coverage_type.value} to policy {policy_id}")
        return InsuranceCoverageResponse(**coverage.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error adding coverage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/coverages/{coverage_id}", response_model=InsuranceCoverageResponse, summary="Update coverage")
async def update_coverage(
    coverage_id: str,
    data: InsuranceCoverageUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a coverage."""
    try:
        company_uuid = UUID(company_id)
        coverage_uuid = UUID(coverage_id)
        
        query = select(InsuranceCoverage).join(
            InsurancePolicy, InsuranceCoverage.policy_id == InsurancePolicy.id
        ).where(
            and_(
                InsuranceCoverage.id == coverage_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        coverage = result.scalar_one_or_none()
        
        if not coverage:
            raise HTTPException(status_code=404, detail="Coverage not found")
        
        if data.coverage_type is not None:
            coverage.coverage_type = data.coverage_type.value
        if data.description is not None:
            coverage.description = data.description
        if data.coverage_limit is not None:
            coverage.coverage_limit = data.coverage_limit
        if data.sub_limit is not None:
            coverage.sub_limit = data.sub_limit
        if data.deductible is not None:
            coverage.deductible = data.deductible
        if data.is_included is not None:
            coverage.is_included = data.is_included
        if data.exclusions is not None:
            coverage.exclusions = data.exclusions
        if data.notes is not None:
            coverage.notes = data.notes
        
        await db.commit()
        await db.refresh(coverage)
        
        logger.info(f"Updated coverage {coverage_id}")
        return InsuranceCoverageResponse(**coverage.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating coverage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/coverages/{coverage_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove coverage")
async def remove_coverage(
    coverage_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove a coverage."""
    try:
        company_uuid = UUID(company_id)
        coverage_uuid = UUID(coverage_id)
        
        query = select(InsuranceCoverage).join(
            InsurancePolicy, InsuranceCoverage.policy_id == InsurancePolicy.id
        ).where(
            and_(
                InsuranceCoverage.id == coverage_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        coverage = result.scalar_one_or_none()
        
        if not coverage:
            raise HTTPException(status_code=404, detail="Coverage not found")
        
        await db.delete(coverage)
        await db.commit()
        
        logger.info(f"Removed coverage {coverage_id}")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error removing coverage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/policies/{policy_id}/documents/", response_model=List[InsuranceDocumentResponse], summary="List policy documents")
async def list_documents(
    policy_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List documents for a policy."""
    try:
        company_uuid = UUID(company_id)
        policy_uuid = UUID(policy_id)
        
        policy_query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.id == policy_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        policy_result = await db.execute(policy_query)
        if not policy_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Policy not found")
        
        query = select(InsuranceDocument).where(InsuranceDocument.policy_id == policy_uuid)
        result = await db.execute(query)
        documents = result.scalars().all()
        
        return [InsuranceDocumentResponse(**d.to_dict()) for d in documents]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/policies/{policy_id}/documents/", response_model=InsuranceDocumentResponse, status_code=status.HTTP_201_CREATED, summary="Upload document")
async def upload_document(
    policy_id: str,
    data: InsuranceDocumentCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document to a policy."""
    try:
        company_uuid = UUID(company_id)
        policy_uuid = UUID(policy_id)
        
        policy_query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.id == policy_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        policy_result = await db.execute(policy_query)
        if not policy_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Policy not found")
        
        document = InsuranceDocument(
            policy_id=policy_uuid,
            document_type=data.document_type.value,
            file_name=data.file_name,
            file_url=data.file_url,
            file_size=data.file_size,
            mime_type=data.mime_type
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        logger.info(f"Uploaded document {data.file_name} to policy {policy_id}")
        return InsuranceDocumentResponse(**document.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove document")
async def remove_document(
    document_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove a document."""
    try:
        company_uuid = UUID(company_id)
        document_uuid = UUID(document_id)
        
        query = select(InsuranceDocument).join(
            InsurancePolicy, InsuranceDocument.policy_id == InsurancePolicy.id
        ).where(
            and_(
                InsuranceDocument.id == document_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        await db.delete(document)
        await db.commit()
        
        logger.info(f"Removed document {document_id}")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error removing document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/claims/", response_model=InsuranceClaimListResponse, summary="List claims")
async def list_claims(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    policy_id: Optional[str] = Query(None, description="Filter by policy ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List insurance claims."""
    try:
        company_uuid = UUID(company_id)
        
        conditions = [
            InsuranceClaim.policy_id.in_(
                select(InsurancePolicy.id).where(InsurancePolicy.company_id == company_uuid)
            )
        ]
        
        if status_filter:
            conditions.append(InsuranceClaim.status == status_filter)
        if policy_id:
            conditions.append(InsuranceClaim.policy_id == UUID(policy_id))
        
        query = select(InsuranceClaim).where(and_(*conditions))
        query = query.order_by(desc(InsuranceClaim.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        claims = result.scalars().all()
        
        count_query = select(func.count(InsuranceClaim.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return InsuranceClaimListResponse(
            claims=[InsuranceClaimResponse(**c.to_dict()) for c in claims],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"Error listing claims: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/claims/{claim_id}", response_model=InsuranceClaimResponse, summary="Get claim details")
async def get_claim(
    claim_id: str,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get claim details."""
    try:
        company_uuid = UUID(company_id)
        claim_uuid = UUID(claim_id)
        
        query = select(InsuranceClaim).join(
            InsurancePolicy, InsuranceClaim.policy_id == InsurancePolicy.id
        ).where(
            and_(
                InsuranceClaim.id == claim_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        claim = result.scalar_one_or_none()
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        return InsuranceClaimResponse(**claim.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting claim: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/claims/", response_model=InsuranceClaimResponse, status_code=status.HTTP_201_CREATED, summary="Create claim")
async def create_claim(
    data: InsuranceClaimCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new insurance claim/sinistro."""
    try:
        company_uuid = UUID(company_id)
        policy_uuid = UUID(data.policy_id)
        
        policy_query = select(InsurancePolicy).where(
            and_(
                InsurancePolicy.id == policy_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        policy_result = await db.execute(policy_query)
        if not policy_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Policy not found")
        
        claim = InsuranceClaim(
            policy_id=policy_uuid,
            claim_number=data.claim_number,
            incident_date=data.incident_date,
            reported_date=data.reported_date,
            description=data.description,
            estimated_loss=data.estimated_loss,
            claimed_amount=data.claimed_amount,
            related_incident_id=UUID(data.related_incident_id) if data.related_incident_id else None,
            status="reported"
        )
        
        db.add(claim)
        await db.commit()
        await db.refresh(claim)
        
        logger.info(f"Created claim {claim.claim_number} for policy {data.policy_id}")
        return InsuranceClaimResponse(**claim.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating claim: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/claims/{claim_id}", response_model=InsuranceClaimResponse, summary="Update claim")
async def update_claim(
    claim_id: str,
    data: InsuranceClaimUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an insurance claim."""
    try:
        company_uuid = UUID(company_id)
        claim_uuid = UUID(claim_id)
        
        query = select(InsuranceClaim).join(
            InsurancePolicy, InsuranceClaim.policy_id == InsurancePolicy.id
        ).where(
            and_(
                InsuranceClaim.id == claim_uuid,
                InsurancePolicy.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        claim = result.scalar_one_or_none()
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        if data.claim_number is not None:
            claim.claim_number = data.claim_number
        if data.description is not None:
            claim.description = data.description
        if data.estimated_loss is not None:
            claim.estimated_loss = data.estimated_loss
        if data.claimed_amount is not None:
            claim.claimed_amount = data.claimed_amount
        if data.settled_amount is not None:
            claim.settled_amount = data.settled_amount
        if data.status is not None:
            claim.status = data.status.value
        if data.related_incident_id is not None:
            claim.related_incident_id = UUID(data.related_incident_id)
        
        await db.commit()
        await db.refresh(claim)
        
        logger.info(f"Updated claim {claim_id}")
        return InsuranceClaimResponse(**claim.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating claim: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
