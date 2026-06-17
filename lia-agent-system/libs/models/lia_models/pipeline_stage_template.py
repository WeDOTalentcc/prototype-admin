"""
PipelineStageTemplate — canonical per-tenant template para etapas de pipeline
(funil) de recrutamento.

Audit 2026-05-20 Sessao I Step 5 / Sprint 2 (catalogos dinamicos):
substitui o catalogo hardcoded DEFAULT_STAGES espalhado em
plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx (15 items)
+ create-job-with-candidates-modal.tsx + add-to-job-modal.tsx por modelo
per-tenant canonical.

Semantica canonical (decisao Paulo 2026-05-20):
- is_master_template=True: items curados pela WeDOTalent, visiveis a todos
  os tenants. company_id NULL (master).
- is_master_template=False: items customizados por uma company especifica.
- parent_template_id NOT NULL: este custom foi clonado de um master (copia
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


class PipelineStageTemplate(Base):
    __tablename__ = "pipeline_stage_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy: company_id NULL apenas para is_master_template=True
    # WT-2022 P0.TENANT: TENANT-EXEMPT - master template global (company_id NULL apenas quando is_master_template=True, curated by WeDOTalent)
    company_id = Column(String(255), nullable=True, index=True)

    # is_master_template=True: curated by WeDOTalent, visible to all tenants
    is_master_template = Column(Boolean, nullable=False, default=False, index=True)

    # parent_template_id: NULL pra master + custom-do-zero; UUID quando custom e copia de master
    parent_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pipeline_stage_templates.id"),
        nullable=True,
        index=True,
    )

    # Canonical JSONB com label + key + color + icon + order + is_default_in_pipeline + substatuses + metadata
    # Schema validado em app/schemas/pipeline_stage_template.py
    data = Column(JSONB, nullable=False, default=dict)

    # Audit canonical
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by = Column(String(255), nullable=True)  # User UUID
    deleted_at = Column(DateTime, nullable=True, index=True)  # Soft-delete

    # Self-referencing relationship for copia chain
    parent = relationship(
        "PipelineStageTemplate",
        remote_side=[id],
        backref="customizations",
    )

    __table_args__ = (
        Index(
            "ix_pipeline_stage_templates_company_master",
            "company_id",
            "is_master_template",
        ),
        Index(
            "ix_pipeline_stage_templates_active",
            "deleted_at",
            "is_master_template",
        ),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return (
            f"<PipelineStageTemplate(id={self.id} "
            f"is_master={self.is_master_template} "
            f"company={self.company_id})>"
        )
