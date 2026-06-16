"""Add module_required and listing_type to agent_marketplace_listings;
make agent_id nullable and add template_id FK for template listings.

Revision ID: 255
Revises: 254
Create Date: 2026-06-09

Fase E — Agent Studio Meta-Platform: wires Marketplace to first-party agents
and templates, adds billing hook foundation.

Changes:
- module_required: nullable String(100) — billing module key gating install
- listing_type: Enum('agent', 'template') NOT NULL default='agent'
- agent_id: made NULLABLE to support template listings (no custom_agents row)
- template_id: nullable UUID FK → agent_template_catalog for listing_type='template'
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "255"
down_revision = "254"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create listing_type enum
    listingtypeenum = sa.Enum("agent", "template", name="listingtypeenum")
    listingtypeenum.create(op.get_bind(), checkfirst=True)

    # 2. Add module_required — nullable String, no FK (billing module key)
    op.add_column(
        "agent_marketplace_listings",
        sa.Column("module_required", sa.String(100), nullable=True),
    )

    # 3. Add listing_type enum column with server_default
    op.add_column(
        "agent_marketplace_listings",
        sa.Column(
            "listing_type",
            sa.Enum("agent", "template", name="listingtypeenum", create_type=False),
            nullable=False,
            server_default="agent",
        ),
    )

    # 4. Make agent_id nullable — template listings have no custom_agents row
    op.alter_column(
        "agent_marketplace_listings",
        "agent_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )

    # 5. Add template_id FK → agent_template_catalog (nullable; used when listing_type='template')
    op.add_column(
        "agent_marketplace_listings",
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_template_catalog.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    # 6. Indexes
    op.create_index("idx_marketplace_listing_type", "agent_marketplace_listings", ["listing_type"])
    op.create_index("idx_marketplace_module_required", "agent_marketplace_listings", ["module_required"])
    op.create_index("idx_marketplace_template_id", "agent_marketplace_listings", ["template_id"])


def downgrade() -> None:
    op.drop_index("idx_marketplace_template_id", table_name="agent_marketplace_listings")
    op.drop_index("idx_marketplace_module_required", table_name="agent_marketplace_listings")
    op.drop_index("idx_marketplace_listing_type", table_name="agent_marketplace_listings")

    op.drop_column("agent_marketplace_listings", "template_id")

    # Restore agent_id NOT NULL — requires no template listings exist
    op.alter_column(
        "agent_marketplace_listings",
        "agent_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    op.drop_column("agent_marketplace_listings", "listing_type")
    op.drop_column("agent_marketplace_listings", "module_required")

    listingtypeenum = sa.Enum("agent", "template", name="listingtypeenum")
    listingtypeenum.drop(op.get_bind(), checkfirst=True)
