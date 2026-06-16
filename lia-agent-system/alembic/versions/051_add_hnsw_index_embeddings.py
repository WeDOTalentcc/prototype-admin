"""Add HNSW index for vector similarity search performance

Revision ID: 051
Revises: 050
Create Date: 2026-04-04

WHY: Reduz busca vetorial de O(n) linear para O(log n).
     Usa IF EXISTS para ser seguro em diferentes ambientes.
"""
from alembic import op

revision = '051'
down_revision = '050'
branch_labels = None
depends_on = None


def _table_exists(conn, table_name):
    result = conn.execute(
        __import__('sqlalchemy').text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)"
        ),
        {"t": table_name}
    )
    return result.scalar()


def upgrade() -> None:
    # Obter conexão raw para verificar tabelas
    bind = op.get_bind()

    # HNSW para job_embeddings (sempre existe)
    if _table_exists(bind, "job_embeddings"):
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_job_embeddings_hnsw
            ON job_embeddings USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)

    # HNSW para embedding_records (pode não existir em todos os ambientes)
    if _table_exists(bind, "embedding_records"):
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_embedding_records_hnsw
            ON embedding_records USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)

    # HNSW para routing_cache_vectors (busca de routing semântico)
    if _table_exists(bind, "routing_cache_vectors"):
        op.execute("""
            CREATE INDEX IF NOT EXISTS idx_routing_cache_vectors_hnsw
            ON routing_cache_vectors USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_job_embeddings_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_embedding_records_hnsw")
    op.execute("DROP INDEX IF EXISTS idx_routing_cache_vectors_hnsw")
