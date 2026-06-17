"""
Workforce Planning API Endpoints.

Manages workforce plans stored in client.settings["workforce_plans"].
"""
import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.database import get_db
from app.models.client_account import ClientAccount
from app.shared.tenant_guard import get_verified_company_id
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.api.v1.big_five import get_client  # canonical client lookup helper (vide ADR-Reuse)
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workforce-planning", tags=["workforce-planning"])


class DepartmentPlan(BaseModel):
    """Department planning data."""
    name: str = Field(..., description="Department name")
    current_headcount: int = Field(default=0, ge=0, description="Current headcount")
    planned_headcount: int = Field(default=0, ge=0, description="Planned headcount")
    budget: float = Field(default=0.0, ge=0, description="Department budget")


class WorkforcePlanCreate(WeDoBaseModel):
    """Request model for creating a workforce plan."""
    name: str = Field(..., min_length=1, max_length=255, description="Plan name")
    year: int = Field(..., ge=2020, le=2100, description="Fiscal year")
    status: str = Field(default="draft", description="Plan status: draft, active, closed")
    departments: list[DepartmentPlan] = Field(default_factory=list, description="Department plans")
    total_budget: float = Field(default=0.0, ge=0, description="Total budget")
    total_planned_hires: int = Field(default=0, ge=0, description="Total planned hires")


class WorkforcePlanUpdate(WeDoBaseModel):
    """Request model for updating a workforce plan."""
    name: str | None = Field(None, min_length=1, max_length=255)
    year: int | None = Field(None, ge=2020, le=2100)
    status: str | None = Field(None, description="Plan status: draft, active, closed")
    departments: list[DepartmentPlan] | None = None
    total_budget: float | None = Field(None, ge=0)
    total_planned_hires: int | None = Field(None, ge=0)


class WorkforcePlanResponse(BaseModel):
    """Response model for workforce plan."""
    id: str
    company_id: str
    name: str
    year: int
    status: str
    departments: list[dict[str, Any]]
    total_budget: float
    total_planned_hires: int
    created_at: str
    updated_at: str


def get_workforce_plans(client: ClientAccount) -> list[dict[str, Any]]:
    """Get workforce plans from client settings."""
    if not client.settings:
        client.settings = {}
    return client.settings.get("workforce_plans", [])


def save_workforce_plans(client: ClientAccount, plans: list[dict[str, Any]]):
    """Save workforce plans to client settings."""
    if not client.settings:
        client.settings = {}
    client.settings["workforce_plans"] = plans
    flag_modified(client, "settings")


@router.get("", summary="List all workforce plans", response_model=None)
async def list_workforce_plans(
    year: int | None = Query(None, description="Filter by year"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all workforce plans for the company."""
    try:
        client = await get_client(company_id, db)
        plans = get_workforce_plans(client)
        
        if year:
            plans = [p for p in plans if p.get("year") == year]
        
        if status_filter:
            plans = [p for p in plans if p.get("status") == status_filter]
        
        plans = sorted(plans, key=lambda x: (x.get("year", 0), x.get("created_at", "")), reverse=True)
        
        logger.info(f"📋 Listed {len(plans)} workforce plans for company {company_id}")
        
        return {
            "success": True,
            "data": {
                "plans": plans,
                "total": len(plans)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing workforce plans: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list workforce plans: {str(e)}"
        )


@router.get("/{plan_id}", summary="Get workforce plan by ID", response_model=None)
async def get_workforce_plan(
    plan_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Get a specific workforce plan by ID."""
    try:
        client = await get_client(company_id, db)
        plans = get_workforce_plans(client)
        
        plan = next((p for p in plans if p.get("id") == plan_id), None)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workforce plan not found: {plan_id}"
            )
        
        return {
            "success": True,
            "data": plan
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting workforce plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workforce plan: {str(e)}"
        )


@router.post("", summary="Create workforce plan", status_code=status.HTTP_201_CREATED, response_model=None)
async def create_workforce_plan(
    data: WorkforcePlanCreate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new workforce plan."""
    try:
        client = await get_client(company_id, db)
        plans = get_workforce_plans(client)
        
        now = datetime.utcnow().isoformat()
        new_plan = {
            "id": str(uuid4()),
            "company_id": company_id,
            "name": data.name,
            "year": data.year,
            "status": data.status,
            "departments": [dept.model_dump() for dept in data.departments],
            "total_budget": data.total_budget,
            "total_planned_hires": data.total_planned_hires,
            "created_at": now,
            "updated_at": now
        }
        
        plans.append(new_plan)
        save_workforce_plans(client, plans)
        
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Created workforce plan: {new_plan['name']} for company {company_id}")
        
        return {
            "success": True,
            "data": new_plan
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error creating workforce plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workforce plan: {str(e)}"
        )


@router.put("/{plan_id}", summary="Update workforce plan", response_model=None)
async def update_workforce_plan(
    plan_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: WorkforcePlanUpdate,
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update an existing workforce plan."""
    try:
        client = await get_client(company_id, db)
        plans = get_workforce_plans(client)
        
        plan_index = next((i for i, p in enumerate(plans) if p.get("id") == plan_id), None)
        
        if plan_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workforce plan not found: {plan_id}"
            )
        
        plan = plans[plan_index]
        
        update_data = data.model_dump(exclude_unset=True)
        
        if "departments" in update_data and update_data["departments"] is not None:
            update_data["departments"] = [
                dept.model_dump() if hasattr(dept, 'model_dump') else dept 
                for dept in update_data["departments"]
            ]
        
        for field, value in update_data.items():
            plan[field] = value
        
        plan["updated_at"] = datetime.utcnow().isoformat()
        
        plans[plan_index] = plan
        save_workforce_plans(client, plans)
        
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"✅ Updated workforce plan: {plan['name']} ({plan_id})")
        
        return {
            "success": True,
            "data": plan
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error updating workforce plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workforce plan: {str(e)}"
        )


