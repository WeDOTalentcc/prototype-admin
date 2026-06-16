"""Sync TriggerType: remap orphaned wsi_score_calculated row + Python enum expansion.

automation tables use VARCHAR (not PG ENUM) -- no ALTER TYPE needed.
communication_automations: 0 rows, no-op.
stage_automation_rules: 1 row with wsi_score_calculated -> remap to screening_completed
(WSI score calculation IS the screening completion event -- semantically equivalent).
"""
from alembic import op
import sqlalchemy as sa

revision = "213_sync_trigger_types_canonical"
down_revision = "212_fix_automation_numeric_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(sa.text("UPDATE stage_automation_rules SET trigger_type = 'screening_completed' WHERE trigger_type = 'wsi_score_calculated'"))


def downgrade() -> None:
    op.execute(sa.text("UPDATE stage_automation_rules SET trigger_type = 'wsi_score_calculated' WHERE trigger_type = 'screening_completed' AND (name ILIKE '%wsi%' OR name ILIKE '%score%')"))
