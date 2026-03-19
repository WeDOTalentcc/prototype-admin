"""No-op migration — pending_actions table already created by 027_add_pending_actions_table.

Revision ID: 031_add_pending_actions_table
Revises: 030_add_prompt_version
Create Date: 2026-03-08

Context:
  This migration was originally a duplicate of 027_add_pending_actions_table.py
  (both tried to CREATE TABLE pending_actions, causing errors on fresh installs).

  The table is created by the 027 branch, which is merged via 033_merge_migration_heads.
  This migration is kept as a no-op to preserve the revision chain:
    030_add_prompt_version → 031 (no-op) → ... → 033_merge → 034 → 035

  Do not add CREATE TABLE here — the table already exists from 027.
"""
from alembic import op  # noqa: F401


revision = "031_add_pending_actions_table"
down_revision = "030_add_prompt_version"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # No-op: pending_actions table already created by 027_add_pending_actions_table
    pass


def downgrade() -> None:
    # No-op: table owned by 027_add_pending_actions_table
    pass
