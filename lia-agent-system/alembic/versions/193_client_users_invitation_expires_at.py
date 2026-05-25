"""client_users invitation_expires_at formal migration (P2-W2-05)

Adds invitation_expires_at column to client_users table as a formal Alembic
migration. The column was previously created via runtime add_client_user_invitation_columns()
in database.py (ADD COLUMN IF NOT EXISTS), so this migration safely uses IF NOT EXISTS
and backfills rows that have invitation_token but no expires_at.

Expiry semantics: INVITATION_TOKEN_EXPIRY_DAYS = 7 (matches ClientUser model constant).

Revision ID: 193
Revises: 192
Create Date: 2026-05-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers
revision = "193"
down_revision = "192"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # ADD COLUMN IF NOT EXISTS — safe even if runtime migration already ran
    conn.execute(text("""
        ALTER TABLE client_users
        ADD COLUMN IF NOT EXISTS invitation_expires_at TIMESTAMP
    """))

    # Backfill: rows with pending invitation_token but no expires_at get
    # expires_at = invited_at + 7 days (or created_at as fallback).
    # Rows older than 7 days are marked expired (now - 1s).
    conn.execute(text("""
        UPDATE client_users
        SET invitation_expires_at = CASE
            WHEN COALESCE(invited_at, created_at) > NOW() - INTERVAL '7 days'
            THEN COALESCE(invited_at, created_at) + INTERVAL '7 days'
            ELSE NOW() - INTERVAL '1 second'
        END
        WHERE invitation_token IS NOT NULL
          AND invitation_expires_at IS NULL
    """))

    # Index (IF NOT EXISTS — safe for idempotency)
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_client_users_invitation_expires_at
        ON client_users(invitation_expires_at)
        WHERE invitation_token IS NOT NULL
    """))


def downgrade():
    op.drop_index(
        "idx_client_users_invitation_expires_at",
        table_name="client_users",
        if_exists=True,
    )
    op.drop_column("client_users", "invitation_expires_at")
