"""
Compliance Health Check API Endpoints.

Provides endpoints for:
- Listing and filtering health check items
- Summary statistics by framework
- Marking items as verified
- Status updates with history tracking
- CSV/JSON export
- Seeding initial data
"""
import csv
import io
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.repositories.dependencies import get_health_check_repo
from app.repositories.health_check_repository import HealthCheckRepository
from app.schemas.health_check import (
    FrameworkSummary,
    HealthCheckHistoryListResponse,
    HealthCheckHistoryResponse,
    HealthCheckItemCreate,
    HealthCheckItemListResponse,
    HealthCheckItemResponse,
    HealthCheckStatusUpdateRequest,
    HealthCheckSummaryResponse,
    HealthCheckVerifyRequest,
    SeedHealthCheckResponse,
)
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health-check", tags=["health-check"])

FRAMEWORK_MAPPING = {
    "ISO_27001": "ISO27001",
    "SOC_2_TYPE_II": "SOC2",
    "SOX": "SOX",
    "LGPD": "LGPD",
    "BCB498": "BCB498",
    "EUAI": "EUAI",
    "NYC144": "NYC144",
}


@router.get("/summary", response_model=HealthCheckSummaryResponse, summary="Get health check summary")
async def get_health_check_summary(
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Get summary statistics for compliance health check by framework."""
    try:
        all_items = await repo.get_all_items()

        if not all_items:
            return HealthCheckSummaryResponse(
                total_items=0,
                by_framework=[],
                overall_compliance_percentage=0.0,
                total_critical_pending=0,
                total_overdue_reviews=0,
                last_updated=datetime.utcnow(),
            )

        frameworks_data = {}
        total_implemented = 0
        total_applicable = 0
        total_critical_pending = 0
        total_overdue = 0
        now = datetime.utcnow()

        for item in all_items:
            fw = item.framework
            if fw not in frameworks_data:
                frameworks_data[fw] = {
                    "total": 0,
                    "implemented": 0,
                    "partial": 0,
                    "pending": 0,
                    "not_applicable": 0,
                    "not_checked": 0,
                    "critical_pending": 0,
                    "overdue_reviews": 0,
                }

            frameworks_data[fw]["total"] += 1

            if item.status == "implemented":
                frameworks_data[fw]["implemented"] += 1
                total_implemented += 1
                total_applicable += 1
            elif item.status == "partial":
                frameworks_data[fw]["partial"] += 1
                total_applicable += 1
            elif item.status == "pending":
                frameworks_data[fw]["pending"] += 1
                total_applicable += 1
                if item.priority == "critical":
                    frameworks_data[fw]["critical_pending"] += 1
                    total_critical_pending += 1
            elif item.status == "not_applicable":
                frameworks_data[fw]["not_applicable"] += 1
            else:
                frameworks_data[fw]["not_checked"] += 1
                total_applicable += 1

            if item.next_review_date and item.next_review_date < now:
                frameworks_data[fw]["overdue_reviews"] += 1
                total_overdue += 1

        framework_summaries = []
        for fw, data in frameworks_data.items():
            applicable = data["total"] - data["not_applicable"]
            compliance_pct = (data["implemented"] / applicable * 100) if applicable > 0 else 0.0
            framework_summaries.append(
                FrameworkSummary(
                    framework=fw,
                    total=data["total"],
                    implemented=data["implemented"],
                    partial=data["partial"],
                    pending=data["pending"],
                    not_applicable=data["not_applicable"],
                    not_checked=data["not_checked"],
                    compliance_percentage=round(compliance_pct, 2),
                    critical_pending=data["critical_pending"],
                    overdue_reviews=data["overdue_reviews"],
                )
            )

        framework_summaries.sort(key=lambda x: x.framework)
        overall_pct = (total_implemented / total_applicable * 100) if total_applicable > 0 else 0.0

        return HealthCheckSummaryResponse(
            total_items=len(all_items),
            by_framework=framework_summaries,
            overall_compliance_percentage=round(overall_pct, 2),
            total_critical_pending=total_critical_pending,
            total_overdue_reviews=total_overdue,
            last_updated=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health check summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", summary="Export health check items", response_model=None)
async def export_health_check(
    framework: str | None = Query(None, description="Filter by framework"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    format: str = Query("csv", description="Export format: csv or json"),
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Export health check items as CSV or JSON file."""
    try:
        items = await repo.list_items_for_export(framework=framework, status_filter=status_filter)

        if format.lower() == "json":
            data = [item.to_dict() for item in items]
            content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            filename = f"health_check_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            return StreamingResponse(
                iter([content]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "Framework", "Category", "Req ID", "Requirement", "Evidence",
            "Status", "Priority", "Last Checked", "Checked By",
            "Next Review", "Review Frequency", "Gap Observation", "Comments",
        ])

        for item in items:
            writer.writerow([
                item.framework,
                item.category,
                item.req_id,
                item.requirement,
                item.evidence or "",
                item.status,
                item.priority,
                item.last_checked_at.isoformat() if item.last_checked_at else "",
                item.checked_by_name or "",
                item.next_review_date.isoformat() if item.next_review_date else "",
                item.review_frequency,
                item.gap_observation or "",
                item.check_comments or "",
            ])

        output.seek(0)
        filename = f"health_check_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed", response_model=SeedHealthCheckResponse, summary="Seed default health check items")
