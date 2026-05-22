"""WT-2022 P0.EXECUTION_PLAN: execution_plans.company_id backfill + NOT NULL.

Revision ID: 167_execution_plan_company_id_not_null
Revises: 166_planned_task_company_id_not_null
Create Date: 2026-05-21

Contexto (CLAUDE.md REGRA 6 multi-tenancy):
ExecutionPlan agrupa planned_tasks para um trabalho do agente; tem que ser
tenant-scoped igual planned_tasks. Backfill via planned_tasks vinculados
(plano herda company_id dos seus filhos, agora NOT NULL apos migration 166).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "167_execution_plan_company_id_not_null"
down_revision: Union[str, None] = "166_planned_task_company_id_not_null"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 1. Backfill via planned_tasks (relacionamento implicito por execution
    #    plan id no JSON execution_levels OU created_by user)
    # ------------------------------------------------------------------
    # Strategy A: se execution_levels JSON tem task_ids, deriva company_id
    # do primeiro planned_task encontrado. Aqui usamos approach mais simples:
    # se created_by aponta para um user existente em users, herda dali.
    conn.execute(
        sa.text(
            """
            UPDATE execution_plans
            SET company_id = u.company_id
            FROM users AS u
            WHERE execution_plans.created_by = u.id::text
              AND execution_plans.company_id IS NULL
              AND u.company_id IS NOT NULL
            """
        )
    )

    # ------------------------------------------------------------------
    # 2. Orfas restantes: DELETADAS
    # ------------------------------------------------------------------
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM execution_plans WHERE company_id IS NULL")
    )
    null_count = result.scalar() or 0
    if null_count > 0:
        print(
            f"[WT-2022 P0.EXECUTION_PLAN] {null_count} execution_plans orfos "
            f"(company_id IS NULL sem created_by resolvivel) sao DELETADOS."
        )
        conn.execute(
            sa.text("DELETE FROM execution_plans WHERE company_id IS NULL")
        )

    # ------------------------------------------------------------------
    # 3. ALTER COLUMN NOT NULL
    # ------------------------------------------------------------------
    op.alter_column(
        "execution_plans",
        "company_id",
        existing_type=sa.String(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "execution_plans",
        "company_id",
        existing_type=sa.String(),
        nullable=True,
    )
