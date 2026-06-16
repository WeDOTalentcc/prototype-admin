"""
CI lint — F11 (AUDIT 2026-04).

Bloqueia regressão do finding T2: o uso de `from langchain_core.tools import tool`
dentro de `app/domains/*/tools/` (ou `app/domains/*/agents/*_tool_registry.py`).

Política canônica: tools de domínio devem usar `@tool_handler(domain, ...)` do
módulo `app/shared/tool_handler.py`, que aplica fail-closed em company_id, audit
trail e module gating de forma uniforme.

Integração com CI:
    - Coberto pelo job de fitness `tests/fitness/test_audit_2026_04_finals.py`
      (`TestF11NoLangchainToolDecoratorRegression`), que executa este script
      como subprocess e valida exit-code 0.
    - Coberto pelo unit guard `tests/test_no_langchain_tool_decorator_guard.py`,
      que valida exit-code para diretório limpo vs. diretório violador (tmp).
    - **Gap conhecido:** o pre-commit (`.pre-commit-config.yaml`) usa o script
      legado `check_no_legacy_tool_decorator.py` (S7.3), que cobre
      `app/domains/*/tools/*.py` mas **não** cobre `*_tool_registry.py`.
      Este script (F11) é mais abrangente. Antes de remover o legado, migrar
      o hook do pre-commit para apontar aqui — ver
      `docs/audits/AUDIT_STATUS_REPORT_2026-04-FINAL.md` §F11.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_DOMAINS = _ROOT / "app" / "domains"

# Captura tanto `from langchain_core.tools import tool`
# quanto variantes com aliases ou múltiplos símbolos.
_FORBIDDEN = re.compile(
    r"^\s*from\s+langchain_core\.tools\s+import\s+(?:[\w\s,]*\b)?tool\b",
    re.MULTILINE,
)


def _scan() -> list[tuple[Path, int, str]]:
    violations: list[tuple[Path, int, str]] = []
    if not _DOMAINS.exists():
        return violations
    targets: list[Path] = []
    for tools_dir in _DOMAINS.glob("*/tools"):
        if tools_dir.is_dir():
            targets.extend(tools_dir.rglob("*.py"))
    for registry in _DOMAINS.glob("*/agents/*_tool_registry.py"):
        targets.append(registry)
    for path in targets:
        try:
            content = path.read_text(errors="ignore")
        except Exception:
            continue
        for match in _FORBIDDEN.finditer(content):
            line_no = content[: match.start()].count("\n") + 1
            violations.append((path.relative_to(_ROOT), line_no, match.group(0).strip()))
    return violations


def main() -> int:
    violations = _scan()
    if not violations:
        print("[F11] OK — no `from langchain_core.tools import tool` in app/domains/**/tools/")
        return 0
    print(
        f"[F11] FAIL — {len(violations)} regression(s) of T2 detected:",
        file=sys.stderr,
    )
    for path, line_no, snippet in violations:
        print(f"  {path}:{line_no}  ->  {snippet}", file=sys.stderr)
    print(
        "\nUse `from app.shared.tool_handler import tool_handler` instead.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
