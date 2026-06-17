"""
IntegrationCatalogEntry — canonical per-tenant catalog para integracoes
(ATS / AI models / Calendar / Communication / CRM-HRIS / MCPs-APIs).

Audit 2026-05-20 Sessão I Step 5 / Sprint 4 (catalogos dinamicos):
substitui o catalogo hardcoded em
`plataforma-lia/src/components/settings/integrations/integration-data.ts`
(370 linhas / 16 entradas — Gemini/Claude/OpenAI/Gupy/Pandapé/Merge/etc)
por modelo per-tenant canonical.

Semantica canonical (decisao Paulo 2026-05-20):
- is_master_template=True: providers curados pela WeDOTalent, visiveis a todos
  os tenants. company_id eh NULL.
- is_master_template=False: items customizados por uma company especifica
  (override de logo, descricao, status, capabilities).
- parent_template_id NOT NULL: este custom foi clonado de um master (cópia
  total canonical A1 — snapshot definitivo, NAO sincroniza com master B1).
- deleted_at NOT NULL: soft-delete canonical (auditabilidade LGPD).

Permissoes (decisao C Paulo 2026-05-20):
- Admin: full CRUD (create, read, update, delete-soft).
- Recrutador: read + create-novos OK; NAO pode deletar nem editar de outros.

Schema canonical do JSONB `data` (validado em
app/schemas/integration_catalog_entry.py):

{
  "provider": "gupy",                     // slug canonical
  "label": "Gupy",
  "category": "ats",                      // ai_models|ats|calendar|...
  "logo_url": "/logos/gupy.png",          // opcional
  "description": "...",                   // shortDescription
  "full_description": "...",              // fullDescription opcional
  "status": "production" | "coming_soon",
  "industries_recommended": ["..."],      // opcional
  "metadata": {                           // catch-all ui hints
    "icon_bg": "bg-pink-500/10",
    "icon_color": "text-pink-600",
    "icon_letter": "Gy",
    "connect_action": "config",
    "config_fields": ["GUPY_API_TOKEN"],
    "capabilities": [{"name": "...", "description": "..."}],
    "is_active_provider": false,
    ...
  }
}
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


class IntegrationCatalogEntry(Base):
    __tablename__ = "integration_catalog_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy: company_id NULL apenas para is_master_template=True
    # WT-2022 P0.TENANT: TENANT-EXEMPT - master template global (company_id NULL apenas quando is_master_template=True, curated by WeDOTalent)
    company_id = Column(String(255), nullable=True, index=True)

    # is_master_template=True: curated by WeDOTalent, visible to all tenants
    is_master_template = Column(Boolean, nullable=False, default=False, index=True)

    # parent_template_id: NULL pra master + custom-do-zero; UUID quando custom é cópia de master
    parent_template_id = Column(
        UUID(as_uuid=True),
        ForeignKey("integration_catalog_entries.id"),
        nullable=True,
        index=True,
    )

    # Canonical JSONB com provider + label + category + status + metadata
    # Schema validado em app/schemas/integration_catalog_entry.py
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
        "IntegrationCatalogEntry",
        remote_side=[id],
        backref="customizations",
    )

    __table_args__ = (
        Index(
            "ix_integration_catalog_company_master",
            "company_id",
            "is_master_template",
        ),
        Index(
            "ix_integration_catalog_active",
            "deleted_at",
            "is_master_template",
        ),
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        provider = (self.data or {}).get("provider") if self.data else None
        return (
            f"<IntegrationCatalogEntry(id={self.id} "
            f"provider={provider} "
            f"is_master={self.is_master_template} "
            f"company={self.company_id})>"
        )
