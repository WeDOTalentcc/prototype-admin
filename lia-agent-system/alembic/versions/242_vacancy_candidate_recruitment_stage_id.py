"""Add vacancy_candidates.recruitment_stage_id structural link (migration 242).

Revision ID: 242
Revises: 241
Create Date: 2026-06-04

Task #1303 — Make the SLA-near-expiration alert reliable by binding a candidate
to the correct funnel stage via a stable identifier instead of fragile textual
name matching.

`SlaNearExpirationDetector` previously discovered a stage SLA by matching the
candidate's free-form ``vacancy_candidates.stage`` text against
``recruitment_stages.name``. Any naming divergence (accentuation, casing, a
later rename) silently broke the join and the alert never fired for those
candidates.

This adds a nullable ``recruitment_stage_id`` column so new stage transitions
record the real ``recruitment_stages.id``; the detector joins by id when present
and falls back to name only for legacy rows. Nullable + no FK constraint keeps
the migration safe on dev and prod (legacy rows and cross-schema data remain
valid) and idempotent via IF NOT EXISTS.
"""
from alembic import op

revision = "242"
down_revision = "241"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE vacancy_candidates "
        "ADD COLUMN IF NOT EXISTS recruitment_stage_id UUID"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vacancy_candidates_recruitment_stage_id "
        "ON vacancy_candidates (recruitment_stage_id)"
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_vacancy_candidates_recruitment_stage_id"
    )
    op.execute(
        "ALTER TABLE vacancy_candidates DROP COLUMN IF EXISTS recruitment_stage_id"
    )
