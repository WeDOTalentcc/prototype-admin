"""Task #276 — índices de performance para GET /candidates.

Revision ID: 081_candidates_list_perf_indexes
Revises: 080_migrate_demo_company_to_uuid
Create Date: 2026-04-16

Contexto
--------
O endpoint ``GET /candidates`` ordena por ``created_at DESC`` filtrando por
``is_active = true`` como default. Havia índices simples em ambas as colunas
(``ix_candidates_is_active`` e ``ix_candidates_created_at``), porém nenhum
índice composto que permitisse ao Postgres ler as páginas já ordenadas,
causando um ``Sort`` in-memory ou Index Scan + filtro subsequente.

Esta migration adiciona:

1. ``ix_candidates_active_created_at`` — composto ``(is_active, created_at
   DESC)`` que cobre o padrão default de listagem e faz ``ORDER BY
   created_at DESC LIMIT n`` virar um ``Index Scan`` direto, sem sort.
2. ``ix_candidates_seniority_level_lower`` — índice FUNCIONAL em
   ``lower(seniority_level)`` para casar com o filtro
   ``func.lower(Candidate.seniority_level) == seniority.lower()`` em
   ``CandidateRepository._build_list_filters``. Um índice em
   ``seniority_level`` puro NÃO seria usado pelo planner para essa query
   porque o operando esquerdo é ``lower(col)``, não ``col``.

Observações
-----------
- ``CREATE INDEX CONCURRENTLY`` não pode rodar dentro de transação, então
  dividimos em ``op.execute`` com ``autocommit_block`` — mantém a migration
  segura em produção sem bloqueio longo de escrita.
- ``IF NOT EXISTS`` torna a migration idempotente/re-runnable caso já
  tenha sido criada manualmente via psql em ambiente de dev.
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "081_candidates_list_perf_indexes"
down_revision = "080_migrate_demo_company_to_uuid"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CREATE INDEX CONCURRENTLY precisa rodar fora da transação gerenciada
    # pelo Alembic — por isso o autocommit_block. Em SQLite (tests) o bloco
    # é no-op e os índices caem para criação síncrona.
    with op.get_context().autocommit_block():
        op.execute(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS
                ix_candidates_active_created_at
            ON candidates (is_active, created_at DESC)
            """
        )
        op.execute(
            """
            CREATE INDEX CONCURRENTLY IF NOT EXISTS
                ix_candidates_seniority_level_lower
            ON candidates (lower(seniority_level))
            WHERE seniority_level IS NOT NULL
            """
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            "DROP INDEX CONCURRENTLY IF EXISTS ix_candidates_active_created_at"
        )
        op.execute(
            "DROP INDEX CONCURRENTLY IF EXISTS ix_candidates_seniority_level_lower"
        )
