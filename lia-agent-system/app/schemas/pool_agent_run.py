"""Pydantic schemas for PoolAgentRun endpoints — Sprint 7C Part 1.5a.

Herdam WeDoBaseModel (REGRA 1: extra='forbid' fail-closed).
NUNCA company_id no request body (REGRA 2). Response inclui company_id (read-only).
"""
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from app.shared.types import WeDoBaseModel


TriggerSource = Literal["cron", "on_demand", "event_driven"]
RunStatus = Literal["queued", "running", "success", "error", "timeout", "cancelled"]


class PoolAgentRunResponse(WeDoBaseModel):
    """Response canonical pra GET .../runs e GET .../runs/{id}."""

    id: UUID
    assignment_id: UUID
    company_id: str
    trigger_source: TriggerSource
    status: RunStatus
    started_at: datetime | None
    finished_at: datetime | None
    dispatch_metadata: dict[str, Any]
    results: dict[str, Any]
    runtime_metrics: dict[str, Any]
    reasoning_payload: list[dict[str, Any]] | None = None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
