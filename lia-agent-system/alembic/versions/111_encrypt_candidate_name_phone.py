"""encrypt candidate name and phone fields

UC-P1-15: Adds name_encrypted and phone_encrypted LargeBinary columns
to the candidates table. The existing name/phone VARCHAR columns are
retained as nullable (for pre-migration rows); new writes will NULL them
and store Fernet-encrypted bytes in *_encrypted columns.

MIGRATION PLAN (2-step safe rollout):
  Step 1 (this migration): Add *_encrypted columns.
  Step 2 (backfill script): Run scripts/backfill_encrypt_candidate_pii.py
         to encrypt existing plaintext rows. Until backfill completes,
         EncryptedFieldMixin reads from raw column as fallback.
  Step 3 (after backfill verified): Optional — run the cleanup migration
         to drop the plaintext name/phone VARCHAR columns.

NOTE: name is used in ILIKE queries (_handler_hooks.py line 51+55,
sourcing_actions.py line 279). Post-backfill those queries will no longer
match rows (name_raw = NULL). A full-text / trigram search index must be
added before dropping the plaintext column. Until then, ILIKE searches
only work for pre-migration rows — compliance takes precedence.

Revision IDs
------------
Revises: 110_add_company_id_to_activity_tables
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "111"
down_revision = "110"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add encrypted backing columns for name and phone.
    # Nullable=True because existing rows don't have encrypted data yet
    # (backfill script handles that separately).
    op.add_column(
        "candidates",
        sa.Column("name_encrypted", sa.LargeBinary(), nullable=True),
    )
    op.add_column(
        "candidates",
        sa.Column("phone_encrypted", sa.LargeBinary(), nullable=True),
    )

    # Make the plaintext name column nullable to allow ORM to set it to NULL on new writes.
    # Previously name was NOT NULL — relax constraint for the transition period.
    op.alter_column(
        "candidates",
        "name",
        existing_type=sa.String(255),
        nullable=True,
    )

    # NOTE: Do NOT drop the plaintext name/phone columns yet.
    # Run scripts/backfill_encrypt_candidate_pii.py first, then verify.
    # Cleanup migration (drop plaintext cols) comes after backfill confirmation.


def downgrade() -> None:
    # Restore name column to NOT NULL before dropping encrypted columns
    op.alter_column(
        "candidates",
        "name",
        existing_type=sa.String(255),
        nullable=False,
    )
    op.drop_column("candidates", "phone_encrypted")
    op.drop_column("candidates", "name_encrypted")
