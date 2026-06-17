"""RBAC Sprint 2 — Department scoping FKs (soft launch).

Revision ID: 198
Revises: 197 (or current head — TBD by alembic merge if needed)
Create Date: 2026-05-25

Plan canonical: ~/.claude/plans/jolly-roaming-moler.md (Phase H RBAC Sprint 2)
Audit base: ~/Documents/wedotalent_audit_2026-05-25/09_rbac_canonical_proposal.md

Mudanças:
1. ADD users.department_id UUID FK → departments(id) — nullable
2. ADD users.manager_id UUID FK → users(id) — nullable, self-ref
3. ADD job_vacancies.department_id UUID FK → departments(id) — nullable
4. Indexes para query performance

Backward compat (soft launch):
- Todos os campos novos NULL por default
- Filter logic em crud.py:list_job_vacancies trata NULL como tenant-wide (legacy)
- Granularidade só "morde" quando cliente popular ambos lados

Quando ativar:
- Cliente popula departments (já tem 15 cadastrados em DB)
- Cliente associa users → department_id (UI: Usuários & Departamentos)
- Cliente associa jobs → department_id (UI: Job edit form)
- Filter automaticamente enforce
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '198'
down_revision = "197"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users.department_id
    op.add_column(
        'users',
        sa.Column(
            'department_id',
            UUID(as_uuid=True),
            sa.ForeignKey('departments.id', ondelete='SET NULL'),
            nullable=True,
            comment='RBAC Sprint 2 (2026-05-25): department scope. NULL = legacy/tenant-wide.'
        )
    )
    op.create_index('idx_users_department_id', 'users', ['department_id'], unique=False)

    # 2. users.manager_id (self-ref) — para approvals futuras
    op.add_column(
        'users',
        sa.Column(
            'manager_id',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
            comment='RBAC Sprint 2 (2026-05-25): self-ref. Reserved for future approval chains. Not used by scope filter (per ADR: dept-only scope).'
        )
    )
    op.create_index('idx_users_manager_id', 'users', ['manager_id'], unique=False)

    # 3. job_vacancies.department_id — NB: tabela já tem 'department' VARCHAR (display label).
    # FK adiciona separadamente; filter usa FK quando NOT NULL, fallback string nunca.
    op.add_column(
        'job_vacancies',
        sa.Column(
            'department_id',
            UUID(as_uuid=True),
            sa.ForeignKey('departments.id', ondelete='SET NULL'),
            nullable=True,
            comment='RBAC Sprint 2 (2026-05-25): department scope FK. Coexiste com job_vacancies.department (string display).'
        )
    )
    op.create_index('idx_job_vacancies_department_id', 'job_vacancies', ['department_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_job_vacancies_department_id', table_name='job_vacancies')
    op.drop_column('job_vacancies', 'department_id')

    op.drop_index('idx_users_manager_id', table_name='users')
    op.drop_column('users', 'manager_id')

    op.drop_index('idx_users_department_id', table_name='users')
    op.drop_column('users', 'department_id')
