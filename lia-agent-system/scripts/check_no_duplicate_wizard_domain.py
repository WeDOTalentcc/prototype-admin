#!/usr/bin/env python3
"""
ADR canonical sensor — check_no_duplicate_wizard_domain (Onda 4.D4 do
PLAN_FIX_wizard_memory_loss 2026-05-10).

Falha CI quando uma mesma "business capability" (ex.: wizard de criacao
de vaga) tem implementacao paralela em mais de um domain.

Heuristica de classificacao (v2 — semantica nao filename):
1. Filtra arquivos `.py` em `app/domains/*` (tudo, exceto __init__.py).
2. Sinaliza arquivo como "wizard implementation" quando satisfaz TODOS:
   a) Importa `langgraph.graph` (compila state graph), OU define
      uma classe `*WizardGraph*` / `*WizardService*` / `*WizardAgent*`.
   b) Match em regex de "vacancy creation" keyword no source: title,
      vacancy, job_creation, criar_vaga, ou nome de stages como
      intake/jd_enrichment/wsi_questions.
3. Agrupa por `business_capability` ("vacancy_wizard").
4. Se >= 2 dominios distintos tem arquivos sinalizados, e violation.
5. Exempt via header `# CANONICAL-EXEMPT: <reason>` (similar a ADR-001).

Exit codes:
    0 — OK
    1 — Violacoes (default BLOCKING)
    2 — Erro

Disciplinas CLAUDE.md aplicadas:
- canonical-agent: enforce single source of truth.
- harness-engineering: sensor computacional BLOCKING (default).
- production-quality: previne classe de bug (state escrito num path,
  lido noutro — mesmo problema que motivou o P0-D na auditoria).
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path


EXEMPT_TAG = "CANONICAL-EXEMPT"

# Regex que marca arquivos que IMPLEMENTAM wizard de criacao de vaga
# (nao apenas mencionam). Combinacao de criterios estruturais + semanticos.
STRUCTURAL_HINTS = re.compile(
    r"(?:from\s+langgraph\.graph\s+import|StateGraph\s*\(|class\s+\w*Wizard\w*(?:Graph|Service|Agent)\b|WizardSessionService\b|JobCreationGraph\b|JobWizardGraph\b)",
    re.MULTILINE,
)
SEMANTIC_HINTS = re.compile(
    r"(?:parsed_title|parsed_seniority|jd_enrichment|wsi_questions|create_job_creation_graph|job_wizard_graph|build_job_wizard|wizard_session_service|wizard_react_agent|criar.?vaga|start_job_wizard)",
    re.MULTILINE | re.IGNORECASE,
)

# Marca de capability — facil de extender no futuro
CAPABILITIES: dict[str, dict[str, re.Pattern[str]]] = {
    "vacancy_wizard": {
        "structural": STRUCTURAL_HINTS,
        "semantic": SEMANTIC_HINTS,
    },
}


def _is_exempt(path: Path) -> tuple[bool, str]:
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4096]
    except OSError as exc:
        return False, f"<io error: {exc}>"
    if EXEMPT_TAG in head:
        match = re.search(rf"{EXEMPT_TAG}:?\s*([^\n]+)", head)
        reason = match.group(1).strip() if match else "<no reason>"
        return True, reason
    return False, ""


def _scan_domain(domain_dir: Path) -> dict[str, list[Path]]:
    """Para cada capability, retorna lista de arquivos sinalizados."""
    matches: dict[str, list[Path]] = defaultdict(list)
    for py in domain_dir.rglob("*.py"):
        if py.name.startswith("__"):
            continue
        if "/__pycache__/" in str(py):
            continue
        # ignora subdir tests/ se houver dentro do dominio
        if "/tests/" in str(py):
            continue
        try:
            content = py.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for capability, hints in CAPABILITIES.items():
            if hints["structural"].search(content) and hints["semantic"].search(content):
                matches[capability].append(py)
    return matches


def scan(root: Path) -> dict[str, dict[str, list[Path]]]:
    """Retorna {capability: {domain: [paths]}}."""
    grouped: dict[str, dict[str, list[Path]]] = defaultdict(lambda: defaultdict(list))
    if not root.exists():
        return grouped
    for domain_dir in sorted(root.iterdir()):
        if not domain_dir.is_dir():
            continue
        domain_matches = _scan_domain(domain_dir)
        for cap, paths in domain_matches.items():
            grouped[cap][domain_dir.name].extend(paths)
    return grouped


def report(grouped: dict[str, dict[str, list[Path]]], root: Path) -> int:
    cwd = Path.cwd()
    violations = 0
    print(f"[canonical-agent] Scanning {root.relative_to(cwd)}...")
    for cap, by_domain in sorted(grouped.items()):
        domains_real: dict[str, list[Path]] = {}
        domains_exempt: list[tuple[str, Path, str]] = []
        for domain, paths in by_domain.items():
            for p in paths:
                ok, reason = _is_exempt(p)
                if ok:
                    domains_exempt.append((domain, p, reason))
                else:
                    domains_real.setdefault(domain, []).append(p)
        if len(domains_real) > 1:
            violations += 1
            print(f"\n[VIOLATION] capability {cap!r} implementada em {len(domains_real)} dominios:")
            for d, paths in sorted(domains_real.items()):
                for p in paths:
                    rel = p.relative_to(cwd) if p.is_absolute() else p
                    print(f"  - {d}/: {rel}")
            print(f"  Fix: consolidar em um unico dominio canonical OU adicionar")
            print(f"       '# {EXEMPT_TAG}: <razao>' no header do arquivo secundario.")
            if domains_exempt:
                print(f"  Exempt (legitimas):")
                for d, p, reason in domains_exempt:
                    rel = p.relative_to(cwd) if p.is_absolute() else p
                    print(f"    - {d}/: {rel}  ({reason})")
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument(
        "paths",
        nargs="*",
        default=["app/domains"],
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Reporta mas retorna exit 0 (legacy ratchet mode).",
    )
    args = parser.parse_args(argv)

    cwd = Path.cwd()
    total_violations = 0
    for path_str in args.paths:
        root = (cwd / path_str).resolve()
        grouped = scan(root)
        total_violations += report(grouped, root)

    if total_violations == 0:
        print("\n[canonical-agent] OK — 0 violations.")
        return 0

    print(f"\n[canonical-agent] {total_violations} violation(s) detectada(s).")
    if args.warn_only:
        print("(--warn-only mode: returning 0)")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
