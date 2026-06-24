"""Add subsidiary + subsidiary_cnpj to job_vacancies and departments.

Revision ID: 293
Revises: 292

Fase 2 do matching de elegibilidade por filial/CNPJ (2026-06-18).

job_vacancies:
  - subsidiary       VARCHAR(255) nullable -- nome da filial (ex: "Filial SP")
  - subsidiary_cnpj  VARCHAR(18)  nullable -- CNPJ formatado da filial

departments:
  - subsidiary_cnpj  VARCHAR(18)  nullable -- CNPJ da filial (complementa defaults JSONB)
  - subsidiary_name  VARCHAR(255) nullable -- nome da filial para display

Nota: Department.defaults JSONB ja e usado para heranca de campos por vaga
(work_model, employment_types, etc.). Os campos subsidiary_* foram adicionados
como colunas proprias para permitir filtragem SQL eficiente e indice futuro.
"""
from alembic import op
import sqlalchemy as sa

revision = "293"
down_revision = "292"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # job_vacancies -- propagado pelo intake.py via dept.defaults
    op.add_column("job_vacancies", sa.Column("subsidiary", sa.String(255), nullable=True))
    op.add_column("job_vacancies", sa.Column("subsidiary_cnpj", sa.String(18), nullable=True))

    # departments -- permite configurar a filial diretamente no cadastro
    op.add_column("departments", sa.Column("subsidiary_name", sa.String(255), nullable=True))
    op.add_column("departments", sa.Column("subsidiary_cnpj", sa.String(18), nullable=True))


def downgrade() -> None:
    op.drop_column("departments", "subsidiary_cnpj")
    op.drop_column("departments", "subsidiary_name")
    op.drop_column("job_vacancies", "subsidiary_cnpj")
    op.drop_column("job_vacancies", "subsidiary")
