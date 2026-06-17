#!/usr/bin/env python3
"""
Bug 1 sensor canonical: detecta routes Next.js que NÃO usam helper canonical
para resolver company_id, e em vez disso redeclaram fallback 'dev_company'
(string literal, falha schema UUID do backend) ou implementam resolveCompanyId
localmente (duplicação que viola REGRA #0 single source of truth).

Run:
    python3 plataforma-lia/scripts/check_proxy_canonical.py
    python3 plataforma-lia/scripts/check_proxy_canonical.py --blocking

Exit codes:
    0  no violations OR warn-only with violations < threshold
    1  blocking mode + violations >= threshold

Output: [file:line] description → Fix suggestion (PT-BR)

Skill canonical: harness-engineering [sensor computacional].
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROUTES_DIR = ROOT / "src" / "app" / "api" / "backend-proxy"
HELPER = ROOT / "src" / "lib" / "api" / "resolve-company-id.ts"

DEV_FALLBACK_LITERAL = re.compile(r"DEV_FALLBACK_COMPANY\s*=\s*['\"]dev_company['\"]")
LOCAL_FUNC = re.compile(r"async\s+function\s+resolveCompanyId\s*\(")


def scan() -> list[tuple[Path, int, str, str]]:
    violations: list[tuple[Path, int, str, str]] = []
    for ts in ROUTES_DIR.rglob("route.ts"):
        try:
            lines = ts.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, 1):
            if DEV_FALLBACK_LITERAL.search(line):
                violations.append((
                    ts, i,
                    "Hardcoded DEV_FALLBACK_COMPANY = 'dev_company' (string, não UUID)",
                    "Import canonical: `import { resolveCompanyId } from '@/lib/api/resolve-company-id'` "
                    "e remova a constante local. Backend require_company_id_strict_match exige UUID, "
                    "string literal causa CROSS-TENANT ATTEMPT (Bug 1 — 2026-05-24).",
                ))
            if LOCAL_FUNC.search(line) and ts != HELPER:
                violations.append((
                    ts, i,
                    "Função local resolveCompanyId duplicando helper canonical",
                    "Remova função local e import: "
                    "`import { resolveCompanyId } from '@/lib/api/resolve-company-id'`. "
                    "REGRA #0 single source of truth.",
                ))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocking", action="store_true",
                        help="Exit 1 on any violation (default: warn-only)")
    parser.add_argument("--max-violations", type=int, default=0)
    args = parser.parse_args()

    violations = scan()
    if not violations:
        print("✅ check_proxy_canonical: 0 violations (baseline canonical)")
        return 0

    print(f"⚠️  check_proxy_canonical: {len(violations)} violation(s) found")
    for path, lineno, desc, fix in violations:
        rel = path.relative_to(ROOT)
        print(f"  [{rel}:{lineno}] {desc}")
        print(f"  → Fix: {fix}\n")

    if args.blocking and len(violations) > args.max_violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
