#!/usr/bin/env python3
"""Sensor anti-ghost de catálogo de tools (harness-engineering, Fase 0).

Garante que todo nome de tool referenciado na camada de GOVERNANÇA
(tool_permissions.yaml: scopes + restricted_tools; tool_registry_metadata.yaml)
existe como tool REAL declarada (`name="..."`) em algum arquivo sob app/.

Ghost = nome referenciado na governança mas NÃO declarado em lugar nenhum.
Um restricted_tool ghost = gate HITL inerte (não dispara). Um scope ghost =
o gate de escopo filtra por um nome que não existe.

Modelo: scripts/check_canonical_pages_sync.py + scripts/check_deprecated_rail_a_tools.py.
Default warn-only (exit 0); --blocking exit 1 quando ghosts > max-violations.

Uso:
    python3 scripts/check_capability_catalog_sync.py            # warn-only
    python3 scripts/check_capability_catalog_sync.py --blocking # CI
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path


def extract_declared_names(source: str) -> set[str]:
    """Nomes de tool declarados como `name="literal"` em chamadas de função."""
    names: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    names.add(kw.value.value)
    return names
