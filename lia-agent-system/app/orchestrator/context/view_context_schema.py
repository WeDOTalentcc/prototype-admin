"""view_context_schema — Pydantic schema for FE→BE view_context payload.

GAP-02-005: formalizes the implicit contract that existed as plain dict.

Design decisions:
- model_config extra="ignore": FE may send extra fields as it evolves; we
  tolerate them rather than failing the entire chat request (view_context is
  best-effort context enrichment, not mission-critical).
- All fields optional with safe defaults: context is always additive; a missing
  field never breaks agent behavior.
- Nested schemas (PaginationStateSchema, ModalAwarenessSchema) match the exact
  shape already used by format_view_context() and lia-context-store.ts.

Usage (parse-and-warn pattern, never fail-closed on context):
    from app.orchestrator.context.view_context_schema import ViewContextSchema, parse_view_context

    validated = parse_view_context(raw_dict_from_fe)
    # validated is always a ViewContextSchema — malformed fields get defaults

Sensor: tests/unit/test_view_context_schema.py
"""
from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)


class PaginationStateSchema(BaseModel):
    """Pagination state reported by the FE table/list component."""

    model_config = ConfigDict(extra="ignore")

    current_page: int = Field(default=1, ge=1)
    total_pages: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1)
    total_items: int | None = None


class ModalAwarenessSchema(BaseModel):
    """Which modal (if any) is currently open on the FE."""

    model_config = ConfigDict(extra="ignore")

    active_modal: str | None = None
    modal_open: bool = False
    modal_context: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_modal_open(self) -> "ModalAwarenessSchema":
        """Keep modal_open consistent with active_modal presence."""
        if self.active_modal:
            self.modal_open = True
        return self


class EntityFocusSchema(BaseModel):
    """Which entity (candidate or job) the recruiter has in focus."""

    model_config = ConfigDict(extra="ignore")

    type: str = "candidate"  # "candidate" | "job"
    id: str
    label: str = ""


class ViewContextSchema(BaseModel):
    """Formal contract for the FE→BE view_context payload.

    The FE sends this as part of every chat message context. It describes
    *what the recruiter is looking at right now* so the agent can give
    context-aware responses ("você tem 12 candidatos nesta busca").

    All fields are optional — the FE may omit any field, and view_context
    as a whole is always optional (best-effort enrichment).
    """

    model_config = ConfigDict(extra="ignore")

    # Page / navigation
    page_type: str | None = None

    # Entity focus
    job_vacancy_id: str | None = None
    candidate_id: str | None = None
    current_stage: str | None = None
    entity_focus: EntityFocusSchema | None = None

    # Pagination (GAP-02-001, already handled by format_view_context)
    pagination_state: PaginationStateSchema | None = None

    # Modal awareness (GAP-02-001)
    active_modal: str | None = None
    modal_awareness: ModalAwarenessSchema | None = None

    # Filters / counts
    filters_active: dict[str, Any] = Field(default_factory=dict)
    active_filters: list[str] = Field(default_factory=list)
    counts: dict[str, Any] = Field(default_factory=dict)

    # Stale-detection timestamp (GAP-02-006)
    captured_at: str | None = None

    # Arbitrary visible entity IDs (list of str)
    visible_ids: list[str] = Field(default_factory=list)

    # Passthrough for legacy fields the FE may still send
    job_title: str | None = None
    job_context: dict[str, Any] | None = None


def parse_view_context(raw: dict[str, Any] | None) -> ViewContextSchema | None:
    """Parse and validate raw view_context dict from FE.

    Returns a ViewContextSchema on success.
    Returns None if raw is None or empty.
    Logs a WARNING for validation errors but never raises — view_context is
    best-effort context enrichment and must never break the chat request.
    """
    if not raw or not isinstance(raw, dict):
        return None
    try:
        return ViewContextSchema.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError or anything else
        logger.warning(
            "view_context validation warning (non-blocking) — raw context kept as-is",
            extra={"error": str(exc), "raw_keys": list(raw.keys())},
        )
        # Graceful degradation: return None so callers fall back to raw dict
        return None
