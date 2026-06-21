"""275 — Adiciona tier_policies a tenant_llm_configs.

Revision ID: 275_add_tier_policies
Revises: 274_seed_ii_agent_studio
Create Date: 2026-06-13

Sprint D (ModelTierResolver): permite override de tier por dominio per-tenant.
Ex: {"screening": {"tier": "heavy", "threshold": 0.70}}
NULL = usa DOMAIN_TIER_DEFAULTS da plataforma (default).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "275_add_tier_policies"
down_revision = "275_seed_ti_agent_studio"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenant_llm_configs",
        sa.Column("tier_policies", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenant_llm_configs", "tier_policies")
