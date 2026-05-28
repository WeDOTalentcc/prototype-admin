#!/usr/bin/env python3
"""Onda 2 F11 (2026-05-27) — sensor canonical de token cyan IA em surfaces agent.

Garante que componentes Studio surface presence (AgentsCard, JobAgentDot,
JobAgentBadge, CandidateTouchIndicator, AgentRunningBanner, pingos do
PipelineRail, pingos do PoolAgentsTab) NUNCA usem hex hardcoded #60BED1
ou variantes — sempre o token canonical:

  - bg-wedo-cyan, text-wedo-cyan, bg-wedo-cyan/15 etc (canonical IA accent)
  - lia-cyan alias (legacy compat)

Regra inquebrável CLAUDE.md (Tailwind tokens canonical):
  > "Cyan IA: bg-lia-cyan (#60BED1), text-lia-cyan para acentos"
  > "Pingo estático: <span className=\"w-1.5 h-1.5 rounded-full bg-lia-cyan\" />"

Modo: BLOCKING por default. Exit 1 quando viola.

Mensagem otimizada pra consumo de LLM:
  - aponta arquivo:linha + literal violado
  - sugere fix exato (token canonical equivalente)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src"

# Hex literals que representam o cyan canonical IA. Encontrar QUALQUER um
# deles em surfaces agent é violação.
FORBIDDEN_HEX = {
    "#60bed1",  # wedo-cyan canonical (lowercase compare)
    "#60bdd1",  # variante errada vista em commits antigos
    "#4da8bb",  # wedo-cyan-dark
}

# Patterns explicitos a alertar (style attrs com backgroundColor/color hex).
# Captura: backgroundColor: '#XXXXXX' OU color: "#XXXXXX" OU style="background:#XXX"
HEX_PATTERN = re.compile(r"#[0-9a-fA-F]{6}\b")

# Surfaces alvo: arquivos que tem "Agent" no nome (case-insensitive)
# OU tem path contendo agent/ OU sao os componentes canonical da Onda 2.
TARGET_FILE_PATTERNS = [
    # F2/F3 — AgentsCard + Banner
    "components/pages/tasks/AgentsCard.tsx",
    "components/pages/tasks/AgentRunningBanner.tsx",
    # F4 — JobAgentDot (Decidir > Vagas Ativas)
    "components/pages/tasks/JobAgentDot.tsx",
    # F5 — JobAgentBadge (header da vaga)
    "components/jobs/JobAgentBadge.tsx",
    # F8 — CandidateTouchIndicator
    "components/candidates/CandidateTouchIndicator.tsx",
    # Hooks: arquivos puros TS, mas check defensivo se hex aparecer
    "hooks/agents/use-active-agents-summary.ts",
    "hooks/agents/use-target-deployments.ts",
    "hooks/agents/use-candidate-touches.ts",
]

# Allowlist explícita: arquivos que DEFINEM os tokens podem ter o hex.
ALLOWLIST_FILES = {
    "tailwind.config.ts",
    "lib/design-tokens.ts",
    "lib/design-tokens.css",
}


def _norm(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Retorna lista de (line_no, raw_line, hex_found) violações."""
    violations: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return violations

    for line_no, line in enumerate(text.splitlines(), start=1):
        # Ignora linhas de comentário com hex (referência documental).
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        for m in HEX_PATTERN.finditer(line):
            hex_val = m.group(0).lower()
            if hex_val in FORBIDDEN_HEX:
                violations.append((line_no, line.strip(), m.group(0)))
    return violations


def main() -> int:
    if not ROOT.exists():
        print(f"[check_cyan_token_for_agents] src/ não encontrado em {ROOT}", file=sys.stderr)
        return 2

    files_to_check: list[Path] = []
    # 1) Arquivos canonical Onda 2 (sempre conferir).
    for rel in TARGET_FILE_PATTERNS:
        p = ROOT / rel
        if p.exists():
            files_to_check.append(p)

    # 2) Heurística broad: qualquer .tsx/.ts em src/ com "agent" no caminho
    #    (case-insensitive) ou no nome do arquivo.
    for ext in ("*.tsx", "*.ts"):
        for path in ROOT.rglob(ext):
            rel = _norm(path)
            if any(allow in rel for allow in ALLOWLIST_FILES):
                continue
            if "/__tests__/" in rel or rel.endswith(".test.tsx") or rel.endswith(".test.ts"):
                continue
            if "agent" in rel.lower() and path not in files_to_check:
                files_to_check.append(path)

    total = 0
    violators: dict[str, list[tuple[int, str, str]]] = {}
    for path in files_to_check:
        viol = scan_file(path)
        if viol:
            violators[_norm(path)] = viol
            total += len(viol)

    if total == 0:
        print("[check_cyan_token_for_agents] OK — 0 violations (token canonical respeitado em todas as surfaces agent).")
        return 0

    print(f"[check_cyan_token_for_agents] ❌ {total} violation(s) encontrada(s):\n")
    for rel, items in sorted(violators.items()):
        for line_no, raw, hex_found in items:
            print(f"  {rel}:{line_no}")
            print(f"    literal proibido: {hex_found}")
            print(f"    linha: {raw[:120]}")
            print(f"    → Fix: substituir por token Tailwind canonical (bg-wedo-cyan, text-wedo-cyan, bg-wedo-cyan/15, etc.). Vide tailwind.config.ts.")
            print()
    print(
        "Por que esse sensor existe: hex hardcoded escapa dark-mode + breakpoints + "
        "design-token refresh. Token canonical garante que cliente customizando AI persona "
        "consegue rebrand-ar consistente.\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
