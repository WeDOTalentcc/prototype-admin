"""WT-2022 P0.TASK: tasks.company_id backfill + NOT NULL (cross-tenant lockdown).

Revision ID: 161_tasks_company_id_not_null
Revises: 160_encrypt_interview_offer_emails
Create Date: 2026-05-21

Contexto (CLAUDE.md REGRA 6 multi-tenancy + harness-engineering):
Sessao anterior fechou cross-tenant em tasks no APP LAYER
(tasks_repository raise ValueError quando company_id ausente).
Mas a COLUNA do DB ainda era nullable=True -- legacy rows orfas
existiam e bypassavam o filter via writes diretos via SQL. Esta migration
encerra o ciclo: backfill por FK indireta + ALTER NOT NULL.

Backfill strategy (ordem de preferencia):
1. related_job_id -> job_vacancies.company_id (canonical Python-owned,
   nullable=False ja).
2. Linhas restantes orfas (sem related_job_id ou job_vacancy ja deletado)
   sao DELETADAS -- decisao operacional segura: task sem company_id eh
   inutilizavel (repo recusa retornar) e nao tem como reassociar com
   certeza ao tenant correto sem heuristica perigosa.

NOT NULL constraint impede regressao a nivel de DB. Mesmo se um caminho
de codigo bypass o repo (e.g., SQL bruto via admin), o DB rejeita.

ADR: # TENANT-EXEMPT: <reason> em libs/models/lia_models/*.py marker
sera respeitado por scripts/check_tenant_columns_not_null.py daqui em diante.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "161_tasks_company_id_not_null"
down_revision: Union[str, None] = "160_encrypt_interview_offer_emails"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Backfill via related_job_id -> job_vacancies.company_id
    # ------------------------------------------------------------------
    conn.execute(
        sa.text(
            """
            UPDATE tasks
            SET company_id = jv.company_id
            FROM job_vacancies AS jv
            WHERE tasks.related_job_id = jv.id
              AND tasks.company_id IS NULL
            """
        )
    )

    # ------------------------------------------------------------------
    # 2. Detectar e deletar orfas remanescentes (safe op decision)
    # ------------------------------------------------------------------
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM tasks WHERE company_id IS NULL")
    )
    null_count = result.scalar() or 0
    if null_count > 0:
        # log claro p/ audit trail -- alembic stdout vai pro deploy log
        print(
            f"[WT-2022 P0.TASK] {null_count} tasks orfas (company_id IS NULL "
            f"sem related_job_id resolvivel) sao DELETADAS para satisfazer "
            f"NOT NULL constraint. Decisao: rows nao-scopaveis a tenant nao "
            f"podem servir multi-tenancy guarantee."
        )
        conn.execute(sa.text("DELETE FROM tasks WHERE company_id IS NULL"))

    # ------------------------------------------------------------------
    # 3. ALTER COLUMN NOT NULL (defesa em camada DB)
    # ------------------------------------------------------------------
    op.alter_column(
        "tasks",
        "company_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "tasks",
        "company_id",
        existing_type=sa.String(length=255),
        nullable=True,
    )
