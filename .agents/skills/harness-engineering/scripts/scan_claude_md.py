#!/usr/bin/env python3
"""scan_claude_md.py — Audita PRESENCA dos guides do harness.

Varre o repositorio em busca dos arquivos de guide canonicos
(CLAUDE.md, AGENTS.md, .cursorrules, replit.md) e dos diretorios de
skills (.agents/skills, .local/skills, .claude/skills) e imprime um
resumo legivel apontando lacunas por componente do harness.

LIMITACAO IMPORTANTE: a checagem de cobertura dos 11 componentes e
HEURISTICA — apenas detecta presenca de palavras-chave nos guides
agregados, NAO faz validacao semantica de qualidade do conteudo. Use o
output como bootstrap para auditoria humana, nao como veredito final.
Para validacao semantica, ver references/audit-template.md (rodado por
um humano ou pela skill `code_review`).

Uso:
    python3 .agents/skills/harness-engineering/scripts/scan_claude_md.py [<repo_path>]

Sem dependencias externas (apenas stdlib).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

GUIDE_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    "replit.md",
    ".windsurfrules",
    ".github/copilot-instructions.md",
]

SKILL_DIRS = [
    ".agents/skills",
    ".local/skills",
    ".claude/skills",
]

# Componentes do harness e palavras-chave que indicam cobertura no
# arquivo de guide (heuristica de presenca, nao de qualidade).
HARNESS_COMPONENTS = {
    "1. Planning loop":      ["planning", "loop", "max_steps", "stop condition", "iteration"],
    "2. Tool layer":         ["tool", "schema", "pydantic", "json schema", "executor"],
    "3. Context management": ["context", "compact", "rag", "lost in the middle", "window"],
    "4. Memoria":            ["memory", "memoria", "filesystem", "checkpoint", "kv store"],
    "5. Sandbox":            ["sandbox", "isolation", "limit", "quota"],
    "6. State persistence":  ["state", "persist", "progress", "replay"],
    "7. Guides":              ["guide", "convention", "convencao", "naming", "regra"],
    "8. Sensors":             ["lint", "test", "teste", "ci", "pre-commit", "guard"],
    "9. Error handling":      ["error", "erro", "retry", "transient", "hitl", "exception"],
    "10. Guardrails":         ["permission", "guardrail", "policy", "tenant", "fairness"],
    "11. Serving layer":      ["audit", "trace", "observabil", "metric", "log"],
}


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(8):
        if (cur / ".git").exists() or (cur / "pyproject.toml").exists() or (cur / "package.json").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve()


SEARCH_ROOTS = ["", "lia-agent-system", "plataforma-lia", "ats-api-copia", "app", "backend", "frontend"]


def scan_guides(repo: Path) -> dict[str, Path | None]:
    found: dict[str, Path | None] = {}
    for rel in GUIDE_FILES:
        hit: Path | None = None
        for root in SEARCH_ROOTS:
            candidate = repo / root / rel if root else repo / rel
            if candidate.is_file():
                hit = candidate
                break
        found[rel] = hit
    return found


def scan_skills(repo: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for sd in SKILL_DIRS:
        path = repo / sd
        if not path.is_dir():
            out[sd] = []
            continue
        skills = []
        for entry in sorted(path.iterdir()):
            if entry.is_dir() and (entry / "SKILL.md").exists():
                skills.append(entry.name)
        out[sd] = skills
    return out


def coverage_for_components(text: str) -> dict[str, bool]:
    lower = text.lower()
    cov: dict[str, bool] = {}
    for component, keywords in HARNESS_COMPONENTS.items():
        cov[component] = any(kw in lower for kw in keywords)
    return cov


def print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main(argv: list[str]) -> int:
    raw = argv[1] if len(argv) > 1 else "."
    repo = find_repo_root(Path(raw))

    print(f"Harness scan — repo root: {repo}")

    print_section("Guide files (system of record do harness)")
    guides = scan_guides(repo)
    aggregated_text = ""
    any_guide = False
    for name, path in guides.items():
        if path is None:
            print(f"  [AUSENTE] {name}")
        else:
            any_guide = True
            try:
                txt = path.read_text(encoding="utf-8", errors="ignore")
            except OSError as exc:
                print(f"  [ERRO]    {name} — {exc}")
                continue
            print(f"  [OK]      {name}  ({len(txt.splitlines())} linhas)  {path.relative_to(repo)}")
            aggregated_text += "\n" + txt

    print_section("Skill directories")
    skills = scan_skills(repo)
    for sd, names in skills.items():
        if not names:
            print(f"  [VAZIO]   {sd}")
        else:
            print(f"  [OK]      {sd}  ({len(names)} skills)")
            for n in names:
                print(f"             - {n}")

    print_section("Cobertura heuristica dos 11 componentes do harness")
    if not any_guide:
        print("  Nenhum guide file encontrado — TODOS os componentes estao descobertos.")
        coverage = {c: False for c in HARNESS_COMPONENTS}
    else:
        coverage = coverage_for_components(aggregated_text)

    missing = []
    for comp, covered in coverage.items():
        flag = "OK     " if covered else "AUSENTE"
        print(f"  [{flag}] {comp}")
        if not covered:
            missing.append(comp)

    print_section("Resumo & proximos passos")
    if missing:
        print(f"  {len(missing)}/11 componentes do harness sem cobertura visivel nos guides:")
        for m in missing:
            print(f"    - {m}")
        print("  Acao: abrir auditoria formal usando references/audit-template.md")
        print("        e popular CLAUDE.md/AGENTS.md com guides faltantes.")
    else:
        print("  Cobertura heuristica completa nos 11 componentes.")
        print("  Acao: validar QUALIDADE dos guides (heuristica so detecta presenca de palavras-chave).")

    return 0 if any_guide else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