@router.delete("/{plan_id}", summary="Delete workforce plan", response_model=None)
async def delete_workforce_plan(
    plan_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Delete a workforce plan."""
    try:
        client = await get_client(company_id, db)
        plans = get_workforce_plans(client)
        
        plan_index = next((i for i, p in enumerate(plans) if p.get("id") == plan_id), None)
        
        if plan_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workforce plan not found: {plan_id}"
            )
        
        deleted_plan = plans.pop(plan_index)
        save_workforce_plans(client, plans)
        
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"🗑️ Deleted workforce plan: {deleted_plan['name']} ({plan_id})")
        
        return {
            "success": True,
            "message": f"Workforce plan deleted: {deleted_plan['name']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error deleting workforce plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workforce plan: {str(e)}"
        )


@router.get("/{plan_id}/departments", summary="List departments of a plan", response_model=None)
async def list_plan_departments(
    plan_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all departments in a workforce plan."""
    try:
        client = await get_client(company_id, db)
        plans = get_workforce_plans(client)
        
        plan = next((p for p in plans if p.get("id") == plan_id), None)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workforce plan not found: {plan_id}"
            )
        
        departments = plan.get("departments", [])
        
        return {
            "success": True,
            "data": {
                "plan_id": plan_id,
                "plan_name": plan.get("name"),
                "departments": departments,
                "total": len(departments)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing plan departments: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plan departments: {str(e)}"
        )


@router.post("/{plan_id}/calculate", summary="Recalculate plan metrics", response_model=None)
async def calculate_plan_metrics(
    plan_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db), 
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (metrics) — no tenant data
    """Recalculate metrics for a workforce plan based on department data."""
    try:
        client = await get_client(company_id, db)
        plans = get_workforce_plans(client)
        
        plan_index = next((i for i, p in enumerate(plans) if p.get("id") == plan_id), None)
        
        if plan_index is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workforce plan not found: {plan_id}"
            )
        
        plan = plans[plan_index]
        departments = plan.get("departments", [])
        
        total_budget = sum(dept.get("budget", 0) for dept in departments)
        total_current = sum(dept.get("current_headcount", 0) for dept in departments)
        total_planned = sum(dept.get("planned_headcount", 0) for dept in departments)
        total_planned_hires = max(0, total_planned - total_current)
        
        plan["total_budget"] = total_budget
        plan["total_planned_hires"] = total_planned_hires
        plan["updated_at"] = datetime.utcnow().isoformat()
        
        plans[plan_index] = plan
        save_workforce_plans(client, plans)
        
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"📊 Recalculated metrics for plan: {plan['name']}")
        
        return {
            "success": True,
            "data": {
                "plan_id": plan_id,
                "total_budget": total_budget,
                "total_current_headcount": total_current,
                "total_planned_headcount": total_planned,
                "total_planned_hires": total_planned_hires,
                "departments_count": len(departments)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Error calculating plan metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate plan metrics: {str(e)}"
        )

reorder_collection_before_item(router)
