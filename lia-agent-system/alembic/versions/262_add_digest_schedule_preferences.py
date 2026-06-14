"""add digest_schedule_preferences table (Fatia 2 — Decisão 3 per-user frequency override)

Fatia 2 (2026-06-12): tabela canonical para frequência de digest por usuário.

Modelo:
- user_id IS NULL     → padrão da empresa (company default)
- user_id = UUID      → override pessoal do recrutador

Precedência no briefing_dispatch:
  1. digest_schedule_preferences WHERE user_id = current_user
  2. digest_schedule_preferences WHERE user_id IS NULL (company default)
  3. HiringPolicy.communication_rules.briefing_frequency
  4. AlertConfig.briefing_frequency (legacy, sunset 2026-08-22)
  5. DEFAULT_BRIEFING_FREQUENCY = "weekly"

Unique constraints via partial indexes (NULL-safe):
  - Um padrão por empresa: UNIQUE(company_id) WHERE user_id IS NULL
  - Um override por usuário: UNIQUE(company_id, user_id) WHERE user_id IS NOT NULL

Revision IDs
------------
Revises: 261
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "262"
down_revision = "261"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(bind)
    if "digest_schedule_preferences" in inspector.get_table_names():
        return  # table already exists (applied outside alembic)
    op.create_table(
        "digest_schedule_preferences",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),  # NULL = empresa default
        sa.Column(
            "frequency",
            sa.String(20),
            nullable=False,
            server_default="weekly",
        ),
        sa.Column("preferred_time_morning", sa.String(5), nullable=True),   # "HH:MM" UTC
        sa.Column("preferred_time_afternoon", sa.String(5), nullable=True),  # para twice_daily
        sa.Column("quiet_hours_start", sa.Integer(), nullable=True),         # 0-23
        sa.Column("quiet_hours_end", sa.Integer(), nullable=True),           # 0-23
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_digest_schedule_preferences_company_id",
        "digest_schedule_preferences",
        ["company_id"],
    )
    op.create_index(
        "ix_digest_schedule_preferences_user_id",
        "digest_schedule_preferences",
        ["user_id"],
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )
    # Partial unique: one company default per company (user_id IS NULL)
    op.create_index(
        "uq_digest_schedule_company_default",
        "digest_schedule_preferences",
        ["company_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NULL"),
    )
    # Partial unique: one per-user override per (company, user)
    op.create_index(
        "uq_digest_schedule_user_override",
        "digest_schedule_preferences",
        ["company_id", "user_id"],
        unique=True,
        postgresql_where=sa.text("user_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_digest_schedule_user_override", "digest_schedule_preferences")
    op.drop_index("uq_digest_schedule_company_default", "digest_schedule_preferences")
    op.drop_index("ix_digest_schedule_preferences_user_id", "digest_schedule_preferences")
    op.drop_index("ix_digest_schedule_preferences_company_id", "digest_schedule_preferences")
    op.drop_table("digest_schedule_preferences")
