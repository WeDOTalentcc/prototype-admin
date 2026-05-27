#!/usr/bin/env python3
"""Wave E Sensor 3 — Detecta callbacks required em AgentStudioPage não passados pelo parent.

Pattern anti-qualidade: declarar callbacks como required no tipo TypeScript (sem `?`)
mas o parent (AgentStudioClient) não os passar via JSX. Resulta em botões no-op ou
TypeErrors em runtime.

Verifica especificamente:
- AgentStudioPage.tsx: quais props de callback são required (sem `?`) na interface
- AgentStudioClient.tsx: quais callbacks são de fato passados no JSX <AgentStudioPage>

Reporta callbacks required que não são passados.

Honra marker: // SENSOR-EXEMPT: <reason>

Exit 0 = OK. Exit 1 = violations encontradas (BLOCKING).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

STUDIO_ROOT = (
    Path(__file__).resolve().parent.parent
    / "src" / "components" / "pages-agent-studio"
)
CLIENT_ROOT = (
    Path(__file__).resolve().parent.parent
    / "src" / "app"
)

PAGE_FILE = STUDIO_ROOT / "AgentStudioPage.tsx"
CLIENT_GLOB_PATTERN = "**/*AgentStudioClient*"

# Detecta props required (sem ?) no interface AgentStudioPageProps
# Pattern: `onXxx: (` ou `onXxx(` sem `?` antes do `:`
REQUIRED_CALLBACK_RE = re.compile(
    r'^\s+'
    r'(on[A-Z][A-Za-z]+)'   # prop name starting with "on"
    r'\s*:\s*'               # required (no ?)
    r'\(',                   # starts with function signature
    re.MULTILINE,
)

# Detecta props optional (com ?) — para excluir
OPTIONAL_CALLBACK_RE = re.compile(
    r'^\s+'
    r'(on[A-Z][A-Za-z]+)'
    r'\?'
    r'\s*:\s*',
    re.MULTILINE,
)

# Detecta callbacks passados no JSX <AgentStudioPage ...>
PASSED_CALLBACK_RE = re.compile(
    r'\b(on[A-Z][A-Za-z]+)\s*=\s*\{',
)

EXEMPT_MARKER = "SENSOR-EXEMPT"


def extract_required_callbacks(content: str) -> set[str]:
    """Extrai nomes de callbacks required da interface Props."""
    # Pegar opcional primeiro para excluir
    optional = set(OPTIONAL_CALLBACK_RE.findall(content))
    required = set(REQUIRED_CALLBACK_RE.findall(content))
    return required - optional


def extract_passed_callbacks(content: str) -> set[str]:
    """Extrai callbacks efetivamente passados via JSX."""
    return set(PASSED_CALLBACK_RE.findall(content))


def main() -> int:
    blocking = "--warn-only" not in sys.argv

    if not PAGE_FILE.exists():
        print(f"[check_no_orphan_callbacks] ⚠️  {PAGE_FILE} não encontrado — pulando.")
        return 0

    page_content = PAGE_FILE.read_text(encoding="utf-8", errors="replace")
    required_callbacks = extract_required_callbacks(page_content)

    if not required_callbacks:
        print(f"[check_no_orphan_callbacks] ✅ Nenhum callback required em AgentStudioPage — OK.")
        return 0

    # Encontrar todos os client files que renderizam AgentStudioPage
    client_files = list(CLIENT_ROOT.glob(CLIENT_GLOB_PATTERN))
    # Também verificar direto no app/agent-studio
    agent_studio_app = CLIENT_ROOT / "[locale]" / "(dashboard)" / "agent-studio"
    client_files += list(agent_studio_app.glob("*.tsx"))

    if not client_files:
        print(f"[check_no_orphan_callbacks] ⚠️  Nenhum AgentStudioClient encontrado — pulando verificação.")
        return 0

    all_violations: list[tuple[str, str]] = []

    for client_file in client_files:
        content = client_file.read_text(encoding="utf-8", errors="replace")
        # Apenas analisar arquivos que usam AgentStudioPage
        if "AgentStudioPage" not in content:
            continue

        passed = extract_passed_callbacks(content)
        missing = required_callbacks - passed

        for cb in sorted(missing):
            # Verificar se há marker de isenção na linha do callback
            if EXEMPT_MARKER not in content:
                all_violations.append((str(client_file.relative_to(CLIENT_ROOT.parent)), cb))

    if not all_violations:
        print(f"[check_no_orphan_callbacks] ✅ 0 violations — todos callbacks required passados.")
        return 0

    print(f"[check_no_orphan_callbacks] {'❌' if blocking else '⚠️'} {len(all_violations)} callback(s) required não passado(s):\n")
    for rel_path, cb in all_violations:
        print(f"  [{rel_path}] callback required '{cb}' não passado ao <AgentStudioPage>")
        print(f"    → Fix: adicionar {cb}={{(arg) => handleAction(arg)}} no JSX de AgentStudioPage,")
        print(f"      ou tornar o callback opcional ({cb}?: ...) se realmente for opcional.")
        print()

    if blocking:
        print(f"[check_no_orphan_callbacks] BLOCKING — corrija antes de commitar.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
