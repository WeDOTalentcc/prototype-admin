"""Export candidates by active search filters — GAP-03-009.

Reutiliza os filtros do endpoint list_candidates para exportar TODOS os
resultados filtrados em CSV, sem exigir seleção manual de IDs.
"""
import csv
import io
import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.auth.dependencies import require_admin_or_recruiter
from app.auth.models import User
from app.domains.candidates.repositories.candidate_repository import CandidateRepository
from app.domains.candidates.dependencies import get_candidate_repo
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from app.shared.compliance.audit_service import audit_service

logger = logging.getLogger(__name__)

router = APIRouter()

_EXPORT_FIELDS = [
    "id", "name", "email", "phone", "linkedin_url",
    "current_title", "current_company", "seniority_level",
    "years_of_experience", "technical_skills", "soft_skills",
    "location_city", "location_state", "location_country",
    "is_remote", "desired_salary_min", "desired_salary_max",
    "salary_currency", "work_model_preference", "source",
    "lia_score", "status", "tags", "created_at", "updated_at",
]

_MAX_EXPORT_ROWS = 5_000


class ExportByFiltersRequest(WeDoBaseModel):
    """Filtros aceitos para export — espelha os query params de list_candidates."""
    search: str | None = None
    status: str | None = None
    source: str | None = None
    seniority: str | None = None
    sort_by: str | None = None
    sort_order: str | None = "desc"
    fields: list[str] | None = None


def _serialize_candidate_row(c, fields: list[str]) -> dict:
    full = {
        "id": str(c.id),
        "name": c.name or "",
        "email": c.email or "",
        "phone": c.phone or "",
        "linkedin_url": c.linkedin_url or "",
        "current_title": c.current_title or "",
        "current_company": c.current_company or "",
        "seniority_level": c.seniority_level or "",
        "years_of_experience": str(c.years_of_experience or ""),
        "technical_skills": ", ".join(c.technical_skills or []),
        "soft_skills": ", ".join(c.soft_skills or []),
        "location_city": c.location_city or "",
        "location_state": c.location_state or "",
        "location_country": c.location_country or "",
        "is_remote": "Sim" if c.is_remote else "Não",
        "desired_salary_min": str(c.desired_salary_min or ""),
        "desired_salary_max": str(c.desired_salary_max or ""),
        "salary_currency": c.salary_currency or "BRL",
        "work_model_preference": c.work_model_preference or "",
        "source": c.source or "",
        "lia_score": str(c.lia_score or ""),
        "status": c.status or "",
        "tags": ", ".join(c.tags or []),
        "created_at": c.created_at.isoformat() if c.created_at else "",
        "updated_at": c.updated_at.isoformat() if c.updated_at else "",
    }
    return {k: full[k] for k in fields if k in full}


@router.post("/export-by-filters")
async def export_candidates_by_filters(
    request: ExportByFiltersRequest,
    current_user: User = Depends(require_admin_or_recruiter),
    candidate_repo: CandidateRepository = Depends(get_candidate_repo),
    company_id: str = Depends(require_company_id),
):
    """Exporta todos os candidatos que correspondem aos filtros ativos como CSV.

    Não requer seleção manual de IDs — exporta o resultado do funil completo.
    Limite: 5.000 registros por exportação (GAP-03-009).
    """
    selected_fields = request.fields if request.fields else _EXPORT_FIELDS

    candidates = await candidate_repo.list_candidates(
        search=request.search,
        status=request.status,
        source=request.source,
        seniority=request.seniority,
        skip=0,
        limit=_MAX_EXPORT_ROWS,
        sort_by=request.sort_by or "created_at",
        sort_order=request.sort_order or "desc",
    )

    try:
        await audit_service.log_decision(
            company_id=company_id,
            agent_name="candidates_export_api",
            decision_type="export_candidates",
            action="export_by_filters",
            decision="exported",
            reasoning=[
                f"filters: search={request.search!r} status={request.status!r} "
                f"source={request.source!r} seniority={request.seniority!r}",
                f"total_rows: {len(candidates)}",
            ],
            criteria_used=["search", "status", "source", "seniority"],
            score=float(len(candidates)),
        )
    except Exception as _ae:
        logger.debug("audit log failed (non-blocking): %s", _ae)

    def generate_csv():
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=selected_fields, extrasaction="ignore")
        writer.writeheader()
        for c in candidates:
            writer.writerow(_serialize_candidate_row(c, selected_fields))
        yield buf.getvalue()

    filename = f"candidatos-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Total": str(len(candidates)),
            "X-Export-Filtered": "true",
        },
    )
