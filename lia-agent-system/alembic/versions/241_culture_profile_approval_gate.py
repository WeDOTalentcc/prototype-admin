"""Context Center approval gate (Fase 5.1) — culture profile HITL approval fields.

Revision ID: 241
Revises: 240
Create Date: 2026-06-04

Auto-generated culture profiles (``source='auto'``, scrape+LLM) must be
human-approved before they feed agent prompts (LGPD/bias governance — the
ghost-context gate). Adds:

- ``is_approved`` BOOLEAN NOT NULL DEFAULT false — existing auto profiles become
  pending (strict gate, product decision 2026-06-04: no live clients yet, do it
  correctly). Human-authored profiles (source != 'auto') are NOT gated by the
  consumer regardless of this flag, so no backfill is required.
- ``approved_at`` TIMESTAMP NULL — when a human approved.
- ``approved_by_user_id`` UUID NULL — who approved.

Consumer gate lives in
``CultureProfileRepository.get_for_agent_context`` (withholds source='auto' &&
not is_approved). UI/approval flows keep using ``get_for_company``.

Idempotent (IF NOT EXISTS). Safe on dev and prod via the standard Alembic flow.
"""
from alembic import op

revision = "241"
down_revision = "240"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE company_culture_profiles "
        "ADD COLUMN IF NOT EXISTS is_approved BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE company_culture_profiles "
        "ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP NULL"
    )
    op.execute(
        "ALTER TABLE company_culture_profiles "
        "ADD COLUMN IF NOT EXISTS approved_by_user_id UUID NULL"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE company_culture_profiles DROP COLUMN IF EXISTS approved_by_user_id"
    )
    op.execute(
        "ALTER TABLE company_culture_profiles DROP COLUMN IF EXISTS approved_at"
    )
    op.execute(
        "ALTER TABLE company_culture_profiles DROP COLUMN IF EXISTS is_approved"
    )
