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
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.health_check import DEFAULT_HEALTH_CHECK_ITEMS, ComplianceHealthCheckHistory, ComplianceHealthCheckItem
from app.models.observability import ComplianceControlLibrary
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health-check", tags=["health-check"])


@router.get("/summary", response_model=HealthCheckSummaryResponse, summary="Get health check summary")
async def get_health_check_summary(
    db: AsyncSession = Depends(get_db)
):
    """Get summary statistics for compliance health check by framework."""
    try:
        query = select(ComplianceHealthCheckItem)
        result = await db.execute(query)
        all_items = result.scalars().all()
        
        if not all_items:
            return HealthCheckSummaryResponse(
                total_items=0,
                by_framework=[],
                overall_compliance_percentage=0.0,
                total_critical_pending=0,
                total_overdue_reviews=0,
                last_updated=datetime.utcnow()
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
                    "overdue_reviews": 0
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
            framework_summaries.append(FrameworkSummary(
                framework=fw,
                total=data["total"],
                implemented=data["implemented"],
                partial=data["partial"],
                pending=data["pending"],
                not_applicable=data["not_applicable"],
                not_checked=data["not_checked"],
                compliance_percentage=round(compliance_pct, 2),
                critical_pending=data["critical_pending"],
                overdue_reviews=data["overdue_reviews"]
            ))
        
        framework_summaries.sort(key=lambda x: x.framework)
        overall_pct = (total_implemented / total_applicable * 100) if total_applicable > 0 else 0.0
        
        return HealthCheckSummaryResponse(
            total_items=len(all_items),
            by_framework=framework_summaries,
            overall_compliance_percentage=round(overall_pct, 2),
            total_critical_pending=total_critical_pending,
            total_overdue_reviews=total_overdue,
            last_updated=datetime.utcnow()
        )
    except Exception as e:
        logger.error(f"Error getting health check summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", summary="Export health check items", response_model=None)
async def export_health_check(
    framework: str | None = Query(None, description="Filter by framework"),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    format: str = Query("csv", description="Export format: csv or json"),
    db: AsyncSession = Depends(get_db)
):
    """Export health check items as CSV or JSON file."""
    try:
        conditions = []
        
        if framework:
            conditions.append(ComplianceHealthCheckItem.framework == framework)
        if status_filter:
            conditions.append(ComplianceHealthCheckItem.status == status_filter)
        
        query = select(ComplianceHealthCheckItem).order_by(
            ComplianceHealthCheckItem.framework,
            ComplianceHealthCheckItem.category,
            ComplianceHealthCheckItem.req_id
        )
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        if format.lower() == "json":
            data = [item.to_dict() for item in items]
            content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            filename = f"health_check_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            return StreamingResponse(
                iter([content]),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "Framework", "Category", "Req ID", "Requirement", "Evidence",
            "Status", "Priority", "Last Checked", "Checked By",
            "Next Review", "Review Frequency", "Gap Observation", "Comments"
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
                item.check_comments or ""
            ])
        
        output.seek(0)
        filename = f"health_check_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed", response_model=SeedHealthCheckResponse, summary="Seed default health check items")
