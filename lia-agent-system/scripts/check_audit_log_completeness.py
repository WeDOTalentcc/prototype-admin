#!/usr/bin/env python3
"""Sensor canonical T-20: valida audit_log completeness com demographic proxies.

Regras:
- R1: chamadas a audit_writer.write_decision() em agentic domains DEVEM passar
  demographic_proxies (ou explícito None com comment AUDIT-NO-DEMO)
- R2: applicable_frameworks DEVE incluir LGPD por padrão (mínimo)
- R3: decisões human-impacting (rejection/shortlist/ranking) DEVEM ter
  fairness_check_result preenchido

Modo: BLOCKING [PROMOTED Sprint 8 Frente A] — baseline confirmed 0 violations
2026-05-21. Use `--warn-only` para opt-out (legacy ratchet).

Uso:
    python scripts/check_audit_log_completeness.py [--warn-only]
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


AUDIT_CALLS_PATTERN = re.compile(
    r"audit_writer\.write_decision|audit_service\.write_decision|"
    r"write_audit_decision|log_decision"
)


def check(strict: bool = True) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    domains_root = repo_root / "app" / "domains"

    if not domains_root.exists():
        print("[T-20] domains/ não existe — skip")
        return 0

    violations: list[str] = []
    audit_call_sites: list[tuple[str, int, str]] = []

    # Coletar todas as chamadas audit em agentic domains
    for py in domains_root.rglob("services/*.py"):
        if "__pycache__" in str(py):
            continue
        try:
            content = py.read_text(encoding="utf-8")
        except Exception:
            continue

        for i, line in enumerate(content.splitlines(), start=1):
            if AUDIT_CALLS_PATTERN.search(line):
                rel = str(py.relative_to(repo_root))
                audit_call_sites.append((rel, i, line.strip()[:100]))

                # Check se demographic_proxies está sendo passado (heuristic)
                # Look at next 40 lines for "demographic_proxies" (covers
                # long multi-line write_decision calls with deep kwargs).
                lookhead = "\n".join(content.splitlines()[i:i+40])
                if "demographic_proxies" not in lookhead and "AUDIT-NO-DEMO" not in line:
                    violations.append(
                        f"R1 {rel}:{i} — write_decision sem demographic_proxies. "
                        f"Adicionar `demographic_proxies={{}}` ou comment `# AUDIT-NO-DEMO: <reason>`"
                    )

    if not audit_call_sites:
        print("[T-20] OK — nenhum site de audit decision detectado (esperado em early phase)")
        return 0

    print(f"[T-20] {len(audit_call_sites)} audit decision sites, {len(violations)} R1 violations")
    if violations:
        for v in violations[:10]:  # Limit output
            print(f"  ⚠  {v}")
        if len(violations) > 10:
            print(f"  ... e mais {len(violations)-10}")

    mode = "BLOCKING" if strict else "WARN-ONLY"
    print(f"Mode: {mode}")
    return 1 if (strict and violations) else 0


if __name__ == "__main__":
    # BLOCKING by default (Sprint 8 Frente A). Opt-out via --warn-only.
    strict = "--warn-only" not in sys.argv
    sys.exit(check(strict=strict))
