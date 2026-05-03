"""
SOX-Compliant Audit Logs API Endpoints.

Provides endpoints for:
- Listing and filtering audit logs
- Viewing individual log details
- Aggregated statistics
- CSV export
- Retention policy management
"""
import csv
import io
import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.admin.repositories.audit_log_repository import AuditLogRepository
from app.models.audit_logs import SOXAuditLog
from app.schemas.audit_logs import (
    AuditLogCreate,
    AuditLogListResponse,
    AuditLogResponse,
    AuditRetentionPolicyCreate,
    AuditRetentionPolicyListResponse,
    AuditRetentionPolicyResponse,
    AuditStatsResponse,
    SeedRetentionPoliciesResponse,
)
from app.shared.tenant_guard import get_verified_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def _build_conditions(
    date_from, date_to, client_id, company_id,
    user_id=None, action_category=None, status_filter=None, action=None, resource_type=None,
):
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
    return conditions


@router.get("/stats", response_model=AuditStatsResponse, summary="Get audit log statistics")
async def get_audit_stats(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    client_id: str | None = Query(None),
    company_id: str | None = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated statistics for audit logs."""
    try:
        conditions = _build_conditions(date_from, date_to, client_id, company_id)
        repo = AuditLogRepository(db)
        stats = await repo.get_stats(conditions)
        return AuditStatsResponse(
            total_logs=stats["total_logs"],
            logs_by_category=stats["logs_by_category"],
            logs_by_status=stats["logs_by_status"],
            failed_actions_count=stats["logs_by_status"].get("failed", 0),
            ai_decisions_count=stats["logs_by_category"].get("ai_decision", 0),
            unique_users=stats["unique_users"],
            unique_clients=stats["unique_clients"],
            period_start=date_from,
            period_end=date_to,
            top_actions=stats["top_actions"],
        )
    except Exception as e:
        logger.error(f"Error getting audit stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", summary="Export audit logs as CSV", response_model=None)
async def export_audit_logs(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    client_id: str | None = Query(None),
    action_category: str | None = Query(None),
    company_id: str | None = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Export audit logs as CSV file for compliance reporting."""
    try:
        conditions = _build_conditions(date_from, date_to, client_id, company_id, action_category=action_category)
        repo = AuditLogRepository(db)
        logs = await repo.export_logs(conditions)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Timestamp", "User ID", "User Email", "Client ID", "Client Name",
            "Action", "Action Category", "Resource Type", "Resource ID",
            "IP Address", "Status", "Details",
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
                str(log.details) if log.details else "",
            ])
        output.seek(0)
        filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention-policies", response_model=AuditRetentionPolicyListResponse)
async def list_retention_policies(db: AsyncSession = Depends(get_db)):
    """List all audit retention policies."""
    try:
        repo = AuditLogRepository(db)
        policies = await repo.list_retention_policies()
        return AuditRetentionPolicyListResponse(
            policies=[AuditRetentionPolicyResponse(**p.to_dict()) for p in policies],
            total=len(policies),
        )
    except Exception as e:
        logger.error(f"Error listing retention policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention-policies/seed", response_model=SeedRetentionPoliciesResponse)
async def seed_retention_policies(db: AsyncSession = Depends(get_db)):
    """Seed default SOX-compliant retention policies."""
    try:
        repo = AuditLogRepository(db)
        created_count, skipped_count = await repo.seed_retention_policies()
        return SeedRetentionPoliciesResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            message=f"Created {created_count} policies, skipped {skipped_count} existing",
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding retention policies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention-policies", response_model=AuditRetentionPolicyResponse)
async def create_retention_policy(
    data: AuditRetentionPolicyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new audit retention policy."""
    try:
        repo = AuditLogRepository(db)
        if await repo.get_retention_policy_by_category(data.category):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Retention policy for category '{data.category}' already exists",
            )
        policy = await repo.create_retention_policy({
            "category": data.category,
            "retention_months": data.retention_months,
            "description": data.description,
            "is_sox_required": data.is_sox_required,
            "legal_basis": data.legal_basis,
        })
        return AuditRetentionPolicyResponse(**policy.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating retention policy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    company_id: str | None = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single audit log entry by ID."""
    try:
        log_uuid = UUID(log_id)
        repo = AuditLogRepository(db)
        log = await repo.get_log_by_id(log_uuid, company_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")
        return AuditLogResponse(**log.to_dict())
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid log ID format")
    except Exception as e:
        logger.error(f"Error getting audit log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    client_id: str | None = Query(None),
    user_id: str | None = Query(None),
    action_category: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    company_id: str | None = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
):
    """List audit logs with optional filtering and pagination."""
    try:
        conditions = _build_conditions(
            date_from, date_to, client_id, company_id,
            user_id=user_id, action_category=action_category,
            status_filter=status_filter, action=action, resource_type=resource_type,
        )
        repo = AuditLogRepository(db)
        logs, total = await repo.list_logs(conditions=conditions, limit=limit, offset=offset)
        return AuditLogListResponse(
            logs=[AuditLogResponse(**log.to_dict()) for log in logs],
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        )
    except Exception as e:
        logger.error(f"Error listing audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=AuditLogResponse)
async def create_audit_log(
    data: AuditLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new audit log entry (internal use)."""
    try:
        repo = AuditLogRepository(db)
        retention_policy = await repo.get_retention_policy_by_category(data.action_category.value)
        if retention_policy:
            retention_years = retention_policy.retention_months // 12
            retention_until = datetime.utcnow() + timedelta(days=retention_policy.retention_months * 30)
        else:
            retention_years = 7
            retention_until = datetime.utcnow() + timedelta(days=7 * 365)

        # R-011: company_id do ContextVar (JWT-validated, nunca do payload)
        from app.middleware.auth_enforcement import _current_company_id
        _cid_str = _current_company_id.get("")
        try:
            from uuid import UUID as _UUID
            _company_id: _UUID | None = _UUID(_cid_str) if _cid_str else None
        except ValueError:
            _company_id = None

        log = await repo.create_log({
            "user_id": data.user_id,
            "user_email": data.user_email,
            "company_id": _company_id,
            "client_id": data.client_id,
            "client_name": data.client_name,
            "action": data.action,
            "action_category": data.action_category.value,
            "resource_type": data.resource_type,
            "resource_id": data.resource_id,
            "ip_address": data.ip_address,
            "user_agent": data.user_agent,
            "status": data.status.value,
            "details": data.details or {},
            "request_id": data.request_id,
            "session_id": data.session_id,
            "retention_years": retention_years,
            "retention_until": retention_until,
        })
        return AuditLogResponse(**log.to_dict())
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating audit log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
