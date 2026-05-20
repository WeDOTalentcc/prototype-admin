"""Add company_id column to calibration_weights (F6.B6 audit 2026-05-20).

Revision ID: 133_calibration_weights_company_id
Revises: 132_job_vacancies_responsibilities
Create Date: 2026-05-20

Root cause (E2E audit 2026-05-20): Model
``libs/models/lia_models/calibration.py:189`` declares::

    company_id = Column(String, nullable=True, index=True)  # multi-tenant isolation

But no alembic migration ever added the column to the DB. Schema drift
detected when WSI question generation tried to query
``calibration_weights`` with ``company_id`` filter and failed with::

    UndefinedColumnError: column calibration_weights.company_id does not exist

This blocks Sprint 2 IA Feature Restoration (F6.B6 chain).

Multi-tenant isolation column — must exist for ADR-LGPD canonical
multi-tenancy. Nullable=True por compatibilidade com rows existentes
sem company_id assignment.

Reversible.
"""
from alembic import op
import sqlalchemy as sa


revision = "133_calibration_weights_company_id"
down_revision = "132_job_vacancies_responsibilities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "calibration_weights",
        sa.Column("company_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_calibration_weights_company_id",
        "calibration_weights",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_calibration_weights_company_id",
        table_name="calibration_weights",
    )
    op.drop_column("calibration_weights", "company_id")
