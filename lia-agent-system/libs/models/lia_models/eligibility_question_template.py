"""
EligibilityQuestionTemplate — canonical per-tenant template para perguntas
de elegibilidade/screening.

Audit 2026-05-20 Sessão I Step 5 / Sprint 1 (catalogos dinamicos):
substitui o catalogo hardcoded em
`plataforma-lia/src/components/settings/eligibility-questions-bank.ts`
(449 linhas / 98 items) por modelo per-tenant canonical.

Semantica canonical (decisao Paulo 2026-05-20):
- is_master_template=True: items curados pela WeDOTalent, visiveis a todos
  os tenants. company_id pode ser NULL (master) OU um sentinel.
- is_master_template=False: items customizados por uma company especifica.
- parent_template_id NOT NULL: este custom foi clonado de um master (cópia
  total canonical A1 — snapshot definitivo, NAO sincroniza com master B1).
- deleted_at NOT NULL: soft-delete canonical (auditabilidade LGPD).

Permissoes (decisao C Paulo 2026-05-20):
- Admin: full CRUD (create, read, update, delete-soft).
- Recrutador: read + create-novos OK; NAO pode deletar nem editar de outros.
"""
import uuid
from datetime import datetime
from typing import Any

from lia_config.database import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship


class EligibilityQuestionTemplate(Base):
    __tablename__ = "eligibility_question_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy: company_id NULL apenas para is_master_template=True
    # WT-2022 P0.TENANT: TENANT-EXEMPT - master template global (company_id NULL apenas quando is_master_template=True, curated by WeDOTalent)
    company_id = Column(String(255), nullable=True, index=True)

    # is_master_template=True: curated by WeDOTalent, visible to all tenants
    is_master_template = Column(Boolean, nullable=False, default=False, index=True)

    # parent_template_id: NULL pra master + custom-do-zero; UUID quando custom é cópia de master
    parent_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("eligibility_question_templates.id"),
        nullable=True,
        index=True,
    )

    # Canonical JSONB com question + type + category + options + triggers
    # Schema validado em app/schemas/eligibility_question_template.py
    data = Column(JSONB, nullable=False, default=dict)

    # Audit canonical
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = Column(String(255), nullable=True)  # User UUID
    deleted_at = Column(DateTime, nullable=True, index=True)  # Soft-delete

    # Self-referencing relationship for cópia chain
    parent = relationship(
        "EligibilityQuestionTemplate",
        remote_side=[id],
        backref="customizations",
    )

    # Onda 4-Fase8 (2026-05-24): fix indentação do {"extend_existing": True}
    # que estava desalinhada (codemod paralelo). Bloqueava alembic upgrade head
    # + qualquer import de lia_models/__init__.py via Python loader (SQLAlchemy
    # tentava parsear o dict como argumento posicional dos Index).
    __table_args__ = (
        Index(
            "ix_elig_templates_company_master",
            "company_id",
            "is_master_template",
        ),
        Index(
            "ix_elig_templates_active",
            "deleted_at",
            "is_master_template",
        ),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return (
            f"<EligibilityQuestionTemplate(id={self.id} "
            f"is_master={self.is_master_template} "
            f"company={self.company_id})>"
        )
