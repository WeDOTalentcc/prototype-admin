"""Backfill vacancy_candidates.recruitment_stage_id from stage name (migration 243).

Revision ID: 243
Revises: 242
Create Date: 2026-06-04

Task #1306 — Make the structural stage link (``vacancy_candidates.recruitment_stage_id``
↔ ``recruitment_stages.id``) reliable end-to-end. Migration 242 added the column
and new writes now populate it, but legacy rows created before this change still
carry only the free-form ``stage`` text.

This one-off backfill resolves ``recruitment_stage_id`` for legacy rows by
matching ``vacancy_candidates.stage`` against ``recruitment_stages.name`` within
the same company, case/whitespace-insensitively. To stay safe it only fills rows
where the link is currently NULL and where the name resolves to exactly ONE
active stage for that company (ambiguous names are left untouched so the SLA
detector keeps its name fallback). Idempotent: re-running only touches NULLs.
"""
from alembic import op

revision = "243"
down_revision = "242"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE vacancy_candidates vc
        SET recruitment_stage_id = rs.id
        FROM recruitment_stages rs
        WHERE vc.recruitment_stage_id IS NULL
          AND vc.stage IS NOT NULL
          AND rs.company_id = vc.company_id
          AND rs.is_active = true
          AND lower(trim(rs.name)) = lower(trim(vc.stage))
          AND (
            SELECT COUNT(*) FROM recruitment_stages rs2
            WHERE rs2.company_id = vc.company_id
              AND rs2.is_active = true
              AND lower(trim(rs2.name)) = lower(trim(vc.stage))
          ) = 1
        """
    )


def downgrade() -> None:
    # No-op: the column itself is dropped by migration 242's downgrade. We do not
    # null out values on downgrade because we cannot distinguish backfilled rows
    # from rows populated by application writes.
    pass
