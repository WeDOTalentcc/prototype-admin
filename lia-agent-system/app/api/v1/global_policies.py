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
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.policy.repositories.global_policy_repository import GlobalPolicyRepository  # DEPRECATED-IMPORT-EXEMPT: V1 API canonical (PlatformPolicy/GlobalPolicy schema — app.domains.policy é canonical, hiring_policy não cobre platform policies)
from app.models.global_policies import PlatformPolicy
from app.schemas.global_policies import (
    CategoryCount,
    CategoryListResponse,
    PolicyAuditLogListResponse,
    PolicyAuditLogResponse,
    PolicyListResponse,
    PolicyResponse,
    PolicyUpdate,
    PolicyWithHistoryResponse,
    SeedPoliciesResponse,
)
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/global-policies", tags=["global-policies"])


def get_user_id_from_header(
    x_user_id: str | None = Header(None, alias="X-User-ID"),
) -> str | None:
    if x_user_id:
        try:
            UUID(x_user_id)
            return x_user_id
        except ValueError:
            pass
    return None


@router.get("", response_model=PolicyListResponse)
async def list_policies(
    category: str | None = Query(None),
    is_active: bool | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all global policies with optional filtering."""
    try:
        conditions = []
        if category:
            conditions.append(PlatformPolicy.category == category)
        if is_active is not None:
            conditions.append(PlatformPolicy.is_active == is_active)
        if search:
            term = f"%{search}%"
            conditions.append(
                PlatformPolicy.name.ilike(term) | PlatformPolicy.description.ilike(term)
            )
        repo = GlobalPolicyRepository(db)
        policies, total = await repo.list_policies(conditions, limit=limit, offset=offset)
        return PolicyListResponse(
            policies=[PolicyResponse(**p.to_dict()) for p in policies],
            total=total, limit=limit, offset=offset,
        )
    except Exception as e:
        logger.error(f"Error listing policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all policy categories with counts."""
    try:
        repo = GlobalPolicyRepository(db)
        rows = await repo.list_categories()
        categories = [CategoryCount(category=r[0], count=r[1], active_count=r[2]) for r in rows]
        return CategoryListResponse(
            categories=categories, total_policies=sum(c.count for c in categories)
        )
    except Exception as e:
        logger.error(f"Error listing categories: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{policy_id}", response_model=PolicyWithHistoryResponse)
async def get_policy(
    policy_id: str,
    include_history: bool = Query(True),
    history_limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get a single policy with optional audit history."""
    try:
        policy_uuid = UUID(policy_id)
        repo = GlobalPolicyRepository(db)
        policy = await repo.get_by_id(policy_uuid)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        policy_data = policy.to_dict()
        if include_history:
            logs, _ = await repo.get_history(policy_uuid, limit=history_limit)
            policy_data["audit_history"] = [PolicyAuditLogResponse(**log.to_dict()) for log in logs]
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


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: str,
    data: PolicyUpdate,
    user_id: str | None = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Update a policy value and create an audit log entry."""
    try:
        policy_uuid = UUID(policy_id)
        repo = GlobalPolicyRepository(db)
        policy = await repo.get_by_id(policy_uuid)
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")

        # Validate value
        if policy.value_type == "number":
            try:
                value = float(data.current_value)
                if policy.min_value is not None and value < float(policy.min_value):
                    raise HTTPException(status_code=400, detail=f"Value must be at least {policy.min_value}")
                if policy.max_value is not None and value > float(policy.max_value):
                    raise HTTPException(status_code=400, detail=f"Value must be at most {policy.max_value}")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid number value")
        elif policy.value_type == "boolean":
            if data.current_value.lower() not in ("true", "false"):
                raise HTTPException(status_code=400, detail="Value must be 'true' or 'false'")
        elif policy.value_type == "select" and policy.options:
            if data.current_value not in policy.options:
                raise HTTPException(status_code=400, detail=f"Value must be one of: {', '.join(policy.options)}")

        uid = UUID(user_id) if user_id else None
        policy = await repo.update_policy(policy, data.current_value, uid, data.change_reason)
        return PolicyResponse(**policy.to_dict())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{policy_id}/history", response_model=PolicyAuditLogListResponse)
async def get_policy_history(
    policy_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get the complete audit history for a specific policy."""
    try:
        policy_uuid = UUID(policy_id)
        repo = GlobalPolicyRepository(db)
        if not await repo.get_by_id(policy_uuid):
            raise HTTPException(status_code=404, detail="Policy not found")
        logs, total = await repo.get_history(policy_uuid, limit=limit, offset=offset)
        return PolicyAuditLogListResponse(
            logs=[PolicyAuditLogResponse(**log.to_dict()) for log in logs],
            total=total, limit=limit, offset=offset,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid policy ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting policy history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed", response_model=SeedPoliciesResponse)
async def seed_default_policies(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Seed the database with default policies. Skips existing policies."""
    try:
        repo = GlobalPolicyRepository(db)
        created, skipped = await repo.seed_defaults()
        return SeedPoliciesResponse(
            created=created,
            skipped=skipped,
            message=f"Created {created} policies, skipped {skipped} existing policies",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
