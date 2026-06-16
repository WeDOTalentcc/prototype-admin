"""UC-P2-20: Tests for AgentRegistryWatcher custom agent hot-reload from DB."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch


def test_reload_custom_agents_method_exists():
    """AgentRegistryWatcher must expose _reload_custom_agents."""
    from app.core.agent_registry_watcher import AgentRegistryWatcher
    watcher = AgentRegistryWatcher.__new__(AgentRegistryWatcher)
    assert hasattr(watcher, "_reload_custom_agents"), (
        "_reload_custom_agents method must exist on AgentRegistryWatcher"
    )
    assert callable(watcher._reload_custom_agents)


def test_reload_custom_agents_returns_zero_on_missing_table():
    """_reload_custom_agents returns 0 when DB table does not exist (graceful degradation)."""
    from app.core.agent_registry_watcher import AgentRegistryWatcher
    watcher = AgentRegistryWatcher.__new__(AgentRegistryWatcher)

    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("relation custom_agents does not exist")

    mock_session_ctx = MagicMock()
    mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_db)
    mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session_cls = MagicMock(return_value=mock_session_ctx)

    with patch("app.core.agent_registry_watcher.AsyncSessionLocal", mock_session_cls, create=True):
        count = watcher._reload_custom_agents()

    assert isinstance(count, int)
    assert count == 0


def test_reload_custom_agents_is_called_by_check_and_reload():
    """check_and_reload must invoke _reload_custom_agents as part of its cycle."""
    import asyncio
    from app.core.agent_registry_watcher import AgentRegistryWatcher

    watcher = AgentRegistryWatcher.__new__(AgentRegistryWatcher)
    watcher._last_mtime = {}
    reload_called = []

    original = AgentRegistryWatcher._reload_custom_agents

    def mock_reload(self):
        reload_called.append(True)
        return 0

    with patch.object(AgentRegistryWatcher, "_reload_custom_agents", mock_reload):
        with patch("app.core.agent_registry_watcher.reload_agents_registry", return_value=[]):
            with patch("os.path.getmtime", return_value=0.0):
                asyncio.get_event_loop().run_until_complete(watcher.check_and_reload())

    assert reload_called, "_reload_custom_agents should be called by check_and_reload"


def test_reload_custom_agents_does_not_raise_on_import_error():
    """_reload_custom_agents must not propagate ImportError (fail-open)."""
    from app.core.agent_registry_watcher import AgentRegistryWatcher
    watcher = AgentRegistryWatcher.__new__(AgentRegistryWatcher)

    with patch("builtins.__import__", side_effect=ImportError("no module")):
        # Should return 0 without raising
        try:
            result = watcher._reload_custom_agents()
        except Exception as exc:
            # If it raises, the test fails with a clear message
            raise AssertionError(
                f"_reload_custom_agents must not propagate exceptions; got {exc!r}"
            ) from exc

    # result should be 0 or int (fail-open)
    assert isinstance(result, int)
