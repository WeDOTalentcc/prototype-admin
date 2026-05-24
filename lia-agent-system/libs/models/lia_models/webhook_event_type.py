"""
WebhookEventType — canonical per-tenant catalogo de eventos de webhook.

Audit 2026-05-20 Sprint 5 (catalogos dinamicos):
substitui o catalogo hardcoded em
`plataforma-lia/src/components/pages-agent-studio/custom-agents/webhook-types.ts`
(6 items) + `lia-agent-system/app/schemas/webhook.py:ALLOWED_EVENTS` (6) +
`libs/models/lia_models/webhook_registration.py:JOB_STATUS_WEBHOOK_EVENTS` (4)
+ `libs/models/lia_models/webhook.py:WebhookEvent` enum (7) por modelo
per-tenant canonical no DB.

Semantica canonical (decisao Paulo 2026-05-20, mesmo pattern de Sprint 1):
- is_master_template=True: items curados pela WeDOTalent (eventos do produto),
  visiveis a todos os tenants. company_id NULL.
- is_master_template=False: items customizados por uma company especifica
  (ex: eventos custom internos do tenant).
- parent_template_id NOT NULL: este custom foi clonado de um master
  (cópia total canonical A1 — snapshot definitivo, NAO sincroniza B1).
- deleted_at NOT NULL: soft-delete canonical (auditabilidade LGPD).

Permissoes (decisao C Paulo 2026-05-20):
- Admin: full CRUD (create, read, update, delete-soft).
- Recrutador: read + create-novos OK; NAO pode deletar nem editar de outros.
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


class WebhookEventType(Base):
    __tablename__ = "webhook_event_types"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy: company_id NULL apenas para is_master_template=True
    # WT-2022 P0.TENANT: TENANT-EXEMPT - master template global (company_id NULL apenas quando is_master_template=True, curated by WeDOTalent)
    company_id = Column(String(255), nullable=True, index=True)

    # is_master_template=True: curated by WeDOTalent, visible to all tenants
    is_master_template = Column(Boolean, nullable=False, default=False, index=True)

    # parent_template_id: NULL pra master + custom-do-zero; UUID quando custom é cópia de master
    parent_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("webhook_event_types.id"),
        nullable=True,
        index=True,
    )

    # Canonical JSONB com event_type + label + category + description + payload_schema + deprecated + metadata
    # Schema validado em app/schemas/webhook_event_type.py
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
        "WebhookEventType",
        remote_side=[id],
        backref="customizations",
    )

    __table_args__ = (
        Index(
            "ix_webhook_event_types_company_master",
            "company_id",
            "is_master_template",
        ),
        Index(
            "ix_webhook_event_types_active",
            "deleted_at",
            "is_master_template",
        ),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return (
            f"<WebhookEventType(id={self.id} "
            f"is_master={self.is_master_template} "
            f"company={self.company_id})>"
        )
