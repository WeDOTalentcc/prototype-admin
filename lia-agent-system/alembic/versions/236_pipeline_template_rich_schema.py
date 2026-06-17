"""Migration 236 -- PipelineTemplate rico: saturation_config + stages enriquecidos.

Revision ID: 236
Revises: 235
Create Date: 2026-06-01
"""
revision = "236"
down_revision = "235"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def upgrade() -> None:
    op.add_column(
        "pipeline_templates",
        sa.Column("saturation_config", JSONB, nullable=True, server_default=None),
    )
    op.execute("""
        UPDATE pipeline_templates
        SET stages = (
            SELECT jsonb_agg(
                s ||
                jsonb_build_object(
                    'display_name', COALESCE(s->>'display_name', s->>'name'),
                    'stage_category', COALESCE(s->>'stage_category', 'custom'),
                    'action_behavior', COALESCE(s->>'action_behavior', 'manual'),
                    'default_channel', COALESCE(s->>'default_channel', 'email'),
                    'sla_hours', CASE
                                   WHEN s->>'sla_hours' IS NOT NULL THEN (s->>'sla_hours')::int
                                   WHEN s->>'sla_days'  IS NOT NULL THEN ((s->>'sla_days')::int * 24)
                                   ELSE 72
                                 END,
                    'is_initial', false,
                    'is_final', false,
                    'is_rejection', false,
                    'is_hired', false,
                    'description', COALESCE(s->>'description', s->>'instructions', ''),
                    'sub_statuses', COALESCE(s->'sub_statuses', '[]'::jsonb)
                )
            )
            FROM jsonb_array_elements(stages::jsonb) AS s
        )
        WHERE stages IS NOT NULL
          AND stages != 'null'::json
          AND stages::text != '[]'
    """)


def downgrade() -> None:
    op.drop_column("pipeline_templates", "saturation_config")
