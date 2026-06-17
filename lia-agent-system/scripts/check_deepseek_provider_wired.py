#!/usr/bin/env python3
"""W2-011 · Sensor BLOCKING — DeepSeek provider canonical wired.

Verifica:
1. Provider class `llm_deepseek.py` existe + canonical interface.
2. `__init__.py` importa + registra `DeepSeekLLMProvider`.
3. `circuit_breaker.py` define `DEEPSEEK_CIRCUIT`.
4. `llm_config.py` /test endpoint tem branch deepseek.
5. `llm_config.py` /providers endpoint lista deepseek com opt_in_only.
6. Migration 182_deepseek_catalog.py existe.
7. Frontend `AI_PROVIDER_IDS` inclui "deepseek".

Exit 0 = OK · Exit 1 = violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLATAFORMA_ROOT = REPO_ROOT.parent / "plataforma-lia"


def check() -> list[str]:
    violations: list[str] = []

    # 1. Provider class
    provider_path = REPO_ROOT / "app" / "shared" / "providers" / "llm_deepseek.py"
    if not provider_path.exists():
        violations.append(
            f"[W2-011] Provider class ausente: {provider_path}\n"
            "  Fix: app/shared/providers/llm_deepseek.py deve existir com class DeepSeekLLMProvider."
        )
        return violations

    p_src = provider_path.read_text(encoding="utf-8")
    if "class DeepSeekLLMProvider(LLMProviderABC):" not in p_src:
        violations.append(
            "[W2-011] DeepSeekLLMProvider deve estender LLMProviderABC."
        )
    if '_provider_name = "deepseek"' not in p_src:
        violations.append('[W2-011] _provider_name deve ser "deepseek".')
    if 'DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"' not in p_src:
        violations.append('[W2-011] DEEPSEEK_BASE_URL constant ausente ou incorreto.')

    # 2. __init__.py registration
    init_path = REPO_ROOT / "app" / "shared" / "providers" / "__init__.py"
    if init_path.exists():
        i_src = init_path.read_text(encoding="utf-8")
        if "from .llm_deepseek import DeepSeekLLMProvider" not in i_src:
            violations.append(
                "[W2-011] providers/__init__.py NÃO importa DeepSeekLLMProvider.\n"
                "  Fix: adicionar 'from .llm_deepseek import DeepSeekLLMProvider'."
            )
        if "LLMProviderFactory.register(DeepSeekLLMProvider)" not in i_src:
            violations.append(
                "[W2-011] providers/__init__.py NÃO registra DeepSeekLLMProvider.\n"
                "  Fix: adicionar 'LLMProviderFactory.register(DeepSeekLLMProvider)'."
            )

    # 3. circuit breaker
    cb_path = REPO_ROOT / "app" / "shared" / "resilience" / "circuit_breaker.py"
    if cb_path.exists():
        cb_src = cb_path.read_text(encoding="utf-8")
        if "DEEPSEEK_CIRCUIT = CircuitBreaker(" not in cb_src:
            violations.append(
                "[W2-011] DEEPSEEK_CIRCUIT ausente em circuit_breaker.py.\n"
                "  Fix: declarar DEEPSEEK_CIRCUIT mirror de OPENAI_CIRCUIT."
            )
        if '"deepseek": DEEPSEEK_CIRCUIT' not in cb_src:
            violations.append(
                "[W2-011] DEEPSEEK_CIRCUIT não mapeado em provider→circuit dict."
            )

    # 4 + 5. llm_config.py
    cfg_path = REPO_ROOT / "app" / "api" / "v1" / "llm_config.py"
    if cfg_path.exists():
        cfg_src = cfg_path.read_text(encoding="utf-8")
        if 'elif request.provider == "deepseek":' not in cfg_src:
            violations.append(
                "[W2-011] /test endpoint NÃO tem branch deepseek.\n"
                "  Fix: adicionar 'elif request.provider == \"deepseek\":' em llm_config.py."
            )
        if '"id": "deepseek"' not in cfg_src:
            violations.append(
                "[W2-011] /providers endpoint NÃO lista deepseek.\n"
                "  Fix: adicionar entrada deepseek com models + opt_in_only flag."
            )
        if '"opt_in_only": True' not in cfg_src:
            violations.append(
                "[W2-011] entrada deepseek em /providers NÃO marca opt_in_only.\n"
                "  Fix: garantir 'opt_in_only': True na entrada deepseek (UI deve refletir)."
            )

    # 6. Migration 182
    mig_path = REPO_ROOT / "alembic" / "versions" / "182_deepseek_catalog.py"
    if not mig_path.exists():
        violations.append(
            f"[W2-011] Migration ausente: {mig_path}\n"
            "  Fix: 182_deepseek_catalog.py deve seed master template em integration_catalog_entries."
        )
    else:
        m_src = mig_path.read_text(encoding="utf-8")
        if 'revision = "182_deepseek_catalog"' not in m_src:
            violations.append('[W2-011] revision incorreta em migration 182.')
        if 'down_revision = "181_idempotency_keys"' not in m_src:
            violations.append('[W2-011] down_revision incorreta em migration 182.')

    # 7. Frontend
    drawer_path = (
        PLATAFORMA_ROOT
        / "src"
        / "components"
        / "settings"
        / "integrations"
        / "IntegrationDetailDrawer.tsx"
    )
    if drawer_path.exists():
        d_src = drawer_path.read_text(encoding="utf-8")
        pattern = re.compile(r'AI_PROVIDER_IDS\s*=\s*\[[^\]]*"deepseek"[^\]]*\]')
        if not pattern.search(d_src):
            violations.append(
                "[W2-011] Frontend AI_PROVIDER_IDS NÃO inclui 'deepseek'.\n"
                "  Fix: editar IntegrationDetailDrawer.tsx → "
                'AI_PROVIDER_IDS = ["gemini","claude","openai","deepseek"].'
            )

    return violations


def main() -> int:
    violations = check()
    if violations:
        print("❌ check_deepseek_provider_wired FAILED:\n", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
            print("", file=sys.stderr)
        print(
            f"\nTotal: {len(violations)} violation(s). "
            "DeepSeek provider é canonical opt-in (W2-011).\n"
            "Não desativar/remover sem aprovação textual explícita do Paulo.",
            file=sys.stderr,
        )
        return 1
    print("✅ check_deepseek_provider_wired OK · W2-011 canonical preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
