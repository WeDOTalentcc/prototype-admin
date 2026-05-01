"""Add native LangGraph checkpointer tables (langgraph-checkpoint-postgres schema).

Revision ID: 027_add_langgraph_native_checkpointer_tables
Revises: 026_add_langgraph_checkpoint_columns
Create Date: 2026-03-08

Fase 1 (Gaps) — Ativação LangGraph:
Cria as tabelas exigidas pelo pacote `langgraph-checkpoint-postgres >= 2.0.0`.
Estas tabelas são distintas da tabela `agent_checkpoints` existente (criada em 012):
- langgraph_checkpoints: checkpoint completo (JSONB) por thread+namespace
- langgraph_checkpoint_writes: writes intermediários/uncommitted por tarefa
- langgraph_checkpoint_blobs: blobs de estado grande (BYTEA) por canal+versão

O método PostgresSaver.setup() também cria estas tabelas automaticamente, mas
tê-las via Alembic garante reprodutibilidade em ambientes sem conexão ativa
(CI, staging cold-start, migrações controladas).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "027_add_langgraph_native_checkpointer_tables"
down_revision = "027_add_pending_actions_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Tabela principal de checkpoints
    # ------------------------------------------------------------------
    op.create_table(
        "langgraph_checkpoints",
        sa.Column("thread_id", sa.Text, nullable=False),
        sa.Column("checkpoint_ns", sa.Text, nullable=False, server_default="''"),
        sa.Column("checkpoint_id", sa.Text, nullable=False),
        sa.Column("parent_checkpoint_id", sa.Text, nullable=True),
        sa.Column("type", sa.Text, nullable=True),
        sa.Column("checkpoint", JSONB, nullable=False),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("thread_id", "checkpoint_ns", "checkpoint_id"),
    )

    # ------------------------------------------------------------------
    # Tabela de writes intermediários (uncommitted writes por tarefa)
    # ------------------------------------------------------------------
    op.create_table(
        "langgraph_checkpoint_writes",
        sa.Column("thread_id", sa.Text, nullable=False),
        sa.Column("checkpoint_ns", sa.Text, nullable=False, server_default="''"),
        sa.Column("checkpoint_id", sa.Text, nullable=False),
        sa.Column("task_id", sa.Text, nullable=False),
        sa.Column("idx", sa.Integer, nullable=False),
        sa.Column("channel", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=True),
        sa.Column("value", JSONB, nullable=True),
        sa.PrimaryKeyConstraint("thread_id", "checkpoint_ns", "checkpoint_id", "task_id", "idx"),
    )

    # ------------------------------------------------------------------
    # Tabela de blobs de estado (estados grandes serializados)
    # ------------------------------------------------------------------
    op.create_table(
        "langgraph_checkpoint_blobs",
        sa.Column("thread_id", sa.Text, nullable=False),
        sa.Column("checkpoint_ns", sa.Text, nullable=False, server_default="''"),
        sa.Column("channel", sa.Text, nullable=False),
        sa.Column("version", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("blob", sa.LargeBinary, nullable=True),
        sa.PrimaryKeyConstraint("thread_id", "checkpoint_ns", "channel", "version"),
    )

    # ------------------------------------------------------------------
    # Índices para performance de lookup
    # ------------------------------------------------------------------
    op.create_index(
        "idx_lg_checkpoints_thread",
        "langgraph_checkpoints",
        ["thread_id"],
    )
    op.create_index(
        "idx_lg_checkpoints_created",
        "langgraph_checkpoints",
        [sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_lg_writes_thread",
        "langgraph_checkpoint_writes",
        ["thread_id", "checkpoint_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_lg_writes_thread", table_name="langgraph_checkpoint_writes")
    op.drop_index("idx_lg_checkpoints_created", table_name="langgraph_checkpoints")
    op.drop_index("idx_lg_checkpoints_thread", table_name="langgraph_checkpoints")

    op.drop_table("langgraph_checkpoint_blobs")
    op.drop_table("langgraph_checkpoint_writes")
    op.drop_table("langgraph_checkpoints")
