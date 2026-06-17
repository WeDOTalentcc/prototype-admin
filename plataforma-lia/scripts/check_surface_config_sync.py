#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sensor S1: verifica que toda tool com card rico em UnifiedMessageList
tem entrada correspondente em SURFACE_CONFIG.
Saida otimizada para consumo de LLM.
Exit 0 sempre (warn-only). Use --blocking para exit 1 em violations.

Detecta dois padroes:
  1. meta?.toolName === "X"  (padrao antigo)
     meta?.type === "X_result" (padrao antigo variante)
  2. raw.type === "X_result" / block.type === "X_result" (padrao response_blocks novo)
     Mapeado via BLOCK_TYPE_TO_TOOL para o nome canonical no SURFACE_CONFIG.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Mapeamento block.type -> nome canonical em SURFACE_CONFIG
BLOCK_TYPE_TO_TOOL = {
    "search_candidates_result": "search_candidates",
    "list_jobs_result": "list_jobs",
    "calibration_result": "get_calibration",
}


def extract_surface_config_tools():
    f = ROOT / "src/lib/surface-config.ts"
    if not f.exists():
        print("ERR surface-config.ts nao encontrado")
        sys.exit(1)
    return set(re.findall(r"^  (\w+):", f.read_text(), re.MULTILINE))


def extract_wired_tools():
    f = ROOT / "src/components/unified-chat/UnifiedMessageList.tsx"
    if not f.exists():
        return []
    lines = f.read_text().split("\n")
    # wired: list of (tool_name, line_number, detection_method)
    wired = []
    seen_tools = set()

    for i, line in enumerate(lines, 1):
        # Padrao 1a: meta?.toolName === "X"
        m = re.search(r"meta\?\.toolName\s*===\s*[\"\x27](\w+)[\"\x27]", line)
        if m:
            tool = m.group(1)
            if tool not in seen_tools:
                wired.append((tool, i, "meta.toolName"))
                seen_tools.add(tool)

        # Padrao 1b: meta?.type === "X_result"
        m = re.search(r"meta\?\.type\s*===\s*[\"\x27](\w+)_result[\"\x27]", line)
        if m:
            tool = m.group(1)
            if tool not in seen_tools:
                wired.append((tool, i, "meta.type"))
                seen_tools.add(tool)

        # Padrao 2: raw.type === "X_result" ou block.type === "X_result"
        m = re.search(r"(?:raw|block)\s*\.\s*type\s*===\s*[\"\x27](\w+)[\"\x27]", line)
        if m:
            block_type = m.group(1)
            if block_type in BLOCK_TYPE_TO_TOOL:
                tool = BLOCK_TYPE_TO_TOOL[block_type]
                if tool not in seen_tools:
                    wired.append((tool, i, "response_blocks:{}".format(block_type)))
                    seen_tools.add(tool)

    return wired


def main():
    st = extract_surface_config_tools()
    wt = extract_wired_tools()
    violations = [(t, l, method) for t, l, method in wt if t not in st]

    if not violations:
        if not wt:
            print("OK surface-config sync: 0 tools wired (nenhuma wired ainda)")
        else:
            print("OK surface-config sync: {} tools wired, todos com entrada em SURFACE_CONFIG".format(len(wt)))
            for t, l, method in wt:
                print("  v {} (via {}, linha {})".format(t, method, l))
        sys.exit(0)

    print("FAIL {} tool(s) com card rico sem entrada no SURFACE_CONFIG:\n".format(len(violations)))
    for t, l, method in violations:
        print("  [UnifiedMessageList.tsx:{}] tool {} detectada via {} mas falta em SURFACE_CONFIG".format(l, t, method))
        print("  Fix: adicionar em src/lib/surface-config.ts:")
        print("    {}: {{ default_surface: panel, fallback_surface: inline-card, can_show_both: true, hitl: false }},".format(t))
        print()

    sys.exit(1 if "--blocking" in sys.argv else 0)


if __name__ == "__main__":
    main()
