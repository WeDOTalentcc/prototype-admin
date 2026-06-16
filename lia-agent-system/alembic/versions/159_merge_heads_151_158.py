"""merge heads 151 + 158 — consolidate Sprint P.1 deferred + Sprints 2-5 catalogs

Revision ID: 159_merge_heads_151_158
Revises: 151_sprint_p1_deferred_tables_fix, 158_merge_sprints_2_to_5
Create Date: 2026-05-21

Bug: post-Sprint 2-5 parallel work, alembic ended up with 2 heads:
    - 151_sprint_p1_deferred_tables_fix  (Sprint P.1: 3 deferred tables
      from migration 148 placeholder no-op fix)
    - 158_merge_sprints_2_to_5          (Sprints 2-5 catalogs merge:
      154 pipeline_stage_templates + 155 alert_rule_templates +
      156 integration_catalog_entries + 157 webhook_event_types)

FAILED: Could not determine revision id from filename 159_merge_heads_151_158.py. Be sure the 'revision' variable is declared inside the script (please see 'Upgrading from Alembic 0.1 to 0.2' in the documentation). would have refused with "Multiple head revisions
present" error. Sprint 0 consolidation 2026-05-21 (P0.B PII encryption,
P0.C DSR SLA cron, and any future migration touching the same head)
needs single linear lineage. This merge is a no-op DDL — purely
graph-level consolidation.

Closes: handoff §2.2 / sinal de alerta §11 #4.
"""
from typing import Sequence, Union

from alembic import op  # noqa: F401  (kept for tooling convention)
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "159_merge_heads_151_158"
down_revision: Union[str, None] = (
    "151_sprint_p1_deferred_tables_fix",
    "158_merge_sprints_2_to_5",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op — graph-level head merge only.

    The actual DDL of the two heads (sprint P.1 tables + catalogs 154-157)
    is applied by their respective migrations; this revision just records
    them as a single point in the alembic version graph so subsequent
    migrations have a unique parent.
    """
    pass


def downgrade() -> None:
    """No-op — see :func:. Downgrading this revision re-introduces
    the multi-head state; intentional only if a future migration needs to
    branch from one specific head."""
    pass
