#!/usr/bin/env python3
"""
Sensor GAP-11-003: detecta `except Exception as e` seguido de
`raise HTTPException(..., detail=str(e))` em endpoints REST.

Padrão proibido (OWASP A09 — info disclosure):
    except Exception as e:
        raise HTTPException(status_code=XXX, detail=str(e))

Padrão permitido (exceções de domínio com mensagem intencional):
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
"""
import re, sys, os, argparse

DANGEROUS_BLOCK = re.compile(
    r"except\s+(?:Exception|BaseException)\s+as\s+\w+\s*:\s*\n"
    r"(?:\s+[^\n]*\n)*?"          # zero ou mais linhas intermediárias (await, log, etc.)
    r"\s+raise\s+HTTPException\s*\([^)]*detail\s*=\s*str\(\w+\)",
    re.MULTILINE,
)

def scan_file(fpath):
    try:
        src = open(fpath, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    violations = []
    for m in DANGEROUS_BLOCK.finditer(src):
        lineno = src[:m.start()].count("\n") + 1
        snippet = m.group()[:120].replace("\n", "\\n")
        violations.append((fpath, lineno, snippet))
    return violations

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paths", nargs="*", default=["app/api/v1"])
    parser.add_argument("--blocking", action="store_true")
    args = parser.parse_args()

    all_violations = []
    for base in args.paths:
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if f.endswith(".py"):
                    all_violations.extend(scan_file(os.path.join(root, f)))

    if all_violations:
        print(f"❌ {len(all_violations)} violation(s) found (GAP-11-003 — OWASP A09 info disclosure):")
        for fpath, line, snippet in all_violations:
            print(f"  {fpath}:{line}")
            print(f"    Pattern: {snippet[:100]}")
            print(f"    → Fix: separar `except ValueError` de `except Exception`; para Exception usar")
            print(f"           logger.error(..., exc_info=True) + detail genérico (não str(e))")
        if args.blocking:
            sys.exit(1)
    else:
        print(f"✅ 0 violations — nenhum `except Exception` com detail=str(e) detectado.")
    return len(all_violations)

if __name__ == "__main__":
    main()
