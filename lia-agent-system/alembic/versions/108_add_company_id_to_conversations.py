"""add company_id to conversations

Revision ID: 108
Revises: 107_job_vacancy_source_stage
Create Date: 2026-05-02

UC-P1-01: Tenant isolation — every conversation must be scoped to a company.
company_id is nullable for backward compat; backfill from users table.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "108"
down_revision = "107_job_vacancy_source_stage"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("conversations", sa.Column("company_id", sa.String(255), nullable=True))
    op.create_index("ix_conversations_company_id", "conversations", ["company_id"])
    # Backfill via user -> company relationship
    op.execute("""
        UPDATE conversations c
        SET company_id = u.company_id
        FROM users u
        WHERE c.user_id = u.id::varchar
        AND c.company_id IS NULL
    """)


def downgrade():
    op.drop_index("ix_conversations_company_id", "conversations")
    op.drop_column("conversations", "company_id")
