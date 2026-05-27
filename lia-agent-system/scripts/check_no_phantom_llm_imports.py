#!/usr/bin/env python3
"""Sensor: detecta imports que não resolvem em runtime.

SSOT: app/shared/providers/llm_factory.py canonical functions são:
  - get_provider_for_tenant
  - get_provider_for_tenant_from_db
  - create_tracked_llm

Banir: `from app.shared.providers.llm_factory import get_llm` (símbolo fantasma).

Fix: substituir por create_tracked_llm(temperature=..., service_name=..., operation=...,
max_output_tokens=..., tenant_id=company_id) — vide commit 305a7e5af como ref.

Esses imports SEMPRE falham em runtime, mascarados por `except Exception` →
features degradadas silenciosamente (sempre no fallback).
"""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "app"
BANNED_IMPORTS = {
    "app.shared.providers.llm_factory": {"get_llm"},
}


def main() -> int:
    violations: list[str] = []
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(text, filename=str(path))
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module in BANNED_IMPORTS:
                    banned = BANNED_IMPORTS[node.module]
                    for alias in node.names:
                        if alias.name in banned:
                            rel = path.relative_to(ROOT.parent)
                            violations.append(
                                f"{rel}:{node.lineno}: import fantasma "
                                f"`from {node.module} import {alias.name}` — não existe em runtime.\n"
                                f"  → Fix: substituir por `create_tracked_llm(temperature=..., "
                                f"service_name=..., operation=..., max_output_tokens=..., tenant_id=company_id)` "
                                f"(vide commit 305a7e5af twin_inference_service.py como referência)."
                            )

    if violations:
        print("\n".join(violations))
        print(f"\n{len(violations)} phantom imports detected.")
        print("Esses imports SEMPRE falham em runtime, mascarados por `except Exception` "
              "→ features degradadas silenciosamente (sempre no fallback).")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
