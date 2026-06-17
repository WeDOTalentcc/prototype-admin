"""Sprint 5 RBAC — add users.can_view_salary BOOLEAN

Plan canonical: ~/.claude/plans/jolly-roaming-moler.md (Sprint 5).
LGPD Art. 6 III (minimização) — financial PII (salary fields) gated by explicit
permission grant. Decision Paulo 2026-05-25: minimal financial-only scope + explicit
permission (not role-based) for granular admin control.

Default FALSE = no one sees salary unless admin explicit-grants.

Revision ID: 204
Revises: 203
"""
from alembic import op
import sqlalchemy as sa


revision = "204"
down_revision = "203"
branch_labels = None
depends_on = None


def upgrade():
    # Add boolean column, default FALSE (no one sees salary by default — opt-in grant)
    op.add_column(
        "users",
        sa.Column(
            "can_view_salary",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Backfill: admins + wedotalent_admin keep the privilege (transitional bootstrap)
    # so existing platform admins can immediately see salary without re-grant.
    op.execute(
        """
        UPDATE users
        SET can_view_salary = true
        WHERE role = 'admin'
"""
    )


def downgrade():
    op.drop_column("users", "can_view_salary")
