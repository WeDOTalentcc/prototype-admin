"""
Tests for checkpoint_service — comportamento no-op quando USE_LANGGRAPH_NATIVE=True.

Garante que:
- save_checkpoint é no-op quando flag=True
- restore_checkpoint retorna None quando flag=True
- delete_checkpoint é no-op quando flag=True
- Todas as funções executam normalmente quando flag=False
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


# ---------------------------------------------------------------------------
# Section 1: _langgraph_native_active helper
# ---------------------------------------------------------------------------

class TestLangGraphNativeActive:

    def test_returns_false_when_setting_false(self):
        from app.services.checkpoint_service import _langgraph_native_active
        with patch("app.core.config.settings") as mock_s:
            mock_s.USE_LANGGRAPH_NATIVE = False
            assert _langgraph_native_active() is False

    def test_returns_true_when_setting_true(self):
        from app.services.checkpoint_service import _langgraph_native_active
        with patch("app.core.config.settings") as mock_s:
            mock_s.USE_LANGGRAPH_NATIVE = True
            assert _langgraph_native_active() is True

    def test_returns_true_on_default_env(self):
        """Fallback seguro — retorna True quando flag está ativo (padrão após Fase 1 Gaps)."""
        from app.services.checkpoint_service import _langgraph_native_active
        # A função importa settings internamente com try/except
        result = _langgraph_native_active()
        assert result is True  # ativado em 08/03/2026 (Fase 1 Gaps)

    def test_default_value_is_true_after_activation(self):
        """Após Fase 1 (Gaps) 08/03/2026, USE_LANGGRAPH_NATIVE=True por padrão."""
        from app.core.config import settings
        assert settings.USE_LANGGRAPH_NATIVE is True


# ---------------------------------------------------------------------------
# Section 2: save_checkpoint no-op
# ---------------------------------------------------------------------------

class TestSaveCheckpointNoOp:

    @pytest.mark.asyncio
    async def test_save_checkpoint_noop_when_flag_true(self):
        from app.services.checkpoint_service import save_checkpoint
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.services.checkpoint_service._langgraph_native_active", return_value=True):
            await save_checkpoint(mock_db, "sess-001", "job_wizard", {"key": "value"})
            mock_db.execute.assert_not_called()
            mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_checkpoint_executes_when_flag_false(self):
        from app.services.checkpoint_service import save_checkpoint
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.services.checkpoint_service._langgraph_native_active", return_value=False):
            with patch("app.services.checkpoint_service.pg_insert") as mock_insert:
                mock_stmt = MagicMock()
                mock_insert.return_value.values.return_value.on_conflict_do_update.return_value = mock_stmt
                await save_checkpoint(mock_db, "sess-001", "job_wizard", {"key": "value"})
                mock_db.execute.assert_called_once()
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_checkpoint_noop_returns_none(self):
        from app.services.checkpoint_service import save_checkpoint
        mock_db = MagicMock()

        with patch("app.services.checkpoint_service._langgraph_native_active", return_value=True):
            result = await save_checkpoint(mock_db, "sess-001", "interview", {})
            assert result is None


# ---------------------------------------------------------------------------
# Section 3: restore_checkpoint no-op
# ---------------------------------------------------------------------------

class TestRestoreCheckpointNoOp:

    @pytest.mark.asyncio
    async def test_restore_checkpoint_returns_none_when_flag_true(self):
        from app.services.checkpoint_service import restore_checkpoint
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()

        with patch("app.services.checkpoint_service._langgraph_native_active", return_value=True):
            result = await restore_checkpoint(mock_db, "sess-001", "job_wizard")
            assert result is None
            mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_restore_checkpoint_queries_db_when_flag_false(self):
        from app.services.checkpoint_service import restore_checkpoint
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.checkpoint_service._langgraph_native_active", return_value=False):
            result = await restore_checkpoint(mock_db, "sess-001", "job_wizard")
            mock_db.execute.assert_called_once()
            assert result is None  # nenhum checkpoint → None

    @pytest.mark.asyncio
    async def test_restore_checkpoint_returns_state_when_flag_false_and_exists(self):
        from app.services.checkpoint_service import restore_checkpoint
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.state_json = {"wizard_stage": "BASIC_INFO", "user_message": "oi"}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch("app.services.checkpoint_service._langgraph_native_active", return_value=False):
            result = await restore_checkpoint(mock_db, "sess-001", "job_wizard")
            assert result is not None
            assert result["wizard_stage"] == "BASIC_INFO"


# ---------------------------------------------------------------------------
# Section 4: delete_checkpoint no-op
# ---------------------------------------------------------------------------

class TestDeleteCheckpointNoOp:

    @pytest.mark.asyncio
    async def test_delete_checkpoint_noop_when_flag_true(self):
        from app.services.checkpoint_service import delete_checkpoint
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()

        with patch("app.services.checkpoint_service._langgraph_native_active", return_value=True):
            await delete_checkpoint(mock_db, "sess-001", "job_wizard")
            mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_checkpoint_deletes_when_flag_false(self):
        from app.services.checkpoint_service import delete_checkpoint
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.services.checkpoint_service._langgraph_native_active", return_value=False):
            await delete_checkpoint(mock_db, "sess-001", "job_wizard")
            mock_db.execute.assert_called_once()
            mock_db.delete.assert_called_once_with(mock_row)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_checkpoint_noop_when_flag_false_and_not_found(self):
        from app.services.checkpoint_service import delete_checkpoint
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.services.checkpoint_service._langgraph_native_active", return_value=False):
            await delete_checkpoint(mock_db, "sess-001", "job_wizard")
            mock_db.delete.assert_not_called()
            mock_db.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Section 5: _sanitize_state
# ---------------------------------------------------------------------------

class TestSanitizeState:

    def test_removes_ephemeral_fields(self):
        from app.services.checkpoint_service import _sanitize_state
        state = {
            "wizard_stage": "BASIC_INFO",
            "user_message": "should be removed",
            "error": "should be removed",
            "tool_calls": ["also removed"],
            "tool_results": {},
            "streaming_chunks": [],
            "job_title": "keeps",
        }
        result = _sanitize_state(state)
        assert "user_message" not in result
        assert "error" not in result
        assert "tool_calls" not in result
        assert "tool_results" not in result
        assert "streaming_chunks" not in result
        assert result["wizard_stage"] == "BASIC_INFO"
        assert result["job_title"] == "keeps"

    def test_removes_non_serializable_callables(self):
        from app.services.checkpoint_service import _sanitize_state
        state = {
            "callback": lambda x: x,  # callable, deve ser removido
            "valid_field": "value",
        }
        result = _sanitize_state(state)
        assert "callback" not in result
        assert result["valid_field"] == "value"

    def test_preserves_nested_dicts(self):
        from app.services.checkpoint_service import _sanitize_state
        state = {
            "nested": {"key": "value"},
            "list_field": [1, 2, 3],
        }
        result = _sanitize_state(state)
        assert result["nested"] == {"key": "value"}
        assert result["list_field"] == [1, 2, 3]
