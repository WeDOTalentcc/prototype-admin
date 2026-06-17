"""create data_incidents table for LGPD Art.48 incident response

Revision ID: a3f91c2e8b4d
Revises: 72bb11ddbbaa
Create Date: 2026-05-02

UC-P0-11: IncidentResponseService for LGPD Art.48 compliance.
Registers data security incidents + admin alert workflow.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "a3f91c2e8b4d"
down_revision = "72bb11ddbbaa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "data_incidents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("company_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "severity",
            sa.Enum("low", "medium", "high", "critical", name="incidentseverity"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "investigating",
                "contained",
                "resolved",
                "reported_anpd",
                name="incidentstatus",
            ),
            nullable=False,
            server_default="open",
        ),
        sa.Column("affected_data_categories", sa.Text(), nullable=True),
        sa.Column("affected_users_count", sa.String(50), nullable=True),
        sa.Column("incident_detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("admin_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("anpd_reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reported_by", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_incidents_company_id", "data_incidents", ["company_id"])
    op.create_index("ix_data_incidents_status", "data_incidents", ["status"])


def downgrade() -> None:
    op.drop_index("ix_data_incidents_status", "data_incidents")
    op.drop_index("ix_data_incidents_company_id", "data_incidents")
    op.drop_table("data_incidents")
    op.execute("DROP TYPE IF EXISTS incidentseverity")
    op.execute("DROP TYPE IF EXISTS incidentstatus")
