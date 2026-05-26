"""Bug 1 fix — department_members.user_id FK + sync user_id when email match

Plan canonical: ~/.claude/plans/jolly-roaming-moler.md.
Decision Paulo 2026-05-25: option B (linkage) — keep department_members table
for external contacts (consultants, hiring manager contact) AND add user_id FK
to link to users table when member IS a platform user.

Revision ID: 205
Revises: 204
"""
from alembic import op
import sqlalchemy as sa


revision = "205"
down_revision = "204"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "department_members",
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
            comment="If member is a platform user, link to users.id. NULL = external contact (no login).",
        ),
    )
    # Backfill: link existing department_members to users by email match
    op.execute(
        """
        UPDATE department_members dm
        SET user_id = u.id
        FROM users u
        WHERE dm.user_id IS NULL
          AND dm.email IS NOT NULL
          AND lower(dm.email) = lower(u.email)
        """
    )


def downgrade():
    op.drop_column("department_members", "user_id")
