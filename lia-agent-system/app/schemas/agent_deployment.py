"""Pydantic schemas for AgentDeployment CRUD.

Onda 3 (Fase 2 Agent Studio) — registrou 2026-05-27:
  - Trigger mode Literal expandido para incluir 9 modes canonical (on_create,
    on_apply, on_enter_stage, etc) + 2 legados (on_new_candidate, scheduled).
    Coerência target_type × trigger_mode enforced em runtime via
    app.shared.trigger_mode_validation.
  - BatchTargetsRequest / BatchTargetsResponse — eliminam N+1 da Onda 2 frontend.
  - BulkDeploymentRequest / BulkDeploymentResponse — acoplar 1 agente a N targets
    em transação atômica.
  - AgentDeploymentWithAgent — used by /jobs/{id}/agents endpoint with joined
    custom_agent metadata.
"""
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from app.shared.types import WeDoBaseModel
from lia_models.agent_deployment import DeploymentTargetType

# ─────────────────────────────────────────────────────────────────────────────
# Trigger mode union (canonical + legacy)
# ─────────────────────────────────────────────────────────────────────────────
# Onda 3 expanded — keep "scheduled" / "on_new_candidate" para backward compat
# com deployments existentes. Validator runtime garante coerência target_type ×
# trigger_mode (vide app.shared.trigger_mode_validation).
TriggerMode = Literal[
    # Canonical Onda 3
    "manual",
    "on_create",
    "on_schedule",
    "on_apply",
    "on_enter_stage",
    "on_exit_stage",
    "on_stuck_in_stage",
    "on_stage_change",
    # Legacy backward-compat
    "on_new_candidate",
    "scheduled",
]


class CreateDeploymentRequest(WeDoBaseModel):
    target_type: Literal["job", "talent_pool", "pipeline_stage", "candidate_list"]
    target_id: str
    target_name: Optional[str] = None
    trigger_mode: TriggerMode = "manual"
    schedule_cron: Optional[str] = None
    config_overrides: dict[str, Any] = Field(default_factory=dict)


class UpdateDeploymentRequest(WeDoBaseModel):
    trigger_mode: Optional[TriggerMode] = None
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


# ─────────────────────────────────────────────────────────────────────────────
# Onda 3.B1 — Batch by-targets (elimina N+1 do frontend Onda 2)
# ─────────────────────────────────────────────────────────────────────────────

#: Limite máximo de target_ids por request batch (read). Garante 1 query SQL
#: agregada manejável + reduz risco de payload abuse.
BATCH_TARGETS_MAX = 100


class BatchTargetsRequest(WeDoBaseModel):
    """Request body for POST /agent-deployments/by-targets."""
    target_type: DeploymentTargetType
    target_ids: list[str] = Field(..., min_length=0, max_length=BATCH_TARGETS_MAX)


class BatchTargetsResponse(BaseModel):
    """Response: dict mapping target_id → list of active deployments."""
    deployments_by_target: dict[str, list[DeploymentResponse]]


# ─────────────────────────────────────────────────────────────────────────────
# Onda 3.B2 — /jobs/{id}/agents canonical shortcut
# ─────────────────────────────────────────────────────────────────────────────


class AgentDeploymentWithAgent(BaseModel):
    """Deployment + joined CustomAgent metadata (name, category, status)."""
    # Deployment fields (mirror DeploymentResponse minus joined)
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
    # Joined CustomAgent metadata
    agent_name: Optional[str] = None
    agent_category: Optional[str] = None
    agent_status: Optional[str] = None
    agent_domain: Optional[str] = None


class JobAgentListResponse(BaseModel):
    """Response for GET /jobs/{job_id}/agents."""
    deployments: list[AgentDeploymentWithAgent]
    total: int


class AttachJobAgentRequest(WeDoBaseModel):
    """Request body for POST /jobs/{job_id}/agents."""
    agent_id: str
    trigger_mode: TriggerMode = "manual"
    schedule_cron: Optional[str] = None
    is_active: bool = True
    config_overrides: dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Onda 3.B3 — Bulk deploy (1 agent → N targets atomic)
# ─────────────────────────────────────────────────────────────────────────────

#: Limite máximo de target_ids por bulk write. Menor que BATCH_TARGETS_MAX porque
#: write é mais caro (validação + insert por target + audit single entry).
BULK_TARGETS_MAX = 50


class BulkDeploymentRequest(WeDoBaseModel):
    """Request body for POST /custom-agents/{agent_id}/deployments/bulk.

    Atomic semantics: validation failure on ANY target rolls back ALL inserts
    (transaction-scoped). Duplicate detection (target already has same agent
    deployed) → soft-skip, included in `skipped` list, does NOT block insert
    of siblings.
    """
    target_type: DeploymentTargetType
    target_ids: list[str] = Field(..., min_length=1, max_length=BULK_TARGETS_MAX)
    trigger_mode: TriggerMode = "manual"
    schedule_cron: Optional[str] = None
    is_active: bool = True
    config_overrides: dict[str, Any] = Field(default_factory=dict)


class BulkDeploymentSkippedItem(BaseModel):
    target_id: str
    reason: str  # ex: "duplicate_active_deployment"


class BulkDeploymentFailedItem(BaseModel):
    target_id: str
    error: str  # mensagem PT-BR


class BulkDeploymentResponse(BaseModel):
    """Bulk response separa created / skipped / failed.

    `created`: deployments efetivamente inseridos (commit atomic).
    `skipped`: targets que já tinham deployment ativo do mesmo agente.
    `failed`: targets que ainda existem mas falharam validação atomicamente
              (na prática, se houver falha, transação reverte e tudo vai pra
              `failed`; created fica vazio).
    """
    created: list[DeploymentResponse]
    skipped: list[BulkDeploymentSkippedItem]
    failed: list[BulkDeploymentFailedItem]
