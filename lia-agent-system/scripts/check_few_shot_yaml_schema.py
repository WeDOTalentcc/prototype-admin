#!/usr/bin/env python3
"""W4-038 · Sensor — schema canonical para `few_shot_examples` em prompt YAMLs.

Walks `app/prompts/domains/*.yaml` + `app/prompts/tenants/*/domains/*.yaml`
e valida `few_shot_examples` section contra o schema canonical
documentado em `app/prompts/shared/few_shot_template.yaml`.

Validações:
- `id` unique within file (case-insensitive)
- `category` em CANONICAL_CATEGORIES enum
- `scenario`, `user_input`, `expected_response` REQUIRED string non-empty
- `demonstrates` opcional, mas se presente DEVE ser list[str]
- Total examples per file <= MAX_FEW_SHOT_PER_AGENT (15)

Modo warn-only por default (ratchet — baseline pode ter pre-existing drift).
Promote para `--blocking` quando baseline atingir 0.

Output otimizado para consumo LLM (mensagens em PT-BR com fix sugerido).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_ROOT = REPO_ROOT / "app" / "prompts"

import re as _re

# Categorias canonical são DOMAIN-SPECIFIC (40+ distintas em uso ativo).
# Sensor valida convenção naming (lowercase + underscore), não enum fechado.
# Único reservado: "auto_evolved" — mark FewShotAutoInserter para FIFO rotation.
CATEGORY_PATTERN = _re.compile(r"^[a-z][a-z0-9_]*$")
RESERVED_CATEGORIES = {"auto_evolved"}  # gerenciado pelo evolution service

REQUIRED_KEYS = {"id", "category", "scenario", "user_input", "expected_response"}
MAX_PER_FILE = 15

# Files to skip (templates, not actual prompts)
SKIP_FILES = {"few_shot_template.yaml"}


def find_yaml_files() -> list[Path]:
    files: list[Path] = []
    # Canonical domain prompts
    for p in (PROMPTS_ROOT / "domains").glob("*.yaml"):
        if p.name not in SKIP_FILES:
            files.append(p)
    # Per-tenant overrides
    tenants_root = PROMPTS_ROOT / "tenants"
    if tenants_root.exists():
        for p in tenants_root.glob("*/domains/*.yaml"):
            if p.name not in SKIP_FILES:
                files.append(p)
    return sorted(files)


def validate_file(path: Path) -> list[str]:
    """Return list of violation strings for this file."""
    violations: list[str] = []
    try:
        import yaml
    except ImportError:
        return [f"[{path}] yaml package not installed — cannot validate"]

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return [f"[{path}] YAML parse error: {e}"]

    if not isinstance(data, dict):
        return []  # Not a dict YAML — skip

    examples = data.get("few_shot_examples")
    if examples is None:
        return []  # No few_shot section — skip (not all YAMLs have it)

    if not isinstance(examples, list):
        return [
            f"[{path}] `few_shot_examples` MUST be a list, got {type(examples).__name__}.\n"
            "  Fix: estruturar como YAML list (- id: ...\\n  category: ...)."
        ]

    if len(examples) > MAX_PER_FILE:
        violations.append(
            f"[{path}] {len(examples)} examples exceeds MAX_PER_FILE={MAX_PER_FILE}.\n"
            "  Fix: remover entries antigas ou consolidar."
        )

    seen_ids: dict[str, int] = {}
    for idx, ex in enumerate(examples):
        prefix = f"[{path}#few_shot_examples[{idx}]]"
        if not isinstance(ex, dict):
            violations.append(
                f"{prefix} entry MUST be a dict, got {type(ex).__name__}."
            )
            continue

        missing = REQUIRED_KEYS - set(ex.keys())
        if missing:
            violations.append(
                f"{prefix} missing required keys: {sorted(missing)}.\n"
                f"  Schema: app/prompts/shared/few_shot_template.yaml"
            )

        ex_id = ex.get("id")
        if ex_id:
            ex_id_norm = str(ex_id).lower()
            if ex_id_norm in seen_ids:
                violations.append(
                    f"{prefix} duplicate id={ex_id!r} (also at index {seen_ids[ex_id_norm]}).\n"
                    f"  Fix: renomear pra id único dentro do file."
                )
            else:
                seen_ids[ex_id_norm] = idx

        category = ex.get("category")
        if category:
            if not isinstance(category, str):
                violations.append(
                    f"{prefix} `category` MUST be str, got {type(category).__name__}."
                )
            elif not CATEGORY_PATTERN.match(category):
                violations.append(
                    f"{prefix} `category` {category!r} viola convenção naming "
                    f"(lowercase + underscore + digits). Pattern: ^[a-z][a-z0-9_]*$.\n"
                    f"  Fix: renomear pra snake_case (ex: 'happy_path', 'pcd_adaptacao')."
                )

        for str_key in ("scenario", "user_input", "expected_response"):
            val = ex.get(str_key)
            if val is not None and (not isinstance(val, str) or not val.strip()):
                violations.append(
                    f"{prefix} `{str_key}` MUST be non-empty string."
                )

        demonstrates = ex.get("demonstrates")
        if demonstrates is not None:
            if not isinstance(demonstrates, list):
                violations.append(
                    f"{prefix} `demonstrates` MUST be a list[str], got {type(demonstrates).__name__}."
                )
            elif not all(isinstance(t, str) for t in demonstrates):
                violations.append(
                    f"{prefix} `demonstrates` items MUST all be str."
                )

    return violations


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="W4-038 · few_shot_examples YAML schema sensor"
    )
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="Exit 1 when violations found (default warn-only).",
    )
    args = parser.parse_args()

    all_violations: list[str] = []
    files = find_yaml_files()
    for path in files:
        all_violations.extend(validate_file(path))

    if all_violations:
        for v in all_violations:
            print(v, file=sys.stderr)
            print("", file=sys.stderr)
        print(
            f"\n⚠  check_few_shot_yaml_schema · {len(all_violations)} violation(s) "
            f"em {len(files)} files.\n"
            "Schema canonical: app/prompts/shared/few_shot_template.yaml\n"
            "CLI manual: scripts/manage_few_shots.py validate",
            file=sys.stderr,
        )
        if args.blocking:
            return 1
        print("(warn-only mode — exit 0)", file=sys.stderr)
        return 0

    print(
        f"✅ check_few_shot_yaml_schema OK · {len(files)} files clean "
        f"(W4-038 canonical preserved)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
