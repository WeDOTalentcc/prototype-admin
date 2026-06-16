#!/usr/bin/env python3
"""
Sensor anti-regressão · W2-012 (2026-05-22)

Verifica LGPD Art 33 region pinning explícito em providers LLM:
- Claude: `anthropic-no-train: true` header declarado na construção do client
- OpenAI: `OpenAI-Beta: data-residency=v1` header
- Gemini: campo `_region` aceito no __init__ (default us-central1 OU None)
- TenantLLMConfig model expõe campo `region` (per-tenant opt-in)

Pattern violação:
- Provider class deleta default_headers (perde declaração LGPD)
- TenantLLMConfig perde campo region (volta a ser global-only)
- Header strings mudam (ex: "no_train" em vez de "no-train")

Mensagem em PT-BR + fix sugerido em sintaxe exata (harness CLAUDE.md).
Modo: BLOCKING por default · --warn-only opt-out.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_FILE = REPO_ROOT / "app/shared/providers/llm_claude.py"
OPENAI_FILE = REPO_ROOT / "app/shared/providers/llm_openai.py"
GEMINI_FILE = REPO_ROOT / "app/shared/providers/llm_gemini.py"
TENANT_MODEL = REPO_ROOT / "libs/models/lia_models/tenant_llm_config.py"


def check_claude_header() -> list[str]:
    errors: list[str] = []
    if not CLAUDE_FILE.exists():
        return [f"❌ {CLAUDE_FILE.relative_to(REPO_ROOT)} ausente"]
    src = CLAUDE_FILE.read_text()
    if "anthropic-no-train" not in src:
        errors.append(
            "❌ Claude provider NÃO declara `anthropic-no-train` header\n"
            f"   File: {CLAUDE_FILE.relative_to(REPO_ROOT)}\n"
            "   Risco LGPD Art 7 §II + Art 33: training opt-out não declarado\n"
            "   FIX em _get_client():\n"
            "       kwargs = {\"api_key\": api_key,\n"
            "                 \"default_headers\": {\"anthropic-no-train\": \"true\"}}\n"
            "       self._client = Anthropic(**kwargs)"
        )
    # Verifica que aceita region em __init__
    if "_region" not in src or "region" not in src:
        errors.append(
            "❌ Claude provider NÃO aceita parâmetro `region` no __init__\n"
            f"   File: {CLAUDE_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: adicionar `region: str | None = None` em __init__ +\n"
            "        `self._region = region`"
        )
    return errors


def check_openai_header() -> list[str]:
    errors: list[str] = []
    if not OPENAI_FILE.exists():
        return [f"❌ {OPENAI_FILE.relative_to(REPO_ROOT)} ausente"]
    src = OPENAI_FILE.read_text()
    if "data-residency=v1" not in src:
        errors.append(
            "❌ OpenAI provider NÃO declara `OpenAI-Beta: data-residency=v1` header\n"
            f"   File: {OPENAI_FILE.relative_to(REPO_ROOT)}\n"
            "   Risco LGPD Art 33: residência de dados não declarada\n"
            "   FIX em _get_client():\n"
            "       self._client = OpenAI(\n"
            "           api_key=api_key,\n"
            "           default_headers={\"OpenAI-Beta\": \"data-residency=v1\"},\n"
            "       )"
        )
    if "_region" not in src or "region" not in src:
        errors.append(
            "❌ OpenAI provider NÃO aceita parâmetro `region` no __init__\n"
            f"   File: {OPENAI_FILE.relative_to(REPO_ROOT)}\n"
            "   FIX: adicionar `region: str | None = None` em __init__"
        )
    return errors


def check_gemini_region() -> list[str]:
    errors: list[str] = []
    if not GEMINI_FILE.exists():
        return [f"❌ {GEMINI_FILE.relative_to(REPO_ROOT)} ausente"]
    src = GEMINI_FILE.read_text()
    if "_region" not in src:
        errors.append(
            "❌ Gemini provider NÃO aceita parâmetro `region` no __init__\n"
            f"   File: {GEMINI_FILE.relative_to(REPO_ROOT)}\n"
            "   Risco LGPD Art 33: região não passada para Vertex/genai SDK\n"
            "   FIX: adicionar `region: str | None = None` em __init__ +\n"
            "        `self._region = region or os.environ.get(\n"
            "             \"LIA_GEMINI_DEFAULT_REGION\", \"us-central1\")`"
        )
    return errors


def check_tenant_model_has_region() -> list[str]:
    errors: list[str] = []
    if not TENANT_MODEL.exists():
        return [f"❌ {TENANT_MODEL.relative_to(REPO_ROOT)} ausente"]
    src = TENANT_MODEL.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [f"❌ Syntax error em {TENANT_MODEL.name}: {exc}"]

    has_region_col = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "region":
                    # Verifica que o valor é uma Column(...) call
                    if isinstance(node.value, ast.Call):
                        func = node.value.func
                        func_name = (
                            func.id if isinstance(func, ast.Name)
                            else getattr(func, "attr", None)
                        )
                        if func_name == "Column":
                            has_region_col = True

    if not has_region_col:
        errors.append(
            "❌ TenantLLMConfig NÃO tem campo `region`\n"
            f"   File: {TENANT_MODEL.relative_to(REPO_ROOT)}\n"
            "   FIX: adicionar antes de `is_active`:\n"
            "       region = Column(String(50), nullable=True)\n"
            "       # LGPD Art 33: per-tenant region pinning (W2-012)\n"
            "       # NULL = usa default global do provider (us-central1 Gemini, etc.)"
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    errors.extend(check_claude_header())
    errors.extend(check_openai_header())
    errors.extend(check_gemini_region())
    errors.extend(check_tenant_model_has_region())

    if errors:
        print(
            f"W2-012 LGPD region pinning · {len(errors)} violation(s):",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
            print(file=sys.stderr)
        print("Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W2-012)",
              file=sys.stderr)

        if args.warn_only:
            print("⚠️  WARN-ONLY mode: exit 0 despite violations", file=sys.stderr)
            return 0
        return 1

    print("✅ LGPD Art 33 region pinning wired (W2-012) · 3 providers + 1 DB schema OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
