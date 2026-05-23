"""Bug #103 (phone test físico 2026-05-23): re-add voice_session_state column.

Root cause discovered via real Twilio call:
    asyncpg.exceptions.UndefinedColumnError: column "voice_session_state" of
    relation "wsi_sessions" does not exist

Migration 055 (`055_add_voice_session_state_to_wsi_sessions.py`) is in the
chain (`down_revision=054`, depended on by 056) but the column does NOT
exist in the live Replit DB. alembic_version is past 055 (currently 188).
Hypothesis: DB was rebuilt at some point with `alembic stamp head` after
055 was authored, skipping physical schema application; OR migration ran
in a now-discarded environment.

Fix canonical:
- Re-create the column via NEW migration 189 with IF NOT EXISTS (idempotent).
- Mirrors migration 055 verbatim (same column type, same GIN index).
- Safe to re-apply on any environment regardless of 055 outcome.

Rolls forward only — irreversible would lose state. downgrade() is a no-op
to preserve forward-only semantics for production DBs.

Refs:
- Phone test físico 2026-05-23 (Call SID CAb2f8ebcd1c036d49ac6546b69bb263ac)
- Original migration: alembic/versions/055_add_voice_session_state_to_wsi_sessions.py
- Persist site: app/domains/voice/repositories/wsi_repository.py:update_voice_session_state
- Read site: app/domains/voice/repositories/wsi_repository.py:get_voice_session_state
"""
from alembic import op


revision = "189_recreate_voice_session_state"
down_revision = "188_custom_agent_triagem_invite_enabled"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE wsi_sessions
        ADD COLUMN IF NOT EXISTS voice_session_state JSONB DEFAULT NULL
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_wsi_sessions_voice_state
        ON wsi_sessions USING GIN (voice_session_state)
        WHERE voice_session_state IS NOT NULL
    """)


def downgrade() -> None:
    # Forward-only: dropping the column would lose in-flight session state
    # of any active voice call. No-op preserves data integrity.
    pass
