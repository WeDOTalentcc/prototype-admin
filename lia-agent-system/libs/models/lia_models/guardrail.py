"""
Guardrail — Fase 3

Regras de comportamento dos agentes persistidas no banco de dados.
Editáveis em produção via interface admin sem necessidade de deploy.

Níveis:
  primary   — aplica a todos os agentes/domínios (company_id=None = global)
  secondary — aplica a um domínio específico (domain != None)

Uso:
  GuardrailRepository.get_active(domain, company_id) → lista de Guardrail
  O ReAct loop consulta guardrails antes de permitir tool calls sensíveis.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from lia_config.database import Base


class Guardrail(Base):
    """
    Regra de comportamento de agente persistida no banco.

    Campos:
        level           'primary' (todos agentes) | 'secondary' (domínio específico)
        domain          None = aplica a todos; ou ex: 'pipeline', 'sourcing', 'cv_screening'
        node            None = todos os nós do domínio; ou nome de nó específico
        tool            None = não bloqueia tool específica; ou nome da tool a bloquear
        rule            Texto da regra em linguagem natural (usado no system prompt)
        blocking_message Mensagem exibida ao usuário quando a ação é bloqueada
        is_active       Pode ser desativado sem deletar (audit trail preservado)
        company_id      None = global (todos tenants); ou UUID do tenant específico
        updated_by      user_id de quem editou por último
        updated_at      timestamp da última edição
    """
    __tablename__ = "guardrails"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    level = Column(String(20), nullable=False, default="primary")  # 'primary' | 'secondary'
    domain = Column(String(100), nullable=True)   # None = todos os domínios
    node = Column(String(100), nullable=True)     # None = todos os nós
    tool = Column(String(200), nullable=True)     # None = não específico de tool
    rule = Column(Text, nullable=False)
    blocking_message = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    # TENANT-EXEMPT: Guardrail com company_id NULL = guardrail global do sistema (comentario inline confirma)
    company_id = Column(String(36), nullable=True)  # None = global
    updated_by = Column(String(36), nullable=False, default="system")
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<Guardrail id={self.id} level={self.level} "
            f"domain={self.domain} tool={self.tool} active={self.is_active}>"
        )
