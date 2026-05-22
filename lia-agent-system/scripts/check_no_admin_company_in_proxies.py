#!/usr/bin/env python3
"""
Sensor: detecta hardcoded `X-Company-ID: 'admin_company'` ou `X-User-Role: 'admin'`
em arquivos de proxy do Next.js (plataforma-lia/src/app/api/backend-proxy/**).

Pattern banido (Wave 4 audit 2026-05-22, commit 93bf8c4d4):
    function getAuthHeaders(): Record<string, string> {
      return {
        'X-Company-ID': 'admin_company',  # ← P0 cross-tenant exfil
        'X-User-Role': 'admin',           # ← P0 privilege escalation
      }
    }

O proxy DEVE usar `getAuthHeaders(request, true)` do helper canonical
`@/lib/api/auth-headers` que reenvia o `Authorization: Bearer <JWT>` do cookie
da sessão — sem hardcode.

Exit 1 quando encontra qualquer violação.

Run:
    python3 lia-agent-system/scripts/check_no_admin_company_in_proxies.py
    python3 lia-agent-system/scripts/check_no_admin_company_in_proxies.py --warn-only
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Padrão proibido — case-sensitive, ignora espaços ao redor de :
PATTERN_ADMIN_COMPANY = re.compile(
    r"""['"]X-Company-ID['"]\s*:\s*['"]admin_company['"]""",
    re.IGNORECASE,
)
PATTERN_ADMIN_ROLE_HARDCODED = re.compile(
    r"""['"]X-User-Role['"]\s*:\s*['"]admin['"]""",
    re.IGNORECASE,
)

PROXY_DIR = "plataforma-lia/src/app/api/backend-proxy"


def find_proxy_files(root: Path) -> list[Path]:
    proxy_root = root / PROXY_DIR
    if not proxy_root.exists():
        return []
    return list(proxy_root.rglob("route.ts"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Reporta violações mas retorna exit 0 (modo ratchet)",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repo root (default: cwd)",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = find_proxy_files(root)
    if not files:
        print(f"⚠ Nenhum arquivo encontrado em {root / PROXY_DIR}")
        return 0

    violations: list[tuple[Path, int, str, str]] = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"⚠ Falha lendo {f}: {e}", file=sys.stderr)
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if PATTERN_ADMIN_COMPANY.search(line):
                violations.append(
                    (
                        f.relative_to(root),
                        lineno,
                        "admin_company",
                        line.strip(),
                    )
                )
            if PATTERN_ADMIN_ROLE_HARDCODED.search(line):
                violations.append(
                    (
                        f.relative_to(root),
                        lineno,
                        "X-User-Role:admin",
                        line.strip(),
                    )
                )

    if not violations:
        print(f"✅ OK — {len(files)} proxies sem admin_company / admin role hardcoded")
        return 0

    print(
        f"❌ {len(violations)} violação(ões) — hardcoded admin_company ou X-User-Role: admin "
        f"em proxies do Next.js. Use getAuthHeaders(request, true) de '@/lib/api/auth-headers'."
    )
    for path, lineno, kind, snippet in violations:
        print(f"  {path}:{lineno}  [{kind}]  {snippet}")
    print()
    print("Fix: substituir getAuthHeaders() local hardcoded por:")
    print("  import { getAuthHeaders } from '@/lib/api/auth-headers'")
    print("  const headers = getAuthHeaders(request, true)")
    print()
    print("Referência: Wave 4 audit 2026-05-22, commit 93bf8c4d4.")

    return 0 if args.warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
