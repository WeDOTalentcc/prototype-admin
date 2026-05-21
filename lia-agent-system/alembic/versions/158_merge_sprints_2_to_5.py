"""merge sprints 2-5 paralelos (pipeline_stages + alert_rules + integrations + webhook_events)

Audit 2026-05-20 Sprints 2/3/4/5 executados em paralelo por 4 agentes
(branches lógicas — todos com down_revision=153_eligibility_question_templates).
Esta migration une os 4 heads canonical em um único head canonical.

Revision ID: 158_merge_sprints_2_to_5
Revises: 154_pipeline_stage_templates, 155_alert_rule_templates, 156_integration_catalog_entries, 157_webhook_event_types
Create Date: 2026-05-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "158_merge_sprints_2_to_5"
down_revision: Union[str, None] = (
    "154_pipeline_stage_templates",
    "155_alert_rule_templates",
    "156_integration_catalog_entries",
    "157_webhook_event_types",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge canonical — no schema changes."""
    pass


def downgrade() -> None:
    """Merge canonical — no schema changes."""
    pass
