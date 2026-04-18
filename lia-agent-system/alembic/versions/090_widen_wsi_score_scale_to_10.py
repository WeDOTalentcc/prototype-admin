"""Task #497 PR2 — flip atômico da escala WSI 0-5 → 0-10.

Revision ID: 090_widen_wsi_score_scale_to_10
Revises: 089_widen_wsi_check_constraints
Create Date: 2026-04-18

Contexto
--------
A migração #497 dobra a resolução do WSI: scores numéricos passam de 0-5
para 0-10 em todo o sistema. Esta revisão é a contraparte de DB para o
flip de código (`wsi_scale.py` SCALE_MAX 5→10). Mantém ranking ordinal
preservado (multiplicação por 2 = transformação linear monotônica).

Tabelas afetadas
----------------
1. ``wsi_results`` — colunas ``overall_wsi``, ``technical_wsi``,
   ``behavioral_wsi`` (numeric/decimal). Faz UPDATE *2 em todas as linhas
   existentes e troca o CHECK de ``BETWEEN 1 AND 5`` para ``BETWEEN 0 AND 10``.

2. ``wsi_response_analyses`` — colunas ``autodeclaration_score``,
   ``context_score``, ``final_score``. Mesmo tratamento.

A migração 089 já cuidou de ``bloom_level`` (1-6) e do enum
``classification`` — não revisitamos esses campos aqui.

Reversibilidade
---------------
``downgrade()`` divide por 2 e re-aplica os CHECKs antigos. Como a
operação é uma transformação linear, não há perda de dados (módulo
arredondamento DECIMAL).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "090_widen_wsi_score_scale_to_10"
down_revision = "089_widen_wsi_check_constraints"
branch_labels = None
depends_on = None


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


def _check_constraint_names(conn, table: str, column: str) -> list[str]:
    """Retorna nomes de TODOS os CHECK constraints que referenciam a coluna."""
    rows = conn.execute(sa.text(
        """
        SELECT con.conname
          FROM pg_constraint con
          JOIN pg_class rel ON rel.oid = con.conrelid
          JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
          JOIN pg_attribute att ON att.attrelid = rel.oid AND att.attnum = ANY(con.conkey)
         WHERE nsp.nspname = 'public'
           AND rel.relname = :t
           AND att.attname = :c
           AND con.contype = 'c'
        """
    ), {"t": table, "c": column}).fetchall()
    return [r[0] for r in rows]


_RESULTS_COLS = ("overall_wsi", "technical_wsi", "behavioral_wsi")
_ANALYSES_COLS = ("autodeclaration_score", "context_score", "final_score")


def upgrade() -> None:
    conn = op.get_bind()

    # --- 1. wsi_results: UPDATE *2 + CHECK BETWEEN 0 AND 10 ---
    if _table_exists(conn, "wsi_results"):
        for col in _RESULTS_COLS:
            if not _column_exists(conn, "wsi_results", col):
                continue
            for cname in _check_constraint_names(conn, "wsi_results", col):
                op.execute(sa.text(
                    f'ALTER TABLE wsi_results DROP CONSTRAINT "{cname}"'
                ))
            # Multiplica scores existentes por 2 (apenas valores não nulos)
            op.execute(sa.text(
                f"UPDATE wsi_results SET {col} = {col} * 2 WHERE {col} IS NOT NULL"
            ))
            op.execute(sa.text(
                f"ALTER TABLE wsi_results "
                f"ADD CONSTRAINT wsi_results_{col}_check_v10 "
                f"CHECK ({col} IS NULL OR ({col} >= 0 AND {col} <= 10))"
            ))

        op.execute(sa.text(
            "COMMENT ON TABLE wsi_results IS "
            "'Final WSI scores (escala /10 — Task #497 PR2). "
            "Pesos technical/behavioral são DINÂMICOS por senioridade "
            "(SENIORITY_WEIGHTS, wsi_deterministic_scorer.py — spec §9.2).'"
        ))

    # --- 2. wsi_response_analyses: UPDATE *2 + CHECK ---
    if _table_exists(conn, "wsi_response_analyses"):
        for col in _ANALYSES_COLS:
            if not _column_exists(conn, "wsi_response_analyses", col):
                continue
            for cname in _check_constraint_names(conn, "wsi_response_analyses", col):
                op.execute(sa.text(
                    f'ALTER TABLE wsi_response_analyses DROP CONSTRAINT "{cname}"'
                ))
            op.execute(sa.text(
                f"UPDATE wsi_response_analyses SET {col} = {col} * 2 WHERE {col} IS NOT NULL"
            ))
            op.execute(sa.text(
                f"ALTER TABLE wsi_response_analyses "
                f"ADD CONSTRAINT wsi_response_analyses_{col}_check_v10 "
                f"CHECK ({col} IS NULL OR ({col} >= 0 AND {col} <= 10))"
            ))


def downgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "wsi_response_analyses"):
        for col in _ANALYSES_COLS:
            if not _column_exists(conn, "wsi_response_analyses", col):
                continue
            for cname in _check_constraint_names(conn, "wsi_response_analyses", col):
                op.execute(sa.text(
                    f'ALTER TABLE wsi_response_analyses DROP CONSTRAINT "{cname}"'
                ))
            op.execute(sa.text(
                f"UPDATE wsi_response_analyses SET {col} = {col} / 2 WHERE {col} IS NOT NULL"
            ))
            op.execute(sa.text(
                f"ALTER TABLE wsi_response_analyses "
                f"ADD CONSTRAINT wsi_response_analyses_{col}_check "
                f"CHECK ({col} IS NULL OR ({col} >= 1 AND {col} <= 5))"
            ))

    if _table_exists(conn, "wsi_results"):
        for col in _RESULTS_COLS:
            if not _column_exists(conn, "wsi_results", col):
                continue
            for cname in _check_constraint_names(conn, "wsi_results", col):
                op.execute(sa.text(
                    f'ALTER TABLE wsi_results DROP CONSTRAINT "{cname}"'
                ))
            op.execute(sa.text(
                f"UPDATE wsi_results SET {col} = {col} / 2 WHERE {col} IS NOT NULL"
            ))
            op.execute(sa.text(
                f"ALTER TABLE wsi_results "
                f"ADD CONSTRAINT wsi_results_{col}_check "
                f"CHECK ({col} IS NULL OR ({col} >= 1 AND {col} <= 5))"
            ))

        op.execute(sa.text(
            "COMMENT ON TABLE wsi_results IS "
            "'Final WSI scores. Pesos technical/behavioral são DINÂMICOS por senioridade "
            "(SENIORITY_WEIGHTS, wsi_deterministic_scorer.py — spec §9.2), não fixos em 70/30.'"
        ))
