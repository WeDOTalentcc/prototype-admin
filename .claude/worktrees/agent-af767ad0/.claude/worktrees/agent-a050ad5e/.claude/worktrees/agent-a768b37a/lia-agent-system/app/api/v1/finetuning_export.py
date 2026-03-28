from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.learning.finetuning_export import FineTuningExportService

router = APIRouter(prefix="/finetuning", tags=["finetuning-export"])

_service = FineTuningExportService()


@router.get("/stats/{company_id}")
async def get_export_stats(
    company_id: str,
    db: AsyncSession = Depends(get_db),
):
    stats = await _service.get_export_stats(company_id, db)
    return stats


@router.post("/export/{company_id}")
async def trigger_export(
    company_id: str,
    format: str = Query(default="claude", regex="^(claude|gpt)$"),
    min_quality: float = Query(default=0.7, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db),
):
    content = await _service.export_to_file(company_id, db, output_format=format)
    lines = content.strip().split("\n") if content.strip() else []
    return {
        "company_id": company_id,
        "format": format,
        "min_quality": min_quality,
        "line_count": len(lines),
        "content": content,
    }
