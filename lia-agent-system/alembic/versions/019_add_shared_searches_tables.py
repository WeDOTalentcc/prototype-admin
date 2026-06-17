"""Add shared_searches tables for collaborative shortlists and search sharing.

Revision ID: 019_add_shared_searches_tables
Revises: 018_add_bias_audit_snapshot
Create Date: 2026-03-03

H.1 — SharedSearches:
Persiste buscas e listas compartilhadas com gestores externos via link seguro (OTP+JWT).
Feedback de gestores rastreado por candidato — auditável SOX / EU AI Act.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "019_add_shared_searches_tables"
down_revision = "018_add_bias_audit_snapshot"
branch_labels = None
depends_on = None


def upgrade():
    # Enum types
    op.execute(
        "CREATE TYPE share_type_enum AS ENUM ('search', 'list')"
    )
    op.execute(
        "CREATE TYPE share_status_enum AS ENUM ('active', 'expired', 'revoked')"
    )
    op.execute(
        "CREATE TYPE share_feedback_decision_enum AS ENUM ('approved', 'maybe', 'rejected')"
    )

    # shared_searches
    op.create_table(
        "shared_searches",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "share_type",
            sa.Enum("search", "list", name="share_type_enum", create_type=False),
            nullable=False,
        ),
        sa.Column("source_query", sa.Text, nullable=True),
        sa.Column("source_list_id", UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),
        sa.Column(
            "status",
            sa.Enum("active", "expired", "revoked", name="share_status_enum", create_type=False),
            nullable=False,
            server_default="active",
        ),
        sa.Column("snapshot_payload", JSONB, nullable=True),
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
    op.create_index(
        "ix_shared_searches_company_id", "shared_searches", ["company_id"]
    )
    op.create_index(
        "ix_shared_searches_expires_at", "shared_searches", ["expires_at"]
    )
    op.create_index(
        "ix_shared_searches_updated_at", "shared_searches", ["updated_at"]
    )

    # shared_search_access
    op.create_table(
        "shared_search_access",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "shared_search_id",
            UUID(as_uuid=True),
            sa.ForeignKey("shared_searches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(200), nullable=True),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("access_token", sa.String(255), nullable=False, unique=True),
        sa.Column("otp_hash", sa.String(255), nullable=True),
        sa.Column("otp_expires_at", sa.DateTime, nullable=True),
        sa.Column("first_accessed_at", sa.DateTime, nullable=True),
        sa.Column("last_accessed_at", sa.DateTime, nullable=True),
        sa.Column(
            "total_views", sa.Integer, nullable=False, server_default="0"
        ),
        sa.UniqueConstraint(
            "shared_search_id", "email", name="uq_shared_search_access_search_email"
        ),
    )
    op.create_index(
        "ix_shared_search_access_shared_search_id",
        "shared_search_access",
        ["shared_search_id"],
    )
    op.create_index(
        "ix_shared_search_access_email", "shared_search_access", ["email"]
    )
    op.create_index(
        "ix_shared_search_access_token",
        "shared_search_access",
        ["access_token"],
        unique=True,
    )

    # shared_search_feedback
    op.create_table(
        "shared_search_feedback",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "shared_search_id",
            UUID(as_uuid=True),
            sa.ForeignKey("shared_searches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("candidate_id", UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_email", sa.String(255), nullable=False),
        sa.Column(
            "decision",
            sa.Enum(
                "approved",
                "maybe",
                "rejected",
                name="share_feedback_decision_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer, nullable=True),
        sa.Column("comment", sa.Text, nullable=True),
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
        sa.UniqueConstraint(
            "shared_search_id",
            "candidate_id",
            "reviewer_email",
            name="uq_shared_search_feedback_search_candidate_reviewer",
        ),
    )
    op.create_index(
        "ix_shared_search_feedback_shared_search_id",
        "shared_search_feedback",
        ["shared_search_id"],
    )
    op.create_index(
        "ix_shared_search_feedback_candidate_id",
        "shared_search_feedback",
        ["candidate_id"],
    )
    op.create_index(
        "ix_shared_search_feedback_reviewer_email",
        "shared_search_feedback",
        ["reviewer_email"],
    )


def downgrade():
    op.drop_index(
        "ix_shared_search_feedback_reviewer_email", "shared_search_feedback"
    )
    op.drop_index(
        "ix_shared_search_feedback_candidate_id", "shared_search_feedback"
    )
    op.drop_index(
        "ix_shared_search_feedback_shared_search_id", "shared_search_feedback"
    )
    op.drop_table("shared_search_feedback")

    op.drop_index("ix_shared_search_access_token", "shared_search_access")
    op.drop_index("ix_shared_search_access_email", "shared_search_access")
    op.drop_index(
        "ix_shared_search_access_shared_search_id", "shared_search_access"
    )
    op.drop_table("shared_search_access")

    op.drop_index("ix_shared_searches_updated_at", "shared_searches")
    op.drop_index("ix_shared_searches_expires_at", "shared_searches")
    op.drop_index("ix_shared_searches_company_id", "shared_searches")
    op.drop_table("shared_searches")

    op.execute("DROP TYPE IF EXISTS share_feedback_decision_enum")
    op.execute("DROP TYPE IF EXISTS share_status_enum")
    op.execute("DROP TYPE IF EXISTS share_type_enum")
