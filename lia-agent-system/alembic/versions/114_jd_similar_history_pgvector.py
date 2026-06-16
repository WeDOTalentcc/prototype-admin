"""Sprint B Phase 1 — Create jd_similar_history with pgvector.

Cria tabela jd_similar_history pra suporte a learning loop "JD Similar History":
- Recruiter inicia vaga → busca JDs similares no histórico (similarity >= 0.7)
- Threshold: company precisa ter >= 10 JDs em histórico
- Outcome tracking: was_filled, time_to_fill_days, candidates_count
- Embedding: pgvector Vector(1536) compatível com OpenAI text-embedding-3-small

Multi-tenancy: company_id em todas as queries (NOT NULL, indexed).
PII: jd_enriched_json contém apenas conteúdo da vaga (sem candidate data).
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "114_jd_similar_history_pgvector"
# Renamed from "101_jd_similar_history_pgvector" during import from agent
# Repl 70fcc952: collided with the existing 101_ revision in the destination
# branch. Slot 114_ on the destination chain is unused, so we rename the
# imported revision id to match the file slot and chain it after 113.
down_revision = "113"
branch_labels = None
depends_on = None


JD_EMBEDDING_DIM = 1536


def upgrade() -> None:
    # Habilitar pgvector extension (idempotent — fail-safe se já existe)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "jd_similar_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Multi-tenancy
        sa.Column("company_id", sa.String(255), nullable=False, index=True),
        sa.Column("job_id", sa.String(255), nullable=True, index=True),
        # Search keys
        sa.Column("title_normalized", sa.String(500), nullable=False, index=True),
        sa.Column("seniority_level", sa.String(50), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        # JD content (no PII)
        sa.Column("jd_enriched_json", postgresql.JSONB, nullable=False),
        # pgvector embedding — OpenAI text-embedding-3-small (1536 dims)
        sa.Column(
            "jd_embedding",
            sa.dialects.postgresql.ARRAY(sa.Float),
            nullable=True,
        ),
        # Outcome tracking
        sa.Column("was_filled", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("time_to_fill_days", sa.Integer, nullable=True),
        sa.Column("candidates_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        # Reuse stats
        sa.Column("reused_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("last_reused_at", sa.DateTime, nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Convert jd_embedding column to pgvector Vector(1536) type.
    # Done via raw SQL because alembic op.create_table doesn't have pgvector type wrapper.
    op.execute(
        f"ALTER TABLE jd_similar_history "
        f"ALTER COLUMN jd_embedding TYPE vector({JD_EMBEDDING_DIM}) "
        f"USING jd_embedding::vector",
    )

    # ── Indexes ─────────────────────────────────────────────────────────────
    op.create_index(
        "ix_jd_similar_company_title",
        "jd_similar_history",
        ["company_id", "title_normalized"],
    )

    # IVFFlat index pra similarity search (cosine distance).
    # lists=100 é razoável até ~1M rows. Reavaliar quando crescer.
    op.execute(
        "CREATE INDEX ix_jd_similar_embedding_cosine ON jd_similar_history "
        "USING ivfflat (jd_embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_index("ix_jd_similar_embedding_cosine", table_name="jd_similar_history")
    op.drop_index("ix_jd_similar_company_title", table_name="jd_similar_history")
    op.drop_table("jd_similar_history")
    # Não removemos pgvector extension (pode ser usado por outras tabelas)
