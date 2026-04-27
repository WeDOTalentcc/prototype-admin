"""Legacy job-wizard routes — DEPRECATED, return HTTP 410 Gone.

The original 5 endpoints (``/interpret``, ``/orchestrate``,
``/salary-benchmark``, ``/evaluate``, ``/step``) were retired by Task
#850 when the ``JobCreationGraph`` (WS ``/ws/agent-chat`` with
``domain=job_creation``) became the single canonical entrypoint for
recruiter-driven job creation.

This module previously kept the legacy LLM-driven handlers running,
which created a covert path that bypassed the canonical
``PolicyGate`` / ``FairnessGuard`` / per-turn audit log of the
graph (see audit finding **N-03** in
``.local/audits/audit-criacao-vaga-2026-04-26-revisao-status.md``,
Revisão 4).

This change converts all 5 endpoints to a canonical 410 response,
mirroring the pattern already used by
``app.domains.ai.services.graph_runner.stream_job_wizard`` and
``app.domains.job_management.services.wizard_orchestrator_service.get_wizard_step``
(Task #857).

Behaviour
---------

* Frontend has **zero** consumers (verified by ``rg`` over
  ``plataforma-lia/src``).
* The router stays mounted at ``/api/v1/lia/job-wizard/*`` so any
  external caller still in the wild receives an explicit 410 with a
  clear migration message.
* Every call emits a structured ``wizard.legacy.deprecated_call`` INFO
  log carrying ``tenant.company_id`` (best-effort, parsed from the
  ``Authorization`` header without touching the DB), the ``caller``,
  the request ``path`` and the optional ``X-Session-ID`` header.
* No request body validation, no ``Depends`` on the database, no LLM
  call. Failing fast and cheap is the entire point.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request

router = APIRouter()
logger = logging.getLogger(__name__)


CANONICAL_DETAIL: dict[str, str] = {
    "error": (
        "Endpoint deprecated. Use WS /ws/agent-chat with "
        "domain=job_creation."
    ),
}


def _best_effort_company_id(request: Request) -> str | None:
    """Pull ``X-Company-ID`` header if the caller set it.

    Deliberately does **not** touch the DB or run JWT validation —
    this is a deprecation log, not an authenticated path.
    """
    header_value = request.headers.get("x-company-id")
    return header_value or None


def _raise_410(endpoint: str, request: Request) -> None:
    company_id = _best_effort_company_id(request)
    logger.info(
        "wizard.legacy.deprecated_call",
        extra={
            "tenant.company_id": company_id,
            "caller": f"lia_assistant.wizard.{endpoint}",
            "path": str(request.url.path),
            "session_id": request.headers.get("x-session-id"),
        },
    )
    raise HTTPException(status_code=410, detail=CANONICAL_DETAIL)


@router.post("/job-wizard/interpret")
async def interpret_user_message(request: Request) -> Any:
    """Deprecated. See module docstring."""
    _raise_410("interpret_user_message", request)


@router.post("/job-wizard/orchestrate")
async def orchestrate_wizard_message(request: Request) -> Any:
    """Deprecated. See module docstring."""
    _raise_410("orchestrate_wizard_message", request)


@router.post("/job-wizard/salary-benchmark")
async def get_salary_benchmark(request: Request) -> Any:
    """Deprecated. See module docstring."""
    _raise_410("get_salary_benchmark", request)


@router.post("/job-wizard/evaluate")
async def evaluate_wizard_input(request: Request) -> Any:
    """Deprecated. See module docstring."""
    _raise_410("evaluate_wizard_input", request)


@router.post("/job-wizard/step")
async def process_wizard_step(request: Request) -> Any:
    """Deprecated. See module docstring."""
    _raise_410("process_wizard_step", request)
