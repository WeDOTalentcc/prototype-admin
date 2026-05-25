#!/usr/bin/env python3
"""Banir string LIA hardcoded + classe wedo-cyan + gradient cyan->violet em pages-agent-studio/.

Justificativa: decisao Paulo 2026-05-25 white-label - nome assistente
configuravel per-tenant via AiPersona. Studio e onde cliente cria SEUS
agentes (identidade propria), nao da assistente da plataforma.

Fix: usar useAiPersona() hook para nome + neutros DS (Ink/Graphite) para cor.

Ref: memory project_white_label_ai_assistant, DESIGN.md "LIA Cyan Exclusivity Rule",
AGENT_STUDIO_IMPLEMENTATION_PLAN.md secao 3 (Sprint 2 REFORMULADO).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "src" / "components" / "pages-agent-studio"

# Allowlist: contexts where LIA literal is legitimate (technical references)
ALLOW_PATTERNS = [
    r"AiPersona",        # tipo TS
    r"useAiPersona",     # hook
    r"lia_persona",      # YAML path reference
    r"lia-text-",        # design token class (lia-text-primary, etc)
    r"lia-bg-",          # design token class
    r"lia-border-",      # design token class
    r"lia-btn-",         # design token class
    r"lia-md",           # shadow token
    r"lia-sm",           # shadow token
    r"lia-lg",           # shadow token
    r"// LIA-OK:",       # explicit allowlist marker
]
ALLOW_RE = re.compile("|".join(ALLOW_PATTERNS))


def main() -> int:
    violations: list[str] = []
    if not ROOT.exists():
        print(f"ERRO: diretorio nao existe: {ROOT}", file=sys.stderr)
        return 2

    for path in sorted(ROOT.rglob("*.tsx")):
        rel = path.relative_to(ROOT.parent.parent.parent).as_posix()
        if "__tests__" in rel or ".bak." in rel:
            continue
        # Sprint 2 scope: AgentStudioPage.tsx is hot file - skip with note
        if path.name == "AgentStudioPage.tsx":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if ALLOW_RE.search(line):
                # check residual LIA/Lia after stripping allowed tokens
                stripped = ALLOW_RE.sub("", line)
                if not re.search(r"\bLIA\b|\bLia\b", stripped):
                    # still check cyan/gradient (those are not allowlisted)
                    pass
                else:
                    violations.append(
                        f"{rel}:{i}: LIA/Lia hardcoded (apos allowlist). "
                        f"Fix: usar useAiPersona().persona?.name ou i18n com {{aiAssistant}}"
                    )
                # cyan/gradient continue below
            else:
                if re.search(r"\bLIA\b|\bLia\b", line):
                    violations.append(
                        f"{rel}:{i}: LIA/Lia hardcoded. "
                        f"Fix: usar useAiPersona().persona?.name ou i18n com {{aiAssistant}}"
                    )
            # Detecta wedo-cyan classes Tailwind (sempre violação no Studio)
            if re.search(r"\bwedo-cyan\b", line):
                violations.append(
                    f"{rel}:{i}: wedo-cyan no Studio. "
                    f"Fix: cyan e exclusiva da assistente quando age - usar token neutro DS "
                    f"(text-ink, text-graphite, bg-powder, border-mist)"
                )
            # Detecta gradient cyan->violet/purple (AI slop pattern)
            if re.search(r"from-(wedo-)?cyan[^\"]*to-(wedo-)?(purple|violet)", line):
                violations.append(
                    f"{rel}:{i}: gradient cyan->violet (AI slop). "
                    f"Fix: usar fundo neutro DS (bg-chalk, bg-powder, bg-card)"
                )

    if violations:
        for v in violations:
            print(v)
        print(
            f"\n{len(violations)} violations. "
            f"Canonical: white-label Studio (memory project_white_label_ai_assistant). "
            f"AgentStudioPage.tsx EXCLUIDO desta sprint (hot file - coordenacao futura)."
        )
        return 1
    print("OK: 0 violations no escopo Sprint 2 (AgentStudioPage.tsx excluido).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
