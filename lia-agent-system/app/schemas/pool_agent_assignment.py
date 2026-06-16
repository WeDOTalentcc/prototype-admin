"""Pydantic schemas for PoolAgentAssignment endpoints — Sub-sprint 7A canonical.

Todos herdam WeDoBaseModel (REGRA 1: extra='forbid' fail-closed).
NUNCA company_id no payload (REGRA 2: vem do JWT via Depends(require_company_id)).
"""
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import Field

from app.shared.types import WeDoBaseModel


class ScheduleType(str, Enum):
    ON_DEMAND = "on_demand"
    CRON = "cron"
    EVENT_DRIVEN = "event_driven"


class AssignmentStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class PoolAgentAssignmentCreate(WeDoBaseModel):
    custom_agent_id: str = Field(..., description="UUID do CustomAgent")
    schedule_type: Literal["on_demand", "cron", "event_driven"] = "on_demand"
    schedule_config: dict[str, Any] = Field(default_factory=dict)
    config_overrides: dict[str, Any] = Field(default_factory=dict)


class PoolAgentAssignmentUpdate(WeDoBaseModel):
    status: Optional[Literal["active", "paused"]] = None
    schedule_type: Optional[Literal["on_demand", "cron", "event_driven"]] = None
    schedule_config: Optional[dict[str, Any]] = None
    config_overrides: Optional[dict[str, Any]] = None


class PoolAgentAssignmentResponse(WeDoBaseModel):
    id: str
    talent_pool_id: str
    custom_agent_id: str
    custom_agent_name: Optional[str] = None
    custom_agent_category: Optional[str] = None
    status: str
    schedule_type: str
    schedule_config: dict[str, Any]
    config_overrides: dict[str, Any]
    last_run_at: Optional[datetime] = None
    last_run_status: Optional[str] = None
    runtime_metrics: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: str
