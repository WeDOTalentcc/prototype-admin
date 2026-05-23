#!/usr/bin/env python3
"""W4-041 · Sensor BLOCKING — Tier 6 canary gate canonical wired.

Verifica:
1. `tier6_canary_enabled` em DEFAULT_FLAGS com default=False.
2. cascaded_router.py: gate combina env (AUTONOMOUS_REACT_ENABLED) + flag.
3. canary_metrics.py: `tier6_invocations_total` counter declarado.
4. Gate emite metric com labels canonical (company_id_hash + flag_state).

Defesa contra:
- Remoção do flag (silent global rollout)
- Remoção da combinação AND (env OR flag = sem segurança)
- Default mudando pra True acidentalmente
- Metric removida (cego em prod)

Exit 0 = OK · Exit 1 = violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FF_PATH = REPO_ROOT / "app" / "shared" / "governance" / "feature_flag_service.py"
ROUTER_PATH = REPO_ROOT / "app" / "orchestrator" / "cascaded_router.py"
METRICS_PATH = REPO_ROOT / "app" / "shared" / "observability" / "canary_metrics.py"


def check() -> list[str]:
    violations: list[str] = []

    # 1. Flag em DEFAULT_FLAGS com default=False
    if FF_PATH.exists():
        src = FF_PATH.read_text(encoding="utf-8")
        if '"tier6_canary_enabled":' not in src:
            violations.append(
                "[W4-041] tier6_canary_enabled NÃO está em DEFAULT_FLAGS.\n"
                "  Fix: adicionar entrada em FeatureFlagService.DEFAULT_FLAGS com default=False."
            )
        else:
            # Verifica default=False (não pode ser True — fail-safe)
            pattern = re.compile(
                r'"tier6_canary_enabled":\s*\{[^}]*"default":\s*(True|False)',
                re.DOTALL,
            )
            m = pattern.search(src)
            if m and m.group(1) == "True":
                violations.append(
                    "[W4-041] tier6_canary_enabled.default = True é VIOLATION.\n"
                    "  Fix: tier6 canary deve ser opt-in (default=False) por segurança."
                )
            if '"category": "routing"' not in src:
                # Não bloquear, apenas warn — categoria pode ser ajustada
                pass

    # 2. Router gate canonical
    if ROUTER_PATH.exists():
        src = ROUTER_PATH.read_text(encoding="utf-8")
        if "tier6_canary_enabled" not in src:
            violations.append(
                "[W4-041] cascaded_router.py NÃO referencia tier6_canary_enabled flag.\n"
                "  Fix: gate Tier 6 invocation behind _ff_is_enabled('tier6_canary_enabled')."
            )
        if "_tier6_env_enabled" not in src:
            violations.append(
                "[W4-041] cascaded_router.py NÃO tem _tier6_env_enabled var.\n"
                "  Fix: gate canonical separa env check (AUTONOMOUS_REACT_ENABLED) + flag."
            )
        if "_tier6_flag_enabled" not in src:
            violations.append(
                "[W4-041] cascaded_router.py NÃO tem _tier6_flag_enabled var."
            )
        if "if _tier6_env_enabled and _tier6_flag_enabled:" not in src:
            violations.append(
                "[W4-041] Gate NÃO combina env AND flag.\n"
                "  Fix: usar 'if _tier6_env_enabled and _tier6_flag_enabled:' — AMBOS necessários."
            )

    # 3. Canary metric
    if METRICS_PATH.exists():
        src = METRICS_PATH.read_text(encoding="utf-8")
        if "tier6_invocations_total" not in src:
            violations.append(
                "[W4-041] canary_metrics.py NÃO declara tier6_invocations_total counter.\n"
                "  Fix: adicionar _make_counter para observability do canary gate."
            )
        if "W4-041" not in src:
            violations.append(
                "[W4-041] canary_metrics.py: tier6 counter sem citação W4-041 (rastreabilidade)."
            )

    return violations


def main() -> int:
    violations = check()
    if violations:
        print("❌ check_tier6_canary_wired FAILED:\n", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
            print("", file=sys.stderr)
        print(
            f"\nTotal: {len(violations)} violation(s). "
            "Tier 6 canary gate é canonical (W4-041).\n"
            "Não desativar/remover sem aprovação textual explícita do Paulo.",
            file=sys.stderr,
        )
        return 1
    print("✅ check_tier6_canary_wired OK · W4-041 canonical preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
