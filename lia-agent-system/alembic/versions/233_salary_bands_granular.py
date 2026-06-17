"""salary_bands granular (escopo org + area + vigencia) + compensation_components.area

Revision ID: 233
Revises: 232
Create Date: 2026-06-01

Torna a faixa salarial granular (mesmo cadastro dos beneficios): escopo por
contrato/departamento/AREA/filial-CNPJ + vigencia. Remove o UNIQUE(company,level)
(multiplas faixas por nivel). Adiciona 'area' tambem na verba (compensation_components).
Idempotente: checa colunas/constraints existentes antes (create_all race).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "233"
down_revision = "232"
branch_labels = None
depends_on = None


def _cols(insp, table):
    return {c["name"] for c in insp.get_columns(table)} if table in insp.get_table_names() else set()


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    sb = _cols(insp, "salary_bands")
    adds = [
        ("contract_types", postgresql.ARRAY(sa.String())),
        ("departments", postgresql.JSONB),
        ("area", postgresql.ARRAY(sa.String())),
        ("subsidiaries", postgresql.JSONB),
        ("valid_from", sa.Date),
        ("valid_until", sa.Date),
    ]
    for name, type_ in adds:
        if name not in sb:
            op.add_column("salary_bands", sa.Column(name, type_, nullable=True))

    # drop UNIQUE(company_id, level) — multiplas faixas por nivel agora
    uniques = {uc["name"] for uc in insp.get_unique_constraints("salary_bands")} if "salary_bands" in insp.get_table_names() else set()
    if "uq_salary_bands_company_level" in uniques:
        op.drop_constraint("uq_salary_bands_company_level", "salary_bands", type_="unique")

    cc = _cols(insp, "compensation_components")
    if "compensation_components" in insp.get_table_names() and "area" not in cc:
        op.add_column("compensation_components", sa.Column("area", postgresql.ARRAY(sa.String()), nullable=True))


def downgrade() -> None:
    for name in ("contract_types", "departments", "area", "subsidiaries", "valid_from", "valid_until"):
        try:
            op.drop_column("salary_bands", name)
        except Exception:
            pass
    try:
        op.create_unique_constraint("uq_salary_bands_company_level", "salary_bands", ["company_id", "level"])
    except Exception:
        pass
    try:
        op.drop_column("compensation_components", "area")
    except Exception:
        pass
