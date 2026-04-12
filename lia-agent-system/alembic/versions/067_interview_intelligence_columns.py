"""Add Interview Intelligence columns to interviews table.

Revision ID: 067
Revises: 066
Create Date: 2026-04-12

Supports Task #161 — Interview Intelligence infrastructure.
Adds: company_id, transcript, transcript_language, transcript_source,
      transcribed_at, completed_at, metadata JSONB.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import inspect as sa_inspect

revision = "067"
down_revision = "066"
branch_labels = None
depends_on = None

COLUMNS_TO_ADD = [
    ("company_id", sa.String(255)),
    ("transcript", sa.Text()),
    ("transcript_language", sa.String(10)),
    ("transcript_source", sa.String(50)),
    ("transcribed_at", sa.DateTime()),
    ("completed_at", sa.DateTime()),
]


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa_inspect(conn)
    cols = [c["name"] for c in insp.get_columns(table)]
    return column in cols


def upgrade() -> None:
    conn = op.get_bind()

    for col_name, col_type in COLUMNS_TO_ADD:
        if not _has_column(conn, "interviews", col_name):
            op.add_column("interviews", sa.Column(col_name, col_type, nullable=True))

    if not _has_column(conn, "interviews", "metadata"):
        op.add_column("interviews", sa.Column("metadata", JSONB(), nullable=True, server_default="{}"))

    insp = sa_inspect(conn)
    existing_indexes = [idx["name"] for idx in insp.get_indexes("interviews")]
    if "ix_interviews_company_id" not in existing_indexes:
        op.create_index("ix_interviews_company_id", "interviews", ["company_id"])


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa_inspect(conn)
    existing_indexes = [idx["name"] for idx in insp.get_indexes("interviews")]
    if "ix_interviews_company_id" in existing_indexes:
        op.drop_index("ix_interviews_company_id", table_name="interviews")

    for col_name in ["metadata", "completed_at", "transcribed_at", "transcript_source", "transcript_language", "transcript", "company_id"]:
        if _has_column(conn, "interviews", col_name):
            op.drop_column("interviews", col_name)
