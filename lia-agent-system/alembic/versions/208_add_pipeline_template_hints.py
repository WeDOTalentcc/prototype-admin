"""Sprint Pipeline Templates — add hint columns + is_archived to pipeline_templates

Plan: ~/.claude/plans/precisamos-fazer-uma-analise-polished-quill.md.
Decision Paulo 2026-05-26:
  - Cliente Afya precisa templates por área (médicos, liderança, TI).
  - Auto-suggest LIA no wizard chat por department/seniority/job_family.
  - is_archived distinto de is_active (legado soft_delete).

Revision ID: 208
Revises: 207
"""
from alembic import op
import sqlalchemy as sa


revision = "208"
down_revision = "207"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "pipeline_templates",
        sa.Column(
            "department_hint",
            sa.JSON(),
            nullable=True,
            comment="Lista de departamentos onde este template aplica. "
                    "Usado por LIA para auto-suggest no wizard chat. Ex: [\"Saude\", \"TI\"]",
        ),
    )
    op.add_column(
        "pipeline_templates",
        sa.Column(
            "seniority_hint",
            sa.JSON(),
            nullable=True,
            comment="Lista de níveis de senioridade. Ex: [\"pleno\", \"senior\", \"executive\"]",
        ),
    )
    op.add_column(
        "pipeline_templates",
        sa.Column(
            "job_family_hint",
            sa.JSON(),
            nullable=True,
            comment="Lista de famílias de cargo. Ex: [\"medico\", \"lideranca\", \"engenheiro\"]",
        ),
    )
    op.add_column(
        "pipeline_templates",
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
            comment="Distinto de is_active (legado soft_delete). is_archived=true esconde "
                    "do seletor de aplicar template mas mantém em analytics histórico.",
        ),
    )
    op.add_column(
        "pipeline_templates",
        sa.Column(
            "updated_by",
            sa.String(length=255),
            nullable=True,
            comment="User email que fez último update — audit trail canonical.",
        ),
    )
    op.create_index(
        "ix_pipeline_templates_company_active_archived",
        "pipeline_templates",
        ["company_id", "is_active", "is_archived"],
    )


def downgrade():
    op.drop_index("ix_pipeline_templates_company_active_archived", table_name="pipeline_templates")
    op.drop_column("pipeline_templates", "updated_by")
    op.drop_column("pipeline_templates", "is_archived")
    op.drop_column("pipeline_templates", "job_family_hint")
    op.drop_column("pipeline_templates", "seniority_hint")
    op.drop_column("pipeline_templates", "department_hint")
