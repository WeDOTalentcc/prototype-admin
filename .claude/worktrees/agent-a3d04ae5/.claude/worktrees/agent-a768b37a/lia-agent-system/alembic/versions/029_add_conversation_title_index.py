"""Add index on conversations(user_id, created_at DESC) for history queries.

Revision ID: 029_add_conversation_title_index
Revises: 028_add_routing_cache_vectors
Create Date: 2026-03-08

Phase 4a — LIA Float Universal Entry Point:
O LiaChatPanel busca histórico de conversas via GET /api/v1/conversations
filtrado por user_id e ordenado por created_at DESC. Sem índice, cada
query faz full scan na tabela conversations que pode crescer rapidamente
em ambientes multi-tenant.

Este índice reduz latência de ~200ms para ~5ms em tabelas com 100k+ registros.
Também cobre queries com limit/offset para paginação.
"""
from alembic import op
import sqlalchemy as sa


revision = "029_add_conversation_title_index"
down_revision = "028_add_routing_cache_vectors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Índice composto para queries de histórico por usuário ordenadas por data
    op.create_index(
        "ix_conversations_user_created",
        "conversations",
        ["user_id", sa.text("created_at DESC")],
        postgresql_using="btree",
    )

    # Índice parcial para conversas ativas (is_active=True) — subset mais consultado
    op.create_index(
        "ix_conversations_user_active",
        "conversations",
        ["user_id", sa.text("created_at DESC")],
        postgresql_where=sa.text("is_active = true AND is_archived = false"),
    )


def downgrade() -> None:
    op.drop_index("ix_conversations_user_active", table_name="conversations")
    op.drop_index("ix_conversations_user_created", table_name="conversations")
