"""
Global Policies API Endpoints.

Provides endpoints for:
- Listing and filtering global policies
- Retrieving individual policies with audit history
- Updating policy values
- Viewing audit history
- Listing categories with counts
- Seeding default policies
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from typing import Optional
from datetime import datetime
import logging
from uuid import UUID

from app.core.database import get_db
from app.models.global_policies import PlatformPolicy, PlatformPolicyAuditLog, DEFAULT_POLICIES
from app.schemas.global_policies import (
    PolicyResponse, PolicyListResponse, PolicyWithHistoryResponse,
    PolicyUpdate, PolicyAuditLogResponse, PolicyAuditLogListResponse,
    CategoryCount, CategoryListResponse, SeedPoliciesResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/global-policies", tags=["global-policies"])


def get_user_id_from_header(
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Optional[str]:
    """Extract user ID from header if present."""
    if x_user_id:
        try:
            UUID(x_user_id)
            return x_user_id
        except ValueError:
            pass
    return None


@router.get("", response_model=PolicyListResponse, summary="List all policies")
async def list_policies(
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    limit: int = Query(100, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """List all global policies with optional filtering."""
    try:
        conditions = []
        
        if category:
            conditions.append(PlatformPolicy.category == category)
        if is_active is not None:
            conditions.append(PlatformPolicy.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            conditions.append(
                PlatformPolicy.name.ilike(search_term) | PlatformPolicy.description.ilike(search_term)
            )
        
        query = select(PlatformPolicy)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(PlatformPolicy.category, PlatformPolicy.name)
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        policies = result.scalars().all()
        
        count_query = select(func.count(PlatformPolicy.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return PolicyListResponse(
            policies=[PolicyResponse(**p.to_dict()) for p in policies],
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error listing policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=CategoryListResponse, summary="List all categories with counts")
async def list_categories(
    db: AsyncSession = Depends(get_db)
):
    """List all policy categories with their counts."""
    try:
        query = select(
            PlatformPolicy.category,
            func.count(PlatformPolicy.id).label("count"),
            func.count(PlatformPolicy.id).filter(PlatformPolicy.is_active == True).label("active_count")
        ).group_by(PlatformPolicy.category)
        
        result = await db.execute(query)
        rows = result.all()
        
        categories = [
            CategoryCount(
                category=row[0],
                count=row[1],
                active_count=row[2]
            )
            for row in rows
        ]
        
        total_policies = sum(c.count for c in categories)
        
        return CategoryListResponse(
            categories=categories,
            total_policies=total_policies
        )
    except Exception as e:
        logger.error(f"Error listing categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{policy_id}", response_model=PolicyWithHistoryResponse, summary="Get single policy with audit history")
async def get_policy(
    policy_id: str,
    include_history: bool = Query(True, description="Include audit history"),
    history_limit: int = Query(10, ge=1, le=100, description="Max history entries"),
    db: AsyncSession = Depends(get_db)
):
    """Get a single policy with optional audit history."""
    try:
        policy_uuid = UUID(policy_id)
        
        query = select(PlatformPolicy).where(PlatformPolicy.id == policy_uuid)
        result = await db.execute(query)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        policy_data = policy.to_dict()
        
        if include_history:
            history_query = select(PlatformPolicyAuditLog).where(
                PlatformPolicyAuditLog.policy_id == policy_uuid
            ).order_by(desc(PlatformPolicyAuditLog.changed_at)).limit(history_limit)
            
            history_result = await db.execute(history_query)
            history_logs = history_result.scalars().all()
            policy_data["audit_history"] = [
                PolicyAuditLogResponse(**log.to_dict()) for log in history_logs
            ]
        else:
            policy_data["audit_history"] = []
        
        return PolicyWithHistoryResponse(**policy_data)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid policy ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{policy_id}", response_model=PolicyResponse, summary="Update policy value")
async def update_policy(
    policy_id: str,
    data: PolicyUpdate,
    user_id: Optional[str] = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db)
):
    """Update a policy value and create an audit log entry."""
    try:
        policy_uuid = UUID(policy_id)
        
        query = select(PlatformPolicy).where(PlatformPolicy.id == policy_uuid)
        result = await db.execute(query)
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        if policy.value_type == "number":
            try:
                value = float(data.current_value)
                if policy.min_value is not None and value < float(policy.min_value):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Value must be at least {policy.min_value}"
                    )
                if policy.max_value is not None and value > float(policy.max_value):
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Value must be at most {policy.max_value}"
                    )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid number value")
        
        elif policy.value_type == "boolean":
            if data.current_value.lower() not in ("true", "false"):
                raise HTTPException(status_code=400, detail="Value must be 'true' or 'false'")
        
        elif policy.value_type == "select" and policy.options:
            if data.current_value not in policy.options:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Value must be one of: {', '.join(policy.options)}"
                )
        
        previous_value = policy.current_value
        
        audit_log = PlatformPolicyAuditLog(
            policy_id=policy_uuid,
            previous_value=previous_value,
            new_value=data.current_value,
            changed_by=UUID(user_id) if user_id else None,
            change_reason=data.change_reason
        )
        db.add(audit_log)
        
        policy.current_value = data.current_value
        policy.updated_by = UUID(user_id) if user_id else None
        
        await db.commit()
        await db.refresh(policy)
        
        return PolicyResponse(**policy.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{policy_id}/history", response_model=PolicyAuditLogListResponse, summary="Get audit history for a policy")
async def get_policy_history(
    policy_id: str,
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db)
):
    """Get the complete audit history for a specific policy."""
    try:
        policy_uuid = UUID(policy_id)
        
        policy_check = select(PlatformPolicy.id).where(PlatformPolicy.id == policy_uuid)
        policy_result = await db.execute(policy_check)
        if not policy_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Policy not found")
        
        query = select(PlatformPolicyAuditLog).where(
            PlatformPolicyAuditLog.policy_id == policy_uuid
        ).order_by(desc(PlatformPolicyAuditLog.changed_at))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        count_query = select(func.count(PlatformPolicyAuditLog.id)).where(
            PlatformPolicyAuditLog.policy_id == policy_uuid
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return PolicyAuditLogListResponse(
            logs=[PolicyAuditLogResponse(**log.to_dict()) for log in logs],
            total=total,
            limit=limit,
            offset=offset
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid policy ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed", response_model=SeedPoliciesResponse, summary="Seed default policies")
async def seed_default_policies(
    db: AsyncSession = Depends(get_db)
):
    """Seed the database with default policies. Skips existing policies."""
    try:
        created = 0
        skipped = 0
        
        for policy_data in DEFAULT_POLICIES:
            existing = await db.execute(
                select(PlatformPolicy).where(PlatformPolicy.name == policy_data["name"])
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue
            
            policy = PlatformPolicy(
                name=policy_data["name"],
                description=policy_data.get("description"),
                category=policy_data["category"],
                value_type=policy_data["value_type"],
                current_value=policy_data["current_value"],
                unit=policy_data.get("unit"),
                min_value=policy_data.get("min_value"),
                max_value=policy_data.get("max_value"),
                options=policy_data.get("options"),
                is_active=True
            )
            db.add(policy)
            created += 1
        
        await db.commit()
        
        return SeedPoliciesResponse(
            created=created,
            skipped=skipped,
            message=f"Created {created} policies, skipped {skipped} existing policies"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
