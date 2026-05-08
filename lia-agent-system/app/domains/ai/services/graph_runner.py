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
