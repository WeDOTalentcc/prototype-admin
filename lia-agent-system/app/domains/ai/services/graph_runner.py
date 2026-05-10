"""
Tombstone module — GraphRunnerService deprecated (HTTP 410 Gone).

Task #857 / N-01: stream_job_wizard now lives in the canonical WS path
/ws/agent-chat with domain=job_creation. This module raises HTTPException(410)
to fail fast for any lingering callers and emit structured deprecation audit logs.
"""
from __future__ import annotations

import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)

_CANONICAL_DETAIL = {
    "error": (
        "Endpoint deprecated. Use WS /ws/agent-chat with "
        "domain=job_creation."
    ),
}
_TOMBSTONE_PATH = "graph_runner"


class GraphRunnerService:
    """Deprecated service. Raises 410 on all method calls."""

    graph = None  # type: ignore[assignment]

    def __init__(self) -> None:
        self.logger = logger

    async def run_job_wizard(
        self,
        *,
        session_id: str,
        user_message: str = "",
        company_id: str = "",
        user_id: str = "",
        **kwargs,
    ) -> dict:
        """Canonical job-wizard invocation via JobCreationGraph singleton.

        Reroutes legacy GraphRunnerService callers to the new canonical graph
        singleton (job_creation_graph). Returns a response dict matching the
        legacy REST shape so existing callers don't need changes.

        Response keys:
          response_text  — recruiter-facing message (built from ws_stage_payload
                           or intake_payload when no explicit message exists)
          job_draft      — the intake_payload dict for form pre-fill
          current_stage  — stage the graph halted at
          reasoning_steps — ["stage:X"] list matching stage_history
          execution_id   — echoes session_id (caller uses for tracking)
        """
        from app.domains.job_creation import graph as jc_graph

        initial_state: dict = {
            "raw_input": user_message,
            "company_id": company_id,
            "user_id": user_id,
        }
        result_state: dict = jc_graph.job_creation_graph.invoke(
            initial_state, session_id
        )

        intake_payload: dict = result_state.get("intake_payload") or {}
        current_stage: str = result_state.get("current_stage") or ""
        stage_history: list = result_state.get("stage_history") or []

        # Build recruiter-facing response_text from canonical ws_stage_payload
        # or fall back to synthesising it from intake_payload fields.
        ws_payload: dict = result_state.get("ws_stage_payload") or {}
        ws_data: dict = ws_payload.get("data") or {}
        response_text: str = ws_data.get("message") or ""
        if not response_text:
            title_field = intake_payload.get("title") or {}
            title_val: str = (
                title_field.get("value") if isinstance(title_field, dict) else ""
            ) or ""
            seniority_field = intake_payload.get("seniority") or {}
            seniority_val: str = (
                seniority_field.get("value") if isinstance(seniority_field, dict) else ""
            ) or ""
            if title_val:
                response_text = f"Captei a vaga: {title_val}"
                if seniority_val:
                    response_text += f" ({seniority_val})"
            else:
                response_text = "Vaga recebida. Vou continuar o preenchimento."

        return {
            "response_text": response_text,
            "job_draft": intake_payload,
            "current_stage": current_stage,
            "reasoning_steps": [f"stage:{s}" for s in stage_history],
            "execution_id": session_id,
        }

    async def stream_job_wizard(
        self,
        *,
        session_id: str,
        user_message: str = "",
        company_id: str = "",
        user_id: str = "",
        **kwargs,
    ):
        """Async generator tombstone — immediately raises HTTPException 410."""
        logger.info(
            "wizard.legacy.deprecated_call",
            extra={
                "tenant.company_id": company_id,
                "caller": "GraphRunnerService.stream_job_wizard",
                "path": _TOMBSTONE_PATH,
            },
        )
        raise HTTPException(status_code=410, detail=_CANONICAL_DETAIL)
        # make this an async generator (unreachable but satisfies type checker)
        if False:  # pragma: no cover
            yield  # type: ignore[misc]
