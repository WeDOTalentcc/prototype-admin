"""Sprint 8 RBAC — add users.can_view_sensitive_pii BOOLEAN DEFAULT true

Plan: ~/.claude/plans/jolly-roaming-moler.md.
Decision Paulo 2026-05-26:
  - Escopo: CPF + DoB + endereço completo + secondary email/phone + personal/business emails lists
  - Estrutura: misto (separado de can_view_salary)
  - Default=true (zero quebra, opt-out per-user via admin grant)

Diff vs Sprint 5 salary (default=false): aqui default=true pra preservar
visibilidade atual; admin pode revogar per-user depois.

Revision ID: 206
Revises: 205
"""
from alembic import op
import sqlalchemy as sa


revision = "207"
down_revision = "206"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "can_view_sensitive_pii",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
            comment="LGPD Art. 5 II — grant to view sensitive PII (CPF, DoB, address, "
                    "secondary contacts). Default true: preserves current behavior; admin "
                    "can revoke per-user. Distinct from can_view_salary (financial PII).",
        ),
    )


def downgrade():
    op.drop_column("users", "can_view_sensitive_pii")
