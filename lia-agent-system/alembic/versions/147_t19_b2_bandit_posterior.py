"""T-19 B.2: BanditPosterior canonical table (ADR-AB-001).

Revision ID: 147_t19_b2_bandit_posterior
Revises: 146_t11_b12_company_training_consent
Create Date: 2026-05-21

Cria table para persistir Thompson sampling posteriors (Beta α, β) per
(test_name, arm, company_id). Resolve gap V4 ThompsonSampler in-memory only.

Pattern canonical:
- UNIQUE(test_name, arm, company_id) — 1 posterior per combination
- α + β floats (Bayesian Beta prior shape parameters)
- n_observations Integer (audit aid)
- company_id nullable (NULL = global test cross-tenant)
- version String(20) (drift detection futuro)

Indexes canonical:
- ix_bandit_posteriors_test_name (lookup by experiment)
- ix_bandit_posteriors_company_id (filter per-company)
- idx_bandit_posteriors_test_lookup (composite hot path)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "147_t19_b2_bandit_posterior"
down_revision = "146_t11_b12_company_training_consent"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create bandit_posteriors table canonical."""
    op.create_table(
        "bandit_posteriors",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("test_name", sa.String(255), nullable=False),
        sa.Column("arm", sa.String(100), nullable=False),
        sa.Column(
            "alpha",
            sa.Float(),
            nullable=False,
            server_default=sa.text("1.0"),
        ),
        sa.Column(
            "beta",
            sa.Float(),
            nullable=False,
            server_default=sa.text("1.0"),
        ),
        sa.Column(
            "n_observations",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("company_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "version",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'1.0'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "test_name", "arm", "company_id",
            name="uq_bandit_posteriors_test_arm_company",
        ),
    )

    op.create_index(
        "ix_bandit_posteriors_test_name",
        "bandit_posteriors",
        ["test_name"],
    )
    op.create_index(
        "ix_bandit_posteriors_company_id",
        "bandit_posteriors",
        ["company_id"],
    )
    op.create_index(
        "idx_bandit_posteriors_test_lookup",
        "bandit_posteriors",
        ["test_name", "company_id"],
    )


def downgrade() -> None:
    """Drop bandit_posteriors table canonical."""
    op.drop_index(
        "idx_bandit_posteriors_test_lookup",
        table_name="bandit_posteriors",
    )
    op.drop_index(
        "ix_bandit_posteriors_company_id",
        table_name="bandit_posteriors",
    )
    op.drop_index(
        "ix_bandit_posteriors_test_name",
        table_name="bandit_posteriors",
    )
    op.drop_table("bandit_posteriors")
