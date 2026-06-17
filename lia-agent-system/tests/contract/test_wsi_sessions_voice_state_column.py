"""
Phone test físico 2026-05-23 — Bug #103 regression sensor.

Discovery context (real Twilio call):
- Call SID CAb2f8ebcd1c036d49ac6546b69bb263ac connected, LIA spoke OK.
- voice_screening_orchestrator.persist_session_state() failed with:
    asyncpg.exceptions.UndefinedColumnError:
    column "voice_session_state" of relation "wsi_sessions" does not exist
- Session state was NOT persisted → call lost on restart.

Root cause:
- Migration 055 (`055_add_voice_session_state_to_wsi_sessions.py`) exists in
  the alembic chain (down_revision=054, depended on by 056) but the column
  was NOT physically present in the live Replit DB.
- alembic_version table reported 188_custom_agent_triagem_invite_enabled
  (past 055) — likely DB was stamped head at some point without applying
  schema diff, or migration ran in a now-discarded environment.

Fix canonical:
- New migration 189_recreate_voice_session_state.py (idempotent IF NOT EXISTS)
- Mirrors migration 055 verbatim (column + GIN index)
- Forward-only downgrade (no-op) to protect in-flight session data

Tests pin:
1. Migration 189 file exists with the correct upgrade SQL.
2. Migration chain is well-formed (189 → 188).
3. WsiRepository persist/load methods still reference the column
   (catches accidental removal of the canonical write path).
4. voice_screening_orchestrator still wires to canonical write path.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "alembic"
    / "versions"
)


class TestVoiceSessionStateMigration:
    """Bug #103: migration 189 must re-add voice_session_state idempotently."""

    def test_migration_189_file_exists(self):
        path = MIGRATIONS_DIR / "189_recreate_voice_session_state.py"
        assert path.exists(), (
            f"Bug #103 fix migration missing at {path}. "
            "phone test 2026-05-23 needs this column to persist session state."
        )

    def test_migration_189_uses_if_not_exists(self):
        """Idempotent ALTER required — DB state at 188 may or may not have column."""
        path = MIGRATIONS_DIR / "189_recreate_voice_session_state.py"
        src = path.read_text()
        assert "ADD COLUMN IF NOT EXISTS voice_session_state JSONB" in src, (
            "Migration must use IF NOT EXISTS — column may already exist "
            "from rolled-forward environments."
        )
        assert "CREATE INDEX IF NOT EXISTS idx_wsi_sessions_voice_state" in src, (
            "Migration must create GIN index for JSONB query performance "
            "(mirrors original migration 055)."
        )

    def test_migration_189_chain_to_188(self):
        path = MIGRATIONS_DIR / "189_recreate_voice_session_state.py"
        src = path.read_text()
        assert 'revision = "189_recreate_voice_session_state"' in src, (
            "revision identifier must be '189_recreate_voice_session_state'"
        )
        assert 'down_revision = "188_custom_agent_triagem_invite_enabled"' in src, (
            "down_revision must chain to 188_custom_agent_triagem_invite_enabled"
        )

    def test_migration_189_downgrade_is_noop(self):
        """Forward-only: downgrade must NOT drop column (would lose in-flight state)."""
        path = MIGRATIONS_DIR / "189_recreate_voice_session_state.py"
        src = path.read_text()
        assert "DROP COLUMN" not in src.upper().replace("# DROP COLUMN", ""), (
            "downgrade() must NOT drop voice_session_state — "
            "forward-only to protect active call data."
        )


class TestWsiRepositoryCanonicalPath:
    """Sensor against accidental removal of canonical voice_session_state path."""

    def test_wsi_repository_has_update_voice_session_state(self):
        from app.domains.voice.repositories.wsi_repository import WsiRepository
        assert hasattr(WsiRepository, "update_voice_session_state"), (
            "WsiRepository.update_voice_session_state is the canonical write "
            "path (F-13 ADR-001). Removing it breaks persist_session_state."
        )

    def test_wsi_repository_has_get_voice_session_state(self):
        from app.domains.voice.repositories.wsi_repository import WsiRepository
        assert hasattr(WsiRepository, "get_voice_session_state"), (
            "WsiRepository.get_voice_session_state is the canonical read "
            "path (F-13 ADR-001). Removing it breaks _load_session_from_db."
        )

    def test_orchestrator_uses_canonical_write_path(self):
        """voice_screening_orchestrator.persist_session_state must call WsiRepository."""
        import inspect
        from app.domains.voice.services import voice_screening_orchestrator
        src = inspect.getsource(voice_screening_orchestrator)
        assert "WsiRepository(db).update_voice_session_state" in src, (
            "persist_session_state must use WsiRepository canonical write — "
            "no direct UPDATE SQL inline (ADR-001 Repository Pattern)."
        )


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DB-dependent smoke check; runs only on Replit with DATABASE_URL",
)
async def test_voice_session_state_column_exists_in_live_db():
    """End-to-end smoke: column physically exists after migration 189 applied.

    Phone test 2026-05-23 discovered the schema drift. This test fails RED
    until `alembic upgrade head` runs in the target environment.
    """
    import asyncpg

    url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    try:
        col_type = await conn.fetchval(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = $1 AND column_name = $2
            """,
            "wsi_sessions",
            "voice_session_state",
        )
    finally:
        await conn.close()
    assert col_type == "jsonb", (
        f"wsi_sessions.voice_session_state must exist as jsonb "
        f"(got {col_type!r}). Run `alembic upgrade head` to apply migration 189."
    )
