#!/usr/bin/env python3
"""
Sensor G-GOV: verifica contratos de governanca em tool registries.

Regras:
  GOV-1: touches_pii=True -> pii_output_fields deve ser declarado
  GOV-2: affects_candidate_decision=True -> lgpd_legal_basis deve ser declarado (LGPD Art.20)
  GOV-3: "delete" em side_effects -> requires_human_review=True deve ser declarado

Exit: 0 = clean, 1 = violacoes encontradas.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOOL_DEF_PATTERN = re.compile(r"ToolDefinition\s*\([^)]*\)", re.DOTALL)


def _has(block: str, field: str) -> bool:
    return bool(re.search(rf"\b{re.escape(field)}\s*=", block))


def _is_true(block: str, field: str) -> bool:
    return bool(re.search(rf"\b{re.escape(field)}\s*=\s*True", block))


def _has_delete(block: str) -> bool:
    return '"delete"' in block or "'delete'" in block


def check_file(py_file: Path, root: Path) -> list[str]:
    rel = py_file.relative_to(root).as_posix()
    try:
        source = py_file.read_text(encoding="utf-8")
    except Exception:
        return []

    violations: list[str] = []
    for match in TOOL_DEF_PATTERN.finditer(source):
        block = match.group()
        lineno = source[: match.start()].count("\n") + 1
        name_m = re.search(r"name\s*=\s*[\x27\x22]([^\x27\x22]+)", block)
        tool_name = name_m.group(1) if name_m else "?"

        # GOV-1
        if _is_true(block, "touches_pii") and not _has(block, "pii_output_fields"):
            violations.append(
                f"  GOV-1 {rel}:{lineno}: tool={tool_name!r} "
                "touches_pii=True mas pii_output_fields nao declarado"
            )

        # GOV-2
        if _is_true(block, "affects_candidate_decision") and not _has(block, "lgpd_legal_basis"):
            violations.append(
                f"  GOV-2 {rel}:{lineno}: tool={tool_name!r} "
                "affects_candidate_decision=True mas lgpd_legal_basis nao declarado (LGPD Art.20)"
            )

        # GOV-3
        if _has_delete(block) and not _is_true(block, "requires_human_review"):
            violations.append(
                f"  GOV-3 {rel}:{lineno}: tool={tool_name!r} "
                'side_effects inclui "delete" mas requires_human_review=True ausente'
            )

    return violations


def main() -> int:
    violations: list[str] = []
    for py_file in ROOT.rglob("*tool_registry*.py"):
        rel = py_file.relative_to(ROOT).as_posix()
        if "test" in rel:
            continue
        violations.extend(check_file(py_file, ROOT))

    if violations:
        print(f"FAIL [G-GOV] {len(violations)} violacao(es) de governanca:")
        print("\n".join(violations[:40]))
        if len(violations) > 40:
            print(f"  ... e mais {len(violations) - 40}")
        print()
        print("INSTRUCOES DE CORRECAO:")
        print("  GOV-1: pii_output_fields=['campo1', 'campo2'] — campos PII no resultado")
        print("  GOV-2: lgpd_legal_basis='LEGITIMATE_INTEREST'  — base legal para Art.20")
        print("         Opcoes: LEGITIMATE_INTEREST, CONSENT, CONTRACT, LEGAL_OBLIGATION")
        print("  GOV-3: requires_human_review=True — revisao humana antes de deleção")
        print("  Ref: libs/agents-core/lia_agents_core/tool_adapter.py (ToolContract)")
        return 1

    print("OK [G-GOV] — todos os ToolDefinition com PII/decisao/delete tem contratos corretos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
