"""
F11 unit guard — exercises `scripts/check_no_langchain_tool_decorator.py`
against synthetic `clean` and `violating` source trees in tmp_path.

Complementa o teste de fitness em `tests/fitness/test_audit_2026_04_finals.py`,
que apenas valida exit-code 0 contra a árvore real do repositório. Aqui
garantimos que o script realmente bloqueia uma regressão (exit-code 1) quando
um arquivo viola a regra.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "check_no_langchain_tool_decorator.py"


def _load_script_module():
    sys.path.insert(0, str(_SCRIPT.parent))
    try:
        # Re-import to pick up monkeypatched module-level constants on each test
        if "check_no_langchain_tool_decorator" in sys.modules:
            del sys.modules["check_no_langchain_tool_decorator"]
        return importlib.import_module("check_no_langchain_tool_decorator")
    finally:
        sys.path.pop(0)


def _build_tree(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def test_script_exists_and_is_executable():
    assert _SCRIPT.exists(), f"missing F11 lint script: {_SCRIPT}"


def test_clean_tree_returns_exit_zero(tmp_path, monkeypatch):
    domains = tmp_path / "app" / "domains"
    _build_tree(
        tmp_path,
        {
            "app/domains/foo/tools/__init__.py": "",
            "app/domains/foo/tools/foo_tool.py": (
                "from app.shared.tool_handler import tool_handler\n"
                "@tool_handler('foo')\n"
                "async def foo(): return {}\n"
            ),
            "app/domains/foo/agents/foo_tool_registry.py": (
                "from app.shared.tool_handler import tool_handler\n"
            ),
        },
    )
    mod = _load_script_module()
    monkeypatch.setattr(mod, "_ROOT", tmp_path)
    monkeypatch.setattr(mod, "_DOMAINS", domains)
    violations = mod._scan()
    assert violations == [], f"unexpected violations on clean tree: {violations}"
    assert mod.main() == 0


def test_violating_tools_dir_is_caught(tmp_path, monkeypatch):
    domains = tmp_path / "app" / "domains"
    _build_tree(
        tmp_path,
        {
            "app/domains/bad/tools/__init__.py": "",
            "app/domains/bad/tools/bad_tool.py": (
                "from langchain_core.tools import tool\n"
                "@tool\n"
                "def bad(): ...\n"
            ),
        },
    )
    mod = _load_script_module()
    monkeypatch.setattr(mod, "_ROOT", tmp_path)
    monkeypatch.setattr(mod, "_DOMAINS", domains)
    violations = mod._scan()
    assert len(violations) == 1
    rel_path, line_no, snippet = violations[0]
    assert "bad_tool.py" in str(rel_path)
    assert line_no == 1
    assert "from langchain_core.tools import tool" in snippet
    assert mod.main() == 1


def test_violating_tool_registry_is_caught(tmp_path, monkeypatch):
    """`*_tool_registry.py` em `app/domains/*/agents/` também é coberto."""
    domains = tmp_path / "app" / "domains"
    _build_tree(
        tmp_path,
        {
            "app/domains/baz/agents/baz_tool_registry.py": (
                "from langchain_core.tools import tool, BaseTool\n"
                "@tool\n"
                "def baz(): ...\n"
            ),
        },
    )
    mod = _load_script_module()
    monkeypatch.setattr(mod, "_ROOT", tmp_path)
    monkeypatch.setattr(mod, "_DOMAINS", domains)
    violations = mod._scan()
    assert len(violations) == 1
    assert "baz_tool_registry.py" in str(violations[0][0])
    assert mod.main() == 1


def test_unrelated_langchain_imports_are_ignored(tmp_path, monkeypatch):
    """Importar outros símbolos de `langchain_core.tools` não deve disparar."""
    domains = tmp_path / "app" / "domains"
    _build_tree(
        tmp_path,
        {
            "app/domains/qux/tools/qux_tool.py": (
                "from langchain_core.tools import BaseTool\n"
                "from langchain_core.tools.base import StructuredTool\n"
            ),
        },
    )
    mod = _load_script_module()
    monkeypatch.setattr(mod, "_ROOT", tmp_path)
    monkeypatch.setattr(mod, "_DOMAINS", domains)
    assert mod._scan() == []
    assert mod.main() == 0
