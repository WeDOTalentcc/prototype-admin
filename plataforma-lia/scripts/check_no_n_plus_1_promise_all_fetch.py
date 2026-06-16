#!/usr/bin/env python3
"""Wave E Sensor 8 — Detecta .map(async ... fetch) N+1 pattern no frontend.

Anti-pattern: iterar uma lista e fazer fetch individual por item
resulta em N requests paralelos não controlados, saturando o servidor
e aumentando latência UI dramaticamente para listas grandes.

Detecta em plataforma-lia/src/:
- `.map(async (` seguido de `fetch(` ou `api.` na mesma linha ou próximas 5 linhas
- `.map((` com callback async que contém chamada de fetch

Solução canonical: usar endpoint batch (/api/backend-proxy/...?ids=a,b,c)
ou Promise.all com Array de IDs (não map individual).

Baseline 2026-05-27: 2 violations existentes (tech debt):
  - src/components/pages/useTasksInterviews.ts:34 — candidateIds.map(fetch)
  - src/components/pages/useTasksPageData.ts:40 — candidateIds.map(fetch)
  Ambos aguardam endpoint batch de candidatos (/candidates?ids=...).

Modo: BLOCKING para novas violations. Baseline existente marcado como known.

Honra marker: // SENSOR-EXEMPT: batch not available

Exit 0 = OK ou apenas violations do baseline. Exit 1 = violations NOVAS (BLOCKING).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src"

MAP_ASYNC_START_RE = re.compile(
    r'\.map\s*\(\s*async\s*(?:\(|[a-zA-Z_$])',
)

FETCH_CALL_RE = re.compile(
    r'\bfetch\s*\(|(?:await\s+)?api\.\w+\s*\(|backendProxy\.\w+\s*\(',
)

EXEMPT_MARKER = "SENSOR-EXEMPT"

# Baseline: violations existentes (tech debt conhecida)
KNOWN_BASELINE = {
    "useTasksInterviews.ts": [34],
    "useTasksPageData.ts": [40],
}


def check_file(path: Path) -> list[tuple[int, str]]:
    violations = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if EXEMPT_MARKER in line:
            i += 1
            continue

        if MAP_ASYNC_START_RE.search(line):
            window_end = min(i + 8, len(lines))
            window = "\n".join(lines[i:window_end])

            if EXEMPT_MARKER in window:
                i += 1
                continue

            if FETCH_CALL_RE.search(window):
                violations.append((
                    i + 1,
                    f"N+1 pattern: .map(async ...) com fetch detectado: {line.strip()!r}",
                ))
        i += 1

    return violations


def is_known_baseline(path: Path, lineno: int) -> bool:
    known_lines = KNOWN_BASELINE.get(path.name, [])
    return any(abs(lineno - kl) <= 3 for kl in known_lines)


def main() -> int:
    all_violations: list[tuple[Path, int, str]] = []
    new_violations: list[tuple[Path, int, str]] = []

    for ext in ("*.ts", "*.tsx"):
        for path in sorted(ROOT.rglob(ext)):
            if "__tests__" in str(path) or ".next" in str(path) or "node_modules" in str(path):
                continue
            for lineno, msg in check_file(path):
                rel = path.relative_to(ROOT.parent)
                all_violations.append((rel, lineno, msg))
                if not is_known_baseline(path, lineno):
                    new_violations.append((rel, lineno, msg))

    if not all_violations:
        print(f"[check_no_n_plus_1_promise_all_fetch] ✅ 0 violations — nenhum N+1 fetch pattern detectado.")
        return 0

    baseline_count = len(all_violations) - len(new_violations)
    print(f"[check_no_n_plus_1_promise_all_fetch] {'❌' if new_violations else '⚠️'} "
          f"{len(all_violations)} violation(s) totais ({baseline_count} baseline, {len(new_violations)} novas):\n")

    for rel_path, lineno, msg in all_violations:
        tag = "[baseline]" if is_known_baseline(Path(str(rel_path)), lineno) else "[NOVO ❌]"
        print(f"  {tag} [{rel_path}:{lineno}] {msg}")

    if new_violations:
        print(f"\n[check_no_n_plus_1_promise_all_fetch] ❌ {len(new_violations)} NOVA(S) violation(s) acima do baseline!")
        print(f"  → Fix: usar endpoint batch ou adicionar // SENSOR-EXEMPT: batch not available")
        print(f"    se batch endpoint ainda não existe (criar card Jira P2).")
        return 1

    print(f"\n[check_no_n_plus_1_promise_all_fetch] Baseline {baseline_count} violations aguardando endpoint batch.")
    print(f"  Nenhuma nova violation introduzida. ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
