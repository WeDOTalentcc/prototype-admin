"""
RoleScopeFilter — permissões declarativas por role, consultadas em runtime.

Sprint C (2026-06-13): substitui gradualmente @requires_permission hardcoded
em endpoints. Permissões vivem na tabela, não no código.

Harness: Guide computacional — enforcement pelo ScopeFilterMiddleware,
         não pelo modelo/LLM.
"""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from lia_config.database import Base


class RoleScopeFilter(Base):
    """Permissão declarativa por (role, resource, action)."""
    __tablename__ = "role_scope_filters"
    __table_args__ = (
        UniqueConstraint("role", "resource", "action", name="uq_role_resource_action"),
        Index("ix_rsf_role_resource", "role", "resource"),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role = Column(String(50), nullable=False, index=True)
    resource = Column(String(80), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    allowed = Column(Boolean, nullable=False, default=True)
    conditions = Column(JSONB, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<RoleScopeFilter {self.role}:{self.resource}:{self.action}={OK if self.allowed else DENY}>"


# ─── Permissões padrão ────────────────────────────────────────────────────────
# Fonte canônica das permissões da plataforma.
# NUNCA adicionar permissão nova só em decorator de endpoint.
# Adicionar AQUI primeiro → sensor check_hardcoded_permissions.py verifica.

_RESOURCES = ["job", "candidate", "screening", "communication", "offer",
               "report", "policy", "hiring_policy", "admin", "platform"]
_CRUD = ["create", "read", "update", "delete"]
_ALL_ACTIONS = _CRUD + ["execute", "admin", "export"]


def _allow(role: str, resource: str, *actions) -> list:
    return [{"role": role, "resource": resource, "action": a, "allowed": True}
            for a in actions]


def _deny(role: str, resource: str, *actions) -> list:
    return [{"role": role, "resource": resource, "action": a, "allowed": False}
            for a in actions]


DEFAULT_ROLE_PERMISSIONS: list = [

    # ── wedotalent_admin — staff WeDOTalent, acesso total ──────────────────
    *_allow("wedotalent_admin", "job",            *_ALL_ACTIONS),
    *_allow("wedotalent_admin", "candidate",      *_ALL_ACTIONS),
    *_allow("wedotalent_admin", "screening",      *_ALL_ACTIONS),
    *_allow("wedotalent_admin", "communication",  *_ALL_ACTIONS),
    *_allow("wedotalent_admin", "offer",          *_ALL_ACTIONS),
    *_allow("wedotalent_admin", "report",         *_ALL_ACTIONS),
    *_allow("wedotalent_admin", "policy",         *_ALL_ACTIONS),
    *_allow("wedotalent_admin", "hiring_policy",  *_ALL_ACTIONS),
    *_allow("wedotalent_admin", "admin",          *_ALL_ACTIONS),
    *_allow("wedotalent_admin", "platform",       *_ALL_ACTIONS),

    # ── admin (tenant_admin) — administrador de uma empresa ────────────────
    *_allow("admin", "job",           *_CRUD),
    *_allow("admin", "candidate",     *_CRUD),
    *_allow("admin", "screening",     *_CRUD),
    *_allow("admin", "communication", *_CRUD),
    *_allow("admin", "offer",         *_CRUD),
    *_allow("admin", "report",        "read", "export"),
    *_allow("admin", "policy",        "read", "update"),
    *_allow("admin", "hiring_policy", *_CRUD),
    *_allow("admin", "admin",         "read", "update"),
    *_deny("admin",  "platform",      "admin"),

    # ── manager (hiring manager) — gestores de contratação ─────────────────
    *_allow("manager", "job",           "read", "update"),
    *_allow("manager", "candidate",     "read", "update"),
    *_allow("manager", "screening",     "read", "update"),
    *_allow("manager", "communication", "read"),
    *_allow("manager", "offer",         "read", "update"),
    *_allow("manager", "report",        "read"),
    *_allow("manager", "hiring_policy", "read"),
    *_deny("manager",  "job",           "create", "delete"),
    *_deny("manager",  "policy",        "create", "update", "delete"),

    # ── recruiter — recrutadores ────────────────────────────────────────────
    *_allow("recruiter", "job",           "create", "read", "update"),
    *_allow("recruiter", "candidate",     "create", "read", "update"),
    *_allow("recruiter", "screening",     "create", "read", "update"),
    *_allow("recruiter", "communication", "create", "read", "update"),
    *_allow("recruiter", "offer",         "create", "read", "update"),
    *_allow("recruiter", "report",        "read"),
    *_deny("recruiter",  "job",           "delete"),
    *_deny("recruiter",  "candidate",     "delete"),
    *_deny("recruiter",  "policy",        "create", "update", "delete"),
    *_deny("recruiter",  "admin",         "create", "update", "delete"),

    # ── viewer — acesso leitura ─────────────────────────────────────────────
    *_allow("viewer", "job",           "read"),
    *_allow("viewer", "candidate",     "read"),
    *_allow("viewer", "screening",     "read"),
    *_allow("viewer", "communication", "read"),
    *_allow("viewer", "offer",         "read"),
    *_allow("viewer", "report",        "read"),
    *_deny("viewer",  "job",           "create", "update", "delete"),
    *_deny("viewer",  "candidate",     "create", "update", "delete"),
    *_deny("viewer",  "screening",     "create", "update", "delete"),
    *_deny("viewer",  "offer",         "create", "update", "delete"),
    *_deny("viewer",  "policy",        "create", "update", "delete"),
    *_deny("viewer",  "admin",         "create", "update", "delete"),

    # digest -- envio/visualizacao de digests (admin-only para outros usuarios)
    *_allow("admin",            "digest", "read", "send_self", "send_others", "send_all"),
    *_allow("wedotalent_admin", "digest", "read", "send_self", "send_others", "send_all"),
    *_allow("recruiter",        "digest", "read", "send_self"),
    *_deny("recruiter",         "digest", "send_others", "send_all"),
    *_allow("manager",          "digest", "read", "send_self"),
    *_deny("manager",           "digest", "send_others", "send_all"),
    *_allow("viewer",           "digest", "read"),
    *_deny("viewer",            "digest", "send_self", "send_others", "send_all"),
]
