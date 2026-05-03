"""add company_id to technical_tests

Revision ID: 109
Revises: 108
Create Date: 2026-05-02

UC-P1-02: Tenant isolation for TechnicalTest.
nullable=True because global tests (is_global=True) have no company_id.
No backfill needed — global tests remain NULL, client tests get populated via app.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "109"
down_revision = "108"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("technical_tests", sa.Column("company_id", sa.String(255), nullable=True))
    op.create_index("ix_technical_tests_company_id", "technical_tests", ["company_id"])


def downgrade():
    op.drop_index("ix_technical_tests_company_id", "technical_tests")
    op.drop_column("technical_tests", "company_id")
