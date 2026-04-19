"""Audit task #544 — outbox durável para AiConsumption.

Revision ID: 095_create_ai_consumption_outbox
Revises: 094_wsi_responses_fk_restrict
Create Date: 2026-04-22

Contexto
--------
O sink de tracking de IA hoje é fire-and-forget (`loop.create_task` em
`usage_tracking_callback.py`). Em shutdown, callbacks pendentes são
canceladas via `CancelledError` e o evento se perde — sem cobertura
auditável para EU AI Act §12 (logs de IA Alto Risco devem sobreviver
operações ordinárias do sistema, incluindo restart).

Esta migration cria `ai_consumption_outbox` — uma fila durável de
payloads pendentes. Pipeline novo:

1. Callback persiste payload no outbox (escrita pequena, idempotente).
2. Worker periódico (lifespan-tied em `app/main.py`) drena lotes,
   chama `TokenTrackingService.record_usage` e marca `delivered_at`.
3. Restart preserva linhas não-entregues; worker as drena no próximo
   boot.

Sem PII no payload (apenas IDs / contadores / nomes de modelo).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "095_create_ai_consumption_outbox"
down_revision = "094_wsi_responses_fk_restrict"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_consumption_outbox",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    # Index para drenagem eficiente: WHERE delivered_at IS NULL ORDER BY created_at.
    op.create_index(
        "ix_ai_consumption_outbox_pending",
        "ai_consumption_outbox",
        ["created_at"],
        postgresql_where=sa.text("delivered_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ai_consumption_outbox_pending",
        table_name="ai_consumption_outbox",
    )
    op.drop_table("ai_consumption_outbox")
