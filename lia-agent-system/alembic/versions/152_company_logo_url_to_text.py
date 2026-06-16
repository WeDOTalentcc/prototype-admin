"""company.logo_url + client_account.logo_url + data_request.portal_logo_url → TEXT

Audit 2026-05-20 Sessão I Step 4: Logo upload arquivo precisa armazenar
base64 data URL (data:image/png;base64,...) que excede o limit String(500).
ALTER as 3 colunas de logo conhecidas para TEXT (sem limit).

Revision ID: 152_logo_url_to_text
Revises: 30c0e47d1f56
Create Date: 2026-05-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '152_logo_url_to_text'
down_revision: Union[str, None] = '30c0e47d1f56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """ALTER colunas de logo de String(500) para TEXT."""
    op.alter_column(
        'company_profiles', 'logo_url',
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        'client_accounts', 'logo_url',
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        'data_request_configs', 'portal_logo_url',
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Reverte para String(500) — DATA LOSS se >500 chars existem!"""
    op.alter_column(
        'company_profiles', 'logo_url',
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.alter_column(
        'client_accounts', 'logo_url',
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.alter_column(
        'data_request_configs', 'portal_logo_url',
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
