"""Merge orphan 027_add_pending_actions_table branch into main chain.

Revision ID: 033_merge_migration_heads
Revises: 027_add_pending_actions_table, 032_add_hitl_tables
Create Date: 2026-03-09

Context:
  Migration 027_add_pending_actions_table was created on an orphan branch
  (both 027_add_langgraph_native_checkpointer_tables and
  027_add_pending_actions_table point to 026 as down_revision, creating
  two branch heads).

  The pending_actions table content was already applied via
  031_add_pending_actions_table on the main chain. This no-op merge migration
  unifies both heads into a single head so that 'alembic heads' returns
  exactly one result.

  No DDL changes — purely a branch merge.
"""
from alembic import op


revision = "033_merge_migration_heads"
down_revision = "032_add_hitl_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
