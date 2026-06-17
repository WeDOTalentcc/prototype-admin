"""Add company_calendar_credentials table (Sprint 5 — Google Calendar).

Revision ID: 017_add_company_calendar_credentials
Revises: 016_add_scheduled_deletion_ai_consumption
Create Date: 2026-03-02

Sprint 5 — Google Calendar:
Armazena credenciais OAuth/Service Account de calendário por empresa.
Suporta múltiplos provedores (google, microsoft).
Credenciais criptografadas via Fernet (app/shared/encryption.py).

Também adiciona campos google_event_id e google_meet_link ao modelo interviews.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "017_add_company_calendar_credentials"
down_revision = "016_add_scheduled_deletion_ai_consumption"
branch_labels = None
depends_on = None


def upgrade():
    # Tabela de credenciais de calendário por empresa
    op.create_table(
        "company_calendar_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "provider",
            sa.String(20),
            nullable=False,
            comment="Provedor: 'google' ou 'microsoft'",
        ),
        sa.Column(
            "encrypted_credentials",
            sa.Text,
            nullable=False,
            comment="JSON criptografado via Fernet com tokens OAuth ou service account",
        ),
        sa.Column("is_active", sa.Boolean, default=True, nullable=False),
        sa.Column("timezone", sa.String(100), default="America/Sao_Paulo", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index(
        "ix_company_calendar_credentials_company_provider",
        "company_calendar_credentials",
        ["company_id", "provider"],
        unique=True,
    )

    # Campos Google Calendar no modelo interviews
    op.add_column(
        "interviews",
        sa.Column("google_event_id", sa.String(255), nullable=True, index=True),
    )
    op.add_column(
        "interviews",
        sa.Column("google_meet_link", sa.String(500), nullable=True),
    )


def downgrade():
    op.drop_column("interviews", "google_meet_link")
    op.drop_column("interviews", "google_event_id")
    op.drop_index("ix_company_calendar_credentials_company_provider")
    op.drop_table("company_calendar_credentials")
