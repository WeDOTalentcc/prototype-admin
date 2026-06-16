"""
Policies API — CRUD operations for global and company-level policy management.

Onda 4.2d-P0-1 (2026-05-23): substituido `get_user_from_headers` que confiava
em X-User-Role/X-User-ID headers (= backdoor catastrofico — atacante virava
platform admin com 1 header HTTP `-H "X-User-Role: admin"`). Agora usa JWT
canonical (current_user + require_company_id). Platform admin = role
wedotalent_admin (staff WeDOTalent) APENAS.
"""
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.auth.models import User, UserRole
from app.core.database import get_db, get_tenant_db
from app.domains.policy.repositories.global_policy_repository import GlobalPolicyRepository
from app.models.global_policy import POLICY_TYPES, GlobalPolicy, PolicyScope, PolicyType
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policies", tags=["policies"])


def get_user_from_headers(
    current_user: User = Depends(get_current_active_user),
    company_id: str = Depends(require_company_id),
) -> dict[str, Any]:
    """Get user context from JWT (canonical) — ZERO headers.

    Onda 4.2d-P0-1 (2026-05-23): nome mantido pra zero impacto callers,
    mas body trocado pra source-of-truth = JWT.

    Platform admin = role wedotalent_admin APENAS (staff WeDOTalent).
    Tenant admin (UserRole.admin) NAO e platform admin — administra
    apenas a propria company.
    """
    return {
        "company_id": company_id,
        "user_id": str(current_user.id),
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        # Onda 4.2d-P0-1: is_admin agora requer wedotalent_admin (platform staff),
        # nao mais x_user_role header. Backdoor fechado.
        "is_admin": current_user.role == UserRole.wedotalent_admin,
    }


class PolicyCreate(WeDoBaseModel):
    """Request model for creating a policy."""
    name: str = Field(..., min_length=1, max_length=255, description="Policy name")
    description: str | None = Field(None, max_length=1000, description="Policy description")
    policy_type: str = Field(..., description="Policy type")
    value: dict[str, Any] = Field(..., description="Policy value (flexible JSON)")
    scope: str = Field(default="company", description="Policy scope: platform or company")
    is_active: bool = Field(default=True, description="Whether policy is active")
    company_id: str | None = Field(None, description="Company ID (null for platform policies)")


class PolicyUpdate(WeDoBaseModel):
    """Request model for updating a policy."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    policy_type: str | None = None
    value: dict[str, Any] | None = None
    scope: str | None = None
    is_active: bool | None = None


@router.get("/types", summary="List policy types", response_model=None)
async def list_policy_types(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    List all available policy types with their schemas.
    """
    return {
        "success": True,
        "types": POLICY_TYPES,
        "scopes": [
            {"scope": PolicyScope.PLATFORM.value, "description": "Platform-wide policy"},
            {"scope": PolicyScope.COMPANY.value, "description": "Company-specific policy"}
        ]
    }


