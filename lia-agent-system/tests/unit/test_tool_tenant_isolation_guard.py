"""Regression test for `scripts/check_tool_tenant_isolation.py` (Task #673).

Pins two contracts:

* The repository currently passes the guard (no UNPROTECTED handlers in
  `app/domains/*/tools/`).
* A handler that ships without `@tool_handler` and without the
  `# tenant-isolation: manual` annotation is reported as a violation.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_tool_tenant_isolation.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("_tti_guard", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_tti_guard"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_repo_passes_tenant_isolation_guard():
    mod = _load_module()
    assert mod.main() == 0


def test_unprotected_function_is_reported(tmp_path: Path, monkeypatch):
    mod = _load_module()
    fake_root = tmp_path
    pkg = fake_root / "app" / "domains" / "fake" / "tools"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "bad.py").write_text(
        "async def do_thing(**kwargs):\n    return {}\n"
    )

    monkeypatch.setattr(mod, "ROOT", fake_root)
    rel = "app/domains/fake/tools/bad.py"
    violations = mod._scan_file(pkg / "bad.py", rel)
    assert any("do_thing" in v and "tool_handler" in v for v in violations), violations


def test_decorated_function_is_clean(tmp_path: Path):
    mod = _load_module()
    pkg = tmp_path / "tools"
    pkg.mkdir()
    (pkg / "ok.py").write_text(
        "from app.shared.tool_handler import tool_handler\n\n"
        "@tool_handler(domain='x')\n"
        "async def safe(**kwargs):\n    return {}\n"
    )
    rel = "app/domains/fake/tools/ok.py"
    assert mod._scan_file(pkg / "ok.py", rel) == []


@pytest.mark.parametrize("name", ["register_x_tools", "get_x_tools", "_helper"])
def test_helper_names_are_exempt(tmp_path: Path, name: str):
    mod = _load_module()
    pkg = tmp_path / "tools"
    pkg.mkdir()
    (pkg / "h.py").write_text(f"def {name}():\n    return None\n")
    rel = "app/domains/fake/tools/h.py"
    assert mod._scan_file(pkg / "h.py", rel) == []
