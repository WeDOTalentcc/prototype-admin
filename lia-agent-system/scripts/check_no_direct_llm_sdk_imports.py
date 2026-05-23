#!/usr/bin/env python3
"""
Sensor anti-regressão · W3-027 (2026-05-23)

Detecta imports DIRETOS de LLM SDKs (anthropic/openai/google.genai) fora
do path canonical `app/shared/providers/`. Pattern viola arquitetura de
factory canonical (`LLMProviderFactory` + `ProviderContainer`).

Pattern violação:
- `from anthropic import Anthropic` em domain/services/ (skipa factory)
- `from openai import OpenAI` direto
- `from google.genai import Client` direto

Pattern canonical:
- `from app.shared.providers.llm_factory import get_provider_for_tenant`
  + `container.get_primary()` → provider instance via factory

Mensagem PT-BR + fix sugerido em sintaxe exata.

Modo: WARN-ONLY (baseline 14 sites · BLOCKING após migration W3-027 full).
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = REPO_ROOT / "app"

# Path patterns que são LEGÍTIMOS pra ter SDK direto (canonical home)
EXEMPT_PREFIXES = (
    "app/shared/providers/",
    "app/shared/llm/",  # outros canonical paths
    "app/core/sentry.py",  # sentry isolated
)

# SDKs proibidos fora dos paths exempt
FORBIDDEN_MODULES = {
    "anthropic",
    "openai",
    "google.genai",
    "google.generativeai",
}


def find_violations() -> list[tuple[str, int, str]]:
    """Returns list of (relative_path, line_number, module_imported)."""
    violations: list[tuple[str, int, str]] = []
    for py_file in APP_DIR.rglob("*.py"):
        if "__pycache__" in py_file.parts:
            continue
        try:
            rel = py_file.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            continue
        # Skip exempt paths
        if any(rel.startswith(p) for p in EXEMPT_PREFIXES):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                # Match exact or prefix (google.genai.types etc.)
                for forbidden in FORBIDDEN_MODULES:
                    if mod == forbidden or mod.startswith(forbidden + "."):
                        violations.append((rel, node.lineno, mod))
                        break
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    for forbidden in FORBIDDEN_MODULES:
                        if name == forbidden or name.startswith(forbidden + "."):
                            violations.append((rel, node.lineno, name))
                            break

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="BLOCKING mode (default WARN-ONLY até migration W3-027 full).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Falha (exit 1) se violations > threshold. Ratchet pattern.",
    )
    args = parser.parse_args()

    violations = find_violations()

    if not violations:
        print("✅ Zero direct LLM SDK imports fora de canonical paths (W3-027)")
        return 0

    print(
        f"W3-027 direct LLM SDK imports · {len(violations)} site(s) fora do "
        f"factory canonical:",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    for rel, lineno, mod in violations[:20]:
        print(f"  ❌ {rel}:{lineno} · imports {mod}", file=sys.stderr)
    if len(violations) > 20:
        print(f"  ... +{len(violations) - 20} more", file=sys.stderr)
    print(file=sys.stderr)
    print(
        "FIX: migrar pra factory canonical:\n"
        "    from app.shared.providers.llm_factory import get_provider_for_tenant\n"
        "    container = get_provider_for_tenant(tenant_id=...)\n"
        "    provider = container.get_primary()\n"
        "    result = await provider.generate(prompt)",
        file=sys.stderr,
    )

    if args.threshold is not None and len(violations) > args.threshold:
        print(f"FAIL: {len(violations)} > threshold {args.threshold}", file=sys.stderr)
        return 1
    if args.strict:
        return 1
    print(
        f"⚠️  WARN-ONLY mode · {len(violations)} site(s) detected. "
        f"BLOCKING após Phase B (W3-027 full migration).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
