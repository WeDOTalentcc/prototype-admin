#!/usr/bin/env python3
"""Fase 2.5 (2026-05-29) — sensor agregado de invariantes do motor unificado.

Espelha `check_phase2_invariants.py` (Onda 5.9). Roda em sequência os sensores
novos da Fase 2.5 (motor de execução unificado: agent_deployments + dispatch +
scheduler + event consumer + BYOK + RLS) e produz relatório estruturado.
Exit 1 quando QUALQUER sensor BLOCKING falha.

Sensores cobertos (Fase 2.5):

Backend (lia-agent-system/scripts/):
  - check_rls_enabled_on_tenant_tables.py      (C2.4) [BLOCKING]
  - check_byok_tenant_id_in_llm_calls.py       (C2.4) [BLOCKING]
  - check_deployment_has_executor.py           (C1.2) [BLOCKING]
  - check_no_new_pool_agent_assignments.py     (C1.5) [BLOCKING]
  - check_no_silent_llm_fallback.py            (REGRA 4) [BLOCKING]

Sub-chamada (Fase 2 — defesa em profundidade):
  - check_phase2_invariants.py                 (Onda 5.9) [BLOCKING agregado]

Uso:
  python3 lia-agent-system/scripts/check_phase25_invariants.py
  python3 lia-agent-system/scripts/check_phase25_invariants.py --verbose
  python3 lia-agent-system/scripts/check_phase25_invariants.py --skip-phase2

Exit codes:
  0 — todos os sensores BLOCKING passaram (warn-only podem ter violations)
  1 — pelo menos 1 sensor BLOCKING falhou

Wiring em CI: `.github/workflows/harness-sensors.yml` job harness-blocking +
`.github/workflows/frontend-ci.yml` step "Phase 2.5 invariants".

REGRA canonical (CLAUDE.md § Fase 2.5 — Motor de execução unificado):
  Todo novo acoplamento agente↔surface usa agent_deployments +
  dispatch_agent_deployment_task, NUNCA pool_agent_assignments.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# scripts/ está dentro de lia-agent-system/. parents[1] = lia-agent-system/,
# parents[2] = workspace root.
LIA_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class SensorSpec:
    label: str
    fase: str
    script: Path  # absoluto
    blocking: bool
    cwd: Path
    args: tuple[str, ...] = ()


def _backend(name: str, label: str, fase: str, blocking: bool, *args: str) -> SensorSpec:
    return SensorSpec(
        label=label,
        fase=fase,
        script=LIA_ROOT / "scripts" / name,
        blocking=blocking,
        cwd=LIA_ROOT,
        args=tuple(args),
    )


SENSORS: list[SensorSpec] = [
    _backend("check_rls_enabled_on_tenant_tables.py", "RLS habilitado em tabelas tenant", "C2.4", True),
    _backend("check_byok_tenant_id_in_llm_calls.py", "BYOK tenant_id em LLM calls", "C2.4", True),
    _backend("check_deployment_has_executor.py", "deployment tem executor (trigger_mode)", "C1.2", True),
    _backend("check_no_new_pool_agent_assignments.py", "no novo write pool_agent_assignments", "C1.5", True),
    _backend("check_no_silent_llm_fallback.py", "no silent LLM fallback (REGRA 4)", "REGRA 4", True),
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
        return SensorResult(spec=spec, exit_code=127, stdout="", stderr=f"script not found: {spec.script}")
    try:
        proc = subprocess.run(
            ["python3", str(spec.script), *spec.args],
            cwd=str(spec.cwd),
            capture_output=True,
            text=True,
            timeout=90,
        )
        if verbose:
            print(f"--- {spec.label} stdout ---")
            print(proc.stdout)
            if proc.stderr:
                print(f"--- {spec.label} stderr ---")
                print(proc.stderr)
        return SensorResult(spec=spec, exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    except subprocess.TimeoutExpired:
        return SensorResult(spec=spec, exit_code=124, stdout="", stderr="timeout 90s")
    except Exception as e:  # noqa: BLE001
        return SensorResult(spec=spec, exit_code=1, stdout="", stderr=f"erro inesperado: {e}")


def run_phase2_subcall(verbose: bool) -> SensorResult:
    """Sub-chamada do agregado Fase 2 (defesa em profundidade)."""
    spec = SensorSpec(
        label="Fase 2 invariants (sub-agregado)",
        fase="Onda 5.9",
        script=LIA_ROOT / "scripts" / "check_phase2_invariants.py",
        blocking=True,
        cwd=LIA_ROOT,
    )
    return run_sensor(spec, verbose)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sensor agregado Fase 2.5 invariants.")
    parser.add_argument("--verbose", action="store_true", help="Imprime stdout/stderr de cada sensor.")
    parser.add_argument(
        "--skip-phase2",
        action="store_true",
        help="Não roda o agregado Fase 2 como sub-chamada (evita dupla execução em CI que já roda phase2).",
    )
    args = parser.parse_args()

    print("🔍 Studio Fase 2.5 — sensor agregado do motor de execução unificado")
    print(f"   Workspace root: {WORKSPACE_ROOT}")
    print(f"   {len(SENSORS)} sensores Fase 2.5 (todos BLOCKING)")
    if not args.skip_phase2:
        print("   + sub-chamada check_phase2_invariants.py (defesa em profundidade)")
    print()

    results: list[SensorResult] = []
    for spec in SENSORS:
        result = run_sensor(spec, args.verbose)
        results.append(result)
        icon = "✅" if result.passed else ("❌" if spec.blocking else "⚠️")
        mode = "BLOCKING" if spec.blocking else "warn-only"
        print(f"   {icon} [{spec.fase}] {spec.label} ({mode}) — exit={result.exit_code}")
        if not result.passed and not args.verbose:
            first_line = (result.stdout or result.stderr).strip().split("\n")[0]
            if first_line:
                print(f"      → {first_line[:120]}")

    if not args.skip_phase2:
        p2 = run_phase2_subcall(args.verbose)
        results.append(p2)
        icon = "✅" if p2.passed else "❌"
        print(f"   {icon} [{p2.spec.fase}] {p2.spec.label} (BLOCKING) — exit={p2.exit_code}")
        if not p2.passed and not args.verbose:
            first_line = (p2.stdout or p2.stderr).strip().split("\n")[0]
            if first_line:
                print(f"      → {first_line[:120]}")

    print()
    blocking_failures = [r for r in results if r.spec.blocking and not r.passed]
    print(f"   Passaram: {sum(1 for r in results if r.passed)}/{len(results)}")
    if blocking_failures:
        print(f"   ❌ BLOCKING falhou: {len(blocking_failures)}")
        for r in blocking_failures:
            rel = r.spec.script.relative_to(WORKSPACE_ROOT)
            print(f"      - {r.spec.label} (rodar `python3 {rel}` pra detalhes)")
        print("\n   Modo: BLOCKING — exit 1.")
        return 1

    print("\n   ✅ Modo: BLOCKING — todos os sensores BLOCKING da Fase 2.5 passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
