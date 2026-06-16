"""Add routing_cache_vectors table for semantic vector cache.

Revision ID: 028_add_routing_cache_vectors
Revises: 027_add_langgraph_native_checkpointer_tables
Create Date: 2026-03-08

Fase 2 — Inteligência do Orquestrador (Gap #1):
Cria a tabela routing_cache_vectors para o VectorSemanticCache.

Diferença em relação ao SemanticCache (hash MD5):
- Hash: "criar vaga dev" e "cria uma vaga pra dev" → MISS (strings diferentes)
- Vector: "criar vaga dev" e "cria uma vaga pra dev" → HIT (cosine_sim ≈ 0.97)

Reduz chamadas LLM em 40-60% após semanas de uso.

O índice IVFFlat acelera a busca por vizinhos mais próximos com
lists=100 (recomendado para tabelas com ~100k a 1M de registros).
Para tabelas menores, o índice pode ser omitido; pgvector fará
sequential scan que já é rápido para poucos registros.
"""
from alembic import op
import sqlalchemy as sa


revision = "028_add_routing_cache_vectors"
down_revision = "027_add_langgraph_native_checkpointer_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Garante que a extensão vector está habilitada
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "routing_cache_vectors",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True) if _has_pg() else sa.String(36),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("message_text", sa.Text, nullable=False),
        # vector(1536): text-embedding-3-small da OpenAI
        # Tipo nativo pgvector — declarado como String aqui, cast explícito nas queries
        sa.Column("message_embedding", sa.Text, nullable=True),
        sa.Column("domain_id", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column(
            "source",
            sa.String(100),
            nullable=False,
            comment="fast_router | llm_cascade:haiku | llm_cascade:sonnet | etc.",
        ),
        sa.Column("hit_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "last_hit_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
        ),
    )

    # Converter a coluna message_embedding para tipo vector(1536) nativo
    # (não suportado diretamente pelo SQLAlchemy sem extensão extra)
    op.execute(
        "ALTER TABLE routing_cache_vectors "
        "ALTER COLUMN message_embedding TYPE vector(1536) "
        "USING message_embedding::vector"
    )

    # Índice IVFFlat para busca eficiente por cosine similarity
    # lists=100 é adequado para até ~1M de registros
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_routing_cache_embedding "
        "ON routing_cache_vectors "
        "USING ivfflat (message_embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )

    op.create_index(
        "idx_routing_cache_domain",
        "routing_cache_vectors",
        ["domain_id"],
    )

    op.create_index(
        "idx_routing_cache_created",
        "routing_cache_vectors",
        [sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_routing_cache_created", table_name="routing_cache_vectors")
    op.drop_index("idx_routing_cache_domain", table_name="routing_cache_vectors")
    op.execute("DROP INDEX IF EXISTS idx_routing_cache_embedding")
    op.drop_table("routing_cache_vectors")


def _has_pg() -> bool:
    """Verifica se o dialeto PostgreSQL está disponível."""
    try:
        from sqlalchemy.dialects import postgresql  # noqa: F401
        return True
    except ImportError:
        return False
