"""Audit M14 — widen WSI CHECK constraints to match scorer reality.

Revision ID: 089_widen_wsi_check_constraints
Revises: 088_index_job_vacancies_external_system_id
Create Date: 2026-04-18

Contexto
--------
A auditoria WSI rev. 5 (achado M14) identificou drift entre o que o scorer
canônico produz e o que o schema aceita:

1. ``wsi_response_analyses.bloom_level CHECK BETWEEN 1 AND 5`` — mas a
   metodologia Bloom canônica tem **6 níveis** (Recordar→Criar) e
   ``wsi_deterministic_scorer.calculate_bloom_level`` itera ``range(6, 0, -1)``.
   Qualquer INSERT com ``bloom_level=6`` levanta ``CheckViolation``.

2. ``wsi_results.classification CHECK IN ('excelente','alto','medio','regular','baixo')`` —
   mas ``classify_wsi_score()`` retorna **6 valores**: ``'excepcional'``,
   ``'excelente'``, ``'alto'``, ``'medio'``, ``'abaixo_da_media'``, ``'regular'``.
   O modelo Pydantic ``WSIResult`` (``wsi_service/models.py:182``) já declara
   os 6 valores. INSERT do scorer canônico levanta ``CheckViolation`` para
   ``excepcional`` ou ``abaixo_da_media``.

3. ``COMMENT ON TABLE wsi_results`` afirma "technical 70% + behavioral 30%",
   mas os pesos canônicos vêm de ``SENIORITY_WEIGHTS`` (8 níveis dinâmicos —
   spec §9.2). Comentário induz devs a erro.

Esta migration corrige esses três pontos. **Não altera dados existentes**
nem o range das colunas decimais (a migração de escala 0-5 → 0-10 é
trabalho separado, audit §17).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "089_widen_wsi_check_constraints"
down_revision = "088_index_job_vacancies_external_system_id"
branch_labels = None
depends_on = None


def _table_exists(conn, table: str) -> bool:
    return bool(conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = :t)"
    ), {"t": table}).scalar())


def _constraint_name(conn, table: str, column: str, contype: str = "c") -> str | None:
    """Find a CHECK constraint name on (table, column). Postgres auto-names them.

    NOTE: pg_constraint.contype is PostgreSQL's internal `"char"` type (1-byte).
    asyncpg refuses to bind Python str to it ("a bytes-like object is required").
    Como `contype` aqui é constante ('c' = CHECK), inlineamos o literal no SQL
    em vez de bindar como parâmetro para manter compat asyncpg + psycopg2.
    """
    if contype not in {"c", "p", "f", "u", "x"}:
        raise ValueError(f"invalid pg contype literal: {contype!r}")
    row = conn.execute(sa.text(
        f"""
        SELECT con.conname
          FROM pg_constraint con
          JOIN pg_class rel ON rel.oid = con.conrelid
          JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
          JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
         WHERE nsp.nspname = 'public'
           AND rel.relname = :t
           AND att.attname = :c
           AND con.contype = '{contype}'
         LIMIT 1
        """
    ), {"t": table, "c": column}).fetchone()
    return row[0] if row else None


def upgrade() -> None:
    conn = op.get_bind()

    # --- 1. wsi_response_analyses.bloom_level: BETWEEN 1 AND 5 → BETWEEN 1 AND 6 ---
    if _table_exists(conn, "wsi_response_analyses"):
        old_name = _constraint_name(conn, "wsi_response_analyses", "bloom_level")
        if old_name:
            op.execute(sa.text(
                f'ALTER TABLE wsi_response_analyses DROP CONSTRAINT "{old_name}"'
            ))
        op.execute(sa.text(
            "ALTER TABLE wsi_response_analyses "
            "ADD CONSTRAINT wsi_response_analyses_bloom_level_check "
            "CHECK (bloom_level BETWEEN 1 AND 6)"
        ))

    # --- 2. wsi_results.classification: 5 valores → 6 valores canônicos ---
    if _table_exists(conn, "wsi_results"):
        old_name = _constraint_name(conn, "wsi_results", "classification")
        if old_name:
            op.execute(sa.text(
                f'ALTER TABLE wsi_results DROP CONSTRAINT "{old_name}"'
            ))

        # Backfill: a tabela canônica de classificação não usa mais 'baixo'
        # (audit code-review SEVERE-1). Linhas legadas com 'baixo' ficariam
        # invisíveis para filtros que migrarem para 'regular'. Migramos in-place
        # ANTES de aplicar o novo CHECK para evitar violation transiente.
        rows_updated = conn.execute(sa.text(
            "UPDATE wsi_results SET classification = 'regular' "
            "WHERE classification = 'baixo'"
        )).rowcount or 0
        if rows_updated:
            print(
                f"[089] Backfill classificação: {rows_updated} linha(s) "
                "migrada(s) de 'baixo' → 'regular' (escala canônica 6 níveis)."
            )

        # Mantemos 'baixo' no CHECK como sinônimo histórico aceito por enquanto
        # (zero linhas ativas após o backfill acima; permite rollback sem dor).
        op.execute(sa.text(
            "ALTER TABLE wsi_results "
            "ADD CONSTRAINT wsi_results_classification_check "
            "CHECK (classification IN ("
            "'excepcional', 'excelente', 'alto', 'medio', 'abaixo_da_media', 'regular', 'baixo'"
            "))"
        ))

        # --- 3. comentário enganoso ---
        op.execute(sa.text(
            "COMMENT ON TABLE wsi_results IS "
            "'Final WSI scores. Pesos technical/behavioral são DINÂMICOS por senioridade "
            "(SENIORITY_WEIGHTS, wsi_deterministic_scorer.py — spec §9.2), não fixos em 70/30.'"
        ))


def downgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "wsi_response_analyses"):
        old_name = _constraint_name(conn, "wsi_response_analyses", "bloom_level")
        if old_name:
            op.execute(sa.text(
                f'ALTER TABLE wsi_response_analyses DROP CONSTRAINT "{old_name}"'
            ))
        # WARNING: dropa linhas com bloom_level=6 (gerados pelo scorer canônico).
        # Se houver rows com bloom_level=6 o downgrade falhará no CHECK — abortar
        # explicitamente em vez de corromper.
        max_bloom = conn.execute(sa.text(
            "SELECT MAX(bloom_level) FROM wsi_response_analyses"
        )).scalar() or 0
        if max_bloom > 5:
            raise RuntimeError(
                f"[089 downgrade] Recusado: existem linhas com bloom_level={max_bloom} > 5. "
                "Downgrade exigiria perda de dados/clamp manual. Resolva antes."
            )
        op.execute(sa.text(
            "ALTER TABLE wsi_response_analyses "
            "ADD CONSTRAINT wsi_response_analyses_bloom_level_check "
            "CHECK (bloom_level BETWEEN 1 AND 5)"
        ))

    if _table_exists(conn, "wsi_results"):
        old_name = _constraint_name(conn, "wsi_results", "classification")
        if old_name:
            op.execute(sa.text(
                f'ALTER TABLE wsi_results DROP CONSTRAINT "{old_name}"'
            ))
        # Backfill reverso: rows com 'excepcional' ou 'abaixo_da_media' precisam
        # ser remapeadas para o vocabulário antigo (5 níveis) antes de re-aplicar
        # o CHECK estrito, ou o ALTER falha. Mapeamento conservador: excepcional
        # → excelente; abaixo_da_media → regular (próximo nível para baixo).
        op.execute(sa.text(
            "UPDATE wsi_results SET classification = 'excelente' "
            "WHERE classification = 'excepcional'"
        ))
        op.execute(sa.text(
            "UPDATE wsi_results SET classification = 'regular' "
            "WHERE classification = 'abaixo_da_media'"
        ))
        op.execute(sa.text(
            "ALTER TABLE wsi_results "
            "ADD CONSTRAINT wsi_results_classification_check "
            "CHECK (classification IN ("
            "'excelente', 'alto', 'medio', 'regular', 'baixo'"
            "))"
        ))
        op.execute(sa.text(
            "COMMENT ON TABLE wsi_results IS "
            "'Final WSI scores (technical 70% + behavioral 30% = overall)'"
        ))
