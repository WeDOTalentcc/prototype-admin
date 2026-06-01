"""drop colunas 'area' de salary_bands + compensation_components (area = departamento)

Revision ID: 234
Revises: 233
Create Date: 2026-06-01

Decisao do produto: "area" e o mesmo eixo que "departamento" (a hierarquia de
departamentos cobre o agrupamento por area). Remove a dimensao 'area' free-text
adicionada em 233. Idempotente (DROP IF EXISTS via inspector).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "234"
down_revision = "233"
branch_labels = None
depends_on = None


def _has(insp, table, col):
    return table in insp.get_table_names() and col in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if _has(insp, "salary_bands", "area"):
        op.drop_column("salary_bands", "area")
    if _has(insp, "compensation_components", "area"):
        op.drop_column("compensation_components", "area")


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not _has(insp, "salary_bands", "area"):
        op.add_column("salary_bands", sa.Column("area", postgresql.ARRAY(sa.String()), nullable=True))
    if not _has(insp, "compensation_components", "area"):
        op.add_column("compensation_components", sa.Column("area", postgresql.ARRAY(sa.String()), nullable=True))
