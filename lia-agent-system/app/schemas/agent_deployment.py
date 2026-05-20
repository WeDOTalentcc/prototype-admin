"""Pydantic schemas for AgentDeployment CRUD."""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class CreateDeploymentRequest(WeDoBaseModel):
    target_type: Literal["job", "talent_pool", "pipeline_stage", "candidate_list"]
    target_id: str
    target_name: Optional[str] = None
    trigger_mode: Literal["manual", "on_new_candidate", "on_stage_change", "scheduled"] = "manual"
    schedule_cron: Optional[str] = None
    config_overrides: dict[str, Any] = Field(default_factory=dict)


class UpdateDeploymentRequest(WeDoBaseModel):
    trigger_mode: Optional[Literal["manual", "on_new_candidate", "on_stage_change", "scheduled"]] = None
    schedule_cron: Optional[str] = None
    is_active: Optional[bool] = None
    config_overrides: Optional[dict[str, Any]] = None
    target_name: Optional[str] = None


class DeploymentResponse(BaseModel):
    id: str
    agent_id: str
    company_id: str
    target_type: str
    target_id: str
    target_name: Optional[str] = None
    trigger_mode: str
    schedule_cron: Optional[str] = None
    is_active: bool
    config_overrides: dict[str, Any] = {}
    execution_count: int = 0
    candidates_processed: int = 0
    last_execution_at: Optional[str] = None
    created_by: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DeploymentListResponse(BaseModel):
    deployments: list[DeploymentResponse]
    total: int


class RunDeploymentRequest(WeDoBaseModel):
    """Manual trigger: run agent on all candidates in target."""
    message: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)


class RunDeploymentResponse(BaseModel):
    deployment_id: str
    agent_id: str
    target_type: str
    target_id: str
    candidates_processed: int = 0
    execution_time_ms: int = 0
    status: str = "completed"
