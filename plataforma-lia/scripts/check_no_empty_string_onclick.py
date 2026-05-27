#!/usr/bin/env python3
"""Wave E Sensor 1 — Detecta IDs de string vazia em payloads de fetch/POST no Agent Studio.

Pattern anti-qualidade: passar `id: ""` ou `agentId=""` como prop quando um ID real
é esperado. Causa bugs silenciosos onde operações IA disparam sem contexto válido.

Detecta:
- Strings literais "" em propriedades que tipicamente são IDs (id, agentId, candidateId, jobId, etc.)
  dentro de payloads JSON.stringify() em chamadas fetch()
- Props JSX com nome de ID e valor "" (ex: <Component agentId="" />)

Honra marker: // SENSOR-EXEMPT: <reason>

Exit 0 = OK. Exit 1 = violations encontradas (BLOCKING).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src" / "components" / "pages-agent-studio"

# Padrões de ID em payloads JSON
ID_KEY_PATTERN = re.compile(
    r'(?:^|[,{]\s*)'           # início de objeto ou vírgula
    r'["\'"]?'                   # aspas opcionais
    r'(?:id|agentId|candidateId|jobId|agent_id|candidate_id|job_id|poolId|pool_id)'
    r'["\'"]?'
    r'\s*:\s*'
    r'""',                       # valor string vazia
    re.MULTILINE,
)

# Props JSX com ID vazio: agentId="" ou candidateId=""
JSX_ID_PROP_PATTERN = re.compile(
    r'\b(?:agentId|candidateId|jobId|agent_id|candidate_id|job_id|poolId|pool_id)'
    r'\s*=\s*""',
)

# Pattern dentro de JSON.stringify com ID vazio
STRINGIFY_ID_PATTERN = re.compile(
    r'JSON\.stringify\s*\(\s*\{[^}]*'
    r'(?:id|agentId|candidateId|jobId)\s*:\s*""'
    r'[^}]*\}',
    re.DOTALL,
)

EXEMPT_MARKER = "SENSOR-EXEMPT"


def check_file(path: Path) -> list[tuple[int, str]]:
    violations = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for lineno, line in enumerate(lines, 1):
        if EXEMPT_MARKER in line:
            continue
        # Verificar prop JSX com ID vazio
        if JSX_ID_PROP_PATTERN.search(line):
            violations.append((lineno, f"Prop JSX com ID vazio detectada: {line.strip()!r}"))
        # Verificar ID em payload literal
        if ID_KEY_PATTERN.search(line):
            violations.append((lineno, f"Propriedade de ID com string vazia em payload: {line.strip()!r}"))
    return violations


def main() -> int:
    blocking = "--warn-only" not in sys.argv
    all_violations: list[tuple[Path, int, str]] = []

    tsx_files = list(ROOT.rglob("*.tsx"))
    ts_files = list(ROOT.rglob("*.ts"))

    for path in sorted(tsx_files + ts_files):
        if "__tests__" in str(path) or ".next" in str(path):
            continue
        for lineno, msg in check_file(path):
            rel = path.relative_to(ROOT.parent.parent)
            all_violations.append((rel, lineno, msg))

    if not all_violations:
        print(f"[check_no_empty_string_onclick] ✅ 0 violations — baseline limpo.")
        return 0

    print(f"[check_no_empty_string_onclick] {'❌' if blocking else '⚠️'} {len(all_violations)} violation(s) encontrada(s):\n")
    for rel_path, lineno, msg in all_violations:
        print(f"  [{rel_path}:{lineno}] {msg}")
        print(f"    → Fix: substituir string vazia por ID real do estado/props, ou adicionar guard `if (!id) return`.")
        print()

    if blocking:
        print(f"[check_no_empty_string_onclick] BLOCKING — corrija violations antes de commitar.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
