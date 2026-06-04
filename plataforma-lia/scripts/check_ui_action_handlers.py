#!/usr/bin/env python3
"""Sensor anti-ghost-action (P0.2, 2026-06-04) — computacional.

Toda ui_action que o contrato BE->FE declara (src/lib/api/kanban-assistant.ts,
campo `ui_action?: ...`) DEVE ter handler no FE: ou esta em GLOBAL_UI_ACTION_TYPES
(src/types/ui-action.ts, tratada globalmente por useUIAction), ou aparece como
`case "X":` num handler page-specific. Acao declarada sem handler = ghost
(silenciosamente descartada) — mesma classe do lia_field_toggles ghost-setting.

Uso: python scripts/check_ui_action_handlers.py [--blocking]
Saida otimizada pra LLM: aponta a acao + onde registrar o fix.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SQ = chr(39)  # single quote, evita-lo no source-literal


def _contract_actions() -> set:
    f = SRC / "lib" / "api" / "kanban-assistant.ts"
    txt = f.read_text(encoding="utf-8")
    out = set()
    for line in txt.splitlines():
        if "ui_action?:" in line:
            out.update(re.findall(SQ + r"([a-z_]+)" + SQ, line))
    return out


def _global_actions() -> set:
    f = SRC / "types" / "ui-action.ts"
    txt = f.read_text(encoding="utf-8")
    m = re.search(r"GLOBAL_UI_ACTION_TYPES[^\[]*\[(.*?)\]", txt, re.DOTALL)
    if not m:
        return set()
    return set(re.findall(r'"([a-z_]+)"', m.group(1)))


def _page_handler_cases() -> set:
    out = set()
    for p in SRC.rglob("*.ts*"):
        sp = str(p)
        if "__tests__" in sp or "node_modules" in sp:
            continue
        try:
            txt = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if "ui_action" not in txt and "UIAction" not in txt and "unhandled" not in txt:
            continue
        # handler pode ser via switch-case OU comparacao de igualdade
        out.update(re.findall(r'case\s+["\']([a-z_]+)["\']\s*:', txt))
        out.update(re.findall(r'===\s*["\']([a-z_]+)["\']', txt))
        out.update(re.findall(r'["\']([a-z_]+)["\']\s*===', txt))
    return out


def main() -> int:
    contract = _contract_actions()
    known = _global_actions() | _page_handler_cases()
    ghosts = sorted(contract - known)
    if ghosts:
        print("[anti-ghost-action] acoes declaradas no contrato BE->FE SEM handler FE:")
        for a in ghosts:
            print("  - " + repr(a) + ": ghost (sera descartada em silencio).")
        print("  -> Fix: registre em GLOBAL_UI_ACTION_TYPES (src/types/ui-action.ts)")
        print("     + handler em useUIAction.ts, OU adicione case no handler page-specific.")
        if "--blocking" in sys.argv:
            return 1
    else:
        print("OK — " + str(len(contract)) + " acoes do contrato BE->FE tem handler FE (0 ghosts).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
