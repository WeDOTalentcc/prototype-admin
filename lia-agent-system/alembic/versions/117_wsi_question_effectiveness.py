"""Sprint B Phase 3 - Create wsi_question_effectiveness table.

Aprendizado por skill hierarquica (filho + parent rollup denormalizado).
Welford incremental: mean + M2 stats sem reler historico.

Multi-tenancy: company_id NOT NULL com indice composto unico.
LGPD: apenas agregados anonimizados.
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "117_wsi_question_effectiveness"
# Renamed from "103_wsi_question_effectiveness" during import from agent
# Repl 70fcc952: collided with existing 103_add_compensation_policy_id_to_jobs
# in the destination branch, and the original down_revision
# "102_bigfive_department_profile" was renamed to "115_bigfive_department_profile"
# by the collision-fix commit. Chained after 116_create_offer_proposals so the
# imported sub-chain has a single coherent head.
down_revision = "116_create_offer_proposals"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wsi_question_effectiveness",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("skill_probed", sa.String(100), nullable=False),
        sa.Column("parent_id", sa.String(100), nullable=False),
        sa.Column("department", sa.String(100), nullable=False, server_default=""),
        sa.Column("seniority_level", sa.String(50), nullable=False, server_default=""),
        # Counts
        sa.Column("times_used", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("times_hired", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("times_rejected", sa.Integer, nullable=False, server_default=sa.text("0")),
        # Welford hired
        sa.Column("mean_score_hired", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("m2_score_hired", sa.Float, nullable=False, server_default=sa.text("0.0")),
        # Welford rejected
        sa.Column("mean_score_rejected", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("m2_score_rejected", sa.Float, nullable=False, server_default=sa.text("0.0")),
        # Computed
        sa.Column("discrimination_score", sa.Float, nullable=False, server_default=sa.text("0.0")),
        # Fairness (Phase 2.5)
        sa.Column("adverse_impact_score", sa.Float, nullable=False, server_default=sa.text("0.0")),
        sa.Column("fairness_blocked", sa.Integer, nullable=False, server_default=sa.text("0")),
        # Timestamps
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
        sa.Column("last_outcome_at", sa.DateTime, nullable=True),
    )

    op.create_index(
        "ix_wsi_eff_unique",
        "wsi_question_effectiveness",
        ["company_id", "skill_probed", "department", "seniority_level"],
        unique=True,
    )
    op.create_index(
        "ix_wsi_eff_parent_lookup",
        "wsi_question_effectiveness",
        ["company_id", "parent_id"],
    )
    op.create_index(
        "ix_wsi_eff_company",
        "wsi_question_effectiveness",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_wsi_eff_company", table_name="wsi_question_effectiveness")
    op.drop_index("ix_wsi_eff_parent_lookup", table_name="wsi_question_effectiveness")
    op.drop_index("ix_wsi_eff_unique", table_name="wsi_question_effectiveness")
    op.drop_table("wsi_question_effectiveness")
