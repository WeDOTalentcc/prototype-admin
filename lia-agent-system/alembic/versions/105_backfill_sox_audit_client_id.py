"""backfill sox_audit_log client_id null and empty to system sentinel

Revision ID: aefc81463fac
Revises: 104
Create Date: 2026-05-02

UC-P0-06: SOXAuditLog.client_id nullable=True prevented RLS enforcement.
Step 1/2: Backfill NULL and empty-string values to 'system' sentinel.
Step 2/2 (next migration): Add NOT NULL constraint.

FairnessGuard previously wrote company_id or "" -> stored empty string "".
Both NULL and "" are normalized to "system" (background/system operations).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "aefc81463fac"
down_revision = "104"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Backfill NULL and empty-string client_id rows to 'system' sentinel.
    # Safe to run on live data: UPDATE with indexed WHERE is lock-minimal.
    op.execute(
        "UPDATE sox_audit_logs "
        "SET client_id = 'system' "
        "WHERE client_id IS NULL OR client_id = ''"
    )


def downgrade() -> None:
    # Cannot reverse -- we would need to know which rows were originally NULL
    # vs empty string vs genuine 'system' entries. Leave as-is; rollback of
    # step 2 (migration 106) will re-allow NULLs if needed.
    pass
