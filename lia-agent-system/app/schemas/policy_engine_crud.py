"""WT-2022 Policies UI Editor — Pydantic CRUD schemas canonical.

Registrado 2026-05-22. Track canonical paralelo aos schemas legacy em
app/schemas/policy.py — esses aqui herdam de WeDoBaseModel (extra=forbid +
validate_assignment) e seguem REGRA 2 (sem company_id no payload, sempre
do JWT via Depends(require_company_id)).

Estrutura mirrors lia_models/policy.py field names:
- BusinessRule:      name, rule_type (ALLOW/DENY/REQUIRE_APPROVAL),
                      conditions, actions, priority, approval_config,
                      is_active, description, rule_metadata
- RateLimitRule:     name, target_type (user/agent/company/endpoint),
                      target_id, action_pattern, limit_value,
                      window_seconds, burst_limit, is_active, description
- EscalationRule:    name, trigger_type, condition, escalate_to,
                      escalation_action, notification_template,
                      cooldown_seconds, priority, is_active, description

REGRA 2 (Pydantic Conventions canonical 2026-05-20): NENHUM schema aqui
declara company_id — esse vem do JWT via require_company_id no endpoint.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import Field

from app.shared.types import WeDoBaseModel


# ─────────────────────────────────────────────────────────────────────────────
# BusinessRule schemas
# ─────────────────────────────────────────────────────────────────────────────


class BusinessRuleCreate(WeDoBaseModel):
    """Create payload — REGRA 2: SEM company_id (vem do JWT)."""

    name: str
    rule_type: str = "allow"  # allow | deny | require_approval
    conditions: dict[str, Any] = {}
    actions: list[str] = []
    priority: int = 100
    approval_config: Optional[dict[str, Any]] = None
    is_active: bool = True
    description: Optional[str] = None
    rule_metadata: Optional[dict[str, Any]] = None


class BusinessRuleUpdate(WeDoBaseModel):
    """Partial update — todos os campos opcionais."""

    name: Optional[str] = None
    rule_type: Optional[str] = None
    conditions: Optional[dict[str, Any]] = None
    actions: Optional[list[str]] = None
    priority: Optional[int] = None
    approval_config: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    rule_metadata: Optional[dict[str, Any]] = None


# ─────────────────────────────────────────────────────────────────────────────
# RateLimitRule schemas
# ─────────────────────────────────────────────────────────────────────────────


class RateLimitRuleCreate(WeDoBaseModel):
    """Create payload — REGRA 2: SEM company_id.

    WT-2022 P3.1 Phase 1 (2026-05-21): ``limit_value`` recebe constraint
    ``Field(..., gt=0)`` — bug fix canonical (aceitava negativo antes,
    quebrava semantica de rate limit).
    """

    name: str
    target_type: str  # user | agent | company | endpoint
    action_pattern: Optional[str] = None
    limit_value: int = Field(..., gt=0, description="Limit value (must be positive)")
    window_seconds: int = Field(..., gt=0, description="Window seconds (must be positive)")
    target_id: Optional[str] = None
    burst_limit: Optional[int] = Field(None, gt=0)
    is_active: bool = True
    description: Optional[str] = None


class RateLimitRuleUpdate(WeDoBaseModel):
    """Partial update.

    WT-2022 P3.1 Phase 1 (2026-05-21): mesmo constraint do Create — quando
    presente, must be positive.
    """

    name: Optional[str] = None
    target_type: Optional[str] = None
    action_pattern: Optional[str] = None
    limit_value: Optional[int] = Field(None, gt=0)
    window_seconds: Optional[int] = Field(None, gt=0)
    target_id: Optional[str] = None
    burst_limit: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None
    description: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# EscalationRule schemas
# ─────────────────────────────────────────────────────────────────────────────


class EscalationRuleCreate(WeDoBaseModel):
    """Create payload — REGRA 2: SEM company_id."""

    name: str
    trigger_type: str
    escalate_to: list[str] = []  # emails / user_ids / roles
    escalation_action: str = "notify_manager"
    condition: dict[str, Any] = {}
    notification_template: Optional[str] = None
    cooldown_seconds: int = 3600
    priority: int = 100
    is_active: bool = True
    description: Optional[str] = None


class EscalationRuleUpdate(WeDoBaseModel):
    """Partial update."""

    name: Optional[str] = None
    trigger_type: Optional[str] = None
    escalate_to: Optional[list[str]] = None
    escalation_action: Optional[str] = None
    condition: Optional[dict[str, Any]] = None
    notification_template: Optional[str] = None
    cooldown_seconds: Optional[int] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
