"""WT-2022 P0.WORK: workforce_entries.company_id backfill + NOT NULL.

Revision ID: 162_workforce_entries_company_id_not_null
Revises: 161_tasks_company_id_not_null
Create Date: 2026-05-21

Contexto (CLAUDE.md REGRA 6 multi-tenancy + harness-engineering):
WorkforceRepository ja enforca company_id em queries/setters
(app layer fail-closed). Esta migration fecha o ciclo no DB: backfill
heuristico + ALTER NOT NULL.

Estrategia de backfill:
1. JOIN via departments.name = workforce_entries.department quando o
   nome de departamento eh UNIQUE em departments (uma unica empresa
   tem aquele nome). Match ambiguo eh ignorado -- nao queremos atribuir
   ao tenant errado por heuristica fraca.
2. Linhas remanescentes (ambiguas ou sem match) sao DELETADAS. Mesma
   decisao do 161: workforce_entry sem company_id eh inutilizavel
   (repo recusa) e nao tem como mapear com seguranca.

Tipo: company_id eh UUID(as_uuid=True) (diferente de tasks que
usa String(255)). Adjustar alter_column accordingly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID


# revision identifiers, used by Alembic.
revision: str = "162_workforce_entries_company_id_not_null"
down_revision: Union[str, None] = "161_tasks_company_id_not_null"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Backfill via departments.name JOIN -- somente matches UNICOS
    #    (departamento name presente em UMA empresa apenas).
    # ------------------------------------------------------------------
    conn.execute(
        sa.text(
            """
            WITH unique_departments AS (
                SELECT name, company_id
                FROM departments
                GROUP BY name, company_id
                HAVING COUNT(*) = 1
            ),
            single_company_names AS (
                SELECT name, (array_agg(company_id))[1] AS company_id
                FROM unique_departments
                GROUP BY name
                HAVING COUNT(*) = 1
            )
            UPDATE workforce_entries we
            SET company_id = scn.company_id
            FROM single_company_names AS scn
            WHERE we.department = scn.name
              AND we.company_id IS NULL
            """
        )
    )

    # ------------------------------------------------------------------
    # 2. Deletar orfas remanescentes (decisao operacional segura)
    # ------------------------------------------------------------------
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM workforce_entries WHERE company_id IS NULL")
    )
    null_count = result.scalar() or 0
    if null_count > 0:
        print(
            f"[WT-2022 P0.WORK] {null_count} workforce_entries orfas "
            f"(company_id IS NULL sem match unico em departments.name) "
            f"sao DELETADAS para satisfazer NOT NULL constraint. "
            f"Decisao: rows sem scope a tenant nao podem servir "
            f"multi-tenancy guarantee."
        )
        conn.execute(
            sa.text("DELETE FROM workforce_entries WHERE company_id IS NULL")
        )

    # ------------------------------------------------------------------
    # 3. ALTER COLUMN NOT NULL (defesa em camada DB)
    # ------------------------------------------------------------------
    op.alter_column(
        "workforce_entries",
        "company_id",
        existing_type=PGUUID(as_uuid=True),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "workforce_entries",
        "company_id",
        existing_type=PGUUID(as_uuid=True),
        nullable=True,
    )
