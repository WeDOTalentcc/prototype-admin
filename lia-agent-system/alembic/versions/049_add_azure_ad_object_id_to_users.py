"""Add azure_ad_object_id column to users table for Teams SSO mapping.

Revision ID: 049
Revises: 048
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = '049'
down_revision = '048'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('azure_ad_object_id', sa.String(255), nullable=True)
    )
    op.create_index(
        'ix_users_azure_ad_object_id',
        'users',
        ['azure_ad_object_id']
    )


def downgrade() -> None:
    op.drop_index('ix_users_azure_ad_object_id', table_name='users')
    op.drop_column('users', 'azure_ad_object_id')
