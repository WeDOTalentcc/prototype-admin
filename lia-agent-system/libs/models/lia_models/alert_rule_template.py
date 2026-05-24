"""
AlertRuleTemplate — canonical per-tenant template para alert rules
(notificações de eventos do pipeline de recrutamento).

Audit 2026-05-20 Sessão I / Sprint 3 (catalogos dinamicos):
substitui o catalogo hardcoded DEFAULT_ALERTS em
plataforma-lia/src/components/settings/communication-hub/CommunicationHub.constants.ts
por modelo per-tenant canonical.

Semantica canonical (decisao Paulo 2026-05-20):
- is_master_template=True: items curados pela WeDOTalent, visiveis a todos
  os tenants. company_id NULL (master).
- is_master_template=False: items customizados por uma company especifica.
- parent_template_id NOT NULL: este custom foi clonado de um master (cópia
  total canonical A1 — snapshot definitivo, NAO sincroniza com master B1).
- deleted_at NOT NULL: soft-delete canonical (auditabilidade LGPD).

Permissoes (decisao C Paulo 2026-05-20):
- Admin: full CRUD (create, read, update, delete-soft).
- Recrutador: read + create-novos OK; NAO pode deletar; edita apenas seus
  proprios (ownership por created_by).
"""
import uuid
from datetime import datetime

from lia_config.database import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship


class AlertRuleTemplate(Base):
    __tablename__ = "alert_rule_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy: company_id NULL apenas para is_master_template=True
    # WT-2022 P0.TENANT: TENANT-EXEMPT - master template global (company_id NULL apenas quando is_master_template=True, curated by WeDOTalent)
    company_id = Column(String(255), nullable=True, index=True)

    # is_master_template=True: curated by WeDOTalent, visible to all tenants
    is_master_template = Column(Boolean, nullable=False, default=False, index=True)

    # parent_template_id: NULL pra master + custom-do-zero; UUID quando custom é cópia de master
    parent_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("alert_rule_templates.id"),
        nullable=True,
        index=True,
    )

    # Canonical JSONB com event_type + label + audience + channels + delay_minutes +
    # schedule_lgpd_compliant + rationale. Schema validado em
    # app/schemas/alert_rule_template.py
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
        "AlertRuleTemplate",
        remote_side=[id],
        backref="customizations",
    )

    __table_args__ = (
        Index(
            "ix_alert_rule_templates_company_master",
            "company_id",
            "is_master_template",
        ),
        Index(
            "ix_alert_rule_templates_active",
            "deleted_at",
            "is_master_template",
        ),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return (
            f"<AlertRuleTemplate(id={self.id} "
            f"is_master={self.is_master_template} "
            f"company={self.company_id})>"
        )
