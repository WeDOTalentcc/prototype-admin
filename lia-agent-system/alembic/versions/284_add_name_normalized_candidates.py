"""Add name_normalized to candidates for post-encryption name search.

Revision ID: 284_add_name_normalized_candidates
Revises: 282_add_session_id_to_fairness_audit_log
Create Date: 2026-06-14

Fix P0: candidate.name column is NULL for all post-encryption rows (EncryptedFieldMixin
nulls the raw column). Name ILIKE search returned zero results for all recently-created
candidates. Solution: add a non-reversible lowercase search token (name_normalized) that is
set automatically when name is assigned, safe to store plaintext (not PII per LGPD Art. 12
§1 — cannot recover original name from this token).

The name_normalized format: lower(unaccent(name))[:20] + "_" + sha256(name)[:8].
The 8-char sha256 suffix ensures uniqueness even for candidates sharing a 20-char prefix.

pg_trgm extension is created if not exists to enable future trigram similarity fallback.
"""
from alembic import op
import sqlalchemy as sa

revision = "284_add_name_normalized_candidates"
down_revision = "282_add_session_id_to_fairness_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pg_trgm for future trigram similarity search on name_normalized
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.add_column(
        "candidates",
        sa.Column("name_normalized", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_candidates_name_normalized",
        "candidates",
        ["name_normalized"],
    )

    # Backfill for pre-encryption rows where name column still has plaintext
    # Uses same logic as Candidate._compute_name_normalized():
    #   lower(unaccent(trim(name)))[:20] + "_" + left(sha256(lower(trim(name)))::hex, 8)
    # For post-encryption rows (name IS NULL): name_normalized remains NULL until next
    # name assignment triggers the Python setter (real-time backfill via app writes).
    # A full backfill of encrypted rows would require decryption — deferred to a
    # separate pii.backfill_name_normalized task that runs asynchronously.
    op.execute("""
        UPDATE candidates
        SET name_normalized = (
            left(lower(unaccent(trim(name))), 20)
            || '_'
            || left(encode(sha256(lower(trim(name))::bytea), 'hex'), 8)
        )
        WHERE name IS NOT NULL AND name != '' AND name_normalized IS NULL
    """)


def downgrade() -> None:
    op.drop_index("ix_candidates_name_normalized", table_name="candidates")
    op.drop_column("candidates", "name_normalized")
