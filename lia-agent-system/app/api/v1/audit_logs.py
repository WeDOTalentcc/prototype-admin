"""
SOX-Compliant Audit Logs API Endpoints.

Provides endpoints for:
- Listing and filtering audit logs
- Viewing individual log details
- Aggregated statistics
- CSV export
- Retention policy management
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Header, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import Optional
from datetime import datetime, timedelta
import logging
import io
import csv
from uuid import UUID

from app.core.database import get_db
from app.shared.tenant_guard import get_verified_company_id
from app.models.audit_logs import (
    SOXAuditLog, AuditRetentionPolicy,
    ActionCategory, AuditStatus,
    DEFAULT_RETENTION_POLICIES
)
from app.schemas.audit_logs import (
    AuditLogResponse, AuditLogListResponse, AuditLogCreate,
    AuditStatsResponse, AuditRetentionPolicyResponse, AuditRetentionPolicyListResponse,
    AuditRetentionPolicyCreate, AuditRetentionPolicyUpdate,
    ActionCategoryEnum, AuditStatusEnum, SeedRetentionPoliciesResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def get_company_id_from_header(
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID")
) -> Optional[str]:
    """Extract company ID from header (optional for platform-wide queries)."""
    if x_company_id:
        try:
            UUID(x_company_id)
        except ValueError:
            if x_company_id not in ["demo_company", "platform"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid X-Company-ID format"
                )
    return x_company_id


@router.get("/stats", response_model=AuditStatsResponse, summary="Get audit log statistics")
async def get_audit_stats(
    date_from: Optional[datetime] = Query(None, description="Start date for stats"),
    date_to: Optional[datetime] = Query(None, description="End date for stats"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    company_id: Optional[str] = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get aggregated statistics for audit logs."""
    try:
        conditions = []
        
        if date_from:
            conditions.append(SOXAuditLog.timestamp >= date_from)
        if date_to:
            conditions.append(SOXAuditLog.timestamp <= date_to)
        
        filter_client_id = client_id or company_id
        if filter_client_id and filter_client_id != "platform":
            conditions.append(SOXAuditLog.client_id == filter_client_id)
        
        base_query = select(SOXAuditLog)
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        total_query = select(func.count(SOXAuditLog.id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        total_result = await db.execute(total_query)
        total_logs = total_result.scalar() or 0
        
        category_query = select(
            SOXAuditLog.action_category,
            func.count(SOXAuditLog.id)
        ).group_by(SOXAuditLog.action_category)
        if conditions:
            category_query = category_query.where(and_(*conditions))
        category_result = await db.execute(category_query)
        logs_by_category = {row[0]: row[1] for row in category_result.fetchall()}
        
        status_query = select(
            SOXAuditLog.status,
            func.count(SOXAuditLog.id)
        ).group_by(SOXAuditLog.status)
        if conditions:
            status_query = status_query.where(and_(*conditions))
        status_result = await db.execute(status_query)
        logs_by_status = {row[0]: row[1] for row in status_result.fetchall()}
        
        failed_count = logs_by_status.get("failed", 0)
        ai_decisions_count = logs_by_category.get("ai_decision", 0)
        
        users_query = select(func.count(func.distinct(SOXAuditLog.user_id)))
        if conditions:
            users_query = users_query.where(and_(*conditions))
        users_result = await db.execute(users_query)
        unique_users = users_result.scalar() or 0
        
        clients_query = select(func.count(func.distinct(SOXAuditLog.client_id)))
        if conditions:
            clients_query = clients_query.where(and_(*conditions))
        clients_result = await db.execute(clients_query)
        unique_clients = clients_result.scalar() or 0
        
        top_actions_query = select(
            SOXAuditLog.action,
            func.count(SOXAuditLog.id).label('count')
        ).group_by(SOXAuditLog.action).order_by(desc('count')).limit(10)
        if conditions:
            top_actions_query = top_actions_query.where(and_(*conditions))
        top_actions_result = await db.execute(top_actions_query)
        top_actions = [{"action": row[0], "count": row[1]} for row in top_actions_result.fetchall()]
        
        return AuditStatsResponse(
            total_logs=total_logs,
            logs_by_category=logs_by_category,
            logs_by_status=logs_by_status,
            failed_actions_count=failed_count,
            ai_decisions_count=ai_decisions_count,
            unique_users=unique_users,
            unique_clients=unique_clients,
            period_start=date_from,
            period_end=date_to,
            top_actions=top_actions
        )
    except Exception as e:
        logger.error(f"Error getting audit stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", summary="Export audit logs as CSV")
async def export_audit_logs(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    action_category: Optional[str] = Query(None, description="Filter by category"),
    company_id: Optional[str] = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Export audit logs as CSV file for compliance reporting."""
    try:
        conditions = []
        
        if date_from:
            conditions.append(SOXAuditLog.timestamp >= date_from)
        if date_to:
            conditions.append(SOXAuditLog.timestamp <= date_to)
        
        filter_client_id = client_id or company_id
        if filter_client_id and filter_client_id != "platform":
            conditions.append(SOXAuditLog.client_id == filter_client_id)
        
        if action_category:
            conditions.append(SOXAuditLog.action_category == action_category)
        
        query = select(SOXAuditLog).order_by(desc(SOXAuditLog.timestamp)).limit(10000)
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            "ID", "Timestamp", "User ID", "User Email", "Client ID", "Client Name",
            "Action", "Action Category", "Resource Type", "Resource ID",
            "IP Address", "Status", "Details"
        ])
        
        for log in logs:
            writer.writerow([
                str(log.id),
                log.timestamp.isoformat() if log.timestamp else "",
                log.user_id or "",
                log.user_email or "",
                log.client_id or "",
                log.client_name or "",
                log.action,
                log.action_category,
                log.resource_type or "",
                log.resource_id or "",
                log.ip_address or "",
                log.status,
                str(log.details) if log.details else ""
            ])
        
        output.seek(0)
        
        filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention-policies", response_model=AuditRetentionPolicyListResponse, summary="List retention policies")
async def list_retention_policies(
    db: AsyncSession = Depends(get_db)
):
    """List all audit retention policies."""
    try:
        query = select(AuditRetentionPolicy).order_by(AuditRetentionPolicy.category)
        result = await db.execute(query)
        policies = result.scalars().all()
        
        return AuditRetentionPolicyListResponse(
            policies=[AuditRetentionPolicyResponse(**p.to_dict()) for p in policies],
            total=len(policies)
        )
    except Exception as e:
        logger.error(f"Error listing retention policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention-policies/seed", response_model=SeedRetentionPoliciesResponse, summary="Seed default retention policies")
async def seed_retention_policies(
    db: AsyncSession = Depends(get_db)
):
    """Seed default SOX-compliant retention policies."""
    try:
        created_count = 0
        skipped_count = 0
        
        for policy_data in DEFAULT_RETENTION_POLICIES:
            existing_query = select(AuditRetentionPolicy).where(
                AuditRetentionPolicy.category == policy_data["category"]
            )
            existing_result = await db.execute(existing_query)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                skipped_count += 1
                continue
            
            policy = AuditRetentionPolicy(**policy_data)
            db.add(policy)
            created_count += 1
        
        await db.commit()
        
        return SeedRetentionPoliciesResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            message=f"Created {created_count} policies, skipped {skipped_count} existing"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding retention policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention-policies", response_model=AuditRetentionPolicyResponse, summary="Create retention policy")
async def create_retention_policy(
    data: AuditRetentionPolicyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new audit retention policy."""
    try:
        existing_query = select(AuditRetentionPolicy).where(
            AuditRetentionPolicy.category == data.category
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Retention policy for category '{data.category}' already exists"
            )
        
        policy = AuditRetentionPolicy(
            category=data.category,
            retention_months=data.retention_months,
            description=data.description,
            is_sox_required=data.is_sox_required,
            legal_basis=data.legal_basis
        )
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        
        return AuditRetentionPolicyResponse(**policy.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating retention policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{log_id}", response_model=AuditLogResponse, summary="Get audit log by ID")
async def get_audit_log(
    log_id: str,
    company_id: Optional[str] = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a single audit log entry by ID."""
    try:
        log_uuid = UUID(log_id)
        
        query = select(SOXAuditLog).where(SOXAuditLog.id == log_uuid)
        
        if company_id and company_id != "platform":
            query = query.where(SOXAuditLog.client_id == company_id)
        
        result = await db.execute(query)
        log = result.scalar_one_or_none()
        
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log not found"
            )
        
        return AuditLogResponse(**log.to_dict())
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid log ID format"
        )
    except Exception as e:
        logger.error(f"Error getting audit log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=AuditLogListResponse, summary="List audit logs")
async def list_audit_logs(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    action_category: Optional[str] = Query(None, description="Filter by action category"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    action: Optional[str] = Query(None, description="Filter by action (partial match)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(50, ge=1, le=500, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    company_id: Optional[str] = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db)
):
    """List audit logs with optional filtering and pagination."""
    try:
        conditions = []
        
        if date_from:
            conditions.append(SOXAuditLog.timestamp >= date_from)
        if date_to:
            conditions.append(SOXAuditLog.timestamp <= date_to)
        
        filter_client_id = client_id or company_id
        if filter_client_id and filter_client_id != "platform":
            conditions.append(SOXAuditLog.client_id == filter_client_id)
        
        if user_id:
            conditions.append(SOXAuditLog.user_id == user_id)
        if action_category:
            conditions.append(SOXAuditLog.action_category == action_category)
        if status_filter:
            conditions.append(SOXAuditLog.status == status_filter)
        if action:
            conditions.append(SOXAuditLog.action.ilike(f"%{action}%"))
        if resource_type:
            conditions.append(SOXAuditLog.resource_type == resource_type)
        
        query = select(SOXAuditLog).order_by(desc(SOXAuditLog.timestamp))
        if conditions:
            query = query.where(and_(*conditions))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        logs = result.scalars().all()
        
        count_query = select(func.count(SOXAuditLog.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        return AuditLogListResponse(
            logs=[AuditLogResponse(**log.to_dict()) for log in logs],
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total
        )
    except Exception as e:
        logger.error(f"Error listing audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=AuditLogResponse, summary="Create audit log entry")
async def create_audit_log(
    data: AuditLogCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new audit log entry (internal use)."""
    try:
        retention_query = select(AuditRetentionPolicy).where(
            AuditRetentionPolicy.category == data.action_category.value
        )
        retention_result = await db.execute(retention_query)
        retention_policy = retention_result.scalar_one_or_none()
        
        if retention_policy:
            retention_years = retention_policy.retention_months // 12
            retention_until = datetime.utcnow() + timedelta(days=retention_policy.retention_months * 30)
        else:
            retention_years = 7
            retention_until = datetime.utcnow() + timedelta(days=7 * 365)
        
        audit_log = SOXAuditLog(
            user_id=data.user_id,
            user_email=data.user_email,
            client_id=data.client_id,
            client_name=data.client_name,
            action=data.action,
            action_category=data.action_category.value,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            status=data.status.value,
            details=data.details or {},
            request_id=data.request_id,
            session_id=data.session_id,
            retention_years=retention_years,
            retention_until=retention_until
        )
        
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        
        return AuditLogResponse(**audit_log.to_dict())
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating audit log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
