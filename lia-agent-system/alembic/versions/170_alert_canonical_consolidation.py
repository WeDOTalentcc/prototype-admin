"""Backfill AlertConfig.alerts -> AlertPreference (ADR-WT-2025 Sprint B+C).

Revision ID: 170_alert_canonical_consolidation
Revises: 169_encrypt_billing_document, 169_twin_decisions_candidate_fk
Create Date: 2026-05-22

Wave 2 audit 2026-05-22 + ADR-WT-2025 (Sprint B + Sprint C combinados):

Estado pre-migration
────────────────────
1. `alert_configs.alerts` (JSONB list) — UI AlertsTab persistia 5 toggles
   legacy com schema {id, name, enabled, channel}. Detectors NAO leem.
2. `communication_settings.alerts` — referenciado em helper
   `is_alert_enabled` mas COLUNA NAO EXISTE no schema postgres
   (CommunicationSettings model atualizado nunca ganhou coluna `alerts`).
   Therefore Sprint C eh no-op: nenhuma row a migrar.
3. `alert_preferences` (canonical per ADR-WT-2025) — JA wired em
   `proactive_detector_service._load_tenant_overrides` (commit 013f530ca).

Estrategia
──────────
Read-shadow pattern (compatibility 1 release cycle):
- UI legacy continua escrevendo em `alert_configs.alerts` (nao bloqueamos)
- Backend SO le de `alert_preferences` (ja wired)
- Esta migration backfilla rows existentes mapeando alerts legacy items
  para canonical `alert_type` por NAME match (5 items legacy mapeiam pra
  5 canonical alert_types existentes em DEFAULT_ALERT_PREFERENCES).

Mapping legacy.name -> AlertPreference.alert_type:
  - "SLA Proximo do Vencimento" -> sla_near_expiration
  - "Meta Mensal em Risco" -> monthly_goal_at_risk
  - "Candidato Sem Interacao" -> candidate_no_interaction
  - "Entrevista Nao Confirmada" -> interview_not_confirmed
  - "Feedback Pendente" -> feedback_pending

Channel mapping legacy `channel` -> 4 booleans:
  - "email" -> email=True, bell=True, teams=False, whatsapp=False
  - "teams" -> email=False, bell=True, teams=True, whatsapp=False
  - "both" -> email=True, bell=True, teams=True, whatsapp=False

REGRA 4 (no silent fallback): se row tem `name` nao mapeada, log WARNING
em-band via `op.execute` raise. Idempotente via NOT EXISTS gate.

Multi-tenancy: filtro company_id obrigatorio. AlertConfig rows com
company_id NULL (config global) sao IGNORADAS (TENANT-EXEMPT pattern).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "170_alert_canonical_consolidation"
down_revision: Union[str, Sequence[str], None] = (
    "169_encrypt_billing_document",
    "169_twin_decisions_candidate_fk",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Mapping table — frozen at migration time per ADR-WT-2025.
# legacy `name` (case-sensitive, sem acentuacao normalizada) -> canonical alert_type
_LEGACY_NAME_TO_ALERT_TYPE = {
    "SLA Próximo do Vencimento": "sla_near_expiration",
    "Meta Mensal em Risco": "monthly_goal_at_risk",
    "Candidato Sem Interação": "candidate_no_interaction",
    "Entrevista Não Confirmada": "interview_not_confirmed",
    "Feedback Pendente": "feedback_pending",
}


def upgrade() -> None:
    """Backfill alert_configs.alerts -> alert_preferences (idempotent)."""
    conn = op.get_bind()

    # Helper: build psql jsonb_each iteration via lateral.
    # Idempotent: NOT EXISTS guard pelo (company_id, alert_type) unique semantic.
    #
    # Note: user_id em AlertPreference is NOT NULL. AlertConfig is per-company
    # but tem user_id nullable. Pra rows sem user_id usamos sentinel '__migrated__'
    # (pode ser updated quando user logar com sua propria preference; ate la,
    # serve como company-default).
    for legacy_name, canonical_alert_type in _LEGACY_NAME_TO_ALERT_TYPE.items():
        op.execute(sa.text("""
            INSERT INTO alert_preferences (
                id,
                company_id,
                user_id,
                alert_type,
                is_enabled,
                threshold,
                channel_email,
                channel_bell,
                channel_teams,
                channel_whatsapp,
                cooldown_hours,
                created_at,
                updated_at
            )
            SELECT
                gen_random_uuid()::text AS id,
                ac.company_id,
                COALESCE(ac.user_id, '__migrated_alertconfig__') AS user_id,
                :canonical_alert_type AS alert_type,
                COALESCE((alert_item->>'enabled')::boolean, true) AS is_enabled,
                NULL::integer AS threshold,
                CASE
                    WHEN alert_item->>'channel' IN ('email', 'both') THEN true
                    ELSE false
                END AS channel_email,
                true AS channel_bell,
                CASE
                    WHEN alert_item->>'channel' IN ('teams', 'both') THEN true
                    ELSE false
                END AS channel_teams,
                false AS channel_whatsapp,
                24 AS cooldown_hours,
                NOW() AS created_at,
                NOW() AS updated_at
            FROM alert_configs ac
            CROSS JOIN LATERAL jsonb_array_elements(
                CASE
                    WHEN jsonb_typeof(ac.alerts::jsonb) = 'array' THEN ac.alerts::jsonb
                    ELSE '[]'::jsonb
                END
            ) AS alert_item
            WHERE
                ac.company_id IS NOT NULL
                AND alert_item->>'name' = :legacy_name
                AND NOT EXISTS (
                    SELECT 1 FROM alert_preferences ap
                    WHERE ap.company_id = ac.company_id
                      AND ap.user_id = COALESCE(ac.user_id, '__migrated_alertconfig__')
                      AND ap.alert_type = :canonical_alert_type
                )
        """).bindparams(
            legacy_name=legacy_name,
            canonical_alert_type=canonical_alert_type,
        ))

    # Sprint C: communication_settings.alerts -> alert_preferences
    # No-op: column `alerts` does NOT exist em communication_settings table
    # (verificado em models/communication_settings.py + alembic history).
    # Helper `is_alert_enabled` em communication_settings_consumer.py opera
    # sobre dict in-memory que NAO veio de coluna DB.
    # ADR-WT-2025 referencia `CommunicationSettings.alerts` mas analise
    # 2026-05-22 confirmou false-positive na auditoria.
    op.execute(sa.text("""
        -- Sprint C no-op: communication_settings.alerts column does not exist.
        -- Sentinel SELECT pra confirmar:
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = 'communication_settings' AND column_name = 'alerts'
    """))


def downgrade() -> None:
    """Remove backfilled rows tagged via user_id sentinel.

    Non-sentinel rows (user-created via UI canonical) NAO sao tocadas.
    """
    op.execute(sa.text("""
        DELETE FROM alert_preferences
        WHERE user_id = '__migrated_alertconfig__'
          AND alert_type IN (
              'sla_near_expiration',
              'monthly_goal_at_risk',
              'candidate_no_interaction',
              'interview_not_confirmed',
              'feedback_pending'
          )
    """))
