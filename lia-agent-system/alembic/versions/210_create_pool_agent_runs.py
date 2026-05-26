"""Sprint 7C Part 1.5a: tabela pool_agent_runs canonical pra histórico de dispatch.

Cada row representa 1 execução de assignment (cron, on_demand, future event_driven).
Orchestrator real (Part 1.5b) escreve aqui. Endpoint GET .../runs lê.

Refs:
- AGENT_STUDIO_SPRINT7_PLAN.md §4 Sprint 7C
- Sprint 7C Part 1 v2 32f15d0a8 (cron infra + dispatch stub)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "210"
down_revision = "209"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pool_agent_runs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "assignment_id",
            UUID(as_uuid=True),
            sa.ForeignKey("pool_agent_assignments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("trigger_source", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dispatch_metadata", JSONB(), nullable=False, server_default="{}"),
        sa.Column("results", JSONB(), nullable=False, server_default="{}"),
        sa.Column("runtime_metrics", JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "trigger_source IN ('cron','on_demand','event_driven')",
            name="chk_par_trigger_source",
        ),
        sa.CheckConstraint(
            "status IN ('queued','running','success','error','timeout','cancelled')",
            name="chk_par_status",
        ),
    )
    op.create_index(
        "idx_pool_agent_runs_assignment",
        "pool_agent_runs",
        ["assignment_id", "created_at"],
    )
    op.create_index(
        "idx_pool_agent_runs_company_status",
        "pool_agent_runs",
        ["company_id", "status"],
    )


def downgrade():
    op.drop_index("idx_pool_agent_runs_company_status", table_name="pool_agent_runs")
    op.drop_index("idx_pool_agent_runs_assignment", table_name="pool_agent_runs")
    op.drop_table("pool_agent_runs")
