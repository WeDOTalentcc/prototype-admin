"""265 — create candidate_embeddings table (pgvector)

Revision ID: 265_candidate_embeddings
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY

revision = "265_candidate_embeddings"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
        CREATE TABLE IF NOT EXISTS candidate_embeddings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL,
            candidate_id UUID NOT NULL,
            name VARCHAR(255),
            summary TEXT,
            skills VARCHAR[] DEFAULT '{}',
            experience_summary TEXT,
            embedding vector(768),
            embedding_text TEXT,
            embedding_provider VARCHAR(50),
            embedding_model VARCHAR(100),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_candidate_embeddings_company_id ON candidate_embeddings (company_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_candidate_embeddings_candidate_id ON candidate_embeddings (candidate_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_candidate_embedding_company ON candidate_embeddings (company_id, is_active)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_candidate_embedding_cid ON candidate_embeddings (company_id, candidate_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_candidate_embeddings_created_at ON candidate_embeddings (created_at)")

    op.execute("ALTER TABLE candidate_embeddings ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE candidate_embeddings FORCE ROW LEVEL SECURITY")
    for action, clause in [
        ("SELECT", "USING"), ("INSERT", "WITH CHECK"),
        ("UPDATE", "USING"), ("DELETE", "USING"),
    ]:
        op.execute(
            f"CREATE POLICY candidate_embeddings_tenant_{action.lower()} "
            f"ON candidate_embeddings FOR {action} "
            f"{clause} (company_id::text = app_current_company_id())"
        )


def downgrade() -> None:
    for action in ["delete", "update", "insert", "select"]:
        op.execute(f"DROP POLICY IF EXISTS candidate_embeddings_tenant_{action} ON candidate_embeddings")
    op.execute("DROP TABLE IF EXISTS candidate_embeddings")
