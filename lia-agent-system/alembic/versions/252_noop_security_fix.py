"""Migration 252 — no-op placeholder (security fix).

The original migration 252 contained a hardcoded bcrypt password hash for a
production admin account, which is a security violation.  That content has been
removed.  This file preserves the revision ID in the Alembic chain so that
databases which already applied revision 252 can continue to run
`alembic upgrade head` without errors.

Revision ID: 252
Revises: 251_drop_duplicate_indexes
Create Date: 2026-06-08
"""
revision = "252"
down_revision = "251_drop_duplicate_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
