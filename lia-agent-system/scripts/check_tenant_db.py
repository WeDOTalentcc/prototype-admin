#!/usr/bin/env python3
"""
Sensor G-TENANTDB: verifica que app/domains/ usa get_tenant_db (RLS-aware),
não get_db (sem RLS), em Depends() de repositórios.

R-012 (Wave 1): todo repo em app/domains/ deve usar get_tenant_db para garantir
que PostgreSQL RLS isola dados por tenant automaticamente.

Exceções documentadas: adicionar arquivo path à ALLOWLIST abaixo com justificativa.

Exit: 0 = clean, 1 = violações encontradas.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Paths explicitamente multi-tenant (admin analytics, etc.) — adicionar com justificativa
ALLOWLIST: set[str] = {
    # "app/domains/admin/repositories/audit_log_repository.py",  # exemplo
}

VIOLATION_PATTERN = re.compile(r"Depends\s*\(\s*get_db\s*\)")


def main() -> int:
    violations: list[str] = []

    for py_file in ROOT.glob("app/domains/**/*.py"):
        rel = py_file.relative_to(ROOT).as_posix()
        if "__pycache__" in rel or "test" in rel:
            continue
        if rel in ALLOWLIST:
            continue
        try:
            source = py_file.read_text(encoding="utf-8")
        except Exception:
            continue

        for lineno, line in enumerate(source.splitlines(), 1):
            if VIOLATION_PATTERN.search(line):
                violations.append(f"  {rel}:{lineno}: Depends(get_db) — usar Depends(get_tenant_db)")

    if violations:
        print(f"FAIL [G-TENANTDB] {len(violations)} uso(s) de Depends(get_db) em app/domains/:")
        print("\n".join(violations[:30]))
        if len(violations) > 30:
            print(f"  ... e mais {len(violations) - 30}")
        print()
        print("INSTRUCAO DE CORRECAO:")
        print("  1. Substituir: from app.core.database import get_db")
        print("     Por:        from app.core.database import get_tenant_db")
        print("  2. Substituir: Depends(get_db)")
        print("     Por:        Depends(get_tenant_db)")
        print("  FastAPI injeta Request automaticamente — sem mudanca de assinatura.")
        print("  Excecoes multi-tenant (admin analytics): adicionar path em ALLOWLIST do sensor.")
        return 1

    print("OK [G-TENANTDB] — todos os Depends em app/domains/ usam get_tenant_db.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
