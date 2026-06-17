"""add company_id to activity_feed and agent_activities

Revision ID: 110
Revises: 109
Create Date: 2026-05-02

UC-P1-03: Tenant isolation for ActivityFeed and AgentActivity.
Combined migration for both activity tables.

Backfill strategy:
- activity_feed: actor_id -> users.company_id (best effort, system/lia rows stay NULL)
- agent_activities: related_job_id -> job_vacancies.company_id (orphaned rows stay NULL)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "110"
down_revision = "109"
branch_labels = None
depends_on = None


def upgrade():
    # activity_feed
    op.add_column("activity_feed", sa.Column("company_id", sa.String(255), nullable=True))
    op.create_index("ix_activity_feed_company_id", "activity_feed", ["company_id"])
    op.execute("""
        UPDATE activity_feed af
        SET company_id = u.company_id
        FROM users u
        WHERE af.actor_id = u.id::varchar
        AND af.company_id IS NULL
    """)

    # agent_activities
    op.add_column("agent_activities", sa.Column("company_id", sa.String(255), nullable=True))
    op.create_index("ix_agent_activities_company_id", "agent_activities", ["company_id"])
    op.execute("""
        UPDATE agent_activities aa
        SET company_id = jv.company_id
        FROM job_vacancies jv
        WHERE aa.related_job_id = jv.id::varchar
        AND aa.company_id IS NULL
    """)


def downgrade():
    op.drop_index("ix_agent_activities_company_id", "agent_activities")
    op.drop_column("agent_activities", "company_id")
    op.drop_index("ix_activity_feed_company_id", "activity_feed")
    op.drop_column("activity_feed", "company_id")
