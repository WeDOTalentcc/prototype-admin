"""Webhook registrations secret_key NOT NULL (P1-W3-11)

Ensures every webhook registration has a secret_key for HMAC signature
verification. Existing NULL rows receive a generated key.

Revision ID: 192
Revises: 191_company_benefits_extended
Create Date: 2026-05-24
"""
from alembic import op
import sqlalchemy as sa
import secrets


# revision identifiers
revision = "192"
down_revision = "191_company_benefits_extended"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Fill existing NULL rows with generated secrets
    op.execute(
        sa.text(
            """
            UPDATE webhook_registrations
            SET secret_key = encode(gen_random_bytes(32), 'hex')
            WHERE secret_key IS NULL
            """
        )
    )

    # 2. Now enforce NOT NULL
    op.alter_column(
        "webhook_registrations",
        "secret_key",
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "webhook_registrations",
        "secret_key",
        nullable=True,
    )
