"""add file_hash to candidate_attachments

GAP-05-006: SHA-256 hash for file-level dedup detection on CV uploads.
Nullable — backfill not needed (existing rows get None, new uploads set hash).
Index on (file_hash, company_id) for fast tenant-scoped dedup lookups.

Revision ID: 287
Revises: 286_add_model_version_to_audit_logs
Create Date: 2026-06-16
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "287"
down_revision = "286_add_model_version_to_audit_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "candidate_attachments",
        sa.Column("file_hash", sa.String(64), nullable=True),
    )
    op.create_index(
        "idx_attach_file_hash_company",
        "candidate_attachments",
        ["file_hash", "company_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_attach_file_hash_company", table_name="candidate_attachments")
    op.drop_column("candidate_attachments", "file_hash")
