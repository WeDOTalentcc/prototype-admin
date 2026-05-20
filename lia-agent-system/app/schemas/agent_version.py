"""Pydantic schemas for agent version history."""
from typing import Any, Optional

from pydantic import BaseModel
from app.shared.types import WeDoBaseModel


class AgentVersionSummary(BaseModel):
    id: str
    agent_id: str
    version: int
    changed_fields: list[str] = []
    change_reason: Optional[str] = None
    changed_by: str
    created_at: Optional[str] = None


class AgentVersionDetail(BaseModel):
    id: str
    agent_id: str
    company_id: str
    version: int
    snapshot_data: dict[str, Any] = {}
    changed_fields: list[str] = []
    change_reason: Optional[str] = None
    changed_by: str
    created_at: Optional[str] = None


class AgentVersionListResponse(BaseModel):
    versions: list[AgentVersionSummary]
    total: int
    limit: int
    offset: int


class RevertVersionRequest(WeDoBaseModel):
    reason: Optional[str] = None
