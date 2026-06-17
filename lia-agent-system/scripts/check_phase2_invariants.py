#!/usr/bin/env python3
"""Onda 5.9 (2026-05-28) — sensor agregado de invariantes Studio Fase 2.

Roda em sequência os sensores BLOCKING + warn-only da Fase 2 e produz
relatorio estruturado. Exit 1 quando QUALQUER sensor BLOCKING falha.

Sensores cobertos (10 BLOCKING + 3 warn-only):

Backend (lia-agent-system/scripts/):
  - check_pool_agent_runs_realtime.py        (Onda 0)  [BLOCKING]
  - check_decision_tree_payload_shape.py     (Onda 1)  [BLOCKING]
  - check_lgpd_data_access_logged.py         (Onda 1)  [BLOCKING]
  - check_target_type_enum_canonical.py      (Onda 2)  [BLOCKING]
  - check_no_duplicate_assignment_table.py   (Onda 3)  [BLOCKING]
  - check_kpi_endpoint_consumes_runtime_metrics.py (Onda 4) [BLOCKING]

Frontend (plataforma-lia/scripts/):
  - check_decision_tree_drawer_uses_canonical_props.py (Onda 1) [BLOCKING]
  - check_ai_persona_in_agent_ui.py          (Onda 1)  [warn-only]
  - check_cyan_token_for_agents.py           (Onda 2)  [BLOCKING]
  - check_trigger_mode_label_canonical.py    (Onda 3)  [warn-only]
  - check_agent_kpi_consumes_canonical.py    (Onda 4 -> Onda 5.4) [BLOCKING]

Uso:
  python3 lia-agent-system/scripts/check_phase2_invariants.py
  python3 lia-agent-system/scripts/check_phase2_invariants.py --verbose

Exit codes:
  0 — todos BLOCKING passaram (warn-only podem ter violations)
  1 — pelo menos 1 BLOCKING falhou

Wiring em CI: `.github/workflows/frontend-ci.yml` step "Phase 2 invariants".
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Resolve workspace root: scripts/ está dentro de lia-agent-system/, então sobe 2 níveis.
ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class SensorSpec:
    label: str
    onda: str
    script: Path  # absoluto
    blocking: bool
    cwd: Path  # cwd para execução (alguns sensores assumem cwd = seu projeto root)


def _backend(name: str, label: str, onda: str, blocking: bool) -> SensorSpec:
    return SensorSpec(
        label=label,
        onda=onda,
        script=ROOT / "lia-agent-system" / "scripts" / name,
        blocking=blocking,
        cwd=ROOT / "lia-agent-system",
    )


def _frontend(name: str, label: str, onda: str, blocking: bool) -> SensorSpec:
    return SensorSpec(
        label=label,
        onda=onda,
        script=ROOT / "plataforma-lia" / "scripts" / name,
        blocking=blocking,
        cwd=ROOT / "plataforma-lia",
    )


SENSORS: list[SensorSpec] = [
    # Backend (lia-agent-system)
    _backend("check_pool_agent_runs_realtime.py", "pool_agent_runs realtime", "Onda 0", True),
    _backend("check_decision_tree_payload_shape.py", "decision_tree payload shape", "Onda 1", True),
    _backend("check_lgpd_data_access_logged.py", "LGPD data_access logged", "Onda 1", True),
    _backend("check_target_type_enum_canonical.py", "target_type enum canonical", "Onda 2", True),
    _backend("check_no_duplicate_assignment_table.py", "no duplicate assignment table", "Onda 3", True),
    _backend("check_kpi_endpoint_consumes_runtime_metrics.py", "KPI endpoint runtime_metrics", "Onda 4", True),
    # Frontend (plataforma-lia)
    _frontend("check_decision_tree_drawer_uses_canonical_props.py", "DecisionTreeDrawer canonical props", "Onda 1", True),
    _frontend("check_ai_persona_in_agent_ui.py", "useAiPersona em agent UI", "Onda 1", False),
    _frontend("check_cyan_token_for_agents.py", "cyan token canonical", "Onda 2", True),
    _frontend("check_trigger_mode_label_canonical.py", "trigger_mode label canonical", "Onda 3", False),
    _frontend("check_agent_kpi_consumes_canonical.py", "agent KPI consumes canonical", "Onda 4 (promoted 5.4)", True),
]


@dataclass
class SensorResult:
    spec: SensorSpec
    exit_code: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def run_sensor(spec: SensorSpec, verbose: bool) -> SensorResult:
    if not spec.script.exists():
        return SensorResult(
            spec=spec,
            exit_code=127,
            stdout="",
            stderr=f"script not found: {spec.script}",
        )
    try:
        proc = subprocess.run(
            ["python3", str(spec.script)],
            cwd=str(spec.cwd),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if verbose:
            print(f"--- {spec.label} stdout ---")
            print(proc.stdout)
            if proc.stderr:
                print(f"--- {spec.label} stderr ---")
                print(proc.stderr)
        return SensorResult(spec=spec, exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    except subprocess.TimeoutExpired:
        return SensorResult(spec=spec, exit_code=124, stdout="", stderr="timeout 60s")
    except Exception as e:  # noqa: BLE001
        return SensorResult(spec=spec, exit_code=1, stdout="", stderr=f"erro inesperado: {e}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sensor agregado Phase 2 invariants.")
    parser.add_argument("--verbose", action="store_true", help="Imprime stdout/stderr de cada sensor.")
    args = parser.parse_args()

    print("🔍 Studio Fase 2 — sensor agregado de invariantes")
    print(f"   Workspace root: {ROOT}")
    print(f"   {len(SENSORS)} sensores ({sum(1 for s in SENSORS if s.blocking)} BLOCKING + {sum(1 for s in SENSORS if not s.blocking)} warn-only)\n")

    results: list[SensorResult] = []
    for spec in SENSORS:
        result = run_sensor(spec, args.verbose)
        results.append(result)
        icon = "✅" if result.passed else ("❌" if spec.blocking else "⚠️")
        mode = "BLOCKING" if spec.blocking else "warn-only"
        print(f"   {icon} [{spec.onda}] {spec.label} ({mode}) — exit={result.exit_code}")
        if not result.passed and not args.verbose:
            # Sempre mostrar primeira linha de output para diagnóstico rápido.
            first_line = (result.stdout or result.stderr).strip().split("\n")[0]
            if first_line:
                print(f"      → {first_line[:120]}")

    print()
    blocking_failures = [r for r in results if r.spec.blocking and not r.passed]
    warn_failures = [r for r in results if not r.spec.blocking and not r.passed]

    print(f"   Passaram: {sum(1 for r in results if r.passed)}/{len(results)}")
    if warn_failures:
        print(f"   ⚠️  warn-only com violations: {len(warn_failures)}")
        for r in warn_failures:
            print(f"      - {r.spec.label}")
    if blocking_failures:
        print(f"   ❌ BLOCKING falhou: {len(blocking_failures)}")
        for r in blocking_failures:
            print(f"      - {r.spec.label} (rodar `python3 {r.spec.script.relative_to(ROOT)}` pra detalhes)")
        print("\n   Modo: BLOCKING — exit 1.")
        return 1

    print("\n   ✅ Modo: BLOCKING — todos os sensores BLOCKING passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
