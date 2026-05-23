#!/usr/bin/env python3
"""
Sensor anti-regressão · W3-020 (2026-05-23)

Detecta NOVAS instâncias hardcoded de persona strings (`Você é a LIA`,
`You are LIA`, `assistente de recrutamento`) fora de YAML canonical
`app/prompts/`.

Pattern violação:
- f-string com "Você é um especialista" em service files
- persona = "..." literal em código (não YAML loader)
- system_prompt = f"You are..."

Pattern canonical:
- from app.shared.prompts.system_prompt_builder import SystemPromptBuilder
- prompt = SystemPromptBuilder.build(domain=..., overrides={...})

Modo: WARN-ONLY (baseline existe, BLOCKING após Phase A 10 sites migrados).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "app"

# Paths exempt: YAML canonical home + tests + this sensor itself
EXEMPT_PREFIXES = (
    "app/prompts/",
    "app/shared/prompts/",  # SystemPromptBuilder + loader
    "tests/",
    "scripts/",
)

# Patterns de persona hardcoded
PERSONA_RE = re.compile(
    r"(?:You\s+are\s+(?:a\s+)?LIA|Você\s+é\s+(?:a\s+|um\s+|uma\s+)?(?:LIA|assistente|especialista|recrutadora?))",
    re.IGNORECASE,
)


def find_violations() -> list[tuple[str, int, str]]:
    violations: list[tuple[str, int, str]] = []
    for py_file in APP_DIR.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            rel = py_file.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            continue
        if any(rel.startswith(p) for p in EXEMPT_PREFIXES):
            continue
        try:
            src = py_file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        for line_idx, line in enumerate(src.split("\n"), 1):
            m = PERSONA_RE.search(line)
            if m:
                snippet = line.strip()[:80]
                violations.append((rel, line_idx, snippet))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--threshold", type=int, default=None)
    args = parser.parse_args()

    violations = find_violations()
    if not violations:
        print("✅ Zero hardcoded persona strings fora de YAML canonical")
        return 0

    print(
        f"W3-020 hardcoded persona · {len(violations)} site(s) (WARN-ONLY até Phase B):",
        file=sys.stderr,
    )
    for rel, lineno, snippet in violations[:15]:
        print(f"  ⚠️  {rel}:{lineno} · {snippet}...", file=sys.stderr)
    if len(violations) > 15:
        print(f"  ... +{len(violations) - 15} more", file=sys.stderr)
    print(file=sys.stderr)
    print(
        "FIX: migrar pra SystemPromptBuilder:\n"
        "    from app.shared.prompts.system_prompt_builder import SystemPromptBuilder\n"
        "    prompt = SystemPromptBuilder.build(domain=\"...\", overrides={...})",
        file=sys.stderr,
    )
    if args.threshold is not None and len(violations) > args.threshold:
        return 1
    if args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
