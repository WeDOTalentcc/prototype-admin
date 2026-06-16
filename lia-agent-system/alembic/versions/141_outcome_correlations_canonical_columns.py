"""Outcome correlations: add canonical columns (Sprint F.4 schema drift P0).

Revision ID: 141_outcome_correlations_canonical_columns
Revises: 140_pattern_cache_canonical_columns
Create Date: 2026-05-20

Schema drift fix for ``outcome_correlations``:

Canonical model (libs/models/lia_models/intelligence_layer.py:203
OutcomeCorrelation) declares 9 columns that did not exist in the DB:

  NOT NULL canonical cols (4 P0):
    1. ``factor`` VARCHAR(100) NOT NULL (indexed)
    2. ``outcome_metric`` VARCHAR(100) NOT NULL (indexed)
    3. ``correlation`` FLOAT NOT NULL
    4. ``sample_size`` INTEGER NOT NULL DEFAULT 0
       (DB já tem coluna sample_size nullable; só apertar NOT NULL + default)

  Nullable canonical cols (5):
    5. ``role_pattern`` VARCHAR(200) NULL
    6. ``seniority`` VARCHAR(50) NULL
    7. ``significance`` FLOAT NULL
    8. ``recommendation`` TEXT NULL
    9. ``factor_values`` JSON (default {})
   10. ``outcome_values`` JSON (default {})

  Composite index ``ix_correlation_lookup`` on (company_id, factor, outcome_metric).

DB legacy columns (``factor_field``, ``outcome_type``, ``correlation_coefficient``,
``p_value``, ``is_significant``, ``insight_text``) are NOT touched here — keep
for backwards compatibility until a follow-up cleanup migration. Sensor will
still flag them in the "extra DB cols" section.

DB tem 0 rows em outcome_correlations — operacao 100% segura, server_default
em NOT NULL cols garante zero falha mesmo se houver rows.
"""
import sqlalchemy as sa
from alembic import op


revision = "141_outcome_correlations_canonical_columns"
down_revision = "140_pattern_cache_canonical_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- NOT NULL canonical cols (P0) ---
    # sample_size já existe como nullable; só apertar NOT NULL com default.
    op.alter_column(
        "outcome_correlations",
        "sample_size",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="0",
    )

    op.add_column(
        "outcome_correlations",
        sa.Column("factor", sa.String(100), nullable=False, server_default=""),
    )
    op.add_column(
        "outcome_correlations",
        sa.Column("outcome_metric", sa.String(100), nullable=False, server_default=""),
    )
    op.add_column(
        "outcome_correlations",
        sa.Column("correlation", sa.Float(), nullable=False, server_default="0"),
    )

    # --- Nullable canonical cols ---
    op.add_column(
        "outcome_correlations",
        sa.Column("role_pattern", sa.String(200), nullable=True),
    )
    op.add_column(
        "outcome_correlations",
        sa.Column("seniority", sa.String(50), nullable=True),
    )
    op.add_column(
        "outcome_correlations",
        sa.Column("significance", sa.Float(), nullable=True),
    )
    op.add_column(
        "outcome_correlations",
        sa.Column("recommendation", sa.Text(), nullable=True),
    )
    op.add_column(
        "outcome_correlations",
        sa.Column("factor_values", sa.JSON(), nullable=True, server_default="{}"),
    )
    op.add_column(
        "outcome_correlations",
        sa.Column("outcome_values", sa.JSON(), nullable=True, server_default="{}"),
    )

    # --- Indexes (model declares: factor index, outcome_metric index,
    #     composite ix_correlation_lookup) ---
    op.create_index(
        "ix_outcome_correlations_factor",
        "outcome_correlations",
        ["factor"],
    )
    op.create_index(
        "ix_outcome_correlations_outcome_metric",
        "outcome_correlations",
        ["outcome_metric"],
    )
    op.create_index(
        "ix_correlation_lookup",
        "outcome_correlations",
        ["company_id", "factor", "outcome_metric"],
    )


def downgrade() -> None:
    op.drop_index("ix_correlation_lookup", table_name="outcome_correlations")
    op.drop_index("ix_outcome_correlations_outcome_metric", table_name="outcome_correlations")
    op.drop_index("ix_outcome_correlations_factor", table_name="outcome_correlations")
    op.drop_column("outcome_correlations", "outcome_values")
    op.drop_column("outcome_correlations", "factor_values")
    op.drop_column("outcome_correlations", "recommendation")
    op.drop_column("outcome_correlations", "significance")
    op.drop_column("outcome_correlations", "seniority")
    op.drop_column("outcome_correlations", "role_pattern")
    op.drop_column("outcome_correlations", "correlation")
    op.drop_column("outcome_correlations", "outcome_metric")
    op.drop_column("outcome_correlations", "factor")
    op.alter_column(
        "outcome_correlations",
        "sample_size",
        existing_type=sa.Integer(),
        nullable=True,
        server_default=None,
    )
