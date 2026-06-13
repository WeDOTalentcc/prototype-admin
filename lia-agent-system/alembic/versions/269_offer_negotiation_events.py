"""267 — offer_negotiation_events table (N2 concierge event log)

Cria tabela canônica para log de eventos de negociação de proposta.
Cada evento registra: tipo, ator, rodada, salário proposto/contra, FairnessGuard snapshot.

Revision ID: 269_offer_negotiation_events
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "269_offer_negotiation_events"
down_revision = None
branch_labels = None
depends_on = None

_TABLE = "offer_negotiation_events"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("offer_id", UUID(as_uuid=True), sa.ForeignKey("offer_proposals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("actor", sa.String(32), nullable=False),
        sa.Column("salary_proposed", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_counter", sa.Numeric(12, 2), nullable=True),
        sa.Column("benefits_snapshot", JSONB(), nullable=True, server_default="{}"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("fairness_snapshot", JSONB(), nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "event_type IN ("
            "'sent','viewed','accepted','declined','counter_proposed',"
            "'concierge_touchpoint','negotiation_round','approved_by_manager',"
            "'expired','cancelled')",
            name="chk_offer_neg_event_type",
        ),
        sa.CheckConstraint(
            "actor IN ('candidate','recruiter','lia','manager')",
            name="chk_offer_neg_actor",
        ),
    )
    op.create_index("ix_offer_neg_events_offer_id", _TABLE, ["offer_id"])
    op.create_index("ix_offer_neg_events_company", _TABLE, ["company_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_offer_neg_events_company", table_name=_TABLE)
    op.drop_index("ix_offer_neg_events_offer_id", table_name=_TABLE)
    op.drop_table(_TABLE)
