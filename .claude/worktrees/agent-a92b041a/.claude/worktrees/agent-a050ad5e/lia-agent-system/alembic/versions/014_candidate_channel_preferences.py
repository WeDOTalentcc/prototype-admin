"""Add channel preferences to candidates (N3).

Revision ID: 014_candidate_channel_preferences
Revises: 013_add_scheduled_deletion_at
Create Date: 2026-02-28

N3 — Preferências de Canal por Candidato:
Adiciona preferred_channels (lista ordenada de canais preferidos) e
channel_opt_out (lista de canais em que o candidato fez opt-out) ao modelo Candidate.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = '014_candidate_channel_preferences'
down_revision = '013_add_scheduled_deletion_at'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar preferred_channels — lista ordenada de canais preferidos
    op.add_column(
        'candidates',
        sa.Column(
            'preferred_channels',
            JSONB,
            nullable=True,
            server_default='["email"]',
            comment='Lista ordenada de canais preferidos: ["email", "whatsapp", "sms"]'
        )
    )

    # Adicionar channel_opt_out — canais em que o candidato fez opt-out
    op.add_column(
        'candidates',
        sa.Column(
            'channel_opt_out',
            JSONB,
            nullable=True,
            server_default='[]',
            comment='Canais em opt-out: ["marketing_email", "whatsapp"]'
        )
    )

    # Índice GIN para busca eficiente dentro dos arrays JSON
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidates_preferred_channels "
        "ON candidates USING GIN (preferred_channels)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_candidates_channel_opt_out "
        "ON candidates USING GIN (channel_opt_out)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_candidates_preferred_channels")
    op.execute("DROP INDEX IF EXISTS idx_candidates_channel_opt_out")
    op.drop_column('candidates', 'preferred_channels')
    op.drop_column('candidates', 'channel_opt_out')
