"""add session_id to fairness_audit_log

Revision ID: 282_add_session_id_to_fairness_audit_log
Revises: 281_add_data_fields_to_recruitment_stages
Create Date: 2026-06-14

Fix D — adiciona coluna session_id (VARCHAR 100 nullable) à tabela
fairness_audit_log para correlacionar bloqueios de fairness com sessões de
chat SSE. Essa coluna também popula correlation_id em
fairness_policy_violations via application-layer logic (sem trigger DB).
"""
from alembic import op
import sqlalchemy as sa

revision = "282_add_session_id_to_fairness_audit_log"
down_revision = "282_add_data_fields_to_recruitment_stages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fairness_audit_log",
        sa.Column("session_id", sa.String(100), nullable=True),
    )
    op.create_index(
        "ix_fairness_audit_log_session_id",
        "fairness_audit_log",
        ["session_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_fairness_audit_log_session_id", table_name="fairness_audit_log")
    op.drop_column("fairness_audit_log", "session_id")
