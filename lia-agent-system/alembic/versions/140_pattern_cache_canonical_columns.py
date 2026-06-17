"""pattern_cache: add canonical NOT NULL columns (schema drift P0).

Revision ID: 140_pattern_cache_canonical_columns
Revises: 139_offer_proposals_hybrid_canonical
Create Date: 2026-05-20

Schema drift P0 fix (relatorio /tmp/schema_drift_report.md).

O modelo PatternCache em libs/models/lia_models/intelligence_layer.py declara
5 colunas NOT NULL que NAO existem no DB:

  - pattern_key      VARCHAR(200) NOT NULL  (index=True)
  - pattern_data     JSON         NOT NULL  default {}
  - sample_size      INTEGER      NOT NULL  default 0
  - confidence       FLOAT        NOT NULL  default 0.0
  - calculated_at    TIMESTAMP    NOT NULL  default now()

DB tem 0 rows em pattern_cache (verificado 2026-05-20) — operacao 100% segura,
ADD COLUMN NOT NULL DEFAULT funciona sem backfill.

Indices criados pra bater com o modelo:
  - ix_pattern_cache_pattern_key (single col, index=True no model)
  - ix_pattern_cache_lookup      (company_id, pattern_type, pattern_key — composite)
  - ix_pattern_cache_expiry      (expires_at — composite single-col declarado em __table_args__)

Legacy cols cache_key / cached_data NAO sao tocadas aqui (cleanup separado, podem
ter referencias em codigo). Old shape continua presente, paralela ao novo schema.
"""
import sqlalchemy as sa
from alembic import op


revision = "140_pattern_cache_canonical_columns"
down_revision = "139_offer_proposals_hybrid_canonical"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. pattern_key VARCHAR(200) NOT NULL — index=True no model
    op.add_column(
        "pattern_cache",
        sa.Column("pattern_key", sa.String(200), nullable=False, server_default=""),
    )

    # 2. pattern_data JSON NOT NULL default {} (modelo: default=dict)
    op.add_column(
        "pattern_cache",
        sa.Column("pattern_data", sa.JSON(), nullable=False, server_default="{}"),
    )

    # 3. sample_size INTEGER NOT NULL default 0
    op.add_column(
        "pattern_cache",
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
    )

    # 4. confidence FLOAT NOT NULL default 0.0
    op.add_column(
        "pattern_cache",
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.0"),
    )

    # 5. calculated_at TIMESTAMP NOT NULL default now()
    op.add_column(
        "pattern_cache",
        sa.Column(
            "calculated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Indices que batem com o modelo
    op.create_index(
        "ix_pattern_cache_pattern_key",
        "pattern_cache",
        ["pattern_key"],
    )
    op.create_index(
        "ix_pattern_cache_lookup",
        "pattern_cache",
        ["company_id", "pattern_type", "pattern_key"],
    )
    op.create_index(
        "ix_pattern_cache_expiry",
        "pattern_cache",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_pattern_cache_expiry", table_name="pattern_cache")
    op.drop_index("ix_pattern_cache_lookup", table_name="pattern_cache")
    op.drop_index("ix_pattern_cache_pattern_key", table_name="pattern_cache")
    op.drop_column("pattern_cache", "calculated_at")
    op.drop_column("pattern_cache", "confidence")
    op.drop_column("pattern_cache", "sample_size")
    op.drop_column("pattern_cache", "pattern_data")
    op.drop_column("pattern_cache", "pattern_key")
