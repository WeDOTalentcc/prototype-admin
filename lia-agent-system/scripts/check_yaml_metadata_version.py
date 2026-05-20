#!/usr/bin/env python3
"""Sensor canonical: YAML metadata.version enforcement (ADR-028-v2 / T-05).

Rejeita qualquer YAML em app/prompts/**/*.yaml sem `metadata.version` field.

ADR-028 (Single Source of Truth Prompts) + ADR-028-v2 enforce versioning
obrigatorio para rollback granular + hot-reload compatibility (T-13 futuro).

Modo: BLOCKING (T-05 promoveu desde inicio).

Uso:
    python scripts/check_yaml_metadata_version.py [--warn-only]
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML nao instalado", file=sys.stderr)
    sys.exit(1)


YAML_DIR = "app/prompts"


def check(warn_only: bool = False) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    yaml_root = repo_root / YAML_DIR

    if not yaml_root.exists():
        print(f"[WARN] {YAML_DIR} nao existe (sensor skip)", file=sys.stderr)
        return 0

    yaml_files = sorted(
        list(yaml_root.rglob("*.yaml")) + list(yaml_root.rglob("*.yml"))
    )

    violations: list[tuple[str, str]] = []
    parse_errors: list[tuple[str, str]] = []

    for yf in yaml_files:
        try:
            data = yaml.safe_load(yf.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                violations.append((str(yf.relative_to(repo_root)), "root nao e dict"))
                continue
            meta = data.get("metadata")
            if not isinstance(meta, dict):
                violations.append(
                    (str(yf.relative_to(repo_root)), "sem secao metadata")
                )
                continue
            if "version" not in meta:
                violations.append(
                    (str(yf.relative_to(repo_root)), "metadata.version ausente")
                )
                continue
            version = meta["version"]
            if not isinstance(version, (str, int, float)):
                violations.append(
                    (
                        str(yf.relative_to(repo_root)),
                        f"metadata.version tipo invalido: {type(version).__name__}",
                    )
                )
        except Exception as e:
            parse_errors.append((str(yf.relative_to(repo_root)), str(e)[:80]))

    if violations or parse_errors:
        print(
            f"[ADR-028-v2] {len(violations)} violations + "
            f"{len(parse_errors)} parse errors em {YAML_DIR}:"
        )
        for path, reason in violations:
            print(f"  ❌ {path}: {reason}")
        for path, err in parse_errors:
            print(f"  ⚠  {path}: PARSE_ERROR {err}")
        print()
        print("CORRECAO canonical:")
        print('  Adicionar ao TOPO do YAML (apos comments):')
        print('    metadata:')
        print('      version: "1.0"')
        print()
        mode = "BLOCKING" if not warn_only else "WARN-ONLY"
        print(f"Mode: {mode}")
        return 1 if (not warn_only and (violations or parse_errors)) else 0

    print(
        f"[ADR-028-v2] OK -- {len(yaml_files)} YAMLs em {YAML_DIR} todos com metadata.version"
    )
    return 0


if __name__ == "__main__":
    warn = "--warn-only" in sys.argv
    sys.exit(check(warn_only=warn))
