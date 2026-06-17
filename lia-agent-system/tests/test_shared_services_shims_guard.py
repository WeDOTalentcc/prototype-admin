"""
Unit guard — exercises `scripts/check_shared_services_shims.py` against
synthetic `clean` and `violating` source trees in tmp_path (Task #1283).

Complementa o teste de fitness em `tests/fitness/test_audit_2026_04_finals.py`
(`TestShimServiceConsolidationGuard`), que apenas valida exit-code 0 contra a
árvore real do repositório. Aqui garantimos que o script realmente detecta uma
regressão (lógica de negócio reintroduzida num shim, ou um shim que parou de
delegar para o domínio).
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _ROOT / "scripts" / "check_shared_services_shims.py"


def _load_script_module():
    sys.path.insert(0, str(_SCRIPT.parent))
    try:
        if "check_shared_services_shims" in sys.modules:
            del sys.modules["check_shared_services_shims"]
        return importlib.import_module("check_shared_services_shims")
    finally:
        sys.path.pop(0)


def _build_tree(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def test_script_exists():
    assert _SCRIPT.exists(), f"missing shim guard script: {_SCRIPT}"


def test_clean_tree_has_no_violations(tmp_path):
    _build_tree(
        tmp_path,
        {
            "app/domains/analytics/services/foo_service.py": (
                "def real_logic():\n    return 42\n"
            ),
            "app/shared/services/foo_service.py": (
                '"""Backwards-compatibility shim."""\n'
                "from app.domains.analytics.services.foo_service import *  # noqa\n"
            ),
        },
    )
    mod = _load_script_module()
    violations = mod._scan(
        shared_dir=tmp_path / "app" / "shared" / "services",
        domains_root=tmp_path / "app" / "domains",
    )
    assert violations == [], f"clean tree should have no violations, got: {violations}"


def test_shim_with_private_reexport_is_clean(tmp_path):
    """Shims that reexport private symbols (for test patching) are still pure."""
    _build_tree(
        tmp_path,
        {
            "app/domains/analytics/services/bar_service.py": (
                "_MIN = 3\n\ndef thing():\n    return _MIN\n"
            ),
            "app/shared/services/bar_service.py": (
                '"""shim."""\n'
                "from app.domains.analytics.services.bar_service import *  # noqa\n"
                "from app.domains.analytics.services.bar_service import _MIN  # noqa\n"
                "try:\n"
                "    from app.domains.analytics.services.bar_service import _MIN as _m\n"
                "except ImportError:\n"
                "    pass\n"
            ),
        },
    )
    mod = _load_script_module()
    violations = mod._scan(
        shared_dir=tmp_path / "app" / "shared" / "services",
        domains_root=tmp_path / "app" / "domains",
    )
    assert violations == [], f"private-reexport shim should be clean, got: {violations}"


def test_shim_with_business_logic_is_flagged(tmp_path):
    """A shim that grows a def/class = duplicated implementation = violation."""
    _build_tree(
        tmp_path,
        {
            "app/domains/analytics/services/baz_service.py": (
                "def real_logic():\n    return 1\n"
            ),
            "app/shared/services/baz_service.py": (
                '"""shim that diverged."""\n'
                "from app.domains.analytics.services.baz_service import *  # noqa\n"
                "\n\ndef real_logic():  # divergent copy!\n    return 2\n"
            ),
        },
    )
    mod = _load_script_module()
    violations = mod._scan(
        shared_dir=tmp_path / "app" / "shared" / "services",
        domains_root=tmp_path / "app" / "domains",
    )
    assert len(violations) == 1, f"expected 1 violation, got: {violations}"
    assert "baz_service.py" in violations[0][0]
    assert "lógica de negócio" in violations[0][1]


def test_shim_not_delegating_is_flagged(tmp_path):
    """A shadowing file that does NOT delegate to the domain twin is a violation."""
    _build_tree(
        tmp_path,
        {
            "app/domains/analytics/services/qux_service.py": (
                "def real_logic():\n    return 1\n"
            ),
            "app/shared/services/qux_service.py": (
                '"""looks like a shim but imports nothing from the domain."""\n'
                "import os  # noqa\n"
            ),
        },
    )
    mod = _load_script_module()
    violations = mod._scan(
        shared_dir=tmp_path / "app" / "shared" / "services",
        domains_root=tmp_path / "app" / "domains",
    )
    assert len(violations) == 1, f"expected 1 violation, got: {violations}"
    assert "qux_service.py" in violations[0][0]
    assert "não delega" in violations[0][1]


def test_shared_only_service_is_ignored(tmp_path):
    """A shared service with NO domain twin is a genuine shared service, not a shim."""
    _build_tree(
        tmp_path,
        {
            "app/shared/services/standalone_service.py": (
                '"""real shared-only service."""\n'
                "def helper():\n    return True\n"
            ),
        },
    )
    mod = _load_script_module()
    violations = mod._scan(
        shared_dir=tmp_path / "app" / "shared" / "services",
        domains_root=tmp_path / "app" / "domains",
    )
    assert violations == [], f"shared-only service must be ignored, got: {violations}"