async def seed_health_check_items(
    db: AsyncSession = Depends(get_db)
):
    """Seed default compliance health check items for all frameworks."""
    try:
        created_count = 0
        skipped_count = 0
        
        for item_data in DEFAULT_HEALTH_CHECK_ITEMS:
            existing_query = select(ComplianceHealthCheckItem).where(
                ComplianceHealthCheckItem.req_id == item_data["req_id"]
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                skipped_count += 1
                continue
            
            item = ComplianceHealthCheckItem(**item_data)
            db.add(item)
            created_count += 1
        
        await db.commit()
        
        return SeedHealthCheckResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            message=f"Created {created_count} items, skipped {skipped_count} existing"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding health check items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


FRAMEWORK_MAPPING = {
    "ISO_27001": "ISO27001",
    "SOC_2_TYPE_II": "SOC2",
    "SOX": "SOX",
    "LGPD": "LGPD",
    "BCB498": "BCB498",
    "EUAI": "EUAI",
    "NYC144": "NYC144",
}


@router.post("/sync-from-library", response_model=SeedHealthCheckResponse, summary="Sync controls from library")
async def sync_from_library(
    db: AsyncSession = Depends(get_db)
):
    """Synchronize controls from compliance_control_library to health check items."""
    try:
        created_count = 0
        skipped_count = 0
        
        library_query = select(ComplianceControlLibrary)
        library_result = await db.execute(library_query)
        library_controls = library_result.scalars().all()
        
        for control in library_controls:
            mapped_framework = FRAMEWORK_MAPPING.get(control.framework, control.framework)
            
            existing_query = select(ComplianceHealthCheckItem).where(
                ComplianceHealthCheckItem.req_id == control.control_id
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                skipped_count += 1
                continue
            
            evidence_list = control.evidence_requirements or []
            evidence_str = ", ".join(evidence_list) if evidence_list else None
            
            priority = "critical" if control.is_mandatory else "medium"
            
            item = ComplianceHealthCheckItem(
                framework=mapped_framework,
                category=control.control_category or "General",
                req_id=control.control_id,
                requirement=control.control_name,
                evidence=evidence_str,
                evidence_details=control.implementation_guidance,
                priority=priority,
                review_frequency="monthly",
                status="not_checked"
            )
            db.add(item)
            created_count += 1
        
        await db.commit()
        
        return SeedHealthCheckResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            message=f"Synced from library: Created {created_count} items, skipped {skipped_count} existing"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error syncing from control library: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{req_id}/history", response_model=HealthCheckHistoryListResponse, summary="Get item history")
async def get_item_history(
    req_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get status change history for a specific health check item."""
    try:
        item_query = select(ComplianceHealthCheckItem).where(
            ComplianceHealthCheckItem.req_id == req_id
        )
        item_result = await db.execute(item_query)
        item = item_result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health check item with req_id '{req_id}' not found"
            )
        
        history_query = select(ComplianceHealthCheckHistory).where(
            ComplianceHealthCheckHistory.item_id == item.id
        ).order_by(desc(ComplianceHealthCheckHistory.created_at))
        
        history_result = await db.execute(history_query)
        history_items = history_result.scalars().all()
        
        return HealthCheckHistoryListResponse(
            history=[HealthCheckHistoryResponse(**h.to_dict()) for h in history_items],
            total=len(history_items)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting item history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{req_id}/check", response_model=HealthCheckItemResponse, summary="Mark item as verified")
async def mark_item_checked(
    req_id: str,
    data: HealthCheckVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Mark a health check item as verified, updating last_checked_at and related fields."""
    try:
        query = select(ComplianceHealthCheckItem).where(
            ComplianceHealthCheckItem.req_id == req_id
        )
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health check item with req_id '{req_id}' not found"
            )
        
        item.last_checked_at = datetime.utcnow()
        
        if data.checked_by_id:
            try:
                item.checked_by_id = UUID(data.checked_by_id)
            except ValueError:
                pass
        
        if data.checked_by_name:
            item.checked_by_name = data.checked_by_name
        
        if data.check_comments:
            item.check_comments = data.check_comments
        
        if data.next_review_date:
            item.next_review_date = data.next_review_date
        elif not item.next_review_date:
            freq_days = {
                "weekly": 7,
                "monthly": 30,
                "quarterly": 90,
                "annual": 365
            }
            days = freq_days.get(item.review_frequency, 30)
            item.next_review_date = datetime.utcnow() + timedelta(days=days)
        
        await db.commit()
        await db.refresh(item)
        
        return HealthCheckItemResponse(**item.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error marking item as checked: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{req_id}/status", response_model=HealthCheckItemResponse, summary="Update item status")
async def update_item_status(
    req_id: str,
    data: HealthCheckStatusUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update the status of a health check item with history tracking."""
    try:
        query = select(ComplianceHealthCheckItem).where(
            ComplianceHealthCheckItem.req_id == req_id
        )
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health check item with req_id '{req_id}' not found"
            )
        
        old_status = item.status
        new_status = data.status.value
        
        if old_status != new_status:
            history = ComplianceHealthCheckHistory(
                item_id=item.id,
                old_status=old_status,
                new_status=new_status,
                changed_by_id=UUID(data.changed_by_id) if data.changed_by_id else None,
                changed_by_name=data.changed_by_name,
                comments=data.comments
            )
            db.add(history)
        
        item.status = new_status
        
        if data.gap_observation is not None:
            item.gap_observation = data.gap_observation
        
        await db.commit()
        await db.refresh(item)
        
        return HealthCheckItemResponse(**item.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating item status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{req_id}", response_model=HealthCheckItemResponse, summary="Get health check item by req_id")
async def get_health_check_item(
    req_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single health check item by its requirement ID."""
    try:
        query = select(ComplianceHealthCheckItem).where(
            ComplianceHealthCheckItem.req_id == req_id
        )
        result = await db.execute(query)
        item = result.scalar_one_or_none()
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Health check item with req_id '{req_id}' not found"
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
    db: AsyncSession = Depends(get_db)
):
    """List health check items with optional filtering and pagination."""
    try:
        conditions = []
        
        if framework:
            conditions.append(ComplianceHealthCheckItem.framework == framework)
        if status_filter:
            conditions.append(ComplianceHealthCheckItem.status == status_filter)
        if category:
            conditions.append(ComplianceHealthCheckItem.category.ilike(f"%{category}%"))
        if priority:
            conditions.append(ComplianceHealthCheckItem.priority == priority)
        if overdue_only:
            conditions.append(ComplianceHealthCheckItem.next_review_date < datetime.utcnow())
        
        query = select(ComplianceHealthCheckItem).order_by(
            ComplianceHealthCheckItem.framework,
            ComplianceHealthCheckItem.category,
            ComplianceHealthCheckItem.req_id
        )
        if conditions:
            query = query.where(and_(*conditions))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        items = result.scalars().all()
        
        count_query = select(func.count(ComplianceHealthCheckItem.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return HealthCheckItemListResponse(
            items=[HealthCheckItemResponse(**item.to_dict()) for item in items],
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total
        )
    except Exception as e:
        logger.error(f"Error listing health check items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=HealthCheckItemResponse, status_code=status.HTTP_201_CREATED, summary="Create health check item")
async def create_health_check_item(
    data: HealthCheckItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new health check item."""
    try:
        existing_query = select(ComplianceHealthCheckItem).where(
            ComplianceHealthCheckItem.req_id == data.req_id
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Health check item with req_id '{data.req_id}' already exists"
            )
        
        item = ComplianceHealthCheckItem(
            framework=data.framework.value,
            category=data.category,
            req_id=data.req_id,
            requirement=data.requirement,
            evidence=data.evidence,
            gap_observation=data.gap_observation,
            status=data.status.value,
            priority=data.priority.value,
            review_frequency=data.review_frequency.value
        )
        db.add(item)
        await db.commit()
        await db.refresh(item)
        
        return HealthCheckItemResponse(**item.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating health check item: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
