#!/usr/bin/env python3
"""
Branch Map Theme Check — pre-commit sensor.

Bloqueia commits em branches genéricas (sprint accumulators) que tocam temas
não mapeados em docs/BRANCH_MAP.md. Mensagem otimizada para LLM consumir e
auto-corrigir.

Invocação:
  python3 scripts/check_branch_map.py <msg_file>

Onde <msg_file> é o path para .git/COMMIT_EDITMSG (passado automaticamente pelo
hook commit-msg).

Conexão:
  - .pre-commit-config.yaml (workspace root) ativa este script no stage commit-msg
  - Regra documentada em CLAUDE.md (Guide 1 + Guide 2 — Branch por tema)
  - Instalação: pip install pre-commit && pre-commit install --hook-type commit-msg
"""
import re
import subprocess
import sys
from pathlib import Path

# Branches que acumulam temas — qualquer tema não-mapeado nelas é bloqueado.
GENERIC_BRANCH_PATTERNS = [
    r"^feat/orch-migration-sprint-[A-Z0-9]+$",
    r"^main$",
    r"^master$",
    r"^develop$",
]

# Convenção de commit: tipo(tema): descrição
THEME_PATTERN = re.compile(
    r"^(?:feat|fix|docs|test|refactor|chore|perf|style|ci|build|revert)\(([^)]+)\):",
    re.MULTILINE,
)

# Prefixes neutros que não vinculam a tema específico — sempre permitidos.
NEUTRAL_THEMES = {
    "nav",        # docs(nav): atualização do BRANCH_MAP
    "deps",       # chore(deps): bump de dependência
    "ci",
    "infra",
    "harness",    # melhoria global de harness
    "docs",       # docs(docs): meta
}


def get_current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def is_generic_branch(branch: str) -> bool:
    return any(re.match(p, branch) for p in GENERIC_BRANCH_PATTERNS)


def find_branch_map() -> Path | None:
    candidates = [
        Path("docs/BRANCH_MAP.md"),
        Path("lia-agent-system/docs/BRANCH_MAP.md"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def main() -> int:
    if len(sys.argv) < 2:
        return 0  # invocado sem msg file — skip

    msg_file = Path(sys.argv[1])
    if not msg_file.exists():
        return 0
    message = msg_file.read_text(encoding="utf-8", errors="replace")

    # commits de merge: pular
    if message.lstrip().startswith("Merge "):
        return 0

    try:
        branch = get_current_branch()
    except subprocess.CalledProcessError:
        return 0  # detached HEAD ou outro estado anômalo — não bloquear

    if not is_generic_branch(branch):
        return 0  # branch já é específica de tema — passa

    match = THEME_PATTERN.search(message)
    if not match:
        # sem prefixo convencional — não tem como inferir tema; passa
        return 0

    theme = match.group(1).strip().lower()
    if theme in NEUTRAL_THEMES:
        return 0

    branch_map = find_branch_map()
    if not branch_map:
        print("warning: BRANCH_MAP.md nao encontrado — sensor desativado", file=sys.stderr)
        return 0

    map_content = branch_map.read_text(encoding="utf-8", errors="replace").lower()
    if theme in map_content:
        return 0  # tema mapeado, OK

    # tema NÃO mapeado em sprint genérica — bloquear com instrução para LLM
    print(f"""
[X] Commit bloqueado pelo Branch Map Theme Check

   Branch ativa     : {branch} (sprint generica que acumula temas)
   Tema do commit   : {theme}
   Status no mapa   : NAO mapeado em docs/BRANCH_MAP.md

   Diagnostico: a regra do CLAUDE.md (Guide 1 - Branch por tema) proibe
   commitar tema novo em branch de sprint generica. Acumulamos historico
   confuso, dificil de extrair em PRs separados depois.

   Como corrigir (escolha 1):

   (A) Crie branch propria para o tema:
       git checkout -b feat/{theme}-<descricao> [milestone/<base>]
       git cherry-pick <commit-anteriores-do-tema>  # se aplicavel
       git commit -m "feat({theme}): <descricao>"

   (B) Se este tema ja existe sob outro nome no BRANCH_MAP, use o nome canonico:
       git commit --amend  # editar prefixo

   (C) Se e um tema novo de verdade, adicione ao mapa antes:
       1. Editar docs/BRANCH_MAP.md:
          - Adicionar nova linha na tabela 'Indice rapido por tema'
          - Adicionar nova secao numerada apos a ultima
       2. git add docs/BRANCH_MAP.md
       3. git commit -m "docs(nav): BRANCH_MAP — adicionar tema {theme}"
       4. Recommit do trabalho original

   (D) Bypass intencional (apenas urgencia justificada):
       git commit --no-verify -m "..."

   Referencias:
   - docs/BRANCH_MAP.md (Indice rapido + Apendice A com templates)
   - lia-agent-system/CLAUDE.md (Guide 1 + Guide 2)
""", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
