"""Pydantic schemas: DigestSchedulePreference (Fatia 2 — Decisão 3)."""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import field_validator

from app.shared.types import WeDoBaseModel

CANONICAL_FREQUENCIES = frozenset({"daily", "twice_daily", "weekly", "monthly"})
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class DigestScheduleRequest(WeDoBaseModel):
    """Body de PUT /notifications/digest-schedule e /notifications/digest-schedule/company."""

    frequency: Literal["daily", "twice_daily", "weekly", "monthly"]
    preferred_time_morning: Optional[str] = None    # "HH:MM" UTC
    preferred_time_afternoon: Optional[str] = None  # "HH:MM" UTC (twice_daily)
    quiet_hours_start: Optional[int] = None          # 0-23
    quiet_hours_end: Optional[int] = None            # 0-23

    @field_validator("preferred_time_morning", "preferred_time_afternoon", mode="before")
    @classmethod
    def _validate_time(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not _TIME_RE.match(v):
            raise ValueError(f"Formato de hora inválido: {v!r} (esperado HH:MM, ex: 08:00)")
        return v

    @field_validator("quiet_hours_start", "quiet_hours_end", mode="before")
    @classmethod
    def _validate_hour(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if not (0 <= v <= 23):
            raise ValueError(f"Hora deve estar entre 0 e 23, recebido: {v}")
        return v


class DigestScheduleResponse(WeDoBaseModel):
    """Resposta de GET/PUT /notifications/digest-schedule."""

    frequency: str
    preferred_time_morning: Optional[str] = None
    preferred_time_afternoon: Optional[str] = None
    quiet_hours_start: Optional[int] = None
    quiet_hours_end: Optional[int] = None
    source: str  # 'user' | 'company_default' | 'policy_fallback'
    user_id: Optional[str] = None

    model_config = {"from_attributes": True}