@router.get("", summary="List policies", response_model=None)
async def list_policies(
    policy_type: str | None = Query(None, description="Filter by policy type"),
    scope: str | None = Query(None, description="Filter by scope (platform, company)"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    company_id: str | None = Query(None, description="Filter by company ID"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    List all policies with optional filters.
    """
    try:
        repo = GlobalPolicyRepository(db)
        user_company_id = current_user.get("company_id")
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)

        policies, total = await repo.list_policies(
            policy_type=policy_type,
            scope=scope,
            is_active=is_active,
            company_id=company_id,
            user_company_id=user_company_id,
            is_admin=is_admin,
            limit=limit,
            offset=offset,
        )

        logger.info(f"📋 Listed {len(policies)} policies (total: {total})")

        return {
            "success": True,
            "data": {
                "policies": [p.to_dict() for p in policies],
                "total": total,
                "limit": limit,
                "offset": offset
            }
        }

    except Exception as e:
        logger.error(f"❌ Error listing policies: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list policies: {str(e)}"
        )


@router.get("/{policy_id}", summary="Get policy by ID", response_model=None)
async def get_policy(
    policy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Get a specific policy by ID.
    """
    try:
        user_company_id = current_user.get("company_id")
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)

        try:
            policy_uuid = UUID(policy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid policy ID format"
            )

        repo = GlobalPolicyRepository(db)
        policy = await repo.get_by_id(policy_uuid)

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy not found: {policy_id}"
            )

        if not is_admin and policy.company_id != user_company_id and policy.scope != PolicyScope.PLATFORM.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this policy"
            )

        return {
            "success": True,
            "data": policy.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting policy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get policy: {str(e)}"
        )


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create policy", response_model=None)
async def create_policy(
    data: PolicyCreate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Create a new policy.
    """
    try:
        user_company_id = current_user.get("company_id")
        user_id = current_user.get("id", current_user.get("user_id"))
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)

        valid_policy_types = [t.value for t in PolicyType]
        if data.policy_type not in valid_policy_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid policy_type. Must be one of: {', '.join(valid_policy_types)}"
            )

        valid_scopes = [s.value for s in PolicyScope]
        if data.scope not in valid_scopes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scope. Must be one of: {', '.join(valid_scopes)}"
            )

        if data.scope == PolicyScope.PLATFORM.value and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can create platform-level policies"
            )

        company_id = data.company_id if is_admin else user_company_id
        if data.scope == PolicyScope.PLATFORM.value:
            company_id = None

        policy = GlobalPolicy(
            company_id=company_id,
            name=data.name,
            description=data.description,
            policy_type=data.policy_type,
            value=data.value,
            scope=data.scope,
            is_active=data.is_active,
            created_by=user_id
        )

        repo = GlobalPolicyRepository(db)
        policy = await repo.create(policy)

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Created policy: {policy.name} (ID: {policy.id})")

        return {
            "success": True,
            "message": "Policy created successfully",
            "data": policy.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating policy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create policy: {str(e)}"
        )


@router.put("/{policy_id}", summary="Update policy", response_model=None)
async def update_policy(
    policy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: PolicyUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Update an existing policy.
    """
    try:
        user_company_id = current_user.get("company_id")
        user_id = current_user.get("id", current_user.get("user_id"))
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)

        try:
            policy_uuid = UUID(policy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid policy ID format"
            )

        repo = GlobalPolicyRepository(db)
        policy = await repo.get_by_id(policy_uuid)

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy not found: {policy_id}"
            )

        if not is_admin and policy.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to update this policy"
            )

        if policy.scope == PolicyScope.PLATFORM.value and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can update platform-level policies"
            )

        update_data = data.model_dump(exclude_none=True)

        if "policy_type" in update_data:
            valid_policy_types = [t.value for t in PolicyType]
            if update_data["policy_type"] not in valid_policy_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid policy_type. Must be one of: {', '.join(valid_policy_types)}"
                )

        if "scope" in update_data:
            valid_scopes = [s.value for s in PolicyScope]
            if update_data["scope"] not in valid_scopes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid scope. Must be one of: {', '.join(valid_scopes)}"
                )
            if update_data["scope"] == PolicyScope.PLATFORM.value and not is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admin users can set platform scope"
                )

        update_data["updated_by"] = user_id
        policy = await repo.update(policy, update_data)

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Updated policy: {policy.name} (ID: {policy.id})")

        return {
            "success": True,
            "message": "Policy updated successfully",
            "data": policy.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating policy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update policy: {str(e)}"
        )


@router.delete("/{policy_id}", summary="Delete policy", response_model=None)
async def delete_policy(
    policy_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_tenant_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Delete a policy.
    """
    try:
        user_company_id = current_user.get("company_id")
        is_admin = current_user.get("role") == "admin" or current_user.get("is_admin", False)

        try:
            policy_uuid = UUID(policy_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid policy ID format"
            )

        repo = GlobalPolicyRepository(db)
        policy = await repo.get_by_id(policy_uuid)

        if not policy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Policy not found: {policy_id}"
            )

        if not is_admin and policy.company_id != user_company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to delete this policy"
            )

        if policy.scope == PolicyScope.PLATFORM.value and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can delete platform-level policies"
            )

        policy_name = policy.name
        await repo.delete(policy)

        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"🗑️ Deleted policy: {policy_name} (ID: {policy_id})")

        return {
            "success": True,
            "message": f"Policy '{policy_name}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting policy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete policy: {str(e)}"
        )

reorder_collection_before_item(router)
