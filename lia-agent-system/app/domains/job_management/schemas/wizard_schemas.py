"""
Wizard step schemas -- shared between domain service and API layer.
Defined here (domain layer) to avoid circular imports from api->domain.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class WizardStepResponse(BaseModel):
    conversation_id: str
    current_stage: int
    next_stage: int | None = None
    stage_name: str
    lia_message: str
    detected_criteria: dict[str, Any] | None = None
    is_complete: bool
    created_job: dict[str, Any] | None = None
    intent_detected: str | None = None
    benchmarks: dict[str, Any] | None = None
    suggestions: dict[str, Any] | None = None
    field_origins: dict[str, dict[str, Any]] | None = None
    stage_skipped: bool | None = None
    skip_reason: str | None = None
    auto_filled_data: dict[str, Any] | None = None
    stages_to_skip: list[int] | None = None
