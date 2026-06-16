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

from app.core.database import get_db, get_tenant_db
from app.repositories.audit_log_repository import AuditLogRepository
from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
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
from app.shared.security.require_company_id import require_company_id
from app.shared.errors import LIAError
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

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
    # Multi-tenancy fail-closed (fix WT-2023): company_id do JWT SEMPRE filtra.
    # Sentinela "platform" removida (security bypass via REGRA ZERO + REGRA 6 CLAUDE.md).
    if not company_id:
        raise HTTPException(status_code=403, detail="company_id required for tenant scoping")
    if client_id is not None and str(client_id) != str(company_id):
        raise HTTPException(
            status_code=403,
            detail="client_id query param must match authenticated tenant",
        )
    conditions.append(SOXAuditLog.client_id == company_id)
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




def _require_tenant_admin(current_user) -> None:
    """LGPD Art. 9 — only tenant admin can view tenant audit log (own data).

    Sprint 7.3 RBAC. Restricts /audit-logs endpoint to admin/wedotalent_admin role.
    Prevents recruiter/viewer from seeing audit trail of other users.
    Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
    """
    from app.auth.models import UserRole
    from fastapi import HTTPException, status as _http_status

    role = getattr(current_user, "role", None)
    role_str = role.value if hasattr(role, "value") else str(role) if role else ""
    if role_str not in (UserRole.admin.value, UserRole.wedotalent_admin.value):
        raise HTTPException(
            status_code=_http_status.HTTP_403_FORBIDDEN,
            detail="Apenas admin do tenant pode acessar logs de auditoria (LGPD Art. 9)",
        )

@router.get("/stats", response_model=AuditStatsResponse, summary="Get audit log statistics")
async def get_audit_stats(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    client_id: str | None = Query(None),
    company_id: str | None = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_or_demo),
    _company_gate: str = Depends(require_company_id),
):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
            recent_24h=stats.get("recent_24h", 0),  # WT-2022 P5.1
            by_severity=stats.get("by_severity", {}),  # WT-2022 P5.1
            period_start=date_from,
            period_end=date_to,
            top_actions=stats["top_actions"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit stats: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/export", summary="Export audit logs as CSV", response_model=None)
async def export_audit_logs(
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    client_id: str | None = Query(None),
    action_category: str | None = Query(None),
    company_id: str | None = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/retention-policies", response_model=AuditRetentionPolicyListResponse)
async def list_retention_policies(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List all audit retention policies."""
    try:
        repo = AuditLogRepository(db)
        policies = await repo.list_retention_policies()
        return AuditRetentionPolicyListResponse(
            policies=[AuditRetentionPolicyResponse(**p.to_dict()) for p in policies],
            total=len(policies),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing retention policies: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/retention-policies/seed", response_model=SeedRetentionPoliciesResponse)
async def seed_retention_policies(db: AsyncSession = Depends(get_db), company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Seed default SOX-compliant retention policies."""
    try:
        repo = AuditLogRepository(db)
        created_count, skipped_count = await repo.seed_retention_policies()
        return SeedRetentionPoliciesResponse(
            created_count=created_count,
            skipped_count=skipped_count,
            message=f"Created {created_count} policies, skipped {skipped_count} existing",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding retention policies: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/retention-policies", response_model=AuditRetentionPolicyResponse)
async def create_retention_policy(
    data: AuditRetentionPolicyCreate,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        raise LIAError(message="Erro interno do servidor")


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    company_id: str | None = Depends(get_verified_company_id),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
        raise LIAError(message="Erro interno do servidor")


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
_company_gate: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """List audit logs with optional filtering and pagination."""
    # Sprint 7.3 LGPD Art. 9: only tenant admin can access audit trail
    _require_tenant_admin(current_user)
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing audit logs: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("", response_model=AuditLogResponse)
async def create_audit_log(
    data: AuditLogCreate,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
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
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating audit log: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
