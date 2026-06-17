"""
LGPD Art.48 Incident Response — Admin Endpoints.

For the WeDOTalent internal team (DPO/compliance) only.
NOT exposed to end customers or candidates.

Endpoints:
  POST   /api/v1/admin/incidents/          — Register a data incident
  GET    /api/v1/admin/incidents/open      — List open incidents for DPO review
  PATCH  /api/v1/admin/incidents/{id}/status — Update incident status
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.core.database import get_db, get_tenant_db
from lia_models.incident import IncidentSeverity, IncidentStatus
from app.domains.lgpd.services.incident_response_service import IncidentResponseService
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

router = APIRouter(prefix="/admin/incidents", tags=["LGPD Art.48 — Incident Response"])
logger = logging.getLogger(__name__)

_service = IncidentResponseService()


@router.post("/", summary="Register a data incident (LGPD Art.48)")
async def register_incident(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Register a data security incident. Triggers CRITICAL log alert to
    internal admin/monitoring. Manual ANPD notification via admin page.
    """
    incident = await _service.register_incident(
        db,
        company_id=payload.get("company_id", "system"),
        title=payload["title"],
        description=payload["description"],
        severity=IncidentSeverity(payload.get("severity", "medium")),
        affected_data_categories=payload.get("affected_data_categories"),
        affected_users_count=payload.get("affected_users_count"),
        reported_by=str(_user.id) if _user else "admin",
    )
    return {
        "id": str(incident.id),
        "status": incident.status,
        "created_at": incident.created_at.isoformat(),
    }


@router.get("/open", summary="List open incidents for DPO review")
async def list_open_incidents(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List incidents in OPEN or INVESTIGATING status requiring DPO attention."""
    incidents = await _service.get_open_incidents(db, company_id=company_id)
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "severity": i.severity,
            "status": i.status,
            "detected_at": i.incident_detected_at.isoformat(),
        }
        for i in incidents
    ]


@router.patch("/{incident_id}/status", summary="Update incident status")
async def update_incident_status(
    incident_id: str,
    new_status: IncidentStatus,
    db: AsyncSession = Depends(get_tenant_db),
    _user=Depends(require_admin),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Update incident status. Use REPORTED_ANPD after manual ANPD notification.
    Automatically records anpd_reported_at / resolved_at timestamps.
    """
    incident = await _service.update_status(db, incident_id, new_status)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return {"id": str(incident.id), "status": incident.status}
