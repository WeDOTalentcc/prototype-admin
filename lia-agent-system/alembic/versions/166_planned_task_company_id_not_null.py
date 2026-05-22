"""WT-2022 P0.PLANNED_TASK: planned_tasks.company_id backfill + NOT NULL.

Revision ID: 166_planned_task_company_id_not_null
Revises: 165_interview_company_id_not_null
Create Date: 2026-05-21

Contexto (CLAUDE.md REGRA 6 multi-tenancy):
PlannedTask representa delegacao automatica de agente para humano dentro de
um tenant. company_id nullable=True abria brecha cross-tenant via writes
SQL diretos. Backfill via related_job_id (canonical Python-owned NOT NULL),
fallback DELETE para orfas.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "166_planned_task_company_id_not_null"
down_revision: Union[str, None] = "165_interview_company_id_not_null"
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
            UPDATE planned_tasks
            SET company_id = jv.company_id
            FROM job_vacancies AS jv
            WHERE planned_tasks.related_job_id = jv.id::text
              AND planned_tasks.company_id IS NULL
            """
        )
    )

    # ------------------------------------------------------------------
    # 2. Orfas restantes: DELETADAS
    # ------------------------------------------------------------------
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM planned_tasks WHERE company_id IS NULL")
    )
    null_count = result.scalar() or 0
    if null_count > 0:
        print(
            f"[WT-2022 P0.PLANNED_TASK] {null_count} planned_tasks orfas "
            f"(company_id IS NULL sem related_job_id resolvivel) sao "
            f"DELETADAS."
        )
        conn.execute(
            sa.text("DELETE FROM planned_tasks WHERE company_id IS NULL")
        )

    # ------------------------------------------------------------------
    # 3. ALTER COLUMN NOT NULL
    # ------------------------------------------------------------------
    op.alter_column(
        "planned_tasks",
        "company_id",
        existing_type=sa.String(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "planned_tasks",
        "company_id",
        existing_type=sa.String(),
        nullable=True,
    )
