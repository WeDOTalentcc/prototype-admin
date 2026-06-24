"""271 — merge all orphaned heads (candidate_embeddings, offer_portal, negotiation, hiring_policy_offer_rules)

Revision ID: 271_merge_all_orphaned_heads
Revises: 268_add_fairness_audit_log_id_to_violations,
         265_candidate_embeddings,
         266_offer_portal_fields,
         269_offer_negotiation_events,
         270_company_hiring_policy_offer_rules
Create Date: 2026-06-13

Merge migration — consolida branches orfas em um unico head antes do Sprint A.
Nenhuma alteracao de schema.
"""
from alembic import op

revision = "271_merge_all_orphaned_heads"
down_revision = (
    "268_add_fairness_audit_log_id_to_violations",
    "265_candidate_embeddings",
    "266_offer_portal_fields",
    "269_offer_negotiation_events",
    "270_company_hiring_policy_offer_rules",
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass  # merge only — no schema changes


def downgrade() -> None:
    pass
