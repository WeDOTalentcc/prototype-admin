from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.learning.ab_testing_service import ABTestingService

router = APIRouter(prefix="/ab-tests", tags=["ab-testing"])

_service = ABTestingService()


class VariantCreate(BaseModel):
    variant_name: str
    prompt_template: str
    traffic_percentage: float = 50.0


class TestCreate(BaseModel):
    test_name: str
    variants: list[VariantCreate]


class MetricRecord(BaseModel):
    variant_name: str
    session_id: str
    company_id: str
    metric_name: str
    metric_value: float
    context: dict[str, Any] | None = None


@router.get("", response_model=None)
async def list_active_tests(
    db: AsyncSession = Depends(get_db),
):
    tests = await _service.list_active_tests(db)
    return {"tests": tests}


@router.post("", response_model=None)
async def create_test(
    body: TestCreate,
    db: AsyncSession = Depends(get_db),
):
    variants_data = [v.model_dump() for v in body.variants]
    result = await _service.create_test(body.test_name, variants_data, db)
    return result


@router.get("/{test_name}/results", response_model=None)
async def get_test_results(
    test_name: str,
    db: AsyncSession = Depends(get_db),
):
    results = await _service.get_test_results(test_name, db)
    return results


@router.post("/{test_name}/record", response_model=None)
async def record_metric(
    test_name: str,
    body: MetricRecord,
    db: AsyncSession = Depends(get_db),
):
    record = await _service.record_metric(
        test_name=test_name,
        variant_name=body.variant_name,
        session_id=body.session_id,
        company_id=body.company_id,
        metric_name=body.metric_name,
        metric_value=body.metric_value,
        db=db,
        context=body.context,
    )
    if record:
        return {"status": "recorded", "id": str(record.id)}
    return {"status": "error", "message": "Failed to record metric"}


@router.get("/{test_name}/variant", response_model=None)
async def get_variant(
    test_name: str,
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    variant = await _service.get_variant(test_name, session_id, db)
    if variant:
        return variant
    return {"error": f"No active variants found for test '{test_name}'"}
