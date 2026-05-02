#!/usr/bin/env python3
"""
Sensor G-TOOLS: verifica que todo ToolDefinition em *_tool_registry.py
declara output_schema= (contrato Pydantic de output).

R-004 (Sprint 1) adicionou o campo output_schema a ToolDefinition e
wired em communication_tool_registry.py como exemplar. Este sensor
detecta registries que ainda nao declararam o campo.

Exit: 0 = clean, 1 = violacoes encontradas.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUTPUT_SCHEMA_PRESENT = re.compile(r"output_schema\s*=")
NAME_PATTERN = re.compile(r"name\s*=\s*[\x27\x22]([^\x27\x22]+)")


def extract_tool_definition_blocks(source: str) -> list[tuple[int, str]]:
    """
    Extract ToolDefinition(...) blocks using balanced parentheses tracking.
    Returns list of (lineno, block_text).
    Fixes: [^)]* regex stops at first ) inside nested calls/dicts.
    """
    blocks = []
    lines = source.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if "ToolDefinition(" in line:
            start_lineno = i + 1  # 1-based
            # Count parens to find block end
            depth = line.count("(") - line.count(")")
            block_lines = [line]
            j = i + 1
            while depth > 0 and j < len(lines):
                next_line = lines[j]
                depth += next_line.count("(") - next_line.count(")")
                block_lines.append(next_line)
                j += 1
            blocks.append((start_lineno, "\n".join(block_lines)))
            i = j
        else:
            i += 1
    return blocks


def main() -> int:
    violations: list[str] = []

    for py_file in ROOT.rglob("*tool_registry*.py"):
        rel = py_file.relative_to(ROOT).as_posix()
        if "test" in rel or "__pycache__" in rel:
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        for lineno, block in extract_tool_definition_blocks(source):
            if not OUTPUT_SCHEMA_PRESENT.search(block):
                name_m = NAME_PATTERN.search(block)
                tool_name = name_m.group(1) if name_m else "?"
                violations.append(f"  {rel}:{lineno}: tool={tool_name!r} sem output_schema")

    if violations:
        print(f"FAIL [G-TOOLS] {len(violations)} ToolDefinition(s) sem output_schema:")
        print("\n".join(violations[:30]))
        if len(violations) > 30:
            print(f"  ... e mais {len(violations) - 30}")
        print()
        print("INSTRUCAO DE CORRECAO:")
        print("  from lia_agents_core.tool_adapter import ToolOutput")
        print("  ToolDefinition(name=..., ..., output_schema=ToolOutput)")
        print("  Exemplar: app/domains/communication/agents/communication_tool_registry.py")
        print("  Ver DEBT-005 para plano de migracao completo.")
        return 1

    print("OK — todos os ToolDefinition declaram output_schema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
