"""W2-012 · add region column to tenant_llm_configs (LGPD Art 33)

Revision ID: 178_tenant_llm_config_region
Revises: 177_custom_agent_voice_enabled
Create Date: 2026-05-22

W2-012 do MASTER_PLAN.md de remediação enterprise.
Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W2-012).

Adiciona campo `region` a tenant_llm_configs para LGPD Art 33 region
pinning per-tenant. NULL = usa default global do provider:
- Gemini: us-central1 (via LIA_GEMINI_DEFAULT_REGION env)
- Claude: sem region constraint (header anthropic-no-train aplicado global)
- OpenAI: sem region constraint (header OpenAI-Beta=data-residency=v1 global)

Cliente que precisa de region específica (ex: sa-east-1 pra dados BR
sob ANPD jurisdição) seta `region` per-tenant via admin UI (Phase B).
"""
from alembic import op
import sqlalchemy as sa


revision = "178_tenant_llm_config_region"
down_revision = "177_custom_agent_voice_enabled"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "tenant_llm_configs",
        sa.Column("region", sa.String(50), nullable=True),
    )


def downgrade():
    op.drop_column("tenant_llm_configs", "region")
