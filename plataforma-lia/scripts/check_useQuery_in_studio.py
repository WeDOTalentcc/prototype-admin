#!/usr/bin/env python3
"""Wave E Sensor 4 — Detecta useState+useEffect(fetch) anti-pattern em pages-agent-studio.

Regra canonical (Settings REGRA 1 — 2026-05-26): server data usa React Query (useQuery),
não useState+useEffect manual. O anti-pattern produz:
- Stale data sem invalidação
- Sem cache/dedup de requests
- Race conditions em concurrent renders

Detecta arquivos em pages-agent-studio que:
1. Usam useEffect com fetch/axios/api call
2. NÃO importam useQuery de @tanstack/react-query

Honra marker: // SENSOR-EXEMPT: <reason> na linha do useEffect

Exit 0 = OK. Exit 1 = violations (BLOCKING).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src" / "components" / "pages-agent-studio"

# Pattern: useEffect com fetch/api dentro
USEEFFECT_FETCH_RE = re.compile(
    r'useEffect\s*\(\s*(?:async\s*)?\(\s*\)\s*=>\s*\{'
    r'(?:(?!useEffect).)*?'  # conteúdo do useEffect
    r'(?:fetch\s*\(|axios\.|api\.|backendProxy\.|/api/)',
    re.DOTALL,
)

# Forma simplificada: linha com useEffect + fetch próximos (5 linhas)
USEEFFECT_LINE_RE = re.compile(r'\buseEffect\s*\(')
FETCH_INSIDE_RE = re.compile(r'\bfetch\s*\(\s*[`"\']|backendProxy\.|/api/backend-proxy')
USEQUERY_IMPORT_RE = re.compile(r'from\s+["\']@tanstack/react-query["\'].*\buseQuery\b')

EXEMPT_MARKER = "SENSOR-EXEMPT"


def file_has_useeffect_fetch(path: Path) -> list[tuple[int, str]]:
    """Retorna violations (lineno, snippet) se arquivo usa useEffect+fetch sem useQuery."""
    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    # Se tem useQuery importado, skip (padrão correto já adotado)
    if USEQUERY_IMPORT_RE.search(content):
        return []

    violations = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if EXEMPT_MARKER in line:
            i += 1
            continue
        if USEEFFECT_LINE_RE.search(line):
            # Verificar as próximas 15 linhas em busca de fetch
            window = "\n".join(lines[i: i + 15])
            if FETCH_INSIDE_RE.search(window):
                violations.append((i + 1, f"useEffect + fetch sem useQuery: {line.strip()!r}"))
        i += 1

    return violations


def main() -> int:
    blocking = "--warn-only" not in sys.argv
    all_violations: list[tuple[Path, int, str]] = []

    for path in sorted(ROOT.rglob("*.tsx")):
        if "__tests__" in str(path) or ".next" in str(path):
            continue
        for lineno, msg in file_has_useeffect_fetch(path):
            rel = path.relative_to(ROOT.parent.parent)
            all_violations.append((rel, lineno, msg))

    if not all_violations:
        print(f"[check_useQuery_in_studio] ✅ 0 violations — nenhum anti-pattern useState+useEffect(fetch) detectado.")
        return 0

    print(f"[check_useQuery_in_studio] {'❌' if blocking else '⚠️'} {len(all_violations)} violation(s):\n")
    for rel_path, lineno, msg in all_violations:
        print(f"  [{rel_path}:{lineno}] {msg}")
        print(f"    → Fix: substituir useState+useEffect(fetch) por:")
        print(f"      import {{ useQuery }} from '@tanstack/react-query'")
        print(f"      const {{ data, isLoading, error }} = useQuery({{")
        print(f"        queryKey: ['recurso', id],")
        print(f"        queryFn: () => fetch('/api/...').then(r => r.json()),")
        print(f"      }})")
        print(f"      Se o useEffect é para side effect (timer, subscription), adicionar // SENSOR-EXEMPT: <reason>")
        print()

    if blocking:
        print(f"[check_useQuery_in_studio] BLOCKING — corrija antes de commitar.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
