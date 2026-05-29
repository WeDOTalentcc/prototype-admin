"""
AgentTemplateCatalog — catálogo seed global de templates pré-prontos do Agent Studio.

Sprint 3 Caminho B (2026-05-25): tabela NOVA, separada do `agent_templates`
existente (que é per-tenant publishable, conceito diferente). Decisão Paulo:
isolar conceitos pra evitar acoplamento.

Conceito canonical:
- Catálogo seed global (`company_id` NULL hoje) — 16 templates pré-prontos.
- Extensibilidade via tabelas auxiliares `agent_categories` + `agent_sectors`.
  Adicionar categoria nova (ex: NPS) = 1 INSERT em `agent_categories` —
  sem deploy de código.
- Read-mostly: clientes consomem via GET. Mutations (POST/PUT/DELETE) apenas
  para staff WeDOTalent (UserRole.wedotalent_admin).

Refs:
- ~/Documents/wedotalent_audit_2026-05-25/AGENT_STUDIO_IMPLEMENTATION_PLAN.md §4
- CLAUDE.md "Per-tenant AI persona canonical pattern" — separação clean similar.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from lia_config.database import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID


class AgentCategory(Base):
    """Catálogo extensível de categorias de templates.

    Extensibilidade NPS: 1 INSERT aqui ativa categoria nova sem deploy
    (Apêndice 8.1 do plano canonical).
    """

    __tablename__ = "agent_categories"
    __table_args__ = ({"extend_existing": True},)

    # PK é slug curto canonical (ex: "screening", "sourcing", "nps")
    id = Column(String(64), primary_key=True)
    label_pt = Column(String(128), nullable=False)
    label_en = Column(String(128), nullable=False)
    icon = Column(String(64), nullable=True)  # lucide-react name
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AgentSector(Base):
    """Catálogo extensível de setores/verticais (tech, saude, ...)."""

    __tablename__ = "agent_sectors"
    __table_args__ = ({"extend_existing": True},)

    id = Column(String(64), primary_key=True)
    label_pt = Column(String(128), nullable=False)
    label_en = Column(String(128), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class AgentTemplateCatalog(Base):
    """Catálogo de templates pré-prontos para o Agent Studio.

    company_id NULL = template global WeDOTalent (default hoje).
    company_id NOT NULL = futuro per-tenant catalog (não usado em V1).

    NÃO confundir com `AgentTemplate` (libs/models/lia_models/agent_template.py)
    que é per-tenant publishable com versionamento YAML.
    """

    __tablename__ = "agent_template_catalog"
    __table_args__ = (
        Index("ix_agent_template_catalog_company", "company_id"),
        Index("ix_agent_template_catalog_active", "is_active"),
        Index("ix_agent_template_catalog_category", "category_id"),
        {"extend_existing": True},
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Slug canonical preservado do hardcoded TS (ex: "tpl-triagem-tech")
    slug = Column(String(128), nullable=False, unique=True, index=True)

    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)

    # FK rígida pra catálogo extensível
    category_id = Column(
        String(64),
        ForeignKey("agent_categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    sector_id = Column(
        String(64),
        ForeignKey("agent_sectors.id", ondelete="SET NULL"),
        nullable=True,
    )

    system_prompt = Column(Text, nullable=False)
    allowed_tools = Column(JSONB, nullable=False, server_default="[]")
    context_level = Column(String(32), nullable=False, default="standard")
    max_steps = Column(Integer, nullable=False, default=10)
    temperature = Column(Float, nullable=False, default=0.7)
    enable_memory = Column(Boolean, nullable=False, default=True)
    excluded_tools = Column(JSONB, nullable=False, server_default="[]")
    tags = Column(JSONB, nullable=False, server_default="[]")
    vertical_prompts = Column(JSONB, nullable=True)

    # White-label per decisão Paulo #10 (2026-05-25 Sprint 2):
    # icon = nome lucide-react canonical (mantemos neutro vs cyan da LIA)
    # accent_color = token DS neutro (ink/graphite/slate/mist)
    icon = Column(String(64), nullable=True)
    accent_color = Column(String(32), nullable=True)
    badge_variant = Column(String(32), nullable=True)

    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    # company_id NULL hoje (templates globais). Future per-tenant marketplace.
    # TENANT-EXEMPT: V1 catálogo global read-mostly; mutations gated por
    # UserRole.wedotalent_admin no endpoint (sem fan-out tenant ainda).
    # C5.3 (2026-05-29): no index=True here — the explicit
    # Index("ix_agent_template_catalog_company") in __table_args__ is the single
    # source of truth. The duplicate ix_agent_template_catalog_company_id
    # (autogenerated by index=True) is dropped in migration 223 (AUDIT 6 P2-10).
    company_id: Optional[str] = Column(String(255), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<AgentTemplateCatalog slug={self.slug} category={self.category_id} "
            f"active={self.is_active}>"
        )
