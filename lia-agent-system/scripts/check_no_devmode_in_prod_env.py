#!/usr/bin/env python3
"""
Sensor G-DEVMODE: bloqueia commit de .env.staging ou .env.production
que contenha LIA_DEV_MODE ativo (=1|true|yes).

R-006 (Sprint 1) gateou DEV_MODE pelo ENVIRONMENT em codigo, mas e'
possivel alguem commitar um .env.staging com LIA_DEV_MODE=true por engano.
Este hook impede que isso chegue ao repo.

HARNESS: sensor computacional (pre-commit). Mensagem de erro otimizada
para LLM — instrucao de correcao em linguagem natural.

Exit: 0 = clean, 1 = violacao encontrada.
"""
import re
import sys
from pathlib import Path

PROTECTED_FILES = [".env.staging", ".env.production"]
DEV_MODE_PATTERN = re.compile(r"^LIA_DEV_MODE\s*=\s*(1|true|yes)", re.I | re.M)

def main() -> int:
    violations = []
    root = Path(".")
    for env_file in PROTECTED_FILES:
        p = root / env_file
        if not p.exists():
            continue
        content = p.read_text(encoding="utf-8")
        if DEV_MODE_PATTERN.search(content):
            violations.append(env_file)

    if violations:
        print("FAIL [G-DEVMODE] LIA_DEV_MODE ativo em arquivo de ambiente protegido:")
        for f in violations:
            print(f"  {f}")
        print()
        print("INSTRUCAO DE CORRECAO:")
        print("  1. Remova ou comente LIA_DEV_MODE em:", ", ".join(violations))
        print("  2. Staging/producao NUNCA devem ter DEV_MODE ativo (R-006).")
        print("  3. Para testes locais, use .env.local ou .env.development.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
