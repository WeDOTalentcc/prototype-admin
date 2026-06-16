"""Onda 1 Fase 2 Agent Studio: pool_agent_runs.reasoning_payload JSONB.

Decision tree do agente (estrutura AgentReasoningStep[]) persistida em real-time
pelo TalentPoolReActAgent.process() — consumido pelo Studio Control Room
(DecisionTreeDrawer) via GET /agent-monitoring/executions/{id}/reasoning.

LGPD Art. 9 trail: cada step declara data_fields_accessed (campos do candidato
lidos), permitindo auditoria por execução de qual PII o agente tocou.

Refs:
- ~/.claude/plans/steady-dazzling-shamir.md Onda 1 B1
- libs/agents-core/lia_agents_core/agent_interface.py AgentReasoningStep
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "215"
down_revision = "214"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "pool_agent_runs",
        sa.Column(
            "reasoning_payload",
            JSONB(),
            nullable=True,
            comment=(
                "Onda 1 Fase 2: decision tree do agente "
                "(estrutura AgentReasoningStep[]) — Studio Control Room"
            ),
        ),
    )


def downgrade():
    op.drop_column("pool_agent_runs", "reasoning_payload")
