#!/usr/bin/env python3
"""W2-009-B · Sensor BLOCKING — Idempotency middleware canonical wired.

Verifica:
1. Migration 181_idempotency_keys.py existe.
2. app/middleware/idempotency.py existe + tem class IdempotencyMiddleware.
3. main.py importa + adiciona IdempotencyMiddleware via app.add_middleware.
4. Header constant é "Idempotency-Key" (HTTP RFC spec — não renomear).

Defesa contra:
- Migration deletada/renomeada
- Middleware file deletado
- main.py wiring quebrado (import OR add_middleware removido)
- Header renamed (quebra clients que mandam "Idempotency-Key")

Exit 0 = OK · Exit 1 = violation.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_PATH = REPO_ROOT / "alembic" / "versions" / "181_idempotency_keys.py"
MIDDLEWARE_PATH = REPO_ROOT / "app" / "middleware" / "idempotency.py"
MAIN_PATH = REPO_ROOT / "app" / "main.py"


def check() -> list[str]:
    violations: list[str] = []

    # 1. Migration exists
    if not MIGRATION_PATH.exists():
        violations.append(
            f"[W2-009-B] Migration ausente: {MIGRATION_PATH}\n"
            f"  Fix: alembic/versions/181_idempotency_keys.py deve existir.\n"
            f"  Esta migration cria a cache table canonical."
        )
        return violations

    mig_src = MIGRATION_PATH.read_text(encoding="utf-8")
    if 'revision = "181_idempotency_keys"' not in mig_src:
        violations.append(
            "[W2-009-B] revision_id incorreto em 181_idempotency_keys.py.\n"
            '  Esperado: revision = "181_idempotency_keys"'
        )
    if 'down_revision = "180_audit_append_only_triggers"' not in mig_src:
        violations.append(
            "[W2-009-B] down_revision incorreto.\n"
            '  Esperado: down_revision = "180_audit_append_only_triggers"\n'
            "  Fix: não alterar cadeia alembic."
        )

    required_cols = [
        "idempotency_key", "company_id", "method", "path",
        "request_hash", "response_status", "response_body", "created_at",
    ]
    for col in required_cols:
        if f'"{col}"' not in mig_src:
            violations.append(
                f"[W2-009-B] Coluna canonical ausente em migration: {col}.\n"
                f"  Fix: idempotency_keys table deve ter coluna {col}."
            )

    # 2. Middleware module exists
    if not MIDDLEWARE_PATH.exists():
        violations.append(
            f"[W2-009-B] Middleware ausente: {MIDDLEWARE_PATH}\n"
            "  Fix: app/middleware/idempotency.py deve existir com class IdempotencyMiddleware."
        )
        return violations

    mw_src = MIDDLEWARE_PATH.read_text(encoding="utf-8")
    if "class IdempotencyMiddleware(BaseHTTPMiddleware)" not in mw_src:
        violations.append(
            "[W2-009-B] Class IdempotencyMiddleware(BaseHTTPMiddleware) ausente.\n"
            "  Fix: middleware deve estender starlette BaseHTTPMiddleware."
        )
    if 'IDEMPOTENCY_HEADER = "Idempotency-Key"' not in mw_src:
        violations.append(
            "[W2-009-B] IDEMPOTENCY_HEADER constant incorreto.\n"
            '  Esperado: IDEMPOTENCY_HEADER = "Idempotency-Key" (HTTP spec).\n'
            "  Fix: não renomear — quebra clients que mandam header canonical."
        )

    # 3. main.py wires middleware
    if not MAIN_PATH.exists():
        violations.append(f"[W2-009-B] main.py ausente: {MAIN_PATH}")
        return violations

    main_src = MAIN_PATH.read_text(encoding="utf-8")
    if "from app.middleware.idempotency import IdempotencyMiddleware" not in main_src:
        violations.append(
            "[W2-009-B] main.py NÃO importa IdempotencyMiddleware.\n"
            "  Fix: adicionar 'from app.middleware.idempotency import IdempotencyMiddleware'."
        )
    if "app.add_middleware(IdempotencyMiddleware)" not in main_src:
        violations.append(
            "[W2-009-B] main.py NÃO adiciona IdempotencyMiddleware.\n"
            "  Fix: adicionar 'app.add_middleware(IdempotencyMiddleware)' após RateLimitMiddleware."
        )

    return violations


def main() -> int:
    violations = check()
    if violations:
        print("❌ check_idempotency_middleware_wired FAILED:\n", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
            print("", file=sys.stderr)
        print(
            f"\nTotal: {len(violations)} violation(s). "
            "Idempotency middleware é canonical pro produto (W2-009-B).\n"
            "Não desativar/remover sem aprovação textual explícita do Paulo.",
            file=sys.stderr,
        )
        return 1
    print("✅ check_idempotency_middleware_wired OK · W2-009-B canonical preserved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
