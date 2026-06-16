"""Task #511 round 3 — converte FK wsi_responses.session_id para ON DELETE RESTRICT.

Revision ID: 094_wsi_responses_fk_restrict
Revises: 093_add_dpo_to_userrole_enum
Create Date: 2026-04-18

Contexto
--------
A migration 092 criou a FK fk_wsi_responses_session com ON DELETE CASCADE,
o que permitiria perda de trilha de auditoria caso uma wsi_session fosse
deletada. Isso conflita com o requisito de "trilha imutável" do EU AI Act
Art. 12 (audit logs de IA de Alto Risco devem sobreviver a operações
ordinárias do sistema). Convertemos para ON DELETE RESTRICT: deletes de
sessão com responses persistidos serão bloqueados, forçando ação explícita
do DPO (purge documentado) antes de remover a sessão.
"""
from __future__ import annotations

from alembic import op


revision = "094_wsi_responses_fk_restrict"
down_revision = "093_add_dpo_to_userrole_enum"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_wsi_responses_session", "wsi_responses", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_wsi_responses_session",
        "wsi_responses",
        "wsi_sessions",
        ["session_id"],
        ["id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_wsi_responses_session", "wsi_responses", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_wsi_responses_session",
        "wsi_responses",
        "wsi_sessions",
        ["session_id"],
        ["id"],
        ondelete="CASCADE",
    )
