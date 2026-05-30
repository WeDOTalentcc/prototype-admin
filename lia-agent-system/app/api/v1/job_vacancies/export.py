"""
Export routes: PDF and Excel reports.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import StreamingResponse
from app.domains.analytics.services.job_report_service import job_report_service

from ._shared import (  # noqa: F401
    get_current_active_user,
    get_user_company_id,
    User,
    get_db,
    AsyncSession,
    Depends,
    HTTPException,
    logger,
)
from app.shared.security.require_company_id import require_company_id
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN

router = APIRouter()


@router.get("/job-vacancies/{job_id}/export/pdf", response_model=None)
async def export_job_vacancy_pdf(
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    report_type: str = Query("analytics", description="Report type: funnel, analytics, or candidates"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Export job vacancy report as PDF."""
    try:
        company_id = get_user_company_id(current_user)

        if report_type == "funnel":
            buffer = await job_report_service.generate_funnel_report(
                job_id=job_id,
                company_id=company_id,
                format="pdf",
                db=db
            )
            filename = f"relatorio_funil_{job_id}.pdf"
        elif report_type == "candidates":
            buffer = await job_report_service.generate_candidate_list_export(
                job_id=job_id,
                company_id=company_id,
                format="pdf",
                db=db
            )
            filename = f"lista_candidatos_{job_id}.pdf"
        else:
            buffer = await job_report_service.generate_analytics_report(
                job_id=job_id,
                company_id=company_id,
                format="pdf",
                db=db
            )
            filename = f"relatorio_analitico_{job_id}.pdf"

        logger.info(f"PDF report exported for job {job_id} by {current_user.id}")

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting PDF report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job-vacancies/{job_id}/export/excel", response_model=None)
async def export_job_vacancy_excel(
    job_id: str = Path(..., pattern=DUAL_ID_PATH_PATTERN),
    report_type: str = Query("analytics", description="Report type: funnel, analytics, or candidates"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user), 
company_id: str = Depends(require_company_id)):
    """Export job vacancy report as Excel file."""
    try:
        company_id = get_user_company_id(current_user)

        if report_type == "funnel":
            buffer = await job_report_service.generate_funnel_report(
                job_id=job_id,
                company_id=company_id,
                format="excel",
                db=db
            )
            filename = f"relatorio_funil_{job_id}.xlsx"
        elif report_type == "candidates":
            buffer = await job_report_service.generate_candidate_list_export(
                job_id=job_id,
                company_id=company_id,
                format="excel",
                db=db
            )
            filename = f"lista_candidatos_{job_id}.xlsx"
        else:
            buffer = await job_report_service.generate_analytics_report(
                job_id=job_id,
                company_id=company_id,
                format="excel",
                db=db
            )
            filename = f"relatorio_analitico_{job_id}.xlsx"

        logger.info(f"Excel report exported for job {job_id} by {current_user.id}")

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting Excel report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
