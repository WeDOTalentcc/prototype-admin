"""
app/shared/chat_types.py — Typed structured_data schemas for chat responses.

R-027: Provides discriminated union for structured_data field.
StructuredDataAdapter.unwrap() fixes double-wrap cache bug (main_orchestrator.py:842).
This file is ADDITIVE — existing ChatResponse classes are unchanged.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class KanbanStructuredData(BaseModel):
    """Structured data for kanban/pipeline responses."""

    model_config = ConfigDict(extra='forbid')

    kind: Literal["kanban"] = "kanban"
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, float] | None = None
    ui_action_params: dict[str, Any] | None = None


class JobsManagementStructuredData(BaseModel):
    """Structured data for job management assistant responses."""

    model_config = ConfigDict(extra='forbid')

    kind: Literal["jobs_management"] = "jobs_management"
    state_updates: dict[str, Any] | None = None
    job_id: str | None = None


class TalentStructuredData(BaseModel):
    """Structured data for talent pool / sourcing responses."""

    model_config = ConfigDict(extra='forbid')

    kind: Literal["talent"] = "talent"
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    total_found: int = 0
    filters_applied: dict[str, Any] | None = None


class ScoreStructuredData(BaseModel):
    """Structured data for WSI / scoring responses."""

    model_config = ConfigDict(extra='forbid')

    kind: Literal["score"] = "score"
    score_breakdown: dict[str, float] = Field(default_factory=dict)
    confidence: float = 0.0
    wrf_scores: list[dict[str, Any]] = Field(default_factory=list)


class ActionResultStructuredData(BaseModel):
    """Structured data for generic action results."""

    model_config = ConfigDict(extra='forbid')

    kind: Literal["action_result"] = "action_result"
    data: dict[str, Any] = Field(default_factory=dict)
    action_type: str | None = None


StructuredData = Annotated[
    Union[
        KanbanStructuredData,
        JobsManagementStructuredData,
        TalentStructuredData,
        ScoreStructuredData,
        ActionResultStructuredData,
    ],
    Field(discriminator="kind"),
]


class StructuredDataAdapter:
    """
    Safe parse/unwrap utility for structured_data dicts.

    unwrap(): detects accidental double-wrap {structured_data: {}} -> inner dict
    parse(): returns typed Pydantic model when kind field present; raw dict otherwise.
    Never raises - safe for production use.
    """

    _KIND_MAP: dict[str, type[BaseModel]] = {
        "kanban": KanbanStructuredData,
        "jobs_management": JobsManagementStructuredData,
        "talent": TalentStructuredData,
        "score": ScoreStructuredData,
        "action_result": ActionResultStructuredData,
    }

    @classmethod
    def unwrap(cls, sd: dict[str, Any] | None) -> dict[str, Any] | None:
        """Detect and unwrap accidental double-wrap from cache serialization."""
        if sd is None:
            return None
        if isinstance(sd, dict) and list(sd.keys()) == ["structured_data"]:
            return sd["structured_data"]
        return sd

    @classmethod
    def parse(
        cls, sd: dict[str, Any] | None
    ) -> "StructuredData | dict[str, Any] | None":
        """Parse to typed StructuredData if kind present; fallback to raw dict."""
        sd = cls.unwrap(sd)
        if not isinstance(sd, dict):
            return sd
        kind = sd.get("kind")
        if kind and kind in cls._KIND_MAP:
            try:
                return cls._KIND_MAP[kind].model_validate(sd)
            except Exception:
                pass  # fallback to raw dict - never raise
        return sd