async def seed_health_check_items(
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Seed default compliance health check items for all frameworks."""
    try:
        created_count, skipped_count = await repo.seed_default_items()
        return SeedHealthCheckResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            message=f"Created {created_count} items, skipped {skipped_count} existing",
        )
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error seeding health check items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-from-library", response_model=SeedHealthCheckResponse, summary="Sync controls from library")
async def sync_from_library(
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Synchronize controls from compliance_control_library to health check items."""
    try:
        created_count, skipped_count = await repo.sync_from_control_library(FRAMEWORK_MAPPING)
        return SeedHealthCheckResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            message=f"Synced from library: Created {created_count} items, skipped {skipped_count} existing",
        )
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error syncing from control library: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{req_id}/history", response_model=HealthCheckHistoryListResponse, summary="Get item history")
async def get_item_history(
    req_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Get status change history for a specific health check item."""
    try:
        item = await repo.get_item_by_req_id(req_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health check item with req_id '{req_id}' not found",
            )

        history_items = await repo.get_item_history(item.id)

        return HealthCheckHistoryListResponse(
            history=[HealthCheckHistoryResponse(**h.to_dict()) for h in history_items],
            total=len(history_items),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting item history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{req_id}/check", response_model=HealthCheckItemResponse, summary="Mark item as verified")
async def mark_item_checked(
    req_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: HealthCheckVerifyRequest,
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Mark a health check item as verified, updating last_checked_at and related fields."""
    try:
        item = await repo.get_item_by_req_id(req_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health check item with req_id '{req_id}' not found",
            )

        item = await repo.mark_item_checked(
            item=item,
            checked_by_id=data.checked_by_id,
            checked_by_name=data.checked_by_name,
            check_comments=data.check_comments,
            next_review_date=data.next_review_date,
        )

        return HealthCheckItemResponse(**item.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error marking item as checked: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{req_id}/status", response_model=HealthCheckItemResponse, summary="Update item status")
async def update_item_status(
    req_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    data: HealthCheckStatusUpdateRequest,
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Update the status of a health check item with history tracking."""
    try:
        item = await repo.get_item_by_req_id(req_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health check item with req_id '{req_id}' not found",
            )

        item = await repo.update_item_status(
            item=item,
            new_status=data.status.value,
            gap_observation=data.gap_observation,
            changed_by_id=data.changed_by_id,
            changed_by_name=data.changed_by_name,
            comments=data.comments,
        )

        return HealthCheckItemResponse(**item.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error updating item status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{req_id}", response_model=HealthCheckItemResponse, summary="Get health check item by req_id")
async def get_health_check_item(
    req_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Get a single health check item by its requirement ID."""
    try:
        item = await repo.get_item_by_req_id(req_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health check item with req_id '{req_id}' not found",
            )

        return HealthCheckItemResponse(**item.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting health check item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=HealthCheckItemListResponse, summary="List health check items")
async def list_health_check_items(
    framework: str | None = Query(None, description="Filter by framework (SOX, SOC2, ISO27001, LGPD, BCB498, EUAI, NYC144)"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    category: str | None = Query(None, description="Filter by category"),
    priority: str | None = Query(None, description="Filter by priority"),
    overdue_only: bool = Query(False, description="Only show items with overdue reviews"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """List health check items with optional filtering and pagination."""
    try:
        items, total = await repo.list_items(
            framework=framework,
            status_filter=status_filter,
            category=category,
            priority=priority,
            overdue_only=overdue_only,
            limit=limit,
            offset=offset,
        )

        return HealthCheckItemListResponse(
            items=[HealthCheckItemResponse(**item.to_dict()) for item in items],
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing health check items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=HealthCheckItemResponse, status_code=status.HTTP_201_CREATED, summary="Create health check item")
async def create_health_check_item(
    data: HealthCheckItemCreate,
    repo: HealthCheckRepository = Depends(get_health_check_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Create a new health check item."""
    try:
        if await repo.item_exists_by_req_id(data.req_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Health check item with req_id '{data.req_id}' already exists",
            )

        item = await repo.create_item(
            framework=data.framework.value,
            category=data.category,
            req_id=data.req_id,
            requirement=data.requirement,
            evidence=data.evidence,
            gap_observation=data.gap_observation,
            status=data.status.value,
            priority=data.priority.value,
            review_frequency=data.review_frequency.value,
        )

        return HealthCheckItemResponse(**item.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await repo.rollback()
        logger.error(f"Error creating health check item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

reorder_collection_before_item(router)
