"""
Reports API - Endpoints for generating candidate reports and automated briefings.
"""
from enum import Enum, StrEnum

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domains.analytics.services.candidate_report_service import candidate_report_service
from app.domains.analytics.services.report_service import report_service
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item
from app.shared.errors import LIAError

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class DailyBriefingSendRequest(WeDoBaseModel):
    """Request model for sending daily briefing."""
    user_id: str
    user_email: str
    user_name: str
    company_name: str = "Sua Empresa"


class WeeklyReportSendRequest(WeDoBaseModel):
    """Request model for sending weekly report."""
    recipient_emails: list[str]
    recipient_name: str = "Equipe"
    company_name: str = "Sua Empresa"


class MonthlyReportSendRequest(WeDoBaseModel):
    """Request model for sending monthly manager report."""
    recipient_emails: list[str]
    recipient_name: str = "Gestão"
    company_name: str = "Sua Empresa"


class ReportPreviewRequest(WeDoBaseModel):
    """Request model for report preview."""
    user_name: str = "Recrutador"
    company_name: str = "Empresa Demo"


class CandidateReportRequest(WeDoBaseModel):
    """Request model for generating a candidate report."""
    candidate_id: str
    job_id: str | None = None
    include_screening: bool = True
    include_tests: bool = True
    format: str = "detailed"


class ComparisonReportRequest(WeDoBaseModel):
    """Request model for generating a comparison report."""
    candidate_ids: list[str]
    job_id: str


@router.post("/candidate", response_model=None)
async def generate_candidate_report(
    request: CandidateReportRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Generate a comprehensive candidate report/parecer."""
    try:
        report = await candidate_report_service.generate_report(
            db=db,
            candidate_id=request.candidate_id,
            job_id=request.job_id,
            include_screening=request.include_screening,
            include_tests=request.include_tests,
            format=request.format
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")


@router.post("/comparison", response_model=None)
async def generate_comparison_report(
    request: ComparisonReportRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Generate a comparison report for multiple candidates."""
    try:
        report = await candidate_report_service.generate_comparison_report(
            db=db,
            candidate_ids=request.candidate_ids,
            job_id=request.job_id
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")


@router.get("/candidate/{candidate_id}", response_model=None)
async def get_candidate_report(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    job_id: str | None = None,
    format: str = Query(default="detailed", enum=["detailed", "executive", "comparison"]),
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Get a candidate report by candidate ID."""
    try:
        report = await candidate_report_service.generate_report(
            db=db,
            candidate_id=candidate_id,
            job_id=job_id,
            format=format
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/daily-briefing/send", response_model=None)
async def send_daily_briefing(
    request: DailyBriefingSendRequest,
    db: AsyncSession = Depends(get_db), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Send a daily briefing email to a recruiter.
    
    Generates a personalized daily briefing with:
    - Urgent actions
    - Pipeline summary
    - Today's schedule
    - Active alerts
    - LIA insights
    """
    try:
        result = await report_service.generate_daily_briefing_email(
            user_id=request.user_id,
            user_email=request.user_email,
            user_name=request.user_name,
            company_name=request.company_name,
            db=db,
            send_email=True
        )
        return {
            "success": result.get("email_sent", False),
            "report_type": "daily_briefing",
            "generated_at": result.get("generated_at"),
            "email_id": result.get("email_id"),
            "error": result.get("email_error")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")


@router.post("/weekly/send", response_model=None)
async def send_weekly_report(request: WeeklyReportSendRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Send a weekly performance report.
    
    Generates a team performance report with:
    - KPIs and trends
    - Funnel conversion rates
    - Recruiter ranking
    - Channel performance
    - LIA recommendations
    """
    try:
        result = await report_service.generate_weekly_performance_report(
            recipient_emails=request.recipient_emails,
            recipient_name=request.recipient_name,
            company_name=request.company_name,
            send_email=True
        )
        return {
            "success": len(result.get("emails_sent", [])) > 0,
            "report_type": "weekly_performance",
            "generated_at": result.get("generated_at"),
            "emails_sent": result.get("emails_sent", []),
            "emails_failed": result.get("emails_failed", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")


@router.post("/monthly/send", response_model=None)
async def send_monthly_report(request: MonthlyReportSendRequest, company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Send a monthly manager/executive report.
    
    Generates an executive report with:
    - Executive summary
    - Strategic KPIs
    - Department breakdown
    - AI predictions
    - Strategic recommendations
    """
    try:
        result = await report_service.generate_monthly_manager_report(
            recipient_emails=request.recipient_emails,
            recipient_name=request.recipient_name,
            company_name=request.company_name,
            send_email=True
        )
        return {
            "success": len(result.get("emails_sent", [])) > 0,
            "report_type": "monthly_manager",
            "generated_at": result.get("generated_at"),
            "emails_sent": result.get("emails_sent", []),
            "emails_failed": result.get("emails_failed", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")


@router.get("/preview/{report_type}", response_class=HTMLResponse, response_model=None)
async def preview_report(
    report_type: ReportType,
    user_name: str = Query(default="Recrutador", description="Name for personalization"),
    company_name: str = Query(default="Empresa Demo", description="Company name for branding"), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Preview a report without sending email.
    
    Returns the HTML content of the report for preview purposes.
    
    Supported report types:
    - daily: Daily briefing report
    - weekly: Weekly performance report
    - monthly: Monthly manager report
    """
    try:
        result = await report_service.preview_report(
            report_type=report_type.value,
            user_name=user_name,
            company_name=company_name
        )
        return HTMLResponse(content=result.get("html_content", ""))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")


@router.get("/preview/{report_type}/json", response_model=None)
async def preview_report_json(
    report_type: ReportType,
    user_name: str = Query(default="Recrutador", description="Name for personalization"),
    company_name: str = Query(default="Empresa Demo", description="Company name for branding"), 
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Preview a report and return JSON with HTML content and metadata.
    
    Useful for embedding previews in frontend applications.
    """
    try:
        result = await report_service.preview_report(
            report_type=report_type.value,
            user_name=user_name,
            company_name=company_name
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise LIAError(message="Erro interno do servidor")

reorder_collection_before_item(router)
