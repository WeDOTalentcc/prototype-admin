"""
SoD (Segregation of Duties) Matrix API Endpoints.

Provides endpoints for:
- Role management
- Conflict definitions
- Violation tracking
- SoD matrix and statistics
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import Optional, List
from datetime import datetime
import logging
from uuid import UUID

from app.core.database import get_db
from app.models.observability import SoDRole, SoDConflict, SoDViolation
from app.shared.tenant_guard import get_verified_company_id
from app.schemas.sod_matrix import (
    SoDRoleResponse, SoDRoleListResponse, SoDRoleCreate, SoDRoleUpdate,
    SoDConflictResponse, SoDConflictListResponse, SoDConflictCreate, SoDExceptionApproval,
    SoDViolationResponse, SoDViolationListResponse, SoDViolationResolve,
    SoDMatrixResponse, SoDMatrixCell, SoDStats
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sod", tags=["sod-matrix"])


def role_to_response(role: SoDRole) -> dict:
    """Convert SoDRole model to response dict format."""
    return {
        "id": str(role.id),
        "company_id": str(role.company_id),
        "name": role.role_name,
        "description": role.department,
        "role_type": "standard",
        "permissions": role.permissions or [],
        "is_sensitive": role.is_critical,
        "is_active": True,
        "created_at": role.created_at.isoformat() if role.created_at else None,
        "updated_at": role.created_at.isoformat() if role.created_at else None
    }


def conflict_to_response(conflict: SoDConflict, role_a_name: str = None, role_b_name: str = None) -> dict:
    """Convert SoDConflict model to response dict format."""
    return {
        "id": str(conflict.id),
        "company_id": str(conflict.company_id),
        "role_a_id": str(conflict.role_a_id),
        "role_a_name": role_a_name,
        "role_b_id": str(conflict.role_b_id),
        "role_b_name": role_b_name,
        "conflict_description": conflict.description,
        "severity": conflict.risk_level,
        "status": "exception_approved" if conflict.is_approved_exception else "active",
        "mitigation_control": None,
        "exception_approved_by": str(conflict.approved_by) if conflict.approved_by else None,
        "exception_approved_at": conflict.approved_at.isoformat() if conflict.approved_at else None,
        "exception_expires_at": conflict.review_required_by.isoformat() if conflict.review_required_by else None,
        "exception_reason": conflict.approval_reason,
        "created_at": conflict.created_at.isoformat() if conflict.created_at else None,
        "updated_at": conflict.created_at.isoformat() if conflict.created_at else None
    }


def violation_to_response(violation: SoDViolation) -> dict:
    """Convert SoDViolation model to response dict format."""
    return {
        "id": str(violation.id),
        "company_id": None,
        "conflict_id": str(violation.conflict_id),
        "user_id": str(violation.user_id),
        "user_name": violation.user_name,
        "detected_at": violation.detected_at.isoformat() if violation.detected_at else None,
        "status": "resolved" if violation.resolved else "open",
        "resolved_at": violation.resolved_at.isoformat() if violation.resolved_at else None,
        "resolved_by": None,
        "resolution_notes": violation.resolution_notes
    }


@router.get("/stats", response_model=SoDStats, summary="Get SoD statistics")
async def get_sod_stats(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated SoD statistics for the company."""
    try:
        company_uuid = UUID(company_id)
        
        roles_query = select(SoDRole).where(SoDRole.company_id == company_uuid)
        roles_result = await db.execute(roles_query)
        roles = roles_result.scalars().all()
        
        conflicts_query = select(SoDConflict).where(SoDConflict.company_id == company_uuid)
        conflicts_result = await db.execute(conflicts_query)
        conflicts = conflicts_result.scalars().all()
        
        conflict_ids = [c.id for c in conflicts]
        
        violations = []
        if conflict_ids:
            violations_query = select(SoDViolation).where(SoDViolation.conflict_id.in_(conflict_ids))
            violations_result = await db.execute(violations_query)
            violations = violations_result.scalars().all()
        
        sensitive_roles = len([r for r in roles if r.is_critical])
        active_conflicts = len([c for c in conflicts if not c.is_approved_exception])
        approved_exceptions = len([c for c in conflicts if c.is_approved_exception])
        open_violations = len([v for v in violations if not v.resolved])
        resolved_violations = len([v for v in violations if v.resolved])
        
        by_severity = {}
        for conflict in conflicts:
            sev = conflict.risk_level or "unknown"
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return SoDStats(
            total_roles=len(roles),
            sensitive_roles=sensitive_roles,
            total_conflicts=len(conflicts),
            active_conflicts=active_conflicts,
            approved_exceptions=approved_exceptions,
            total_violations=len(violations),
            open_violations=open_violations,
            resolved_violations=resolved_violations,
            by_severity=by_severity
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting SoD stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matrix", response_model=SoDMatrixResponse, summary="Get SoD matrix")
async def get_sod_matrix(
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get SoD matrix showing conflicts between roles."""
    try:
        company_uuid = UUID(company_id)
        
        roles_query = select(SoDRole).where(SoDRole.company_id == company_uuid)
        roles_result = await db.execute(roles_query)
        roles = roles_result.scalars().all()
        
        conflicts_query = select(SoDConflict).where(SoDConflict.company_id == company_uuid)
        conflicts_result = await db.execute(conflicts_query)
        conflicts = conflicts_result.scalars().all()
        
        conflict_map = {}
        for conflict in conflicts:
            key = (str(conflict.role_a_id), str(conflict.role_b_id))
            conflict_map[key] = conflict
            reverse_key = (str(conflict.role_b_id), str(conflict.role_a_id))
            conflict_map[reverse_key] = conflict
        
        matrix_cells = []
        for role_a in roles:
            for role_b in roles:
                if str(role_a.id) >= str(role_b.id):
                    continue
                
                key = (str(role_a.id), str(role_b.id))
                conflict = conflict_map.get(key)
                
                matrix_cells.append(SoDMatrixCell(
                    role_a_id=str(role_a.id),
                    role_a_name=role_a.role_name,
                    role_b_id=str(role_b.id),
                    role_b_name=role_b.role_name,
                    has_conflict=conflict is not None,
                    conflict_id=str(conflict.id) if conflict else None,
                    severity=conflict.risk_level if conflict else None,
                    status="exception_approved" if conflict and conflict.is_approved_exception else "active" if conflict else None
                ))
        
        return SoDMatrixResponse(
            roles=[SoDRoleResponse(**role_to_response(r)) for r in roles],
            conflicts=matrix_cells,
            total_conflicts=len(conflicts)
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error getting SoD matrix: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles", response_model=SoDRoleListResponse, summary="List roles")
async def list_roles(
    role_type: Optional[str] = Query(None, description="Filter by role type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List roles with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [SoDRole.company_id == company_uuid]
        
        query = select(SoDRole).where(and_(*conditions))
        query = query.order_by(desc(SoDRole.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        roles = result.scalars().all()
        
        count_query = select(func.count(SoDRole.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return SoDRoleListResponse(
            roles=[SoDRoleResponse(**role_to_response(r)) for r in roles],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing roles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roles", response_model=SoDRoleResponse, status_code=status.HTTP_201_CREATED, summary="Create role")
async def create_role(
    data: SoDRoleCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new role."""
    try:
        company_uuid = UUID(company_id)
        
        role = SoDRole(
            company_id=company_uuid,
            role_code=f"ROLE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            role_name=data.name,
            department=data.description,
            permissions=data.permissions or [],
            is_critical=data.is_sensitive
        )
        
        db.add(role)
        await db.commit()
        await db.refresh(role)
        
        logger.info(f"Created role {role.id} for company {company_id}")
        return SoDRoleResponse(**role_to_response(role))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/roles/{role_id}", response_model=SoDRoleResponse, summary="Update role")
async def update_role(
    role_id: str,
    data: SoDRoleUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing role."""
    try:
        company_uuid = UUID(company_id)
        role_uuid = UUID(role_id)
        
        query = select(SoDRole).where(
            and_(
                SoDRole.id == role_uuid,
                SoDRole.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        role = result.scalar_one_or_none()
        
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        
        if data.name is not None:
            role.role_name = data.name
        if data.description is not None:
            role.department = data.description
        if data.permissions is not None:
            role.permissions = data.permissions
        if data.is_sensitive is not None:
            role.is_critical = data.is_sensitive
        
        await db.commit()
        await db.refresh(role)
        
        logger.info(f"Updated role {role_id}")
        return SoDRoleResponse(**role_to_response(role))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating role: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conflicts", response_model=SoDConflictListResponse, summary="List conflicts")
async def list_conflicts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List conflicts with optional filters."""
    try:
        company_uuid = UUID(company_id)
        conditions = [SoDConflict.company_id == company_uuid]
        
        if severity:
            conditions.append(SoDConflict.risk_level == severity)
        if status_filter:
            if status_filter == "exception_approved":
                conditions.append(SoDConflict.is_approved_exception == True)
            elif status_filter == "active":
                conditions.append(SoDConflict.is_approved_exception == False)
        
        query = select(SoDConflict).where(and_(*conditions))
        query = query.order_by(desc(SoDConflict.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        conflicts = conflicts_result = result.scalars().all()
        
        count_query = select(func.count(SoDConflict.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        role_ids = set()
        for conflict in conflicts:
            role_ids.add(conflict.role_a_id)
            role_ids.add(conflict.role_b_id)
        
        role_names = {}
        if role_ids:
            roles_query = select(SoDRole).where(SoDRole.id.in_(role_ids))
            roles_result = await db.execute(roles_query)
            for role in roles_result.scalars().all():
                role_names[str(role.id)] = role.role_name
        
        conflict_responses = []
        for conflict in conflicts:
            resp = conflict_to_response(
                conflict,
                role_a_name=role_names.get(str(conflict.role_a_id)),
                role_b_name=role_names.get(str(conflict.role_b_id))
            )
            conflict_responses.append(SoDConflictResponse(**resp))
        
        return SoDConflictListResponse(
            conflicts=conflict_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing conflicts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conflicts", response_model=SoDConflictResponse, status_code=status.HTTP_201_CREATED, summary="Create conflict")
async def create_conflict(
    data: SoDConflictCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conflict definition."""
    try:
        company_uuid = UUID(company_id)
        role_a_uuid = UUID(data.role_a_id)
        role_b_uuid = UUID(data.role_b_id)
        
        role_a_query = select(SoDRole).where(
            and_(SoDRole.id == role_a_uuid, SoDRole.company_id == company_uuid)
        )
        role_a_result = await db.execute(role_a_query)
        role_a = role_a_result.scalar_one_or_none()
        
        role_b_query = select(SoDRole).where(
            and_(SoDRole.id == role_b_uuid, SoDRole.company_id == company_uuid)
        )
        role_b_result = await db.execute(role_b_query)
        role_b = role_b_result.scalar_one_or_none()
        
        if not role_a:
            raise HTTPException(status_code=404, detail="Role A not found")
        if not role_b:
            raise HTTPException(status_code=404, detail="Role B not found")
        
        conflict = SoDConflict(
            company_id=company_uuid,
            role_a_id=role_a_uuid,
            role_b_id=role_b_uuid,
            conflict_type="authorization_execution",
            description=data.conflict_description,
            risk_level=data.severity.value,
            is_approved_exception=False
        )
        
        db.add(conflict)
        await db.commit()
        await db.refresh(conflict)
        
        logger.info(f"Created conflict {conflict.id} for company {company_id}")
        return SoDConflictResponse(**conflict_to_response(conflict, role_a.role_name, role_b.role_name))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating conflict: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conflicts/{conflict_id}/approve", response_model=SoDConflictResponse, summary="Approve exception")
async def approve_exception(
    conflict_id: str,
    data: SoDExceptionApproval,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Approve an exception for a conflict."""
    try:
        company_uuid = UUID(company_id)
        conflict_uuid = UUID(conflict_id)
        
        query = select(SoDConflict).where(
            and_(
                SoDConflict.id == conflict_uuid,
                SoDConflict.company_id == company_uuid
            )
        )
        result = await db.execute(query)
        conflict = result.scalar_one_or_none()
        
        if not conflict:
            raise HTTPException(status_code=404, detail="Conflict not found")
        
        conflict.is_approved_exception = True
        conflict.approval_reason = data.reason
        conflict.approved_at = datetime.utcnow()
        if data.expires_at:
            conflict.review_required_by = data.expires_at
        
        await db.commit()
        await db.refresh(conflict)
        
        role_a_query = select(SoDRole).where(SoDRole.id == conflict.role_a_id)
        role_a_result = await db.execute(role_a_query)
        role_a = role_a_result.scalar_one_or_none()
        
        role_b_query = select(SoDRole).where(SoDRole.id == conflict.role_b_id)
        role_b_result = await db.execute(role_b_query)
        role_b = role_b_result.scalar_one_or_none()
        
        logger.info(f"Approved exception for conflict {conflict_id}")
        return SoDConflictResponse(**conflict_to_response(
            conflict,
            role_a.role_name if role_a else None,
            role_b.role_name if role_b else None
        ))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conflict ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error approving exception: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations", response_model=SoDViolationListResponse, summary="List violations")
async def list_violations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List violations with optional filters."""
    try:
        company_uuid = UUID(company_id)
        
        conflicts_query = select(SoDConflict.id).where(SoDConflict.company_id == company_uuid)
        conflicts_result = await db.execute(conflicts_query)
        conflict_ids = [c for c in conflicts_result.scalars().all()]
        
        if not conflict_ids:
            return SoDViolationListResponse(violations=[], total=0, limit=limit, offset=offset)
        
        conditions = [SoDViolation.conflict_id.in_(conflict_ids)]
        
        if status_filter:
            if status_filter == "resolved":
                conditions.append(SoDViolation.resolved == True)
            elif status_filter == "open":
                conditions.append(SoDViolation.resolved == False)
        
        query = select(SoDViolation).where(and_(*conditions))
        query = query.order_by(desc(SoDViolation.detected_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        violations = result.scalars().all()
        
        count_query = select(func.count(SoDViolation.id)).where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return SoDViolationListResponse(
            violations=[SoDViolationResponse(**violation_to_response(v)) for v in violations],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid company ID format")
    except Exception as e:
        logger.error(f"Error listing violations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/violations/{violation_id}/resolve", response_model=SoDViolationResponse, summary="Resolve violation")
async def resolve_violation(
    violation_id: str,
    data: SoDViolationResolve,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Resolve a violation."""
    try:
        company_uuid = UUID(company_id)
        violation_uuid = UUID(violation_id)
        
        conflicts_query = select(SoDConflict.id).where(SoDConflict.company_id == company_uuid)
        conflicts_result = await db.execute(conflicts_query)
        conflict_ids = [c for c in conflicts_result.scalars().all()]
        
        query = select(SoDViolation).where(
            and_(
                SoDViolation.id == violation_uuid,
                SoDViolation.conflict_id.in_(conflict_ids)
            )
        )
        result = await db.execute(query)
        violation = result.scalar_one_or_none()
        
        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")
        
        violation.resolved = True
        violation.resolved_at = datetime.utcnow()
        violation.resolution_notes = data.resolution_notes
        
        await db.commit()
        await db.refresh(violation)
        
        logger.info(f"Resolved violation {violation_id}")
        return SoDViolationResponse(**violation_to_response(violation))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid violation ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error resolving violation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
