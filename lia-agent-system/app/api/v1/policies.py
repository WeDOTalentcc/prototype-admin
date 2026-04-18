"""
Global Policies API Endpoints.

Provides CRUD operations for global and company-level policy management.
"""
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.policy.repositories.global_policy_repository import GlobalPolicyRepository
from lia_models.global_policy import POLICY_TYPES, GlobalPolicy, PolicyScope, PolicyType
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN
from typing import Annotated
from fastapi import Path

# Task #489 — UUID-or-digit constraint for dual-ID path params,
# preventing static sibling routes from being shadowed by
# item handlers (Task #455-class bug).
_DualId = Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policies", tags=["policies"])


def get_user_from_headers(
    x_company_id: str | None = Header(None, alias="X-Company-ID"),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    x_user_role: str | None = Header(None, alias="X-User-Role")
) -> dict[str, Any]:
    """
    Get user context from request headers.
    Used for development and internal API calls.
    """
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company ID required. Please provide X-Company-ID header."
        )
    return {
        "company_id": x_company_id,
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin"
    }


class PolicyCreate(BaseModel):
    """Request model for creating a policy."""
    name: str = Field(..., min_length=1, max_length=255, description="Policy name")
    description: str | None = Field(None, max_length=1000, description="Policy description")
    policy_type: str = Field(..., description="Policy type")
    value: dict[str, Any] = Field(..., description="Policy value (flexible JSON)")
    scope: str = Field(default="company", description="Policy scope: platform or company")
    is_active: bool = Field(default=True, description="Whether policy is active")
    company_id: str | None = Field(None, description="Company ID (null for platform policies)")


class PolicyUpdate(BaseModel):
    """Request model for updating a policy."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    policy_type: str | None = None
    value: dict[str, Any] | None = None
    scope: str | None = None
    is_active: bool | None = None


@router.get("/types", summary="List policy types", response_model=None)
async def list_policy_types():
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
    db: AsyncSession = Depends(get_db)
):
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
    policy_id: _DualId,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
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
    db: AsyncSession = Depends(get_db)
):
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
    policy_id: _DualId,
    data: PolicyUpdate,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
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
    policy_id: _DualId,
    current_user: dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
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

# Task #489 — Keep collection-scoped routes ahead of item-scoped
# routes so a static sibling segment cannot be silently shadowed
# by an {*_id} handler (the Task #455 routing-shadowing bug).
from app.api.v1._path_patterns import reorder_collection_before_item as _reorder_collection_before_item  # noqa: E402

_reorder_collection_before_item(router)
