"""W1-006 part 2 · BEFORE UPDATE/DELETE/TRUNCATE triggers em audit_execution_metadata

Revision ID: 180_audit_append_only_triggers
Revises: 179_custom_agent_whatsapp_enabled
Create Date: 2026-05-23

W1-006 part 2 do MASTER_PLAN.md de remediação enterprise.
Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W1-006 part 2).
Tests: tests/integration/test_audit_append_only_triggers.py
Sensor: scripts/check_audit_append_only_triggers.py

Adiciona triggers append-only canonical a `audit_execution_metadata`:
- Function `audit_execution_metadata_block_update()` — raise exception
- Function `audit_execution_metadata_block_delete()` — raise exception
- Trigger BEFORE UPDATE — bloqueia toda modificação row-level
- Trigger BEFORE DELETE — bloqueia toda deleção row-level
- Statement trigger BEFORE TRUNCATE — bloqueia limpeza por table

Pre-audit confirmou ZERO callers UPDATE em audit_execution_metadata
(write path é append-only por design via audit_writer.py). Triggers
não quebram produção, apenas enforçam invariante runtime.

Mitigations:
- Tampering attempt (DBA admin UPDATE) → exception + audit trail Postgres logs
- Accidental DELETE → exception, recovery via backup
- TRUNCATE bypass → statement trigger bloqueia
- Complementar à hash chain SHA-256 (migration 176) que detecta tampering
  via verify_audit_chain.py rerun digest

Escape hatch (emergency): role com `SUPERUSER` pode DROP/ALTER trigger.
Postgres logs registram qualquer ALTER TRIGGER fora do canonical flow.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "180_audit_append_only_triggers"
down_revision = "179_custom_agent_whatsapp_enabled"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Function: block UPDATE
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION audit_execution_metadata_block_update()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_execution_metadata é append-only (W1-006 part 2). '
                'UPDATE bloqueado · use INSERT em audit_log_human_reviews para HITL flow.'
                USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$ LANGUAGE plpgsql;
    """))

    # 2. Function: block DELETE
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION audit_execution_metadata_block_delete()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_execution_metadata é append-only (W1-006 part 2). '
                'DELETE bloqueado · soft-delete via campo nullable se necessário.'
                USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$ LANGUAGE plpgsql;
    """))

    # 3. Function: block TRUNCATE (statement-level)
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION audit_execution_metadata_block_truncate()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'audit_execution_metadata é append-only (W1-006 part 2). '
                'TRUNCATE bloqueado · table cannot be wiped.'
                USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$ LANGUAGE plpgsql;
    """))

    # 4. Attach triggers
    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS audit_execution_metadata_block_update_trigger
        ON audit_execution_metadata
    """))
    op.execute(sa.text("""
        CREATE TRIGGER audit_execution_metadata_block_update_trigger
        BEFORE UPDATE ON audit_execution_metadata
        FOR EACH ROW
        EXECUTE FUNCTION audit_execution_metadata_block_update()
    """))

    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS audit_execution_metadata_block_delete_trigger
        ON audit_execution_metadata
    """))
    op.execute(sa.text("""
        CREATE TRIGGER audit_execution_metadata_block_delete_trigger
        BEFORE DELETE ON audit_execution_metadata
        FOR EACH ROW
        EXECUTE FUNCTION audit_execution_metadata_block_delete()
    """))

    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS audit_execution_metadata_block_truncate_trigger
        ON audit_execution_metadata
    """))
    op.execute(sa.text("""
        CREATE TRIGGER audit_execution_metadata_block_truncate_trigger
        BEFORE TRUNCATE ON audit_execution_metadata
        FOR EACH STATEMENT
        EXECUTE FUNCTION audit_execution_metadata_block_truncate()
    """))


def downgrade():
    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS audit_execution_metadata_block_update_trigger
        ON audit_execution_metadata
    """))
    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS audit_execution_metadata_block_delete_trigger
        ON audit_execution_metadata
    """))
    op.execute(sa.text("""
        DROP TRIGGER IF EXISTS audit_execution_metadata_block_truncate_trigger
        ON audit_execution_metadata
    """))
    op.execute(sa.text("DROP FUNCTION IF EXISTS audit_execution_metadata_block_update()"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS audit_execution_metadata_block_delete()"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS audit_execution_metadata_block_truncate()"))
