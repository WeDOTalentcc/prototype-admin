"""Add LGPD retention columns to activity_feed table.

Revision ID: 197
Revises: 196
Create Date: 2026-05-25

Context (Task 2.C — LGPD retention 2026-05-25):
  LGPD (Lei 13.709/2018) Art. 15 requires data to be deleted when its purpose
  ends or retention period expires. Art. 20 requires transparency about
  automated decisions. Art. 7 requires a documented legal basis for every
  personal data processing operation.

  Three nullable columns added to `activity_feed`:

  1. retention_expires_at (TIMESTAMP): when this record should be purged.
     Null = system event or indefinite retention (e.g. audit logs, LGPD
     legal_obligation basis). Candidate-related activities should be set to
     created_at + 24 months per WeDO retention policy (Art. 15 §1 —
     legitimate_interests basis). A future scheduled job reads this column to
     batch-delete expired rows.

  2. legal_basis (VARCHAR 50): LGPD Art. 7 legal basis for data processing.
     canonical values: consent | contract | legal_obligation | vital_interests
                       | public_task | legitimate_interests
     Null = not yet classified (legacy rows); new inserts must populate this.
     Default at application level: 'legitimate_interests' (recruitment).

  3. decision_type (VARCHAR 50): LGPD Art. 20 automated decision transparency.
     canonical values: automated | human_review | human_final | no_decision
     Null = not applicable (non-decision activities). New automated screening
     activities must set automated or human_review.

Migration strategy: ADD COLUMN ... NULL (no default at DB level, avoids
table rewrite on large tables). Application layer sets values on new inserts.
Existing rows left NULL — classified as legacy data, subject to bulk-update
script (separate ops task, out of scope of this migration).

Index on retention_expires_at for future purge scheduler query:
  WHERE retention_expires_at <= NOW() AND retention_expires_at IS NOT NULL
"""
import sqlalchemy as sa
from alembic import op

revision = "197"
down_revision = "196"
depends_on = None

TABLE = "activity_feed"


def upgrade() -> None:
    op.add_column(
        TABLE,
        sa.Column("retention_expires_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        TABLE,
        sa.Column("legal_basis", sa.String(50), nullable=True),
    )
    op.add_column(
        TABLE,
        sa.Column("decision_type", sa.String(50), nullable=True),
    )
    # Index for purge scheduler: SELECT id FROM activity_feed
    #   WHERE retention_expires_at <= NOW() AND retention_expires_at IS NOT NULL
    op.create_index(
        "idx_activity_feed_retention_expires",
        TABLE,
        ["retention_expires_at"],
        postgresql_where=sa.text("retention_expires_at IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_activity_feed_retention_expires", table_name=TABLE)
    op.drop_column(TABLE, "decision_type")
    op.drop_column(TABLE, "legal_basis")
    op.drop_column(TABLE, "retention_expires_at")
