"""
ARQUIVO NOVO: libs/models/lia_models/agent_template.py

Modelo AgentTemplate para o Agent Studio.

COMO APLICAR:
  1. Copiar para libs/models/lia_models/agent_template.py
  2. Adicionar import em libs/models/lia_models/__init__.py:
     from .agent_template import AgentTemplate
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from lia_config.database import Base


class AgentTemplateStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AgentTemplate(Base):
    """
    Template de agente LIA customizável por empresa.

    company_id=None → template público da WeDO (fallback global)
    company_id=<id> → template customizado do cliente (prioridade sobre WeDO)

    Cada edição cria uma nova versão (versões publicadas são imutáveis).
    O registry sempre usa a versão published mais recente do cliente,
    com fallback para o template público WeDO.
    """

    __tablename__ = "agent_templates"
    __table_args__ = (
        Index("ix_agent_templates_company_domain", "company_id", "domain", "status"),
        Index("ix_agent_templates_public", "domain", "status"),
        {"extend_existing": True},
    )

    id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # NULL = template público WeDO; preenchido = customizado pelo cliente
    company_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    name: Mapped[str] = mapped_column(String(500), nullable=False)

    # Domínio do agente (sourcing, pipeline, wsi, lia_assistant, job_wizard, etc.)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)

    # System prompt em YAML com variáveis {{variable_name}}
    system_prompt_yaml: Mapped[str] = mapped_column(Text, nullable=False)

    # Versão: começa em 1, incrementa a cada save
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Status do ciclo de vida
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=AgentTemplateStatus.DRAFT
    )

    # Template WeDO de origem (rastreabilidade de customizações)
    base_template_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey("agent_templates.id"), nullable=True
    )

    # Quem criou este template
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    @property
    def is_public(self) -> bool:
        """Template público da WeDO (não pertence a nenhuma empresa)."""
        return self.company_id is None

    @property
    def is_published(self) -> bool:
        return self.status == AgentTemplateStatus.PUBLISHED

    def __repr__(self) -> str:
        return (
            f"<AgentTemplate domain={self.domain} company={self.company_id or 'WeDO'} "
            f"v={self.version} status={self.status}>"
        )
