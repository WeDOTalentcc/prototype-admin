"""Create offer_proposals table for E10 (Proposta & Negociação).

Revision ID: 098_create_offer_proposals_table
Revises: 097_reconcile_recruitment_campaigns_columns
Create Date: 2026-04-21

Idempotent — only creates the table when it doesn't already exist, so
environments that bootstrapped via ``Base.metadata.create_all`` stay
healthy and environments running Alembic head pick the table up cleanly.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "098_create_offer_proposals_table"
down_revision = "097_reconcile_recruitment_campaigns_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "offer_proposals" in inspector.get_table_names():
        return

    op.create_table(
        "offer_proposals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("company_id", sa.String(length=255), nullable=False),
        sa.Column("job_vacancy_id", UUID(as_uuid=True), nullable=True),
        sa.Column("candidate_id", UUID(as_uuid=True), nullable=True),
        sa.Column("vacancy_candidate_id", UUID(as_uuid=True), nullable=True),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("candidate_email", sa.String(length=255), nullable=True),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True, server_default="BRL"),
        sa.Column("salary", sa.Float(), nullable=True),
        sa.Column("bonus_pct", sa.Float(), nullable=True),
        sa.Column("bonus_target", sa.Float(), nullable=True),
        sa.Column("benefits", JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb")),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("response_deadline", sa.DateTime(), nullable=True),
        sa.Column("custom_clauses", JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb")),
        sa.Column("letter_markdown", sa.Text(), nullable=True),
        sa.Column("letter_html", sa.Text(), nullable=True),
        sa.Column("template_version", sa.String(length=32), nullable=True),
        sa.Column("llm_provider", sa.String(length=32), nullable=True),
        sa.Column("llm_model", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("current_round", sa.Float(), nullable=True, server_default="0"),
        sa.Column("rounds", JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb")),
        sa.Column("approval_request_id", UUID(as_uuid=True), nullable=True),
        sa.Column("approval_required_level", sa.String(length=32), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("sent_via", JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb")),
        sa.Column("candidate_responded_at", sa.DateTime(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("declined_at", sa.DateTime(), nullable=True),
        sa.Column("decline_reason", sa.Text(), nullable=True),
        sa.Column("e11_triggered", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("e12_triggered", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_offer_proposals_company_id", "offer_proposals", ["company_id"]
    )
    op.create_index(
        "ix_offer_proposals_status", "offer_proposals", ["status"]
    )
    op.create_index(
        "ix_offer_proposals_job_vacancy_id", "offer_proposals", ["job_vacancy_id"]
    )
    op.create_index(
        "ix_offer_proposals_candidate_id", "offer_proposals", ["candidate_id"]
    )
    op.create_index(
        "ix_offer_proposals_vacancy_candidate_id",
        "offer_proposals",
        ["vacancy_candidate_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "offer_proposals" not in inspector.get_table_names():
        return
    for ix in (
        "ix_offer_proposals_vacancy_candidate_id",
        "ix_offer_proposals_candidate_id",
        "ix_offer_proposals_job_vacancy_id",
        "ix_offer_proposals_status",
        "ix_offer_proposals_company_id",
    ):
        try:
            op.drop_index(ix, table_name="offer_proposals")
        except Exception:
            pass
    op.drop_table("offer_proposals")
