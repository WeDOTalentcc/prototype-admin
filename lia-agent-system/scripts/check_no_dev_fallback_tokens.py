#!/usr/bin/env python3
"""R-006 sensor canonical.

Detecta strings literais sugestivas de dev-fallback (dev-fallback-token,
test-token, demo-key, etc) em endpoints públicos sem gate _DEV_MODE
explícito num raio razoável (<=30 linhas antes da ocorrência).

Uso: python scripts/check_no_dev_fallback_tokens.py

Exit codes:
  0 — limpo
  1 — violations detectadas (CI block)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API_DIR = ROOT / "app" / "api" / "v1"

# Padrões suspeitos: tokens hardcoded que cheiram a dev/test/demo.
SUSPICIOUS_LITERALS = [
    r'"dev-fallback-token"',
    r'"test-token"',
    r'"demo-key"',
    r'"fake-jwt"',
    r'"dummy-secret"',
    r'"placeholder-bearer"',
]
PATTERN = re.compile("|".join(SUSPICIOUS_LITERALS))


def main() -> int:
    violations: list[str] = []
    if not API_DIR.exists():
        print(f"⚠ {API_DIR} não existe — nada a checar.", file=sys.stderr)
        return 0

    for f in sorted(API_DIR.glob("*.py")):
        try:
            text = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠ falhou ao ler {f}: {e}", file=sys.stderr)
            continue

        lines = text.splitlines()
        for i, line in enumerate(lines, 1):
            if PATTERN.search(line):
                # Heurística: se 0..30 linhas antes mencionam _DEV_MODE,
                # consideramos gated.
                ctx_start = max(0, i - 31)
                ctx = "\n".join(lines[ctx_start:i])
                gated = ("_DEV_MODE" in ctx) or ("if dev_mode" in ctx.lower())
                if not gated:
                    violations.append(
                        f"{f.relative_to(ROOT)}:{i}: {line.strip()[:100]}"
                    )

    if violations:
        print(
            "❌ Dev-fallback tokens em endpoints sem gate _DEV_MODE:",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(
            "\nUse pattern R-006: importar _DEV_MODE de "
            "app.middleware.auth_enforcement, raise HTTPException(503) em prod, "
            "usar fallback só em DEV.",
            file=sys.stderr,
        )
        return 1

    print("✓ Sem dev-fallback tokens não-gated detectados em app/api/v1/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
