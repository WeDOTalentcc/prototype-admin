"""Add byok_soft_cap + byok_active to ai_credits_balance.

Revision ID: 175_byok_soft_cap
Revises: 174_briefing_frequency_canonical
Create Date: 2026-05-22

ADR-WT-2027 BYOK Strategy (Opcao C, decidido por Paulo 2026-05-22)
==================================================================

Contexto
--------
Auditoria Wave 4 (2026-05-22) revelou Bug B3: ``ai_credit_gate.check_credit_budget``
bloqueava tenants BYOK quando ``current_usage >= monthly_limit``, mesmo
quando o tenant pagava direto ao provider. UI prometia BYOK = unmetered, mas
backend silenciosamente bloqueava -- credibility break.

Decisao Opcao C (Paulo + Anderson):
1. BYOK ativo -> gate em **track-only mode** (loga consumption, nao bloqueia).
2. Tenant pode configurar ``byok_soft_cap`` opcional (alarm Grafana, nao block).
3. WeDoTalent continua rastreando consumption pra LGPD Art. 37 + audit trail.
4. Default ``byok_soft_cap=NULL`` (sem alarm); tenant define via
   ``/api/v1/ai-credits/byok-soft-cap``.

Changes
-------
- ADD ``byok_soft_cap INTEGER NULL`` -- tenant-managed soft cap (alarm only,
  never blocks). NULL = no alarm (default).
- ADD ``byok_active BOOLEAN NOT NULL DEFAULT FALSE`` -- denormalized flag
  refreshed by ``tenant_llm_context.update_llm_config`` write path. Cached
  here for fast gate check (avoids re-reading ``tenant_llm_configs`` on
  every LLM call). Source of truth remains ``tenant_llm_configs.providers``;
  this flag is a read-perf optimization.

Multi-tenancy: row-level (each ``ai_credits_balance`` row scoped to one
``company_id`` already via unique index). No new tenant filter needed.

LGPD: no PII in new columns; ``byok_soft_cap`` is integer (token count),
``byok_active`` is boolean.

REGRA 4: no silent default for ``byok_active`` other than False (the
fail-safe direction -- if denormalized flag is wrong, gate enforces; tenant
might be charged on WeDo budget unnecessarily but no money leaks the
opposite direction).

Idempotent
----------
Uses ``op.add_column`` directly. Alembic guards against re-run via
``alembic_version`` table. Downgrade drops both columns cleanly.

Skills aplicadas
----------------
- canonical-fix (BYOK detection helper canonical)
- harness-engineering (sensors + Grafana counters)
- production-quality:canonical-standards (Pydantic R1, ADR-001)
- TDD (10 contract tests em tests/contract/test_byok_gate_skip.py)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "175_byok_soft_cap"
down_revision = "174_briefing_frequency_canonical"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add BYOK columns to ai_credits_balance.

    Idempotent: alembic guards via alembic_version table, but the IF NOT
    EXISTS pattern is also safe for hot re-run during dev iteration.
    """
    op.execute(
        """
        ALTER TABLE ai_credits_balance
            ADD COLUMN IF NOT EXISTS byok_soft_cap INTEGER,
            ADD COLUMN IF NOT EXISTS byok_active BOOLEAN NOT NULL DEFAULT FALSE;
        """
    )


def downgrade() -> None:
    """Remove BYOK columns from ai_credits_balance.

    Safe rollback: gate falls back to pre-175 behavior (WeDo-paid path
    always taken, no BYOK skip). Track-only mode disabled, hard block
    re-enabled for all tenants (matches behavior before this migration).
    """
    op.execute(
        """
        ALTER TABLE ai_credits_balance
            DROP COLUMN IF EXISTS byok_active,
            DROP COLUMN IF EXISTS byok_soft_cap;
        """
    )
