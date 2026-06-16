from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, get_user_company_id
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.shared.learning.ab_testing_service import ab_testing_service as _service, ABTestingService
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel

router = APIRouter(prefix="/ab-tests", tags=["ab-testing"])



class VariantCreate(WeDoBaseModel):
    variant_name: str
    prompt_template: str
    traffic_percentage: float = 50.0


class TestCreate(WeDoBaseModel):
    test_name: str
    variants: list[VariantCreate]


class MetricRecord(BaseModel):
    variant_name: str
    session_id: str
    # company_id intentionally removed — derived from JWT to prevent IDOR (UC-P0-08)
    metric_name: str
    metric_value: float
    context: dict[str, Any] | None = None


class BusinessMetricRecord(BaseModel):
    variant_name: str
    session_id: str
    # company_id intentionally removed — derived from JWT to prevent IDOR (UC-P0-08)
    satisfaction_score: float | None = None
    response_edited: bool | None = None
    time_to_decision_ms: float | None = None
    context: dict[str, Any] | None = None


@router.get("", response_model=None)
async def list_active_tests(
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    tests = await _service.list_active_tests(db, company_id=company_id)
    return {"tests": tests}


@router.post("", response_model=None)
async def create_test(
    body: TestCreate,
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    variants_data = [v.model_dump() for v in body.variants]
    result = await _service.create_test(body.test_name, variants_data, db)
    return result


@router.get("/{test_name}/results", response_model=None)
async def get_test_results(
    test_name: str,
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    results = await _service.get_test_results(test_name, db)
    return results


@router.post("/{test_name}/record", response_model=None)
async def record_metric(
    test_name: str,
    body: MetricRecord,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # UC-P0-08: company_id MUST come from the JWT, never from the request body
    company_id = get_user_company_id(current_user)
    record = await _service.record_metric(
        test_name=test_name,
        variant_name=body.variant_name,
        session_id=body.session_id,
        company_id=company_id,
        metric_name=body.metric_name,
        metric_value=body.metric_value,
        db=db,
        context=body.context,
    )
    if record:
        return {"status": "recorded", "id": str(record.id)}
    return {"status": "error", "message": "Failed to record metric"}


@router.post("/{test_name}/record-business-metrics", response_model=None)
async def record_business_metrics(
    test_name: str,
    body: BusinessMetricRecord,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # UC-P0-08: company_id MUST come from the JWT, never from the request body
    company_id = get_user_company_id(current_user)
    recorded_ids: list[str] = []

    if body.satisfaction_score is not None:
        rec = await _service.record_metric(
            test_name=test_name,
            variant_name=body.variant_name,
            session_id=body.session_id,
            company_id=company_id,
            metric_name="satisfaction_score",
            metric_value=body.satisfaction_score,
            db=db,
            context=body.context,
        )
        if rec:
            recorded_ids.append(str(rec.id))

    if body.response_edited is not None:
        rec = await _service.record_metric(
            test_name=test_name,
            variant_name=body.variant_name,
            session_id=body.session_id,
            company_id=company_id,
            metric_name="response_edited",
            metric_value=1.0 if body.response_edited else 0.0,
            db=db,
            context=body.context,
        )
        if rec:
            recorded_ids.append(str(rec.id))

    if body.time_to_decision_ms is not None:
        rec = await _service.record_metric(
            test_name=test_name,
            variant_name=body.variant_name,
            session_id=body.session_id,
            company_id=company_id,
            metric_name="time_to_decision_ms",
            metric_value=body.time_to_decision_ms,
            db=db,
            context=body.context,
        )
        if rec:
            recorded_ids.append(str(rec.id))

    if recorded_ids:
        return {"status": "recorded", "ids": recorded_ids, "metrics_count": len(recorded_ids)}
    return {"status": "error", "message": "No metrics were recorded"}


@router.get("/{test_name}/variant", response_model=None)
async def get_variant(
    test_name: str,
    session_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    variant = await _service.get_variant(test_name, session_id, db)
    if variant:
        return variant
    return {"error": f"No active variants found for test '{test_name}'"}
