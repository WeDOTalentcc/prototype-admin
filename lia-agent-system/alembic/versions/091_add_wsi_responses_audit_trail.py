"""Task #511 — Compliance EU AI Act WSI: audit trail + response_hash.

Revision ID: 091_add_wsi_responses_audit_trail
Revises: 090_widen_wsi_score_scale_to_10
Create Date: 2026-04-18

Contexto
--------
EU AI Act Art. 12 (logging) + LGPD Art. 20 exigem trilha de auditoria imutável
para sistemas de IA de Alto Risco em recrutamento. Hoje as respostas vivem em
`wsi_response_analyses` misturadas com flags/scores derivados.

Esta revisão:
  1. Cria `wsi_responses` (audit trail puro: id, session_id, question_id,
     raw_text, response_hash, candidate_id, company_id, created_at).
  2. Adiciona coluna `response_hash VARCHAR(64)` em `wsi_response_analyses`,
     faz backfill via SHA-256 nativa do Postgres (`pgcrypto.digest`), depois
     define NOT NULL.
  3. Índices: (session_id, question_id) para lookup por sessão; (response_hash)
     para detecção de duplicatas e integridade.

Reversibilidade
---------------
`downgrade()` dropa a tabela e a coluna sem perda em `wsi_response_analyses`
(o hash é derivável a qualquer momento). Idempotente: usa IF EXISTS.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "091_add_wsi_responses_audit_trail"
down_revision = "090_widen_wsi_score_scale_to_10"
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


def upgrade() -> None:
    conn = op.get_bind()

    # pgcrypto: precisamos para o backfill SHA-256 nativo.
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))

    # 1. Cria wsi_responses (audit trail imutável)
    if not _table_exists(conn, "wsi_responses"):
        op.execute(sa.text("""
            CREATE TABLE wsi_responses (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(255) NOT NULL,
                question_id VARCHAR(255) NOT NULL,
                raw_text TEXT NOT NULL,
                response_hash VARCHAR(64) NOT NULL,
                candidate_id VARCHAR(255),
                company_id VARCHAR(255),
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        op.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS ix_wsi_responses_session_question "
            "ON wsi_responses (session_id, question_id)"
        ))
        op.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS ix_wsi_responses_hash "
            "ON wsi_responses (response_hash)"
        ))
        op.execute(sa.text(
            "COMMENT ON TABLE wsi_responses IS "
            "'Audit trail imutavel das respostas WSI (EU AI Act Art. 12 / LGPD Art. 20). "
            "Task #511 — escrito por wsi_voice_orchestrator e triagem_session_service.'"
        ))

    # 2. Adiciona response_hash em wsi_response_analyses
    if _table_exists(conn, "wsi_response_analyses") and not _column_exists(
        conn, "wsi_response_analyses", "response_hash"
    ):
        op.execute(sa.text(
            "ALTER TABLE wsi_response_analyses ADD COLUMN response_hash VARCHAR(64)"
        ))

        # Backfill: SHA-256 sobre f"{session_id}:{question_id}:{lower(response_text)}"
        # (espaços não colapsados aqui — o app aplicará normalização full em escritas
        # futuras; o backfill garante apenas que a coluna fique populada para
        # registros legados, sem violar NOT NULL).
        #
        # NOTA OPERACIONAL (round 3): hashes computados aqui NÃO são bit-a-bit
        # comparáveis com hashes gerados em runtime pelo `hash_response()`
        # (que normaliza whitespace via `\s+ -> " "`). Consequência: para
        # detecção de duplicata cross-row em registros legados é necessário
        # rehash explícito após normalização. Aceitável porque (a) a coluna
        # serve primariamente a integridade NOT NULL e auditoria forense
        # registro-a-registro, e (b) o universo legado é finito e migrável
        # sob demanda. Se for necessária comparabilidade total, rodar script
        # de re-hash one-shot consumindo `hash_response` do app.
        op.execute(sa.text("""
            UPDATE wsi_response_analyses
            SET response_hash = encode(
                digest(
                    session_id || ':' || question_id || ':' || lower(coalesce(response_text, '')),
                    'sha256'
                ),
                'hex'
            )
            WHERE response_hash IS NULL
        """))

        op.execute(sa.text(
            "ALTER TABLE wsi_response_analyses "
            "ALTER COLUMN response_hash SET NOT NULL"
        ))
        op.execute(sa.text(
            "CREATE INDEX IF NOT EXISTS ix_wsi_response_analyses_hash "
            "ON wsi_response_analyses (response_hash)"
        ))


def downgrade() -> None:
    conn = op.get_bind()

    if _table_exists(conn, "wsi_response_analyses") and _column_exists(
        conn, "wsi_response_analyses", "response_hash"
    ):
        op.execute(sa.text(
            "DROP INDEX IF EXISTS ix_wsi_response_analyses_hash"
        ))
        op.execute(sa.text(
            "ALTER TABLE wsi_response_analyses DROP COLUMN response_hash"
        ))

    if _table_exists(conn, "wsi_responses"):
        op.execute(sa.text("DROP INDEX IF EXISTS ix_wsi_responses_session_question"))
        op.execute(sa.text("DROP INDEX IF EXISTS ix_wsi_responses_hash"))
        op.execute(sa.text("DROP TABLE wsi_responses"))
