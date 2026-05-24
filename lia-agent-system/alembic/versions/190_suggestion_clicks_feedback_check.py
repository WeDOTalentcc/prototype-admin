"""190 — suggestion_click_events table + interaction_feedback CHECK constraint

Onda 4-Fase8 (2026-05-24):

1. P1-3 Fase 2 — Sistema de aprendizado canonical:
   Cria suggestion_click_events table para capturar cliques em sugestões
   da LIA (ChatSuggestionsPanel + ChatWorkflowReels + chips + smart prompts).
   Append-only, multi-tenant via company_id.

2. P2-9 — feedback_category CHECK constraint condicional:
   Garante que thumbs='down' SEMPRE tem feedback_category (UI já força via
   popover, este constraint é defense-in-depth). thumbs='up' ou NULL podem
   ter category=NULL (sem motivo necessário). Cleanup dos 3 orphan records
   de jan/2026 (test data, todos com category=NULL).
"""
from alembic import op
import sqlalchemy as sa


revision = "190_suggestion_clicks_feedback_check"
down_revision = "189_recreate_voice_session_state"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. P1-3 Fase 2: suggestion_click_events table ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_click_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            company_id UUID NOT NULL,
            user_id VARCHAR(100) NOT NULL,
            suggestion_id VARCHAR(100) NOT NULL,
            suggestion_text VARCHAR(500) NOT NULL,
            suggestion_source VARCHAR(50) NOT NULL,
            page_context VARCHAR(100),
            chat_mode VARCHAR(20),
            click_metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)

    # Indexes pra queries comuns de Fase 3 (top suggestions per tenant/page/window)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_suggestion_click_company_id
        ON suggestion_click_events (company_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_suggestion_click_user_id
        ON suggestion_click_events (user_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_suggestion_click_suggestion_id
        ON suggestion_click_events (suggestion_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_suggestion_click_source
        ON suggestion_click_events (suggestion_source)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_suggestion_click_created_at
        ON suggestion_click_events (created_at)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_suggestion_click_company_page_created
        ON suggestion_click_events (company_id, page_context, created_at)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_suggestion_click_company_suggestion
        ON suggestion_click_events (company_id, suggestion_id)
    """)

    # Source value allowlist enforce (mirror dos Python SUGGESTION_SOURCES)
    op.execute("""
        ALTER TABLE suggestion_click_events
        ADD CONSTRAINT suggestion_source_allowlist
        CHECK (suggestion_source IN (
            'panel_static',
            'panel_dynamic',
            'reel_card',
            'chip_settings',
            'smart_prompt',
            'reel_action'
        ))
    """)

    # ── 2. P2-9: feedback_category CHECK constraint condicional ──

    # Cleanup orphan records (3 records de jan/2026, todos com category=NULL).
    # Safe: created_at < 2026-05-01 e feedback_category IS NULL (test data).
    op.execute("""
        DELETE FROM interaction_feedback
        WHERE feedback_category IS NULL
          AND created_at < '2026-05-01'
          AND (thumbs = 'down' OR thumbs IS NULL OR thumbs = '')
    """)

    # CHECK condicional: se thumbs='down', feedback_category é obrigatório.
    # thumbs='up' ou NULL: category pode ficar NULL (sem motivo necessário).
    op.execute("""
        ALTER TABLE interaction_feedback
        ADD CONSTRAINT feedback_category_required_when_thumbs_down
        CHECK (thumbs IS DISTINCT FROM 'down' OR feedback_category IS NOT NULL)
    """)


def downgrade() -> None:
    # Drop constraint primeiro (depende da coluna)
    op.execute("""
        ALTER TABLE interaction_feedback
        DROP CONSTRAINT IF EXISTS feedback_category_required_when_thumbs_down
    """)

    # Drop table (cascata indexes)
    op.execute("DROP TABLE IF EXISTS suggestion_click_events")
