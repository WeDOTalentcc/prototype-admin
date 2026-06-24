"""Testa o sensor check_federated_hitl_coverage — detecção positiva/negativa + baseline real.

Consolidação do chat (2026-06-09): prepara o "copiloto onipotente" garantindo que
toda ação de escrita federada passe por HITL. Sensor cego não tem valor — este
teste prova que ele DETECTA uma escrita não-gated e RESPEITA leitura + allowlist.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SENSOR = Path(__file__).resolve().parents[1] / "scripts" / "check_federated_hitl_coverage.py"
_spec = importlib.util.spec_from_file_location("check_federated_hitl_coverage", _SENSOR)
sensor = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sensor)

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _mk_root(tmp_path: Path, spec_tools: list, hitl: set) -> Path:
    d = tmp_path / "app/domains/recruiter_assistant/agents"
    d.mkdir(parents=True)
    spec_repr = "[" + ", ".join(f'("src", "{n}")' for n in spec_tools) + "]"
    (d / "recruiter_copilot_tool_registry.py").write_text(
        f"_FEDERATION_SPEC = {spec_repr}\n", encoding="utf-8"
    )
    hitl_repr = "frozenset({" + ", ".join(f'"{h}"' for h in hitl) + "})"
    (d / "recruiter_copilot_react_agent.py").write_text(
        f"class A:\n    _HITL_ACTION_TYPES = {hitl_repr}\n", encoding="utf-8"
    )
    return tmp_path


def test_baseline_real_code_zero_violations():
    """O código real (federado atual) deve estar limpo."""
    assert sensor.scan(_REPO_ROOT) == []


def test_detects_ungated_write_tool(tmp_path):
    """update_hiring_policy (escrita) fora do HITL -> violação (o caso 'cobrir tudo')."""
    root = _mk_root(tmp_path, ["list_jobs", "update_hiring_policy"], {"batch_move_candidates"})
    v = sensor.scan(root)
    assert len(v) == 1
    assert v[0]["tool"] == "update_hiring_policy"


def test_gated_write_tool_passes(tmp_path):
    """Escrita que ESTÁ no HITL -> sem violação."""
    root = _mk_root(tmp_path, ["update_benefits"], {"update_benefits"})
    assert sensor.scan(root) == []


def test_read_tool_ignored(tmp_path):
    """Tool de leitura (list/view/get) -> ignorada."""
    root = _mk_root(tmp_path, ["list_candidates", "view_job_details", "get_pipeline_summary"], set())
    assert sensor.scan(root) == []


def test_allowlist_respected(tmp_path):
    """start_creation_from_source bate 'start_' mas está na allowlist -> sem violação."""
    root = _mk_root(tmp_path, ["start_creation_from_source"], set())
    assert sensor.scan(root) == []
