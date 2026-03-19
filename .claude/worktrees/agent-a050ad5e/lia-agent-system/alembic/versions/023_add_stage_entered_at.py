"""Add stage_entered_at to vacancy_candidates for Pipeline Velocity Engine.

Revision ID: 023_add_stage_entered_at
Revises: 022_reconcile_missing_schemas
Create Date: 2026-03-06

Context:
  Adds stage_entered_at TIMESTAMP to vacancy_candidates so the Pipeline Velocity
  Engine (Sprint 1B) can calculate time-in-stage without joining the history table.

  Backfill: existing rows receive updated_at as a conservative proxy
  (i.e., time since last update rather than time since stage entry).
  PipelineStageService.transition_candidate() now sets this column whenever
  from_stage != to_stage, so all future transitions will be precise.
"""
from alembic import op
import sqlalchemy as sa


revision = "023_add_stage_entered_at"
down_revision = "022_reconcile_missing_schemas"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column (nullable, no default — backfill below)
    op.add_column(
        "vacancy_candidates",
        sa.Column("stage_entered_at", sa.DateTime(), nullable=True),
    )

    # Backfill: use updated_at as conservative proxy for existing rows
    op.execute(
        "UPDATE vacancy_candidates SET stage_entered_at = updated_at WHERE stage_entered_at IS NULL"
    )

    # Index for velocity queries (ORDER BY stage_entered_at, WHERE stage_entered_at IS NOT NULL)
    op.create_index(
        "ix_vacancy_candidates_stage_entered_at",
        "vacancy_candidates",
        ["stage_entered_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_vacancy_candidates_stage_entered_at", table_name="vacancy_candidates")
    op.drop_column("vacancy_candidates", "stage_entered_at")
