from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.learning.finetuning_export import finetuning_export_service as _service
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

router = APIRouter(prefix="/finetuning", tags=["finetuning-export"])


@router.get("/stats/{company_id}", response_model=None)
async def get_export_stats(
    company_id: str,
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    stats = await _service.get_export_stats(company_id, db)
    return stats


@router.post("/export/{company_id}", response_model=None)
async def trigger_export(
    company_id: str,
    format: str = Query(default="claude", pattern="^(claude|gpt)$"),
    min_quality: float = Query(default=0.7, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
_company_gate: str = Depends(require_company_id_strict_match("path.company_id"))):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    content = await _service.export_to_file(company_id, db, output_format=format)
    lines = content.strip().split("\n") if content.strip() else []
    return {
        "company_id": company_id,
        "format": format,
        "min_quality": min_quality,
        "line_count": len(lines),
        "content": content,
    }
