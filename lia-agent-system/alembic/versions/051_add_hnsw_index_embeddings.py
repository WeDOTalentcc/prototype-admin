"""Add HNSW index for vector similarity search performance

Revision ID: 051
Revises: 050
Create Date: 2026-04-04

WHY: embedding_records e job_embeddings usavam busca linear O(n) para cosine similarity.
     O HNSW (Hierarchical Navigable Small World) reduz para O(log n), essencial em produção
     com milhares de candidatos por empresa.

PARÂMETROS ESCOLHIDOS:
  m=16             → número de conexões por nó no grafo (tradeoff: memória vs recall)
  ef_construction=64 → tamanho da fila durante construção (tradeoff: tempo de build vs qualidade)
  vector_cosine_ops → operador correto para embeddings normalizados (text-embedding-3-*)

VERIFICAÇÃO PÓS-MIGRATION:
  EXPLAIN ANALYZE
    SELECT id, content, embedding <=> '[...]' AS distance
    FROM embedding_records
    WHERE company_id = 'empresa_teste'
    ORDER BY distance
    LIMIT 10;
  → deve mostrar "Index Scan using idx_embedding_records_hnsw"
  → NÃO deve mostrar "Seq Scan"
"""
from alembic import op

revision = '051'
down_revision = '050'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Index HNSW para embedding_records (busca semântica de candidatos por vaga)
    # CREATE INDEX CONCURRENTLY não bloqueia writes durante a construção
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_embedding_records_hnsw
        ON embedding_records USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Index HNSW para job_embeddings (matching vaga → candidato, JD search)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_embeddings_hnsw
        ON job_embeddings USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)

    # Index HNSW para conversation_memories (busca semântica no histórico de conversas)
    # Verifica se a tabela existe antes de criar (pode não existir em todos os ambientes)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'conversation_memories'
            ) THEN
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversation_memories_hnsw
                ON conversation_memories USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_embedding_records_hnsw")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_job_embeddings_hnsw")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_conversation_memories_hnsw")
