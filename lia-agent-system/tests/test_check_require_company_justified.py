"""Testa o sensor check_require_company_justified — detecção positiva e negativa.

Sprint 3 enterprise-readiness (2026-06-08). Guard de governança: toda exceção ao
fail-closed de tenant (require_company=False) deve ter justificativa inline.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SENSOR = Path(__file__).resolve().parents[1] / "scripts" / "check_require_company_justified.py"
_spec = importlib.util.spec_from_file_location("check_require_company_justified", _SENSOR)
sensor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sensor)


def _write(tmp_path: Path, code: str) -> Path:
    p = tmp_path / "mod.py"
    p.write_text(code, encoding="utf-8")
    return p


def test_detects_unjustified_require_company_false(tmp_path):
    code = (
        "@tool_handler(\"d\", require_company=False)\n"
        "async def f(**kwargs):\n"
        "    pass\n"
    )
    v = sensor.scan_file(_write(tmp_path, code))
    assert len(v) == 1


def test_passes_with_inline_justification(tmp_path):
    code = (
        "@tool_handler(\"d\", require_company=False)  # kept: pure lookup, no tenant data\n"
        "async def f(**kwargs):\n"
        "    pass\n"
    )
    v = sensor.scan_file(_write(tmp_path, code))
    assert v == []


def test_ignores_require_company_true_default(tmp_path):
    code = (
        "@tool_handler(\"d\")\n"
        "async def f(**kwargs):\n"
        "    pass\n"
    )
    v = sensor.scan_file(_write(tmp_path, code))
    assert v == []


def test_ignores_explicit_require_company_true(tmp_path):
    code = (
        "@tool_handler(\"d\", require_company=True)\n"
        "async def f(**kwargs):\n"
        "    pass\n"
    )
    v = sensor.scan_file(_write(tmp_path, code))
    assert v == []
