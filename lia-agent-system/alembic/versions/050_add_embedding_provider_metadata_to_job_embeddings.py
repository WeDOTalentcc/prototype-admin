"""Add embedding_provider and embedding_model columns to job_embeddings table.

Task #134: Embedding Provider Factory — Arquitetura multi-provider.

Adds provider/model metadata per vector to:
1. Enable traceability of which provider/model generated each embedding.
2. Enforce strict same-provider filtering in pgvector similarity queries to
   prevent dimension mismatches.

Dimension strategy:
  The existing Vector(768) column type is preserved. Both providers write
  768-dimensional vectors:
  - GeminiEmbeddingProvider: text-embedding-004 natively produces 768-dim.
  - OpenAIEmbeddingProvider: text-embedding-3-small with dimensions=768
    (OpenAI's dimension-reduction feature, available for v3 models).
  This avoids any schema migration while keeping all embeddings comparable
  within the same provider bucket.

Backfill: existing rows with embeddings are assumed to be from Gemini
and are tagged accordingly.

Revision ID: 050
Revises: 049
Create Date: 2026-04-04
"""
from alembic import op
import sqlalchemy as sa

revision = '050'
down_revision = '049'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'job_embeddings',
        sa.Column(
            'embedding_provider',
            sa.String(50),
            nullable=True,
            comment='Provider used to generate this vector (gemini, openai, etc.)',
        )
    )
    op.add_column(
        'job_embeddings',
        sa.Column(
            'embedding_model',
            sa.String(100),
            nullable=True,
            comment='Specific model used (e.g. text-embedding-004, text-embedding-3-small)',
        )
    )

    op.execute(
        "UPDATE job_embeddings SET embedding_provider = 'gemini', "
        "embedding_model = 'text-embedding-004' "
        "WHERE embedding IS NOT NULL AND embedding_provider IS NULL"
    )

    op.create_index(
        'idx_job_embedding_provider',
        'job_embeddings',
        ['embedding_provider'],
    )

    op.create_index(
        'idx_job_embedding_provider_model',
        'job_embeddings',
        ['company_id', 'embedding_provider', 'embedding_model'],
    )


def downgrade() -> None:
    op.drop_index('idx_job_embedding_provider_model', table_name='job_embeddings')
    op.drop_index('idx_job_embedding_provider', table_name='job_embeddings')
    op.drop_column('job_embeddings', 'embedding_model')
    op.drop_column('job_embeddings', 'embedding_provider')
