"""Reconcile recruitment_campaigns columns with the SQLAlchemy model.

Revision ID: 097_reconcile_recruitment_campaigns_columns
Revises: 096_align_self_scheduling_links_table
Create Date: 2026-04-21

Context
-------
``recruitment_campaigns`` was originally created by migration 064. In several
environments the table was instead created earlier via the
``Base.metadata.create_all`` boot path in ``app/core/database.py:init_db`` —
back when the model had a much narrower schema (``current_stage`` /
``stages_config`` / no ``created_by`` / no per-stage counters). Once those
environments adopted Alembic at head=064+ the existing table was never
reconciled, so the live schema drifted from the model:

    asyncpg.exceptions.UndefinedColumnError:
      column recruitment_campaigns.created_by does not exist

This migration is **idempotent** and reconciles every column the
``RecruitmentCampaign`` model declares in
``libs/models/lia_models/recruitment_campaign.py``. It:

* Adds each missing column with a server_default that backfills existing
  rows in a single statement.
* Promotes ``created_by`` to ``NOT NULL`` after backfilling ``'system'`` for
  any historical rows (none in dev today, but defensive for staging/prod).
* Promotes ``stages``, ``current_stage_index``, and ``stage_history`` to
  ``NOT NULL`` after seeding their defaults.
* Creates the model's three indexes if missing.

Legacy columns ``current_stage`` (varchar) and ``stages_config`` (jsonb) are
left in place — they hold no live data anyone reads, but dropping them is a
separate decision (some `init_db` paths still emit them via reflection-style
boot). A follow-up will remove them once the ``Base.metadata.create_all``
boot path is fully retired.

Down migration is intentionally a **no-op**. The columns this migration
reconciles are *owned by migration 064* — on a canonical lineage they
already exist before 097 runs and 097's upgrade is a no-op. Dropping
them in downgrade would therefore destroy schema that belongs to 096's
state. Reverting 097 simply means "stop trying to reconcile drift";
the columns themselves should remain.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "097_reconcile_recruitment_campaigns_columns"
down_revision = "096_align_self_scheduling_links_table"
branch_labels = None
depends_on = None


_TABLE = "recruitment_campaigns"

_NEW_COLUMNS: list[tuple[str, sa.Column]] = [
    ("created_by", sa.Column("created_by", sa.String(64), nullable=True, server_default="system")),
    ("description", sa.Column("description", sa.Text(), nullable=True)),
    ("stages", sa.Column("stages", JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb"))),
    (
        "current_stage_index",
        sa.Column("current_stage_index", sa.Integer(), nullable=True, server_default="0"),
    ),
    ("total_candidates", sa.Column("total_candidates", sa.Integer(), nullable=True, server_default="0")),
    (
        "candidates_screened",
        sa.Column("candidates_screened", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "candidates_contacted",
        sa.Column("candidates_contacted", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "candidates_interviewed",
        sa.Column("candidates_interviewed", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "candidates_offered",
        sa.Column("candidates_offered", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "candidates_hired",
        sa.Column("candidates_hired", sa.Integer(), nullable=True, server_default="0"),
    ),
    (
        "stage_history",
        sa.Column("stage_history", JSONB(), nullable=True, server_default=sa.text("'[]'::jsonb")),
    ),
]

_NOT_NULL_AFTER_BACKFILL = ["created_by", "stages", "current_stage_index", "stage_history"]

_INDEXES: list[tuple[str, list[str]]] = [
    ("idx_campaign_company", ["company_id"]),
    ("idx_campaign_status", ["status"]),
    ("idx_campaign_job", ["job_id"]),
]


def _existing_columns(inspector: sa.engine.reflection.Inspector) -> set[str]:
    if _TABLE not in inspector.get_table_names():
        return set()
    return {c["name"] for c in inspector.get_columns(_TABLE)}


def _existing_indexes(inspector: sa.engine.reflection.Inspector) -> set[str]:
    if _TABLE not in inspector.get_table_names():
        return set()
    return {ix["name"] for ix in inspector.get_indexes(_TABLE)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _TABLE not in inspector.get_table_names():
        # Nothing to reconcile; migration 064 will create the canonical table.
        return

    existing = _existing_columns(inspector)

    # Add every missing column with a server_default so PostgreSQL backfills
    # historical rows in a single ALTER TABLE statement.
    for name, column in _NEW_COLUMNS:
        if name not in existing:
            op.add_column(_TABLE, column)

    # Belt-and-braces backfill for environments where the column already
    # existed but held NULLs from an older partial migration.
    op.execute(f"UPDATE {_TABLE} SET created_by = 'system' WHERE created_by IS NULL")
    op.execute(f"UPDATE {_TABLE} SET stages = '[]'::jsonb WHERE stages IS NULL")
    op.execute(f"UPDATE {_TABLE} SET current_stage_index = 0 WHERE current_stage_index IS NULL")
    op.execute(f"UPDATE {_TABLE} SET stage_history = '[]'::jsonb WHERE stage_history IS NULL")

    for col in _NOT_NULL_AFTER_BACKFILL:
        op.alter_column(_TABLE, col, nullable=False)

    indexes = _existing_indexes(inspector)
    for ix_name, cols in _INDEXES:
        if ix_name not in indexes:
            op.create_index(ix_name, _TABLE, cols)


def downgrade() -> None:
    # Intentional no-op. See module docstring: every column/index this
    # migration touches is owned by migration 064. Dropping them on
    # downgrade would corrupt the canonical 096 state on environments
    # whose schema was never drifted in the first place.
    return
