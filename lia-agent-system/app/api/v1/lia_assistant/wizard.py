"""Tombstone replacement for app/api/v1/lia_assistant/wizard.py

All 5 legacy wizard REST endpoints now return HTTP 410 Gone.
Canonical path: WS /ws/agent-chat with domain=job_creation.

Task #857 / N-03: No request body validation, no DB access, no LLM call.
Structured deprecation log emitted per call for audit trail.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from fastapi import Depends
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

_CANONICAL_DETAIL = {
    "error": (
        "Endpoint deprecated. Use WS /ws/agent-chat with "
        "domain=job_creation."
    ),
}

_MODULE = "lia_assistant.wizard"
router = APIRouter()


def _emit_deprecation_log(
    request: Request,
    endpoint_name: str,
) -> None:
    """Emit structured 'wizard.legacy.deprecated_call' log for audit trail."""
    company_id = request.headers.get("X-Company-ID") or None
    session_id = request.headers.get("X-Session-ID", "")
    path = str(request.url.path)
    logger.info(
        "wizard.legacy.deprecated_call",
        extra={
            "tenant.company_id": company_id,
            "caller": f"{_MODULE}.{endpoint_name}",
            "path": path,
            "session_id": session_id,
        },
    )


# ---------------------------------------------------------------------------
# Stub schemas — kept so downstream imports don't break
# ---------------------------------------------------------------------------

class _AnyBody(BaseModel):
    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Tombstone endpoints — all return 410 Gone
# ---------------------------------------------------------------------------

@router.post("/job-wizard/interpret")
async def interpret_user_message(request: Request, company_id: str = Depends(require_company_id)) -> None:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _emit_deprecation_log(request, "interpret_user_message")
    raise HTTPException(status_code=410, detail=_CANONICAL_DETAIL)


@router.post("/job-wizard/orchestrate")
async def orchestrate_wizard_message(request: Request, company_id: str = Depends(require_company_id)) -> None:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _emit_deprecation_log(request, "orchestrate_wizard_message")
    raise HTTPException(status_code=410, detail=_CANONICAL_DETAIL)


@router.post("/job-wizard/salary-benchmark")
async def get_salary_benchmark(request: Request, company_id: str = Depends(require_company_id)) -> None:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _emit_deprecation_log(request, "get_salary_benchmark")
    raise HTTPException(status_code=410, detail=_CANONICAL_DETAIL)


@router.post("/job-wizard/evaluate")
async def evaluate_wizard_input(request: Request, company_id: str = Depends(require_company_id)) -> None:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _emit_deprecation_log(request, "evaluate_wizard_input")
    raise HTTPException(status_code=410, detail=_CANONICAL_DETAIL)


@router.post("/job-wizard/step")
async def process_wizard_step(request: Request, company_id: str = Depends(require_company_id)) -> None:
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    _emit_deprecation_log(request, "process_wizard_step")
    raise HTTPException(status_code=410, detail=_CANONICAL_DETAIL)
