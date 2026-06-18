#!/usr/bin/env python3
"""Sensor H-6 — verifica que nenhum arquivo backend emite ui_action string fora da allowlist canônica.

Motivação (Bug H-6, 2026-06-18):
  Strings como navigate_page, start_job_wizard, suggest_pipeline_template, etc.
  foram encontradas emitidas por produtores backend mas não estão em
  _ACTIONABLE_TOOL_UI_ACTIONS. O browser descarta silenciosamente a diretiva
  (string mismatch): agente diz navegar/abrir modal mas nada acontece na UI.

Fonte de verdade:
  app/orchestrator/execution/agentic_loop.py → _ACTIONABLE_TOOL_UI_ACTIONS

Padrões detectados (Python/YAML/JSON):
  - ui_action="XXX" ou ui_action: "XXX" onde XXX não está na allowlist
  - "ui_action": "XXX" (JSON dict inline)

Uso:
  python scripts/check_ui_action_canonical_strings.py           # exit 1 se violations
  python scripts/check_ui_action_canonical_strings.py --warn    # exit 0 sempre (warn only)
  python scripts/check_ui_action_canonical_strings.py --baseline N  # exit 1 se > N violations

Exit 0 → OK (baseline limpo ou --warn)
Exit 1 → violations encontradas
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent

# Allowlist canônica — single source of truth em agentic_loop.py
# Atualizar aqui SE e SOMENTE SE _ACTIONABLE_TOOL_UI_ACTIONS for atualizado lá.
CANONICAL_UI_ACTIONS: frozenset[str] = frozenset({
    "navigate_to",
    "open_modal",
    "close_modal",
    "open_offer_review",
    "wizard_step",
    "open_panel",
    "close_panel",
    "scroll_to",
    "settings_open_tab",
    "open_communication_modal",
    "open_schedule_modal",
    "open_screening_modal",
    "apply_table_state",
    "select_rows",
    "bulk_execute",
    "start_wizard_seeded",
})

# Padrões para detectar ui_action string literal em código
PATTERNS: list[re.Pattern] = [
    # Python/JSON: "ui_action": "value" or ui_action="value"
    re.compile(r"""["']?ui_action["']?\s*[:=]\s*["']([a-z_]+)["']"""),
    # YAML block: ui_action: value (sem aspas)
    re.compile(r"""^[ \t]*ui_action:\s+([a-z_]+)\s*$""", re.MULTILINE),
]

# Arquivos/pastas a ignorar (testes, sensor si mesmo, schemas genéricos)
SKIP_PATTERNS: list[str] = [
    "scripts/check_ui_action",   # este próprio sensor
    "scripts/check_ui_action_sync",
    "tests/",
    "__pycache__",
    ".pyc",
    "agentic_loop.py",           # fonte de verdade — define a allowlist
    "ws_message_schemas.py",     # schema genérico com type union
]


def should_skip(path: Path) -> bool:
    path_str = str(path)
    return any(skip in path_str for skip in SKIP_PATTERNS)


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Retorna lista de (linha, string_encontrada, contexto) para violations."""
    violations: list[tuple[int, str, str]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return violations

    for pattern in PATTERNS:
        for m in pattern.finditer(content):
            action_str = m.group(1)
            if not action_str:
                continue
            # Ignora placeholders de variável
            if "{" in action_str or action_str.startswith("$"):
                continue
            if action_str not in CANONICAL_UI_ACTIONS:
                line_no = content[: m.start()].count("\n") + 1
                ctx = m.group(0).strip()
                violations.append((line_no, action_str, ctx))

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn", action="store_true", help="warn-only mode (exit 0 sempre)")
    parser.add_argument("--baseline", type=int, default=0,
                        help="exit 1 somente se violations > baseline (default 0)")
    args = parser.parse_args()

    app_dir = WORKSPACE / "app"
    if not app_dir.exists():
        print(f"ERRO: diretório app/ não encontrado em {WORKSPACE}", file=sys.stderr)
        return 1

    extensions = ("*.py", "*.yaml", "*.yml")
    files: list[Path] = []
    for ext in extensions:
        files.extend(app_dir.rglob(ext))

    total_violations = 0
    violation_lines: list[str] = []

    for path in sorted(files):
        if should_skip(path):
            continue
        file_violations = scan_file(path)
        for line_no, action_str, ctx in file_violations:
            total_violations += 1
            rel = path.relative_to(WORKSPACE)
            violation_lines.append(
                f"  [{rel}:{line_no}] ui_action='{action_str}' NÃO está na allowlist canônica\n"
                f"    Contexto: {ctx}\n"
                f"    → Fix: substituir '{action_str}' por valor canônico OU adicionar à\n"
                f"      _ACTIONABLE_TOOL_UI_ACTIONS em agentic_loop.py + GLOBAL_UI_ACTION_TYPES em\n"
                f"      app/shared/websocket/ws_message_schemas.py + ui-action.ts no frontend.\n"
                f"    → Canônicas disponíveis: {sorted(CANONICAL_UI_ACTIONS)}\n"
            )

    if total_violations == 0:
        print(
            f"OK check_ui_action_canonical_strings: 0 violations "
            f"(allowlist com {len(CANONICAL_UI_ACTIONS)} actions canônicas)"
        )
        return 0

    mode = "WARN" if args.warn else "FAIL"
    over_baseline = total_violations > args.baseline

    print(
        f"{mode} check_ui_action_canonical_strings: {total_violations} violation(s) "
        f"(baseline={args.baseline}) — ui_action string(s) fora da allowlist canônica\n"
    )
    print("\n".join(violation_lines))
    print(
        "IMPORTANTE: ui_action strings inválidas são descartadas SILENCIOSAMENTE pelo browser.\n"
        "O agente emite a diretiva mas a navegação/modal/ação nunca acontece (Bug H-6).\n"
        "Corrigir SEMPRE no produtor (arquivo que emite ui_action), não no consumidor.\n"
        "Para adicionar nova action: atualizar agentic_loop.py + ws_message_schemas.py + ui-action.ts"
    )

    if args.warn:
        return 0
    return 1 if over_baseline else 0


if __name__ == "__main__":
    sys.exit(main())
