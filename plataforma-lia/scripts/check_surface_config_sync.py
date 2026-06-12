#!/usr/bin/env python3
"""
Sensor S1: verifica que toda tool com card rico em UnifiedMessageList
tem entrada correspondente em SURFACE_CONFIG.
Saida otimizada para consumo de LLM.
Exit 0 sempre (warn-only). Use --blocking para exit 1 em violations.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


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
    wired = []
    for i, line in enumerate(lines, 1):
        m = re.search(r'meta\?\.toolName\s*===\s*["\x27](\w+)["\x27]', line)
        if m:
            wired.append((m.group(1), i))
        m = re.search(r'meta\?\.type\s*===\s*["\x27](\w+)_result["\x27]', line)
        if m:
            wired.append((m.group(1), i))
    return wired


def main():
    st = extract_surface_config_tools()
    wt = extract_wired_tools()
    v = [(t, l) for t, l in wt if t not in st]

    if not v:
        suffix = ", todos com entrada em SURFACE_CONFIG" if wt else " (nenhuma wired ainda)"
        print("OK surface-config sync: {} tools wired{}".format(len(wt), suffix))
        sys.exit(0)

    print("FAIL {} tool(s) com card rico sem entrada no SURFACE_CONFIG:\n".format(len(v)))
    for t, l in v:
        print("  [UnifiedMessageList.tsx:{}] tool '{}' tem card rico mas falta em SURFACE_CONFIG".format(l, t))
        print("  Fix: adicionar em src/lib/surface-config.ts:")
        print("    {}: {{ default_surface: 'panel', fallback_surface: 'inline-card', can_show_both: true, hitl: false }},".format(t))
        print()

    sys.exit(1 if "--blocking" in sys.argv else 0)


if __name__ == "__main__":
    main()
