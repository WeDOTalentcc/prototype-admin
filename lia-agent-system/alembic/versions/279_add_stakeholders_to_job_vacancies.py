# encoding: utf-8
"""279 - add stakeholders JSONB to job_vacancies

Revision ID: 279_add_stakeholders_to_job_vacancies
Revises: 278_create_domain_events_outbox
Create Date: 2026-06-13

T10 - Stakeholders/envolvidos adicionais por vaga (HRBP, lider de area,
comite de contratacao, entrevistadores). JSONB array de objetos com
name, email, role. Default [].
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "279_add_stakeholders_to_job_vacancies"
down_revision = "278_create_domain_events_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "job_vacancies",
        sa.Column("stakeholders", JSONB, server_default="[]", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("job_vacancies", "stakeholders")
