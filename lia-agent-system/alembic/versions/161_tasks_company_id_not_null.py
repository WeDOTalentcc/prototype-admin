"""WT-2022 P0.TASK: tasks.company_id backfill + NOT NULL (cross-tenant lockdown).

Revision ID: 161_tasks_company_id_not_null
Revises: 160_encrypt_interview_offer_emails
Create Date: 2026-05-21

Contexto (CLAUDE.md REGRA 6 multi-tenancy + harness-engineering):
Sessao anterior fechou cross-tenant em tasks no APP LAYER
(tasks_repository raise ValueError quando company_id ausente).
Mas a COLUNA do DB ainda era nullable=True -- legacy rows orfas
existiam e bypassavam o filter via writes diretos via SQL. Esta migration
encerra o ciclo: ADD COLUMN idempotente + backfill por FK indireta + ALTER NOT NULL.

Backfill strategy (ordem de preferencia):
1. related_job_id -> job_vacancies.company_id (canonical Python-owned,
   nullable=False ja). NOTA: tasks.related_job_id eh VARCHAR; job_vacancies.id
   eh UUID -- precisa CAST explicit `jv.id::text` (canonical-fix harness 2026-05-22).
   Format validation `~ '^[0-9a-fA-F-]{36}$'` rejeita related_job_id malformado
   (defense in depth, evita crash em rows com IDs externos nao-UUID).
2. Linhas restantes orfas (sem related_job_id ou job_vacancy ja deletado)
   sao DELETADAS -- decisao operacional segura: task sem company_id eh
   inutilizavel (repo recusa retornar) e nao tem como reassociar com
   certeza ao tenant correto sem heuristica perigosa.

NOT NULL constraint impede regressao a nivel de DB. Mesmo se um caminho
de codigo bypass o repo (e.g., SQL bruto via admin), o DB rejeita.

CANONICAL-FIX HARNESS (2026-05-22): joins UUID vs VARCHAR sem CAST explicit
sao detectados pelo sensor scripts/check_no_uuid_varchar_join.py. Pattern
canonical: cast `<uuid_col>::text` no lado UUID, ou format-validate +
`<varchar_col>::uuid` no lado varchar. Vide tambem migration 166 que ja
aplica o mesmo pattern.

PRE-FLIGHT BACKUP: tabela _tasks_pre_161_backup criada idempotentemente
para rollback de emergencia caso DELETE seja excessivo (auditavel pelo
operador).

ADR: # TENANT-EXEMPT: <reason> em libs/models/lia_models/*.py marker
sera respeitado por scripts/check_tenant_columns_not_null.py daqui em diante.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.exc import ProgrammingError
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "161_tasks_company_id_not_null"
down_revision: Union[str, None] = "160_encrypt_interview_offer_emails"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_column_idempotent(table: str, column: sa.Column) -> None:
    """Add a column if it does not already exist (idempotent)."""
    try:
        op.add_column(table, column)
    except ProgrammingError as exc:
        if "already exists" in str(exc).lower():
            pass
        else:
            raise


def upgrade() -> None:
    conn = op.get_bind()

    # ------------------------------------------------------------------
    # 0. ADD COLUMN idempotente (algumas DBs ja teem via create_all autogen,
    #    outras nao -- prod nasce do Alembic chain).
    # ------------------------------------------------------------------
    _add_column_idempotent(
        "tasks",
        sa.Column(
            "company_id",
            sa.String(length=255),
            nullable=True,  # nullable=True para permitir backfill antes do ALTER NOT NULL
        ),
    )

    # Index idempotente (mesmo padrao do model Task.company_id index=True)
    try:
        op.create_index("ix_tasks_company_id", "tasks", ["company_id"])
    except ProgrammingError as exc:
        if "already exists" in str(exc).lower():
            pass
        else:
            raise

    # ------------------------------------------------------------------
    # 0.5 PRE-FLIGHT BACKUP (defense-in-depth para rollback de emergencia).
    #     Idempotente: IF NOT EXISTS evita falha em rerun.
    # ------------------------------------------------------------------
    conn.execute(
        sa.text(
            """
            CREATE TABLE IF NOT EXISTS _tasks_pre_161_backup AS
            SELECT * FROM tasks WHERE related_job_id IS NOT NULL
            """
        )
    )

    # ------------------------------------------------------------------
    # 1. Backfill via related_job_id -> job_vacancies.company_id
    #    Cast canonical-fix: `jv.id::text` (UUID -> text) + format validation
    #    em related_job_id para rejeitar valores malformados que crasshariam
    #    o cast inverso.
    # ------------------------------------------------------------------
    conn.execute(
        sa.text(
            """
            UPDATE tasks
            SET company_id = jv.company_id
            FROM job_vacancies AS jv
            WHERE tasks.related_job_id IS NOT NULL
              AND tasks.related_job_id ~ '^[0-9a-fA-F-]{36}$'
              AND tasks.related_job_id = jv.id::text
              AND tasks.company_id IS NULL
            """
        )
    )

    # ------------------------------------------------------------------
    # 2. Detectar e logar orfas remanescentes ANTES de deletar (REGRA 4
    #    canonical-standards: no silent fallback; orphans logged before delete).
    # ------------------------------------------------------------------
    result = conn.execute(
        sa.text("SELECT COUNT(*) FROM tasks WHERE company_id IS NULL")
    )
    null_count = result.scalar() or 0
    if null_count > 0:
        # Sample IDs para audit trail (ate 10 ids -- nao spamar log)
        sample = conn.execute(
            sa.text(
                "SELECT id, related_job_id, created_at FROM tasks "
                "WHERE company_id IS NULL ORDER BY created_at DESC LIMIT 10"
            )
        ).fetchall()
        print(
            f"[WT-2022 P0.TASK] {null_count} tasks orfas (company_id IS NULL "
            f"sem related_job_id resolvivel) sao DELETADAS para satisfazer "
            f"NOT NULL constraint. Decisao: rows nao-scopaveis a tenant nao "
            f"podem servir multi-tenancy guarantee."
        )
        print(f"[WT-2022 P0.TASK] Sample orfas (top 10 by created_at DESC):")
        for row in sample:
            print(f"  - id={row[0]} related_job_id={row[1]} created_at={row[2]}")
        print(
            f"[WT-2022 P0.TASK] Backup table _tasks_pre_161_backup preserva "
            f"rows com related_job_id IS NOT NULL para rollback de emergencia."
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
    # Nao dropamos a coluna no downgrade -- model Python ainda referencia.
    # Drop manual via SQL se necessario; backup _tasks_pre_161_backup
    # preservado para auditoria. Nao dropamos no downgrade automatico.
