"""Testa o sensor check_agent_mro_compliance — prova que detecta violações.

Gap G hardening (2026-06-08). Um sensor que nunca detecta é cego; este teste
prova deteccao positiva (sem mixin / ordem errada) E negativa (correto / docstring).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SENSOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_agent_mro_compliance.py"
_spec = importlib.util.spec_from_file_location("check_agent_mro_compliance", _SENSOR_PATH)
sensor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sensor)


def _write(tmp_path: Path, code: str) -> Path:
    p = tmp_path / "agent_mod.py"
    p.write_text(code, encoding="utf-8")
    return p


def test_detects_missing_mixin(tmp_path):
    code = (
        "class FooAgent(LangGraphReActBase, EnhancedAgentMixin):\n"
        "    pass\n"
    )
    violations = sensor.scan_file(_write(tmp_path, code))
    assert len(violations) == 1
    assert violations[0]["severity"] == "error"
    assert "FooAgent" in violations[0]["klass"]


def test_detects_wrong_order(tmp_path):
    code = (
        "class BarAgent(LangGraphReActBase, TenantAwareAgentMixin):\n"
        "    pass\n"
    )
    violations = sensor.scan_file(_write(tmp_path, code))
    assert len(violations) == 1
    assert violations[0]["severity"] == "warning"


def test_passes_correct_order(tmp_path):
    code = (
        "class OkAgent(TenantAwareAgentMixin, LangGraphReActBase, EnhancedAgentMixin):\n"
        "    pass\n"
    )
    violations = sensor.scan_file(_write(tmp_path, code))
    assert violations == []


def test_ignores_non_react_class(tmp_path):
    code = (
        "class SomeService:\n"
        "    pass\n"
    )
    violations = sensor.scan_file(_write(tmp_path, code))
    assert violations == []


def test_ignores_docstring_and_template(tmp_path):
    # Classe mencionada apenas em docstring/string NAO e ClassDef no AST.
    code = (
        '''"""Exemplo:\n'''
        "    class WizardReActAgent(LangGraphReActBase, EnhancedAgentMixin):\n"
        '''        ...\n"""\n'''
        "x = 1\n"
    )
    violations = sensor.scan_file(_write(tmp_path, code))
    assert violations == []
