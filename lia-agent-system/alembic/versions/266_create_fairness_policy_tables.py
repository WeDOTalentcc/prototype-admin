"""266 - create fairness_policy_rules, fairness_policy_activations, fairness_policy_violations tables

Revision ID: 266_fairness_policies
Revises: 264_add_vacancy_alert_configs
Create Date: 2026-06-13

Compliance: LGPD Art.6/11 + EU AI Act Annex III item 4
ADR ref: ADR-001 (storage) + sec9 Definicoes Arquiteturais v0.4.1
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, UUID

revision = "266_fairness_policies"
down_revision = "264_add_vacancy_alert_configs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # fairness_policy_rules
    # ------------------------------------------------------------------
    op.create_table(
        "fairness_policy_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=True),
        sa.Column("scope", sa.String(30), nullable=False),
        sa.Column("domain", sa.String(50), nullable=True),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("body_json", JSON, nullable=False, server_default="{}"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_fairness_rules_company_id", "fairness_policy_rules", ["company_id"])
    op.create_index("ix_fairness_rules_scope_domain", "fairness_policy_rules", ["scope", "domain"])
    op.create_index("ix_fairness_rules_company_id_status", "fairness_policy_rules", ["company_id", "status"])

    # ------------------------------------------------------------------
    # fairness_policy_activations
    # ------------------------------------------------------------------
    op.create_table(
        "fairness_policy_activations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=True),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("rule_id", UUID(as_uuid=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("activated_by", UUID(as_uuid=True), nullable=True),
        sa.Column("deactivated_at", sa.DateTime(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default="true"),
        sa.UniqueConstraint("company_id", "domain", "rule_id", name="uq_activation_company_domain_rule"),
    )
    op.create_index("ix_activation_company_id", "fairness_policy_activations", ["company_id"])
    op.create_index("ix_activation_rule_id", "fairness_policy_activations", ["rule_id"])
    op.create_index(
        "ix_activation_company_domain_current",
        "fairness_policy_activations",
        ["company_id", "domain", "is_current"],
    )
    op.create_foreign_key(
        "fk_activation_rule_id",
        "fairness_policy_activations",
        "fairness_policy_rules",
        ["rule_id"],
        ["id"],
    )

    # ------------------------------------------------------------------
    # fairness_policy_violations
    # ------------------------------------------------------------------
    op.create_table(
        "fairness_policy_violations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("rule_id", UUID(as_uuid=True), nullable=True),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("violation_type", sa.String(80), nullable=False),
        sa.Column("input_snapshot_hash", sa.String(64), nullable=True),
        sa.Column("decision_context", JSON, nullable=True),
        sa.Column("was_blocked", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("detected_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("correlation_id", sa.String(80), nullable=True),
    )
    op.create_index("ix_violations_company_id", "fairness_policy_violations", ["company_id"])
    op.create_index("ix_violations_rule_id", "fairness_policy_violations", ["rule_id"])
    op.create_index("ix_violations_correlation_id", "fairness_policy_violations", ["correlation_id"])
    op.create_index(
        "ix_violations_company_domain_detected",
        "fairness_policy_violations",
        ["company_id", "domain", "detected_at"],
    )
    op.create_foreign_key(
        "fk_violation_rule_id",
        "fairness_policy_violations",
        "fairness_policy_rules",
        ["rule_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_table("fairness_policy_violations")
    op.drop_table("fairness_policy_activations")
    op.drop_table("fairness_policy_rules")
