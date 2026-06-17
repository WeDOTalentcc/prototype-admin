#!/usr/bin/env python3
"""Wave E Sensor 3 — Detecta callbacks required em AgentStudioPage não passados pelo parent.

Pattern anti-qualidade: declarar callbacks como required no tipo TypeScript (sem `?`)
na interface AgentStudioPageProps mas o parent (AgentStudioClient) não os passar via JSX.
Resulta em botões no-op ou TypeErrors em runtime.

Verifica especificamente:
- AgentStudioPage.tsx: quais props de callback são required (sem `?`) em AgentStudioPageProps
- AgentStudioClient.tsx: quais callbacks são de fato passados no JSX <AgentStudioPage>

Reporta callbacks required que não são passados pelo parent.

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
CLIENT_FILE = (
    CLIENT_ROOT
    / "[locale]" / "(dashboard)" / "agent-studio"
    / "AgentStudioClient.tsx"
)

EXEMPT_MARKER = "SENSOR-EXEMPT"


def extract_props_interface(content: str) -> tuple[set[str], set[str]]:
    """
    Extrai callbacks required e optional da interface AgentStudioPageProps.
    Retorna (required_callbacks, optional_callbacks).
    """
    # Isolar o bloco da interface AgentStudioPageProps
    interface_match = re.search(
        r'interface\s+AgentStudioPageProps\s*\{([^}]*)\}',
        content,
        re.DOTALL,
    )
    if not interface_match:
        return set(), set()

    interface_body = interface_match.group(1)

    # Callbacks optional: `on<Name>?: (`
    optional = set(re.findall(r'\b(on[A-Z][A-Za-z]+)\?:', interface_body))

    # Callbacks required: `on<Name>:` SEM `?`
    # Usar negative lookbehind para garantir que não tem `?`
    all_callbacks = set(re.findall(r'\b(on[A-Z][A-Za-z]+)\s*:', interface_body))
    required = all_callbacks - optional

    return required, optional


def extract_passed_props(content: str) -> set[str]:
    """Extrai props efetivamente passadas no JSX <AgentStudioPage ...>."""
    # Encontrar o bloco JSX do AgentStudioPage
    jsx_match = re.search(
        r'<AgentStudioPage\b([^/]|/(?!>))*(?:/>|>)',
        content,
        re.DOTALL,
    )
    if not jsx_match:
        return set()

    jsx_block = jsx_match.group(0)
    # Extrair nomes de props passadas
    return set(re.findall(r'\b(on[A-Z][A-Za-z]+)\s*=\s*\{', jsx_block))


def main() -> int:
    blocking = "--warn-only" not in sys.argv

    if not PAGE_FILE.exists():
        print(f"[check_no_orphan_callbacks] ⚠️  {PAGE_FILE} não encontrado — pulando.")
        return 0

    page_content = PAGE_FILE.read_text(encoding="utf-8", errors="replace")

    # Verificar marker de isenção global
    if EXEMPT_MARKER in page_content:
        print(f"[check_no_orphan_callbacks] ✅ SENSOR-EXEMPT encontrado — pulando.")
        return 0

    required_callbacks, optional_callbacks = extract_props_interface(page_content)

    if not required_callbacks:
        print(f"[check_no_orphan_callbacks] ✅ Nenhum callback required em AgentStudioPageProps — OK.")
        return 0

    if not CLIENT_FILE.exists():
        print(f"[check_no_orphan_callbacks] ⚠️  AgentStudioClient.tsx não encontrado — pulando verificação.")
        return 0

    client_content = CLIENT_FILE.read_text(encoding="utf-8", errors="replace")
    passed_props = extract_passed_props(client_content)
    missing = required_callbacks - passed_props

    if not missing:
        print(f"[check_no_orphan_callbacks] ✅ 0 violations — todos {len(required_callbacks)} callback(s) required passados.")
        return 0

    print(f"[check_no_orphan_callbacks] {'❌' if blocking else '⚠️'} {len(missing)} callback(s) required não passado(s):\n")
    for cb in sorted(missing):
        print(f"  [AgentStudioClient.tsx] callback required '{cb}' não passado ao <AgentStudioPage>")
        print(f"    → Fix: adicionar {cb}={{(arg) => handleAction(arg)}} no JSX,")
        print(f"      ou tornar o callback opcional ({cb}?: ...) se realmente for opcional.")
        print()

    if blocking:
        print(f"[check_no_orphan_callbacks] BLOCKING — corrija antes de commitar.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
