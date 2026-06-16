#!/usr/bin/env python3
"""Sensor canonical T-07 R1 ratchet (ADR-029-v3).

Compara R1 violations atual contra baseline em scripts/r1_baseline.json.
Política "no-new-violations":
- PR que adiciona R1 nova → exit 1 (BLOCKING)
- PR que remove R1 (boy-scout) → suggest baseline update
- Mesmo count: exit 0

Uso:
    python scripts/check_pydantic_R1_ratchet.py [--update-baseline]
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def parse_r1_violations(output: str) -> dict[str, str]:
    """Parse output do sensor canonical, return {class_name: file:line}."""
    pattern = re.compile(r"❌ R1 violation: (\w+) em (app/[^:]+):(\d+)")
    violations = {}
    for line in output.splitlines():
        m = pattern.search(line)
        if m:
            class_name, file_path, line_no = m.groups()
            violations[class_name] = f"{file_path}:{line_no}"
    return violations


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    baseline_path = repo_root / "scripts" / "r1_baseline.json"
    sensor_path = repo_root / "scripts" / "check_pydantic_conventions.py"
    update_mode = "--update-baseline" in sys.argv

    if not baseline_path.exists():
        print(f"[T-07 R1 RATCHET] Baseline não existe — gerar com:")
        print(f"  python3 scripts/generate_r1_baseline.py")
        return 1

    if not sensor_path.exists():
        print(f"[T-07 R1 RATCHET] Sensor canonical não encontrado: {sensor_path}")
        return 1

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_classes = set(baseline.get("by_class", {}).keys())
    baseline_count = baseline.get("total_count", 0)

    # Rodar sensor canonical
    result = subprocess.run(
        ["python3", str(sensor_path), "app/"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr

    current = parse_r1_violations(output)
    current_classes = set(current.keys())
    current_count = len(current_classes)

    new_violations = current_classes - baseline_classes
    removed = baseline_classes - current_classes

    if update_mode:
        print(f"[UPDATE MODE] Regenerando baseline com {current_count} R1 atuais...")
        # Delega para generate_r1_baseline.py
        return subprocess.run(
            ["python3", str(repo_root / "scripts" / "generate_r1_baseline.py")],
            cwd=str(repo_root),
        ).returncode

    if new_violations:
        print(f"[T-07 R1 RATCHET] ❌ {len(new_violations)} NEW R1 violations (sobre baseline {baseline_count}):")
        for cls in sorted(new_violations):
            print(f"  + {cls}: {current.get(cls, '?')}")
        print()
        print("CORRECAO canonical:")
        print("  (a) Herdar de WeDoBaseModel: class X(WeDoBaseModel):")
        print("  (b) Adicionar model_config = ConfigDict(extra='forbid')")
        print("  (c) Comment R1-EXEMPT: <reason> <ticket> acima da classe")
        print("  (d) Adicionar a SKIP_R1 em scripts/check_pydantic_conventions.py")
        print()
        print("Mode: BLOCKING")
        return 1

    if removed:
        print(f"[T-07 R1 RATCHET] ✅ {len(removed)} R1 REMOVIDAS (boy-scout):")
        for cls in sorted(removed):
            print(f"  - {cls}")
        print()
        print(f"Atualize baseline com:")
        print(f"  python3 scripts/check_pydantic_R1_ratchet.py --update-baseline")
        print()
        print(f"Count: baseline={baseline_count} → current={current_count}")
        return 0  # NÃO bloqueia — sugere atualizar

    # Same count, no diff
    print(f"[T-07 R1 RATCHET] OK -- R1 count estável ({current_count} == baseline {baseline_count})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
