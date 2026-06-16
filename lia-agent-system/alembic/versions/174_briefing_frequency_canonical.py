"""Backfill briefing_frequency: AlertConfig -> HiringPolicy.communication_rules (Sprint D+1 partial).

Revision ID: 174_briefing_frequency_canonical
Revises: 173_rls_policy_batch_1
Create Date: 2026-05-22

Sprint D+1 PARTIAL — registered 2026-05-22
==========================================

Contexto (ADR-WT-2025 §Sprint D+1 partial execution)
----------------------------------------------------
Sprint D fechou cutover do CATALOGO de alertas (AlertConfig.alerts ->
AlertPreference) em 2026-05-22. **Mas o campo `briefing_frequency` ficou
fora da consolidacao Sprint D** porque o catalogo de alertas
(toggles per alert_type) tem semantica distinta do frequency dispatcher
(daily|weekly|twice_daily|monthly).

Atraves do read-shadow pattern continuado, esta migration:
1. Backfilla `briefing_frequency` de `AlertConfig` para
   `CompanyHiringPolicy.communication_rules.briefing_frequency` (JSONB)
   - mesmo local que `lia_tone`, `preferred_channel`, `ai_persona` etc.
2. NAO toca `alert_configs` (preserva backward-compat ate Sprint D+2
   DROP TABLE alert_configs ~2026-09-22).
3. Idempotente: WHERE clause garante que rows ja com briefing_frequency
   no JSONB NAO sao sobrescritas (caso re-run da migration).

Per ADR-WT-2025: briefing_frequency canonical post-Sprint-D+2 vive em
`CompanyHiringPolicy.communication_rules.briefing_frequency` (Opcao A
do plan, evita over-engineering de tabela propria).

Multi-tenancy: filtra apenas AlertConfig rows com company_id IS NOT NULL
(global default configs sao TENANT-EXEMPT, nao migram).

LGPD: nenhum dado pessoal envolvido — briefing_frequency e config de
recorrencia per company, sem PII.

REGRA 4 (no silent fallback): se briefing_frequency em AlertConfig for
NULL ou string vazia, NAO escrevemos no JSONB (deixamos cair em default
'weekly' do read path).

Skills aplicadas:
- canonical-fix (HiringPolicy single source of truth)
- harness-engineering (telemetry counters + read-shadow)
- production-quality:canonical-standards
- TDD (6 contract tests em tests/contract/test_briefing_canonical_migration.py)
"""
from alembic import op


# revision identifiers, used by Alembic
revision = "174_briefing_frequency_canonical"
down_revision = "173_rls_policy_batch_1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Backfill briefing_frequency from AlertConfig -> HiringPolicy.communication_rules.

    Idempotent: only writes when target JSONB key is missing.
    Skips AlertConfig rows with NULL/empty briefing_frequency or NULL company_id.
    """
    op.execute(
        """
        UPDATE company_hiring_policies hp
        SET communication_rules = jsonb_set(
                COALESCE(hp.communication_rules::jsonb, '{}'::jsonb),
                '{briefing_frequency}',
                to_jsonb(src.briefing_frequency),
                true
            )::json,
            updated_at = NOW()
        FROM (
            SELECT DISTINCT ON (ac.company_id)
                   ac.company_id,
                   ac.briefing_frequency
              FROM alert_configs ac
             WHERE ac.company_id IS NOT NULL
               AND ac.briefing_frequency IS NOT NULL
               AND ac.briefing_frequency <> ''
               AND ac.briefing_frequency IN ('daily', 'weekly', 'twice_daily', 'monthly')
             ORDER BY ac.company_id, ac.updated_at DESC NULLS LAST
        ) src
        WHERE hp.company_id = src.company_id
          AND (hp.communication_rules::jsonb->>'briefing_frequency') IS NULL;
        """
    )


def downgrade() -> None:
    """Remove briefing_frequency key from HiringPolicy.communication_rules.

    Safe rollback: AlertConfig.briefing_frequency continues existing until
    Sprint D+2 DROP TABLE alert_configs, so removing the JSONB key only
    re-exposes the legacy read path (which dispatch still understands via
    fallback during the transition).
    """
    op.execute(
        """
        UPDATE company_hiring_policies
        SET communication_rules = (communication_rules::jsonb - 'briefing_frequency')::json,
            updated_at = NOW()
        WHERE communication_rules::jsonb ? 'briefing_frequency';
        """
    )
