"""Task #346 — adicionar coluna company_id ao Candidate (multi-tenant scope).

Revision ID: 082_add_candidate_company_id
Revises: 081_candidates_list_perf_indexes
Create Date: 2026-04-17

Contexto
--------
A auditoria #287 (causa raiz #4) identificou que o modelo ``Candidate`` não
tinha coluna ``company_id`` — apenas ``current_company`` (texto livre). Como
consequência, não havia enforcement multi-tenant a nível de candidato no
banco, e todas as rows existentes nasceram sem tenant.

A task #295 já preparou o caller side: ``CandidateRepository._build_list_filters``
aplica ``Candidate.company_id == company_id`` quando o atributo existe (no-op
forward-compat). Esta migration adiciona a coluna + backfill para que esse
filtro vire efetivo automaticamente, sem mudar o caller.

Estratégia de backfill
----------------------
1. Adiciona coluna NULLABLE.
2. Tenta preencher com ``vacancy_candidates.company_id`` (a assignment mais
   recente por candidato dita a empresa). Cobre candidatos que já entraram
   em algum funil/vaga.
3. Os remanescentes (candidatos sem nenhum vínculo de vaga — ex. importados
   por staging Pearch e nunca promovidos a um job) ficam atrelados ao
   tenant demo (``DEMO_COMPANY_UUID``). É a escolha conservadora: em DEV
   esses candidatos são da seed/demo; em prod, nenhum tenant real perde
   visibilidade dos seus próprios candidatos porque o passo 2 já cobriu
   100% dos candidatos com pipeline.
4. ALTER COLUMN para NOT NULL.
5. Cria índice composto ``(company_id, is_active, created_at DESC)``
   espelhando ``ix_candidates_active_created_at`` (migration 081) com
   tenant scope no prefixo, garantindo que ``GET /candidates`` filtrado
   por tenant continue sem ``Sort`` in-memory.

Observações
-----------
- ``CREATE INDEX CONCURRENTLY`` precisa rodar fora da transação Alembic →
  uso de ``autocommit_block``.
- ``IF NOT EXISTS`` torna a criação do índice idempotente.
- Todo o passo de backfill é tolerante a tabelas inexistentes (fresh DB).
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "082_add_candidate_company_id"
down_revision = "081_candidates_list_perf_indexes"
branch_labels = None
depends_on = None


DEMO_COMPANY_UUID = "00000000-0000-4000-a000-000000000001"


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = :t)"
    ), {"t": table}).scalar())


def _column_exists(conn, table: str, column: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c)"
    ), {"t": table, "c": column}).scalar())


def upgrade() -> None:
    conn = op.get_bind()

    # Step 1 — add column NULLABLE so the existing rows don't fail the insert.
    if not _column_exists(conn, "candidates", "company_id"):
        op.add_column(
            "candidates",
            sa.Column("company_id", sa.String(length=255), nullable=True),
        )

    # Step 2 — backfill from VacancyCandidate (most recent assignment per candidate).
    if _table_exists(conn, "vacancy_candidates"):
        result = conn.execute(sa.text("""
            UPDATE candidates AS c
            SET company_id = sub.company_id
            FROM (
                SELECT DISTINCT ON (candidate_id)
                    candidate_id,
                    company_id
                FROM vacancy_candidates
                WHERE company_id IS NOT NULL AND company_id <> ''
                ORDER BY candidate_id, created_at DESC
            ) AS sub
            WHERE c.id = sub.candidate_id
              AND c.company_id IS NULL
        """))
        if result.rowcount:
            print(f"[082] candidates.company_id: backfilled {result.rowcount} "
                  f"rows from vacancy_candidates")

    # Step 3 — remaining rows (no pipeline link) fall back to the demo tenant.
    fallback = conn.execute(sa.text("""
        UPDATE candidates
        SET company_id = :demo
        WHERE company_id IS NULL OR company_id = ''
    """), {"demo": DEMO_COMPANY_UUID})
    if fallback.rowcount:
        print(f"[082] candidates.company_id: defaulted {fallback.rowcount} "
              f"orphan rows to demo tenant {DEMO_COMPANY_UUID}")

    # Step 4 — flip to NOT NULL now that every row has a value.
    op.alter_column(
        "candidates",
        "company_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    # Step 5 — composite index mirroring 081 with tenant scope as the leading
    # column. Rolls out CONCURRENTLY to avoid locking the candidates table.
    with op.get_context().autocommit_block():
        op.execute(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS
                ix_candidates_company_active_created_at
            ON candidates (company_id, is_active, created_at DESC)
            """
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "DROP INDEX CONCURRENTLY IF EXISTS ix_candidates_company_active_created_at"
        )
    op.drop_column("candidates", "company_id")
