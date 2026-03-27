"""Add LangGraph native checkpoint columns to agent_checkpoints.

Revision ID: 026_add_langgraph_checkpoint_columns
Revises: 025_add_agent_execution_metadata
Create Date: 2026-03-07

Fase 3 — LangGraph Native:
Amplia a tabela agent_checkpoints (criada em 012) para suportar
o formato de checkpoint do LangGraph nativo:
- checkpoint_data: blob completo do checkpoint (JSONB)
- metadata_json: metadados do checkpoint (step, source, etc.)
- checkpoint_id: ID único do checkpoint (formato LangGraph)
- parent_checkpoint_id: ID do checkpoint pai (para histórico de turnos)

Isso permite usar a tabela existente como backend para um
PostgresSaver customizado, sem depender de langgraph-checkpoint-postgres.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "026_add_langgraph_checkpoint_columns"
down_revision = "025_add_agent_execution_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adiciona colunas LangGraph-compatíveis à tabela existente
    op.add_column(
        "agent_checkpoints",
        sa.Column("checkpoint_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "agent_checkpoints",
        sa.Column("parent_checkpoint_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "agent_checkpoints",
        sa.Column("checkpoint_data", JSONB, nullable=True),
    )
    op.add_column(
        "agent_checkpoints",
        sa.Column("checkpoint_metadata", JSONB, nullable=True, server_default="{}"),
    )
    op.add_column(
        "agent_checkpoints",
        sa.Column("checkpoint_ns", sa.String(255), nullable=True, server_default="''"),
    )

    # Índice para lookup por checkpoint_id (usado em restauração de state)
    op.create_index(
        "idx_agent_checkpoints_checkpoint_id",
        "agent_checkpoints",
        ["checkpoint_id"],
        postgresql_where=sa.text("checkpoint_id IS NOT NULL"),
    )

    # Tabela de writes pendentes (writes uncommitted do LangGraph)
    op.create_table(
        "agent_checkpoint_writes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("thread_id", sa.String(255), nullable=False),
        sa.Column("checkpoint_ns", sa.String(255), nullable=False, server_default="''"),
        sa.Column("checkpoint_id", sa.String(255), nullable=False),
        sa.Column("task_id", sa.String(255), nullable=False),
        sa.Column("idx", sa.Integer, nullable=False),
        sa.Column("channel", sa.String(255), nullable=False),
        sa.Column("type", sa.String(100), nullable=True),
        sa.Column("blob", sa.LargeBinary, nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_checkpoint_writes_lookup",
        "agent_checkpoint_writes",
        ["thread_id", "checkpoint_ns", "checkpoint_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_checkpoint_writes_lookup", table_name="agent_checkpoint_writes")
    op.drop_table("agent_checkpoint_writes")

    op.drop_index("idx_agent_checkpoints_checkpoint_id", table_name="agent_checkpoints")
    op.drop_column("agent_checkpoints", "checkpoint_ns")
    op.drop_column("agent_checkpoints", "checkpoint_metadata")
    op.drop_column("agent_checkpoints", "checkpoint_data")
    op.drop_column("agent_checkpoints", "parent_checkpoint_id")
    op.drop_column("agent_checkpoints", "checkpoint_id")
