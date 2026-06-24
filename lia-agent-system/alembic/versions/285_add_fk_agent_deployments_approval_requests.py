"""Add FK constraints: agent_deployments and agent_approval_requests -> custom_agents.

Revision ID: 285_add_fk_agent_deployments_approval_requests
Revises: 284_add_name_normalized_candidates
Create Date: 2026-06-14

GAP-4 (auditoria 2026-06-14): agent_deployments.agent_id e
agent_approval_requests.agent_id nao tinham FK para custom_agents.id.
Joins eram manuais, cascade deletes nao funcionavam no ORM.

Esta migration adiciona:
  - FK agent_deployments.agent_id -> custom_agents.id ON DELETE CASCADE
  - FK agent_approval_requests.agent_id -> custom_agents.id ON DELETE CASCADE

ON DELETE CASCADE: deletar um custom_agent remove automaticamente seus deployments
e approval requests associados, evitando registros orfaos.
"""

revision = "285_add_fk_agent_deployments_approval_requests"
down_revision = "284_add_name_normalized_candidates"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # agent_deployments.agent_id -> custom_agents.id
    op.create_foreign_key(
        "fk_agent_deployments_agent_id",
        "agent_deployments",
        "custom_agents",
        ["agent_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # agent_approval_requests.agent_id -> custom_agents.id
    op.create_foreign_key(
        "fk_agent_approval_requests_agent_id",
        "agent_approval_requests",
        "custom_agents",
        ["agent_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_agent_approval_requests_agent_id", "agent_approval_requests", type_="foreignkey")
    op.drop_constraint("fk_agent_deployments_agent_id", "agent_deployments", type_="foreignkey")
