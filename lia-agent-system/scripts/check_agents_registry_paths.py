#!/usr/bin/env python3
"""
Sensor canonical: cada class_path em app/agents_registry.yaml deve resolver
via importlib (módulo + classe existem).

Uso: python scripts/check_agents_registry_paths.py

Exit codes:
  0 — todos os class_path resolvem
  1 — algum class_path quebrou
  2 — registry não encontrado
"""
import importlib
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "app" / "agents_registry.yaml"

# Permitir resolver `app.*` quando rodado como script standalone
# (sem precisar configurar PYTHONPATH externo).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    if not REGISTRY.exists():
        print(f"FAIL: {REGISTRY} não encontrado", file=sys.stderr)
        return 2

    data = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    agents = data.get("agents", []) if isinstance(data, dict) else []

    failures = []
    checked = 0
    for cfg in agents:
        name = cfg.get("name", "?")
        class_path = cfg.get("class_path", "")
        enabled = cfg.get("enabled", True)
        if not enabled:
            continue
        checked += 1
        if not class_path:
            failures.append((name, "(sem class_path)"))
            continue
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            mod = importlib.import_module(module_path)
            getattr(mod, class_name)
        except (ImportError, AttributeError, ValueError) as exc:
            failures.append((name, f"{class_path} — {exc}"))

    if failures:
        print("class_paths inválidos em agents_registry.yaml:", file=sys.stderr)
        for name, reason in failures:
            print(f"  - {name}: {reason}", file=sys.stderr)
        print(
            "\nCorrigir antes do deploy. Para emergencial em prod, "
            "setar LIA_ALLOW_REGISTRY_DRIFT=1 (mas o registry ainda não carrega esses agents).",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {checked} class_paths em registry resolvem corretamente")
    return 0


if __name__ == "__main__":
    sys.exit(main())
