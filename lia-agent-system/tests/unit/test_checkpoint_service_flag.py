"""
Tests for checkpoint_service.

Garante que:
- save_checkpoint persiste estado no banco de dados
- restore_checkpoint retorna o estado persistido
- delete_checkpoint remove o checkpoint do banco
- _sanitize_state remove campos efêmeros corretamente

Nota: LangGraph usa PostgresSaver nativamente. As funções deste módulo
são usadas apenas por paths de legado (ex: start_node customizado).
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestSaveCheckpoint:

    @pytest.mark.asyncio
    async def test_save_checkpoint_executes_db(self):
        from app.shared.services.checkpoint_service import save_checkpoint
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.services.checkpoint_service.pg_insert") as mock_insert:
            mock_stmt = MagicMock()
            mock_insert.return_value.values.return_value.on_conflict_do_update.return_value = mock_stmt
            await save_checkpoint(mock_db, "sess-001", "job_wizard", {"key": "value"})
            mock_db.execute.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_checkpoint_returns_none(self):
        from app.shared.services.checkpoint_service import save_checkpoint
        mock_db = MagicMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch("app.services.checkpoint_service.pg_insert") as mock_insert:
            mock_stmt = MagicMock()
            mock_insert.return_value.values.return_value.on_conflict_do_update.return_value = mock_stmt
            result = await save_checkpoint(mock_db, "sess-001", "interview", {})
            assert result is None


class TestRestoreCheckpoint:

    @pytest.mark.asyncio
    async def test_restore_checkpoint_returns_none_when_not_found(self):
        from app.shared.services.checkpoint_service import restore_checkpoint
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await restore_checkpoint(mock_db, "sess-001", "job_wizard")
        mock_db.execute.assert_called_once()
        assert result is None

    @pytest.mark.asyncio
    async def test_restore_checkpoint_returns_state_when_exists(self):
        from app.shared.services.checkpoint_service import restore_checkpoint
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_row.state_json = {"wizard_stage": "BASIC_INFO", "user_message": "oi"}
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await restore_checkpoint(mock_db, "sess-001", "job_wizard")
        assert result is not None
        assert result["wizard_stage"] == "BASIC_INFO"


class TestDeleteCheckpoint:

    @pytest.mark.asyncio
    async def test_delete_checkpoint_deletes_when_found(self):
        from app.shared.services.checkpoint_service import delete_checkpoint
        mock_db = MagicMock()
        mock_row = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        await delete_checkpoint(mock_db, "sess-001", "job_wizard")
        mock_db.execute.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_row)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_checkpoint_noop_when_not_found(self):
        from app.shared.services.checkpoint_service import delete_checkpoint
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        await delete_checkpoint(mock_db, "sess-001", "job_wizard")
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()


class TestSanitizeState:

    def test_removes_ephemeral_fields(self):
        from app.shared.services.checkpoint_service import _sanitize_state
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
        from app.shared.services.checkpoint_service import _sanitize_state
        state = {
            "callback": lambda x: x,
            "valid_field": "value",
        }
        result = _sanitize_state(state)
        assert "callback" not in result
        assert result["valid_field"] == "value"

    def test_preserves_nested_dicts(self):
        from app.shared.services.checkpoint_service import _sanitize_state
        state = {
            "nested": {"key": "value"},
            "list_field": [1, 2, 3],
        }
        result = _sanitize_state(state)
        assert result["nested"] == {"key": "value"}
        assert result["list_field"] == [1, 2, 3]
