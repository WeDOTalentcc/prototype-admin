"""T-20: Audit log schema com demographic proxies + fairness decisions.

Revision ID: 144_t20_audit_demographic_proxies
Revises: 139_t02_rls_high_priority
Create Date: 2026-05-20

Reviewer U4 push: criar audit_log schema PROACTIVE com campos demographic proxies
+ fairness decisions ESTRUTURADAS. Previne refactor 3-4 sprints se NYC LL144 /
EU AI Act ativar futuro.

Adiciona à audit_logs:
- demographic_proxies JSONB (inferred only, anonymized, consent-gated)
- fairness_check_result JSONB (L1/L2/L3 outputs)
- variant_used VARCHAR (A/B test variant if applicable)
- applicable_frameworks JSONB (LL144/CO_SB205/EU_AI_ACT/CA_FEHA/LGPD)
- current_rule_compliance BOOLEAN (4/5ths rule pass/fail)
- decision_outcome VARCHAR (approved|rejected|escalated|reviewed_by_human)
- candidate_id_hash VARCHAR(64) (SHA-256 one-way, LGPD-safe)
- audit_metadata JSONB

Compliance frameworks habilitados:
- LGPD Art. 20 (explicabilidade)
- NYC LL144 (bias audit annual, 4/5ths rule, demographic dataset)
- EU AI Act Annex III item 4 (recrutamento high-risk)
- CO SB205 (Colorado AI Act 2026)
- CA FEHA (Fair Employment and Housing Act AI provisions)

ADR-035: docs/specs/ai/ADR-035-audit-log-demographic-proxies.md
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "144_t20_audit_demographic_proxies"
down_revision = "139_t02_rls_high_priority"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add demographic proxies + fairness fields to audit_logs."""
    # ADD COLUMNS (all nullable initial — backfill via decision pipeline)
    op.add_column(
        "audit_logs",
        sa.Column("demographic_proxies", JSONB, nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("fairness_check_result", JSONB, nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("variant_used", sa.String(100), nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("applicable_frameworks", JSONB, nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("current_rule_compliance", sa.Boolean, nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("decision_outcome", sa.String(50), nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("candidate_id_hash", sa.String(64), nullable=True),
    )
    op.add_column(
        "audit_logs",
        sa.Column("audit_metadata", JSONB, nullable=True),
    )

    # Indexes para queries comuns
    op.create_index(
        "ix_audit_logs_frameworks",
        "audit_logs",
        ["applicable_frameworks"],
        postgresql_using="gin",
    )
    op.create_index(
        "ix_audit_logs_decision_outcome",
        "audit_logs",
        ["decision_outcome"],
    )
    op.create_index(
        "ix_audit_logs_candidate_id_hash",
        "audit_logs",
        ["candidate_id_hash"],
    )
    op.create_index(
        "ix_audit_logs_rule_compliance",
        "audit_logs",
        ["current_rule_compliance"],
    )


def downgrade() -> None:
    """Remove T-20 columns + indexes."""
    op.drop_index("ix_audit_logs_rule_compliance", table_name="audit_logs")
    op.drop_index("ix_audit_logs_candidate_id_hash", table_name="audit_logs")
    op.drop_index("ix_audit_logs_decision_outcome", table_name="audit_logs")
    op.drop_index("ix_audit_logs_frameworks", table_name="audit_logs")
    op.drop_column("audit_logs", "audit_metadata")
    op.drop_column("audit_logs", "candidate_id_hash")
    op.drop_column("audit_logs", "decision_outcome")
    op.drop_column("audit_logs", "current_rule_compliance")
    op.drop_column("audit_logs", "applicable_frameworks")
    op.drop_column("audit_logs", "variant_used")
    op.drop_column("audit_logs", "fairness_check_result")
    op.drop_column("audit_logs", "demographic_proxies")
