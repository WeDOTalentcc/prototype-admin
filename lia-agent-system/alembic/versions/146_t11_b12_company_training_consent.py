"""T-11 B.1.2: CompanyTrainingConsent canonical table (ADR-RLHF-001).

Revision ID: 146_t11_b12_company_training_consent
Revises: 145_job_vacancies_created_at_default
Create Date: 2026-05-21

Cria table tenant-level training data consent (T-11 fine-tune pipeline).

Schema canonical:
- 1 row per company_id (UNIQUE constraint)
- consent_given (default False) + granted_at + revoked_at lifecycle
- version + legal_basis (LGPD Art. 7 §I)
- audit trail (consent_source, ip_address, user_id_granted/revoked)
- revoke_reason canonical (LGPD Art. 18 cascade)

Indexes canonical:
- ix_company_training_consents_company_id (lookup canonical)
- ix_company_training_consents_revoked_at (filter active)
- idx_company_training_consents_active (composite — list_quality_feedback hot path)

Sentinel: tests/unit/test_p0_t11_b12_company_training_consent.py asserts
table presence + UNIQUE constraint + indexes.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = "146_t11_b12_company_training_consent"
down_revision = "145_job_vacancies_created_at_default"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create company_training_consents table canonical."""
    op.create_table(
        "company_training_consents",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "consent_given",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("granted_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column(
            "version",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'1.0'"),
        ),
        sa.Column(
            "legal_basis",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'LGPD_ART_7_I'"),
        ),
        sa.Column("consent_source", sa.String(50), nullable=True),
        sa.Column("consent_text", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_id_granted", sa.String(100), nullable=True),
        sa.Column("user_id_revoked", sa.String(100), nullable=True),
        sa.Column("revoke_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "company_id", name="uq_company_training_consents_company_id"
        ),
    )

    # Lookup canonical index
    op.create_index(
        "ix_company_training_consents_company_id",
        "company_training_consents",
        ["company_id"],
    )
    # Filter active (consent_given + revoked_at) — hot path em list_quality_feedback
    op.create_index(
        "idx_company_training_consents_active",
        "company_training_consents",
        ["company_id", "consent_given", "revoked_at"],
    )
    # Revoked filter (LGPD Art. 18 cascade audit)
    op.create_index(
        "ix_company_training_consents_revoked_at",
        "company_training_consents",
        ["revoked_at"],
    )


def downgrade() -> None:
    """Drop company_training_consents table canonical."""
    op.drop_index(
        "ix_company_training_consents_revoked_at",
        table_name="company_training_consents",
    )
    op.drop_index(
        "idx_company_training_consents_active",
        table_name="company_training_consents",
    )
    op.drop_index(
        "ix_company_training_consents_company_id",
        table_name="company_training_consents",
    )
    op.drop_table("company_training_consents")
