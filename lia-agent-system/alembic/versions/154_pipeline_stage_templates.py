"""Create pipeline_stage_templates + seed master canonical (15 items).

Audit 2026-05-20 Sessao I Step 5 / Sprint 2 (catalogos dinamicos):
substitui catalogo hardcoded DEFAULT_STAGES (espalhado em
plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx +
create-job-with-candidates-modal.tsx + add-to-job-modal.tsx) por
modelo per-tenant canonical no DB.

Schema canonical:
- is_master_template=True: items curados pela WeDOTalent (NULL company_id)
- is_master_template=False: customs por company (company_id NOT NULL)
- parent_template_id: NOT NULL quando custom e copia de master (canonical A1)
- soft-delete via deleted_at

Revision ID: 154_pipeline_stage_templates
Revises: 153_eligibility_question_templates
Create Date: 2026-05-21

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "154_pipeline_stage_templates"
down_revision: Union[str, None] = "153_eligibility_question_templates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# MASTER_ITEMS canonical — espelha DEFAULT_STAGES de
# plataforma-lia/src/components/settings/RecruitmentJourneyConfig.tsx (15 items)
# Schema canonical da data JSONB:
#   label (display_name pt-BR/EN canonical fallback)
#   key (snake_case canonical, igual ao "name" da DEFAULT_STAGES)
#   color (CSS var token)
#   icon (lucide name)
#   order (1..15)
#   is_default_in_pipeline (true = aparece por padrao no novo pipeline)
#   action_behavior (intake|screening|passive|scheduling|evaluation|verification|offer|conclusion_*)
#   default_channel (email|email_whatsapp)
#   stage_category (system|custom|catalog)
#   type (system|custom|default)  # compat antigo RecruitmentStage
#   sla_hours (0 quando indefinido)
#   metadata (extra)
MASTER_ITEMS = [
    {"label": "Sourcing", "key": "sourcing", "color": "var(--lia-text-secondary)", "icon": "search", "order": 1, "is_default_in_pipeline": True, "action_behavior": "intake", "default_channel": "email", "stage_category": "system", "type": "system", "sla_hours": 0},
    {"label": "Screening", "key": "screening", "color": "var(--wedo-purple)", "icon": "file-text", "order": 2, "is_default_in_pipeline": True, "action_behavior": "screening", "default_channel": "email", "stage_category": "system", "type": "system", "sla_hours": 0},
    {"label": "Long List", "key": "long_list", "color": "var(--lia-border-subtle)", "icon": "list", "order": 3, "is_default_in_pipeline": True, "action_behavior": "passive", "default_channel": "email", "stage_category": "custom", "type": "custom", "sla_hours": 72},
    {"label": "Short List", "key": "short_list", "color": "var(--lia-border-subtle)", "icon": "list-checks", "order": 4, "is_default_in_pipeline": True, "action_behavior": "passive", "default_channel": "email", "stage_category": "custom", "type": "custom", "sla_hours": 72},
    {"label": "HR Interview", "key": "interview_hr", "color": "var(--lia-text-tertiary)", "icon": "users", "order": 5, "is_default_in_pipeline": True, "action_behavior": "scheduling", "default_channel": "email_whatsapp", "stage_category": "system", "type": "system", "sla_hours": 0},
    {"label": "Technical Test", "key": "technical_test", "color": "var(--lia-border-subtle)", "icon": "code-2", "order": 6, "is_default_in_pipeline": True, "action_behavior": "evaluation", "default_channel": "email", "stage_category": "custom", "type": "custom", "sla_hours": 120},
    {"label": "English Test", "key": "english_test", "color": "var(--lia-border-subtle)", "icon": "languages", "order": 7, "is_default_in_pipeline": False, "action_behavior": "evaluation", "default_channel": "email", "stage_category": "custom", "type": "custom", "sla_hours": 120},
    {"label": "Technical Interview", "key": "interview_technical", "color": "var(--status-warning)", "icon": "code", "order": 8, "is_default_in_pipeline": True, "action_behavior": "scheduling", "default_channel": "email_whatsapp", "stage_category": "custom", "type": "custom", "sla_hours": 120},
    {"label": "Manager Interview", "key": "interview_manager", "color": "var(--status-success)", "icon": "briefcase", "order": 9, "is_default_in_pipeline": True, "action_behavior": "scheduling", "default_channel": "email_whatsapp", "stage_category": "custom", "type": "custom", "sla_hours": 120},
    {"label": "Final Interview", "key": "interview_final", "color": "var(--lia-border-subtle)", "icon": "award", "order": 10, "is_default_in_pipeline": False, "action_behavior": "scheduling", "default_channel": "email_whatsapp", "stage_category": "custom", "type": "custom", "sla_hours": 120},
    {"label": "References", "key": "references", "color": "var(--lia-bg-tertiary)", "icon": "phone", "order": 11, "is_default_in_pipeline": False, "action_behavior": "verification", "default_channel": "email", "stage_category": "custom", "type": "custom", "sla_hours": 72},
    {"label": "Offer", "key": "offer", "color": "var(--lia-text-secondary)", "icon": "file-check", "order": 12, "is_default_in_pipeline": True, "action_behavior": "offer", "default_channel": "email", "stage_category": "catalog", "type": "default", "sla_hours": 72},
    {"label": "Offer Declined", "key": "offer_declined", "color": "var(--status-warning)", "icon": "x", "order": 13, "is_default_in_pipeline": False, "action_behavior": "conclusion_declined", "default_channel": "email", "stage_category": "catalog", "type": "default", "sla_hours": 0},
    {"label": "Hired", "key": "hired", "color": "var(--status-success)", "icon": "check-circle", "order": 14, "is_default_in_pipeline": True, "action_behavior": "conclusion_hired", "default_channel": "email", "stage_category": "system", "type": "system", "sla_hours": 0},
    {"label": "Rejected", "key": "rejected", "color": "var(--status-error)", "icon": "x-circle", "order": 15, "is_default_in_pipeline": True, "action_behavior": "conclusion_rejected", "default_channel": "email", "stage_category": "system", "type": "system", "sla_hours": 0},
]


def upgrade() -> None:
    """Create table + seed 15 master items canonical."""
    op.create_table(
        "pipeline_stage_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(255), nullable=True, index=True),
        sa.Column("is_master_template", sa.Boolean, nullable=False, default=False, index=True),
        sa.Column(
            "parent_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pipeline_stage_templates.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("data", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.String(255), nullable=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True, index=True),
    )

    # Composite indexes canonical
    op.create_index(
        "ix_pipeline_stage_templates_company_master",
        "pipeline_stage_templates",
        ["company_id", "is_master_template"],
    )
    op.create_index(
        "ix_pipeline_stage_templates_active",
        "pipeline_stage_templates",
        ["deleted_at", "is_master_template"],
    )

    # Seed master canonical (15 items espelhando DEFAULT_STAGES canonical)
    import uuid
    import json as _json

    connection = op.get_bind()
    insert_sql = sa.text(
        """
        INSERT INTO pipeline_stage_templates
        (id, company_id, is_master_template, parent_template_id, data, created_at, updated_at, created_by, deleted_at)
        VALUES (:id, NULL, TRUE, NULL, CAST(:data AS JSONB), NOW(), NOW(), 'system-seed-2026-05-21', NULL)
        """
    )
    for item in MASTER_ITEMS:
        new_uuid = str(uuid.uuid4())
        connection.execute(
            insert_sql,
            {"id": new_uuid, "data": _json.dumps(item, ensure_ascii=False)},
        )


def downgrade() -> None:
    """Drop table — DATA LOSS de customs canonical."""
    op.drop_index("ix_pipeline_stage_templates_active", table_name="pipeline_stage_templates")
    op.drop_index("ix_pipeline_stage_templates_company_master", table_name="pipeline_stage_templates")
    op.drop_table("pipeline_stage_templates")
