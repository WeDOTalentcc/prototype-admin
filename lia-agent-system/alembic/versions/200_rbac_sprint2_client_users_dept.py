"""RBAC Sprint 2 Phase 2 — client_users.department_id + manager_id.

Revision ID: 199
Revises: 198
Create Date: 2026-05-25

Plan canonical: ~/.claude/plans/jolly-roaming-moler.md

Mudanças:
- ADD client_users.department_id UUID FK → departments(id)
- ADD client_users.manager_id UUID FK → client_users(id) self-ref
- Indexes

Razão: UI writes via ClientUserUpdate schema → client_users table.
Filter reads from users.department_id (auth table). Sync happens em endpoint level.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "200"
down_revision = "199"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'client_users',
        sa.Column(
            'department_id',
            UUID(as_uuid=True),
            sa.ForeignKey('departments.id', ondelete='SET NULL'),
            nullable=True,
            comment='RBAC Sprint 2 (2026-05-25): department FK. UI writes here; endpoint syncs to users.department_id.'
        )
    )
    op.create_index('idx_client_users_department_id', 'client_users', ['department_id'], unique=False)

    op.add_column(
        'client_users',
        sa.Column(
            'manager_id',
            UUID(as_uuid=True),
            sa.ForeignKey('client_users.id', ondelete='SET NULL'),
            nullable=True,
            comment='RBAC Sprint 2 (2026-05-25): self-ref para approval chains futuras.'
        )
    )
    op.create_index('idx_client_users_manager_id', 'client_users', ['manager_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_client_users_manager_id', table_name='client_users')
    op.drop_column('client_users', 'manager_id')
    op.drop_index('idx_client_users_department_id', table_name='client_users')
    op.drop_column('client_users', 'department_id')
