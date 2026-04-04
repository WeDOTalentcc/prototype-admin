"""Add voice_session_state JSONB column to wsi_sessions for voice call persistence.

Task #139: Fix Core Voice Screening — Sessão DB, Perguntas WSI, Compliance.

Adds a JSONB column to wsi_sessions so the VoiceScreeningOrchestrator can
persist and restore in-flight session state (transcript_segments, questions_asked,
session metadata) even across server restarts.
"""

revision = '055'
down_revision = '054'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def upgrade():
    op.execute("""
        ALTER TABLE wsi_sessions
        ADD COLUMN IF NOT EXISTS voice_session_state JSONB DEFAULT NULL
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_wsi_sessions_voice_state
        ON wsi_sessions USING GIN (voice_session_state)
        WHERE voice_session_state IS NOT NULL
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_wsi_sessions_voice_state")
    op.execute("ALTER TABLE wsi_sessions DROP COLUMN IF EXISTS voice_session_state")
