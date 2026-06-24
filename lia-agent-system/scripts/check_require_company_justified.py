#!/usr/bin/env python3
"""Sensor canônico (AST): toda exceção ao fail-closed de tenant (`require_company=False`
em @tool_handler) DEVE ter justificativa inline auditável.

Origem: Sprint 3 enterprise-readiness (2026-06-08). `tool_handler` é fail-closed
por default (require_company=True → bloqueia a tool sem company_id, retornando
_TENANT_REQUIRED_RESPONSE). `require_company=False` desativa esse gate — só é
correto para tools genuinamente tenant-free (ontologia pura, market data externo)
ou agregação cross-tenant by-design (platform benchmarks). Cada uma dessas
exceções é uma decisão de segurança multi-tenancy (LGPD/SOX) que DEVE ser
documentada e auditável — não pode aparecer silenciosamente.

Este sensor NÃO detecta vazamento (distinguir agregação cross-tenant legítima de
vazamento via análise de SQL seria frágil); é um guard de GOVERNANÇA (feedforward):
força que toda exceção ao gate carregue uma justificativa inline (comentário `#`),
de modo que um revisor/auditor sempre veja POR QUE o tenant-gate foi desativado.

Uso:
    python3 scripts/check_require_company_justified.py             # blocking
    python3 scripts/check_require_company_justified.py --json
    python3 scripts/check_require_company_justified.py --warn-only

Baseline 2026-06-08: 0 violações (7 usos, todos justificados com `# kept: ...`).
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

DECORATOR = "tool_handler"
KW = "require_company"
SCAN_DIRS = ["app"]
IGNORE_SUFFIXES = ("tool_handler.py",)  # define o parâmetro, não o usa


def _has_require_company_false(call: ast.Call) -> bool:
    for kw in call.keywords:
        if kw.arg == KW and isinstance(kw.value, ast.Constant) and kw.value.value is False:
            return True
    return False


def _call_name(call: ast.Call) -> str:
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def scan_file(path: Path) -> list[dict]:
    violations: list[dict] = []
    try:
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return violations
    lines = src.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_name(node) != DECORATOR:
            continue
        if not _has_require_company_false(node):
            continue
        # Linhas que o decorator ocupa (1-indexed → slice 0-indexed)
        start = node.lineno
        end = getattr(node, "end_lineno", start) or start
        span = lines[start - 1:end]
        has_comment = any("#" in ln for ln in span)
        if not has_comment:
            violations.append({
                "file": str(path),
                "line": start,
                "reason": (
                    f"@{DECORATOR}(..., {KW}=False) sem justificativa inline — "
                    f"desativar o fail-closed de tenant exige documentar o porquê."
                ),
                "fix": (
                    f"adicione comentário na mesma linha, ex: "
                    f"`@{DECORATOR}(\"<domain>\", {KW}=False)  # kept: <razão tenant-free/cross-tenant>`"
                ),
            })
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--warn-only", action="store_true")
    parser.add_argument("--max-violations", type=int, default=0)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    violations: list[dict] = []
    for scan_dir in SCAN_DIRS:
        base = root / scan_dir
        if not base.exists():
            continue
        for py in base.rglob("*.py"):
            if "__pycache__" in py.parts or str(py).endswith(IGNORE_SUFFIXES):
                continue
            violations.extend(scan_file(py))

    if args.json:
        print(json.dumps({"total": len(violations), "violations": violations},
                         indent=2, ensure_ascii=False))
    else:
        for v in violations:
            rel = v["file"].replace(str(root) + "/", "")
            print(f"❌ [{rel}:{v['line']}] {v['reason']}")
            print(f"   → Fix: {v['fix']}")
        if not violations:
            print(f"✅ check_require_company_justified: 0 violações "
                  f"(toda exceção {KW}=False tem justificativa inline).")

    if args.warn_only:
        return 0
    if len(violations) > args.max_violations:
        print(f"\n❌ {len(violations)} exceção(ões) de tenant-gate sem justificativa "
              f"(max: {args.max_violations}).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
