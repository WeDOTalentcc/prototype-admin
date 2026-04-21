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
    # Relatorio humano (default — comportamento original):
    python3 .agents/skills/harness-engineering/scripts/scan_claude_md.py [<repo_path>]

    # Modo CI/pre-commit (regression gate contra baseline):
    python3 .agents/skills/harness-engineering/scripts/scan_claude_md.py --check [<repo_path>]

    # Atualiza o baseline (rode quando voce *intencionalmente* aceita o estado atual):
    python3 .agents/skills/harness-engineering/scripts/scan_claude_md.py --update-baseline [<repo_path>]

O baseline vive em `.agents/skills/harness-engineering/harness-baseline.json`.
`--check` falha (exit 1) se um guide do baseline desaparece OU se a cobertura
heuristica de algum dos 11 componentes regride. Mensagens de erro sao escritas
no formato LLM-friendly descrito na skill (instrucao de correcao embutida).

Sem dependencias externas (apenas stdlib).
"""

from __future__ import annotations

import json
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


BASELINE_REL_PATH = ".agents/skills/harness-engineering/harness-baseline.json"


def collect_state(repo: Path) -> dict:
    """Coleta o estado atual: guides presentes + componentes cobertos."""
    guides = scan_guides(repo)
    aggregated_text = ""
    present_guides = []
    for name, path in guides.items():
        if path is None:
            continue
        present_guides.append(name)
        try:
            aggregated_text += "\n" + path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            pass
    coverage = (
        coverage_for_components(aggregated_text) if aggregated_text else {c: False for c in HARNESS_COMPONENTS}
    )
    covered_components = sorted(c for c, ok in coverage.items() if ok)
    return {
        "present_guides": sorted(present_guides),
        "covered_components": covered_components,
    }


def load_baseline(repo: Path) -> dict | None:
    bp = repo / BASELINE_REL_PATH
    if not bp.is_file():
        return None
    try:
        return json.loads(bp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_baseline(repo: Path, state: dict) -> Path:
    bp = repo / BASELINE_REL_PATH
    bp.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "_comment": (
            "Snapshot do harness — usado por scan_claude_md.py --check para "
            "detectar regressao. Atualize SOMENTE quando voce intencionalmente "
            "aceita o novo estado (ex: removeu um guide deprecado de proposito). "
            "Para regenerar: python3 .agents/skills/harness-engineering/"
            "scripts/scan_claude_md.py --update-baseline"
        ),
        "required_guides": state["present_guides"],
        "required_covered_components": state["covered_components"],
    }
    bp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return bp


def run_check(repo: Path) -> int:
    """Modo CI: compara estado atual contra baseline e falha em regressao."""
    baseline = load_baseline(repo)
    state = collect_state(repo)

    if baseline is None:
        print(
            "ERROR: harness baseline ausente em "
            f"{BASELINE_REL_PATH} — sem snapshot, nao da pra detectar regressao.\n"
            "  Como corrigir: rode "
            "`python3 .agents/skills/harness-engineering/scripts/scan_claude_md.py "
            "--update-baseline` e commite o arquivo gerado.\n"
            "  Por que isso importa: a skill harness-engineering exige "
            "'nunca o mesmo erro duas vezes' — sem baseline, regressao de guide passa "
            "silenciosa pro merge."
        )
        return 1

    required_guides = set(baseline.get("required_guides", []))
    required_components = set(baseline.get("required_covered_components", []))
    present_guides = set(state["present_guides"])
    covered_components = set(state["covered_components"])

    missing_guides = sorted(required_guides - present_guides)
    lost_components = sorted(required_components - covered_components)

    if not missing_guides and not lost_components:
        print(
            f"OK: harness scan passou — {len(present_guides)} guide(s) presentes, "
            f"{len(covered_components)}/11 componentes cobertos (baseline respeitado)."
        )
        return 0

    # Mensagens de erro otimizadas para LLM (instrucao de correcao embutida).
    print("ERROR: harness regression detectada — guides ou cobertura cairam abaixo do baseline.\n")
    print(f"  Baseline: {BASELINE_REL_PATH}")
    print(f"  Skill de referencia: .agents/skills/harness-engineering/SKILL.md\n")

    if missing_guides:
        print("  [GUIDES AUSENTES] Os arquivos abaixo existiam no baseline e sumiram:")
        for g in missing_guides:
            print(
                f"    - {g} — restaure o arquivo (git restore HEAD -- {g}) OU, se a "
                f"remocao foi intencional, rode "
                f"`python3 .agents/skills/harness-engineering/scripts/scan_claude_md.py "
                f"--update-baseline` e commite o baseline atualizado junto com a remocao."
            )
        print()

    if lost_components:
        print(
            "  [COBERTURA REGREDIU] Componentes do harness que estavam cobertos pelos "
            "guides e nao estao mais (heuristica de palavras-chave):"
        )
        for c in lost_components:
            kws = ", ".join(HARNESS_COMPONENTS.get(c, ["(componente fora do catalogo atual)"])[:3])
            print(
                f"    - {c} — reintroduza nos guides (CLAUDE.md/AGENTS.md/replit.md) "
                f"uma secao mencionando termos como: {kws}. Ver SKILL.md secao "
                f"'Checklist dos 11 componentes'. Se a remocao foi intencional, "
                f"atualize o baseline."
            )
        print()

    print(
        "  Acao recomendada: NAO regenerar baseline cegamente. Primeiro decida se a "
        "regressao foi intencional (entao update-baseline) ou acidental (entao "
        "restaure o conteudo). 'Nunca o mesmo erro duas vezes' — Hashimoto harness."
    )
    return 1


def main(argv: list[str]) -> int:
    args = argv[1:]
    mode = "report"
    positional: list[str] = []
    for a in args:
        if a == "--check":
            mode = "check"
        elif a == "--update-baseline":
            mode = "update-baseline"
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("--"):
            print(f"ERROR: flag desconhecida: {a}\nUso: ver --help.")
            return 2
        else:
            positional.append(a)

    raw = positional[0] if positional else "."
    repo = find_repo_root(Path(raw))

    if mode == "check":
        return run_check(repo)
    if mode == "update-baseline":
        state = collect_state(repo)
        bp = write_baseline(repo, state)
        print(f"Baseline atualizado: {bp.relative_to(repo)}")
        print(f"  required_guides: {len(state['present_guides'])}")
        print(f"  required_covered_components: {len(state['covered_components'])}/11")
        print("  Commite o arquivo para que a regressao seja detectada nos PRs.")
        return 0

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
