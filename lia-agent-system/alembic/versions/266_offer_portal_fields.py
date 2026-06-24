"""266 — offer_proposals portal fields (candidate_token, acceptance_url, portal timestamps)

Adds Phase 1 fields for the candidate-facing offer portal (N1) and
negotiation notes (N2/N3 concierge). All columns are nullable with no
server_default so they never break existing rows.

Fields added:
  candidate_token      — UUID unique index; generated on first send; portal access key
  acceptance_url       — Text; full URL to /portal/proposta/{token}
  candidate_viewed_at  — DateTime; set when candidate opens portal page
  candidate_response_notes — Text; free-text from candidate on acceptance/decline
  negotiation_context_notes — Text; internal recruiter notes for N3 rounds
  offer_link_sent_at   — DateTime; set when acceptance_url was delivered to candidate

Revision ID: 266_offer_portal_fields
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "266_offer_portal_fields"
down_revision = None
branch_labels = None
depends_on = None

_TABLE = "offer_proposals"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column("candidate_token", UUID(as_uuid=True), nullable=True))
    op.add_column(_TABLE, sa.Column("acceptance_url", sa.Text(), nullable=True))
    op.add_column(_TABLE, sa.Column("candidate_viewed_at", sa.DateTime(), nullable=True))
    op.add_column(_TABLE, sa.Column("candidate_response_notes", sa.Text(), nullable=True))
    op.add_column(_TABLE, sa.Column("negotiation_context_notes", sa.Text(), nullable=True))
    op.add_column(_TABLE, sa.Column("offer_link_sent_at", sa.DateTime(), nullable=True))

    # Unique index on candidate_token — each token maps to exactly one proposal
    op.create_index(
        "ix_offer_proposals_candidate_token",
        _TABLE,
        ["candidate_token"],
        unique=True,
        postgresql_where=sa.text("candidate_token IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_offer_proposals_candidate_token", table_name=_TABLE)
    op.drop_column(_TABLE, "offer_link_sent_at")
    op.drop_column(_TABLE, "negotiation_context_notes")
    op.drop_column(_TABLE, "candidate_response_notes")
    op.drop_column(_TABLE, "candidate_viewed_at")
    op.drop_column(_TABLE, "acceptance_url")
    op.drop_column(_TABLE, "candidate_token")
