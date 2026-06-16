"""Fix schema drift between SQLAlchemy models/code and the database (migration 240).

Revision ID: 240
Revises: 239
Create Date: 2026-06-03

Aligns the database with what the application code expects, eliminating the
runtime errors observed in the backend logs:

1. ``communication_settings.alerts_enabled`` — the canonical model
   (``lia_models.communication_settings.CommunicationSettings``) declares this
   column (P0-W1-06 ghost-setting toggle) but it was never added to the DB, so
   the communication-settings panel returned HTTP 500.

2. ``wsi_sessions.score`` — ``PipelineMonitor._detect_high_score_no_action``
   selects ``ws.score``/filters ``ws.score > 80``; the column was missing,
   logging ``column ws.score does not exist`` on every pipeline scan.

3. ``userrole`` enum — ``app.auth.models.UserRole`` defines ``manager`` and
   ``wedotalent_admin``, but the PG enum only had ``admin/recruiter/viewer/dpo``.
   The daily digest crashed with ``invalid input value for enum userrole:
   "manager"``.

4. ``policy_evaluation_logs`` RLS — migration 125 created the tenant policies
   WITHOUT the canonical ``app_current_company_id() IS NULL`` fail-open escape
   hatch that migration 040 established for system/background writes. The policy
   engine logs evaluations from a non-tenant session (``AsyncSessionLocal``,
   no ``app.company_id`` GUC), so under FORCE ROW LEVEL SECURITY the WITH CHECK
   failed and inserts were rejected. We recreate the 4 policies with the
   fail-open-on-NULL-session predicate (tenant isolation still enforced whenever
   a session HAS set its company context).

Fully idempotent (IF NOT EXISTS / DROP POLICY IF EXISTS), safe on dev and prod
via the existing Alembic flow.
"""
from alembic import op

revision = "240"
down_revision = "239"
branch_labels = None
depends_on = None


# Canonical fail-open-on-NULL-session predicate (mirrors migration 040).
# nullable UUID company_id.
_POLICY_EVAL_PRED = (
    "(app_current_company_id() IS NULL "
    "OR company_id IS NULL "
    "OR (company_id)::text = app_current_company_id())"
)


def upgrade() -> None:
    # 1. communication_settings.alerts_enabled -------------------------------
    op.execute(
        "ALTER TABLE communication_settings "
        "ADD COLUMN IF NOT EXISTS alerts_enabled BOOLEAN NOT NULL DEFAULT TRUE"
    )

    # 2. wsi_sessions.score --------------------------------------------------
    op.execute(
        "ALTER TABLE wsi_sessions "
        "ADD COLUMN IF NOT EXISTS score DOUBLE PRECISION"
    )

    # 3. userrole enum: add missing canonical values -------------------------
    # ADD VALUE IF NOT EXISTS is supported inside a transaction on PG 12+
    # (we never reference the new values within this same migration).
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'manager'")
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'wedotalent_admin'")

    # 4. policy_evaluation_logs RLS: restore fail-open-on-NULL-session -------
    op.execute("ALTER TABLE policy_evaluation_logs ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE policy_evaluation_logs FORCE ROW LEVEL SECURITY;")

    for op_kind in ("select", "insert", "update", "delete"):
        op.execute(
            f"DROP POLICY IF EXISTS policy_evaluation_logs_tenant_{op_kind} "
            "ON policy_evaluation_logs;"
        )

    op.execute(
        "CREATE POLICY policy_evaluation_logs_tenant_select "
        "ON policy_evaluation_logs FOR SELECT "
        f"USING ({_POLICY_EVAL_PRED});"
    )
    op.execute(
        "CREATE POLICY policy_evaluation_logs_tenant_insert "
        "ON policy_evaluation_logs FOR INSERT "
        f"WITH CHECK ({_POLICY_EVAL_PRED});"
    )
    op.execute(
        "CREATE POLICY policy_evaluation_logs_tenant_update "
        "ON policy_evaluation_logs FOR UPDATE "
        f"USING ({_POLICY_EVAL_PRED});"
    )
    op.execute(
        "CREATE POLICY policy_evaluation_logs_tenant_delete "
        "ON policy_evaluation_logs FOR DELETE "
        f"USING ({_POLICY_EVAL_PRED});"
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON policy_evaluation_logs TO lia_app;"
    )


def downgrade() -> None:
    # Restore the migration-125 (strict, no session-NULL escape) policies.
    strict_pred = "((company_id IS NULL) OR ((company_id)::text = app_current_company_id()))"

    for op_kind in ("delete", "update", "insert", "select"):
        op.execute(
            f"DROP POLICY IF EXISTS policy_evaluation_logs_tenant_{op_kind} "
            "ON policy_evaluation_logs;"
        )
    op.execute(
        "CREATE POLICY policy_evaluation_logs_tenant_select "
        "ON policy_evaluation_logs FOR SELECT "
        f"USING ({strict_pred});"
    )
    op.execute(
        "CREATE POLICY policy_evaluation_logs_tenant_insert "
        "ON policy_evaluation_logs FOR INSERT "
        f"WITH CHECK ({strict_pred});"
    )
    op.execute(
        "CREATE POLICY policy_evaluation_logs_tenant_update "
        "ON policy_evaluation_logs FOR UPDATE "
        f"USING ({strict_pred});"
    )
    op.execute(
        "CREATE POLICY policy_evaluation_logs_tenant_delete "
        "ON policy_evaluation_logs FOR DELETE "
        f"USING ({strict_pred});"
    )

    op.execute("ALTER TABLE wsi_sessions DROP COLUMN IF EXISTS score")
    op.execute(
        "ALTER TABLE communication_settings DROP COLUMN IF EXISTS alerts_enabled"
    )
    # NOTE: PostgreSQL cannot drop individual enum values; the added
    # userrole values ('manager', 'wedotalent_admin') are intentionally left
    # in place on downgrade (they are harmless and removing them is unsafe).
