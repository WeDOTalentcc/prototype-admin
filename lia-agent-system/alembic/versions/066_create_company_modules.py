"""Create company_modules table for monetizable modules.

Revision ID: 066
Revises: 065
Create Date: 2026-04-11

Supports Task #157 — Módulos Monetizáveis infrastructure.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "066"
down_revision = "065"
branch_labels = None
depends_on = None

BETA_MODULES = [
    "talent_intelligence_pro",
    "internal_mobility",
    "interview_intelligence",
    "workforce_planning",
    "candidate_nurture",
]

COMING_SOON_MODULES = [
    "onboarding_suite",
    "predictive_analytics",
]


def upgrade() -> None:
    op.create_table(
        "company_modules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", sa.String(100), sa.ForeignKey("credit_accounts.company_id"), nullable=False),
        sa.Column("module_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="beta"),
        sa.Column("tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("activated_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column("metadata", JSONB, nullable=True, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_company_modules_company", "company_modules", ["company_id"])
    op.create_index(
        "ix_company_modules_company_module",
        "company_modules",
        ["company_id", "module_name"],
        unique=True,
    )

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT DISTINCT company_id FROM credit_accounts")).fetchall()

    for row in rows:
        cid = row[0]
        for mod in BETA_MODULES:
            conn.execute(
                sa.text(
                    "INSERT INTO company_modules (id, company_id, module_name, status, tier) "
                    "VALUES (gen_random_uuid(), :cid, :mod, 'beta', 'free') "
                    "ON CONFLICT (company_id, module_name) DO NOTHING"
                ),
                {"cid": cid, "mod": mod},
            )
        for mod in COMING_SOON_MODULES:
            conn.execute(
                sa.text(
                    "INSERT INTO company_modules (id, company_id, module_name, status, tier) "
                    "VALUES (gen_random_uuid(), :cid, :mod, 'coming_soon', 'free') "
                    "ON CONFLICT (company_id, module_name) DO NOTHING"
                ),
                {"cid": cid, "mod": mod},
            )


def downgrade() -> None:
    op.drop_index("ix_company_modules_company_module", table_name="company_modules")
    op.drop_index("ix_company_modules_company", table_name="company_modules")
    op.drop_table("company_modules")
