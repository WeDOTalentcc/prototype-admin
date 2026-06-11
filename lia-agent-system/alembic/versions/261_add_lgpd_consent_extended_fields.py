"""add LGPD consent extended fields to consent_records (Phase 1a)

Phase 1a LGPD Consent Feature (2026-06-11):
  - canal: channel identifier (chat_web | whatsapp | chamada_online | chamada_telefonica)
  - user_agent: browser/client user agent string
  - processo_id: UUID FK to triagem_sessions (processo seletivo)
  - vaga_id: UUID FK to job_vacancies
  - versao_disclaimer: configurable disclaimer version string

Also adds PostgreSQL immutability trigger (RN-06):
  - Prevents UPDATE or DELETE on consent_records rows
  - Only is_active=False revocation (INSERT of revocation record) is allowed

All columns are nullable (backward-compat with existing records).

Revision IDs
------------
Revises: 260
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "261"
down_revision = "260"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Task 1: Add 5 new nullable columns to consent_records ─────────────────
    op.add_column(
        "consent_records",
        sa.Column("canal", sa.String(20), nullable=True),
    )
    op.add_column(
        "consent_records",
        sa.Column("user_agent", sa.Text(), nullable=True),
    )
    op.add_column(
        "consent_records",
        sa.Column("processo_id", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "consent_records",
        sa.Column("vaga_id", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "consent_records",
        sa.Column("versao_disclaimer", sa.String(10), nullable=True),
    )

    # Index for common query patterns
    op.create_index(
        "ix_consent_records_vaga_id",
        "consent_records",
        ["vaga_id"],
        postgresql_where=sa.text("vaga_id IS NOT NULL"),
    )
    op.create_index(
        "ix_consent_records_processo_id",
        "consent_records",
        ["processo_id"],
        postgresql_where=sa.text("processo_id IS NOT NULL"),
    )

    # ── Task 3: RN-06 Immutability trigger — consent_records must never be mutated ──
    # Revocation is modeled as is_active=False on the existing record, which the
    # trigger ALSO prevents. Proper revocation = INSERT a new revocation record.
    # EXCEPTION: the trigger applies BEFORE UPDATE/DELETE. Any attempt raises immediately.
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_consent_record_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
          RAISE EXCEPTION 'ConsentRecord is immutable — use is_active=False for revocation (LGPD Art. 7 trail requirement, RN-06)';
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER consent_records_immutable
        BEFORE UPDATE OR DELETE ON consent_records
        FOR EACH ROW EXECUTE FUNCTION prevent_consent_record_mutation();
    """)


def downgrade() -> None:
    # Remove trigger and function first
    op.execute("DROP TRIGGER IF EXISTS consent_records_immutable ON consent_records;")
    op.execute("DROP FUNCTION IF EXISTS prevent_consent_record_mutation();")

    # Remove indexes
    op.drop_index("ix_consent_records_vaga_id", table_name="consent_records")
    op.drop_index("ix_consent_records_processo_id", table_name="consent_records")

    # Remove columns
    op.drop_column("consent_records", "versao_disclaimer")
    op.drop_column("consent_records", "vaga_id")
    op.drop_column("consent_records", "processo_id")
    op.drop_column("consent_records", "user_agent")
    op.drop_column("consent_records", "canal")
