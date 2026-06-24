"""Migration 298: add company_id to calibration_feedback (LGPD Art.18 tenant erasure anchor).

Revision ID: 298_add_company_id_to_calibration_feedback
Revises: 297_add_ia_sidebar_columns
Create Date: 2026-06-19

Adds:
  - company_id VARCHAR NOT NULL to calibration_feedback

NOT NULL invariant: POST /api/v1/search/calibration/feedback always has company_id
via require_company_id (JWT). server_default=\'\' used only for idempotency on
pre-existing rows (URL was broken before this migration — table has 0 rows in prod).
Default is dropped after column creation so future writes without company_id fail.
ADR-001: trava invariante multi-tenant na tabela.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "298_add_company_id_to_calibration_feedback"
down_revision = "297_add_ia_sidebar_columns"
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c"
    ), {"t": table, "c": column})
    return result.fetchone() is not None


def upgrade():
    conn = op.get_bind()
    if not _column_exists(conn, "calibration_feedback", "company_id"):
        # Step 1: add with server_default to handle any pre-existing rows safely
        op.add_column(
            "calibration_feedback",
            sa.Column("company_id", sa.String(), nullable=False, server_default=""),
        )
        # Step 2: drop the server_default — future inserts must provide company_id
        op.alter_column("calibration_feedback", "company_id", server_default=None)


def downgrade():
    conn = op.get_bind()
    if _column_exists(conn, "calibration_feedback", "company_id"):
        op.drop_column("calibration_feedback", "company_id")
