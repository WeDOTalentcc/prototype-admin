#!/usr/bin/env python3
"""
Sensor anti-regressão · W3-027 (2026-05-23, v2 BLOCKING)

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

Inline exemption (linha-level):
- Adicionar `# W3-027-EXEMPT: <motivo>` na mesma linha do import
  para marcá-lo como legítimo (infra layer, tool_use forçado, etc.)
- O motivo é obrigatório — sentinela de qualidade.

Mensagem PT-BR + fix sugerido em sintaxe exata.

Modo: BLOCKING por default (W3-027 full migration completa 2026-05-23).
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
    "app/shared/providers/",  # factory canonical + provider implementations
    "app/shared/llm/",        # outros canonical paths (callbacks, etc.)
    "app/core/sentry.py",     # sentry isolated
    # W3-027 (2026-05-23): infra-layer files exempted — monkey-patchers e tenant-aware gateways
    "app/shared/llm_bootstrap.py",       # monkey-patches SDK constructors (infra floor)
    "app/shared/tenant_llm_context.py",  # tenant-aware client gateway functions
    # LLMService singleton — core orchestrator, usa google.genai.types (não client raw)
    # e gemini_native property necessita genai.Client para Replit AI Integration base_url
    "app/domains/ai/services/llm.py",
)

# SDKs proibidos fora dos paths exempt
FORBIDDEN_MODULES = {
    "anthropic",
    "openai",
    "google.genai",
    "google.generativeai",
}

EXEMPT_MARKER = "W3-027-EXEMPT"


def _line_has_exempt_marker(source_lines: list[str], lineno: int) -> bool:
    """Check if the source line at lineno has a W3-027-EXEMPT inline comment."""
    if 1 <= lineno <= len(source_lines):
        return EXEMPT_MARKER in source_lines[lineno - 1]
    return False


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
        # Skip exempt path prefixes
        if any(rel.startswith(p) for p in EXEMPT_PREFIXES):
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source)
            source_lines = source.splitlines()
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                # Match exact or prefix (google.genai.types etc.)
                for forbidden in FORBIDDEN_MODULES:
                    if mod == forbidden or mod.startswith(forbidden + "."):
                        if not _line_has_exempt_marker(source_lines, node.lineno):
                            violations.append((rel, node.lineno, mod))
                        break
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    for forbidden in FORBIDDEN_MODULES:
                        if name == forbidden or name.startswith(forbidden + "."):
                            if not _line_has_exempt_marker(source_lines, node.lineno):
                                violations.append((rel, node.lineno, name))
                            break

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="WARN-ONLY mode (não falha com exit 1). Padrão: BLOCKING.",
    )
    parser.add_argument(
        # Legacy alias: --strict foi o flag antigo de BLOCKING; agora BLOCKING é default
        "--strict",
        action="store_true",
        help="(deprecated alias — BLOCKING é agora o default)",
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
        print("✅ Zero direct LLM SDK imports fora de canonical paths (W3-027 BLOCKING)")
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
        "FIX A — migrar pra factory canonical:\n"
        "    from app.shared.providers.llm_factory import get_provider_for_tenant\n"
        "    container = get_provider_for_tenant(tenant_id=...)\n"
        "    provider = container.get_primary()\n"
        "    result = await provider.generate(prompt)\n"
        "\n"
        "FIX B — se o uso é legítimo (infra layer, tool_use forçado, test shim):\n"
        "    Adicionar # W3-027-EXEMPT: <motivo> na mesma linha do import.\n"
        "    Motivo obrigatório (ex: 'tool_choice forcing not in factory API').",
        file=sys.stderr,
    )

    if args.threshold is not None and len(violations) > args.threshold:
        print(f"FAIL: {len(violations)} > threshold {args.threshold}", file=sys.stderr)
        return 1
    if args.warn_only:
        print(
            f"⚠️  WARN-ONLY mode · {len(violations)} site(s) detected.",
            file=sys.stderr,
        )
        return 0
    # Default: BLOCKING
    print(
        f"❌ BLOCKING · {len(violations)} violation(s). "
        f"Fix antes de commitar (W3-027).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
