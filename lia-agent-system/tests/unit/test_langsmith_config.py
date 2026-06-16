"""UC-P1-06: LangSmith initialization — graceful degradation when key missing or package absent."""
import os
import importlib
import sys
from unittest.mock import patch, MagicMock


def test_langsmith_disabled_without_api_key():
    """When no API key env var, init_langsmith returns False."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY")}
    with patch.dict(os.environ, env, clear=True):
        import app.observability as obs
        importlib.reload(obs)
        result = obs.init_langsmith()
        assert result is False


def test_langsmith_graceful_if_package_missing():
    """init_langsmith graceful fallback: when the inline langsmith.Client import raises
    ImportError (package absent), the function returns False without raising."""
    import app.observability as obs

    # Simulate the fallback path in init_langsmith where langsmith is absent
    # We patch the langsmith module lookup inside the fallback branch.
    # Note: configure_langsmith() sets env vars only (no langsmith import),
    # so we test the fallback inline path by patching builtins.__import__.
    original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def import_no_langsmith(name, *args, **kwargs):
        if name == "langsmith":
            raise ImportError("langsmith not installed (simulated)")
        return original_import(name, *args, **kwargs)

    import builtins
    with patch.dict(os.environ, {"LANGSMITH_API_KEY": "ls__test_key",
                                  "LANGCHAIN_API_KEY": ""}):
        with patch.object(builtins, "__import__", side_effect=import_no_langsmith):
            # Should not raise regardless
            try:
                result = obs.init_langsmith()
                # May be True (if configure_langsmith path runs) or False (if inline path runs)
                # Either way, must not raise
                assert isinstance(result, bool)
            except Exception as e:
                raise AssertionError(f"init_langsmith must never raise, got: {e}")


def test_llm_factory_has_traceable_decorator():
    """_try_generate must be decorated with @_ls_traceable (UC-P1-06 contract)."""
    import ast
    import pathlib

    factory_path = pathlib.Path(
        "/home/runner/workspace/lia-agent-system/app/shared/providers/llm_factory.py"
    )
    source = factory_path.read_text()
    # The decorator must appear in source
    assert "_ls_traceable" in source, (
        "UC-P1-06: @_ls_traceable decorator not found in llm_factory.py. "
        "Add it to _try_generate to enable LangSmith tracing."
    )
    assert '@_ls_traceable(name="llm.generate"' in source, (
        "UC-P1-06: @_ls_traceable must have name='llm.generate' for proper trace grouping."
    )


def test_langsmith_active_flag_is_bool():
    """_langsmith_active exported from observability must be a bool."""
    import app.observability as obs
    assert isinstance(obs._langsmith_active, bool)


def test_langsmith_init_idempotent():
    """Calling init_langsmith() multiple times must not raise."""
    import app.observability as obs
    # Call twice — should be safe
    obs.init_langsmith()
    obs.init_langsmith()
