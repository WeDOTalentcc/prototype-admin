"""add cpf_hash and phone_hash columns to candidates

Fase 1 (2026-06-10, ADR-LGPD-002 resolve-then-strip): indexed SHA-256 hash columns
for CPF and phone, enabling chat entity-resolution by identifier WITHOUT leaking the
raw identifier to the LLM vendor. Mirrors email_hash (migration 060).

Schema-only (2-step safe rollout, same as migration 111):
  Step 1 (this migration): add cpf_hash/phone_hash columns + indexes.
  Step 2 (backfill): run scripts/backfill_candidate_identifier_hash.py (idempotent)
         to populate hashes for existing rows. New writes populate automatically
         via EncryptedFieldMixin (_pii_encrypt_fields triples updated).

Revision IDs
------------
Revises: 258
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "259"
down_revision = "258"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("cpf_hash", sa.String(64), nullable=True))
    op.add_column("candidates", sa.Column("phone_hash", sa.String(64), nullable=True))
    op.create_index("ix_candidates_cpf_hash", "candidates", ["cpf_hash"])
    op.create_index("ix_candidates_phone_hash", "candidates", ["phone_hash"])


def downgrade() -> None:
    op.drop_index("ix_candidates_phone_hash", table_name="candidates")
    op.drop_index("ix_candidates_cpf_hash", table_name="candidates")
    op.drop_column("candidates", "phone_hash")
    op.drop_column("candidates", "cpf_hash")
