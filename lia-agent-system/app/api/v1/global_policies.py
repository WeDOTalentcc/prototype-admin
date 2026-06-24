"""
Global Policies API — platform-wide policy management.

Provides endpoints for:
- Listing and filtering global policies (all authenticated users)
- Retrieving individual policies with audit history
- Updating policy values (wedotalent_admin ONLY — Onda 4.2d-P0-5)
- Viewing audit history
- Listing categories with counts
- Seeding default policies (wedotalent_admin ONLY — Onda 4.2d-P0-7)

Onda 4.2d-P0-5,6,7 (2026-05-23): regulatory hardening:
- Mutations (PUT/SEED) gated por wedotalent_admin (staff WeDOTalent apenas).
- user_id agora vem do JWT, nao mais X-User-ID header forjavel
  (fechou SOX non-repudiation gap em platform_policy_audit_logs).
"""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.models import User, UserRole
from app.core.database import get_db, get_tenant_db
from app.domains.policy.repositories.global_policy_repository import GlobalPolicyRepository
from app.models.global_policies import PlatformPolicy
from app.schemas.global_policies import (
    PolicyCategoryCount,
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
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.shared.errors import LIAError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/global-policies", tags=["global-policies"])


def require_wedotalent_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Onda 4.2d-P0-5 (2026-05-23): gate pra mutacoes em platform globals.

    Tenant admin nao pode mutar platform globals — apenas staff WeDOTalent.
    """
    if current_user.role != UserRole.wedotalent_admin:
        raise HTTPException(
            status_code=403,
            detail=(
                "Only WeDOTalent staff can modify platform-global policies. "
                "Contact WeDOTalent support to request changes."
            ),
        )
    return current_user


def get_user_id_from_header(
    current_user: User = Depends(get_current_active_user),
) -> str:
    """Get user ID from JWT (NO header).

    Onda 4.2d-P0-6 (2026-05-23): antes lia X-User-ID header forjavel,
    gravava no audit_log = quebrava SOX non-repudiation. Agora JWT-only.
    Nome mantido pra zero impacto callers.
    """
    return str(current_user.id)


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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing policies: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/categories", response_model=CategoryListResponse)
async def list_categories(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all policy categories with counts."""
    try:
        repo = GlobalPolicyRepository(db)
        rows = await repo.list_categories()
        categories = [PolicyCategoryCount(category=r[0], count=r[1], active_count=r[2]) for r in rows]
        return CategoryListResponse(
            categories=categories, total_policies=sum(c.count for c in categories)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing categories: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/{policy_id}", response_model=PolicyWithHistoryResponse)
async def get_policy(
    policy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
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
        raise LIAError(message="Erro interno do servidor")


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: PolicyUpdate,
    user_id: str = Depends(get_user_id_from_header),
    db: AsyncSession = Depends(get_tenant_db),
    # Onda 4.2d-P0-5 (2026-05-23): wedotalent_admin gate. Antes qualquer
    # tenant admin podia editar policy platform-global afetando TODAS empresas.
    _staff: User = Depends(require_wedotalent_admin),
    company_id: str = Depends(require_company_id),
):
    """Update a policy value and create an audit log entry (staff-only)."""
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
        raise LIAError(message="Erro interno do servidor")


@router.get("/{policy_id}/history", response_model=PolicyAuditLogListResponse)
async def get_policy_history(
    policy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
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
        raise LIAError(message="Erro interno do servidor")


@router.post("/seed", response_model=SeedPoliciesResponse)
async def seed_default_policies(
    db: AsyncSession = Depends(get_db),
    # Onda 4.2d-P0-7 (2026-05-23): wedotalent_admin gate. Antes qualquer
    # autenticado podia rodar seed, vandalizar policies platform-wide.
    _staff: User = Depends(require_wedotalent_admin),
    company_id: str = Depends(require_company_id),
):
    """Seed the database with default policies. Skips existing policies (staff-only)."""
    try:
        repo = GlobalPolicyRepository(db)
        created, skipped = await repo.seed_defaults()
        return SeedPoliciesResponse(
            created=created,
            skipped=skipped,
            message=f"Created {created} policies, skipped {skipped} existing policies",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding policies: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
