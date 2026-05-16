from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException, status

from app.auth.dependencies import get_current_user, get_user_company_id, require_admin
from app.core.database import get_db
from app.domains.compliance.services.compliance_reporter import ComplianceReporter
from app.auth.models import User
from app.schemas.envelope import ResponseEnvelope, ok_envelope, error_envelope
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["compliance-report"])


@router.get("/report", response_model=ResponseEnvelope, summary="Generate compliance report")
async def get_compliance_report(
    company_id: str = Query(..., description="Company UUID to generate report for"),
    from_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    to_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_admin),
_company_gate: str = Depends(require_company_id_strict_match("query.company_id"))):
    # UC-P0-08: admin é role, NÃO é fronteira de tenant. company_id da query
    # tem que bater com o tenant do JWT do usuário autenticado.
    jwt_company = get_user_company_id(current_user)
    if not company_id or str(company_id) != str(jwt_company):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="company_id does not match authenticated tenant",
        )
    company_id = str(jwt_company)
    reporter = ComplianceReporter(db=db)
    report = await reporter.generate_report(company_id, from_date, to_date)
    return ok_envelope(report, meta={"company_id": company_id})
