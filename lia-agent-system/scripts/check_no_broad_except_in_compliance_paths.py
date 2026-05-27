#!/usr/bin/env python3
"""Wave E Sensor 7 — Detecta broad except silencioso em paths hitl/fairness/audit/compliance.

Anti-pattern (REGRA 4 CLAUDE.md): `except Exception` sem re-raise e sem logger
em paths críticos de compliance resulta em falhas silenciosas. Decisões de HITL,
auditoria LGPD e fairness são ativáveis judicialmente — falha deve ser visível.

Detecta em arquivos com hitl/fairness/audit/compliance no path ou nome:
- `except Exception:` seguido APENAS de `pass` como corpo (silent swallow)
  MAS excluindo: padrões de cleanup de DB (rollback, close, etc.)

Legítimos (NÃO detecta):
- `except Exception as exc: logger.warning/error(...)` — tem log
- `except Exception: db.rollback()` — operação de cleanup
- `except Exception: raise SomeOtherException(...)` — re-raise
- `except Exception as e: raise` — re-raise
- Blocos aninhados de rollback como cleanup pós-error principal

Baseline 2026-05-27: sensor em warn-only. Promover a BLOCKING quando
todos os `# REGRA-4-EXEMPT` forem adicionados nas violations legítimas.

Honra marker: # REGRA-4-EXEMPT: <reason>

Exit 0 sempre em modo default (warn-only). Exit 1 com --blocking.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOMAINS_ROOT = REPO_ROOT / "app" / "domains"
SHARED_ROOT = REPO_ROOT / "app" / "shared"

# Palavras-chave nos paths para identificar arquivos compliance-critical
COMPLIANCE_PATH_KEYWORDS = {"hitl", "fairness", "audit", "compliance"}

EXEMPT_MARKER = "REGRA-4-EXEMPT"

# Padrões de body que indicam cleanup legítimo (não contam como silencioso)
CLEANUP_BODY_PATTERNS = re.compile(
    r'\b(?:rollback|close|cleanup|disconnect|unsubscribe|cancel|abort)\b',
    re.IGNORECASE,
)


def is_compliance_file(path: Path) -> bool:
    """Verifica se o arquivo é um path compliance-critical."""
    parts = {p.lower() for p in path.parts}
    stem = path.stem.lower()
    return bool(
        COMPLIANCE_PATH_KEYWORDS & parts or
        any(kw in stem for kw in COMPLIANCE_PATH_KEYWORDS)
    )


def has_logger_call_in_body(body: list[ast.stmt]) -> bool:
    """Verifica se há logger.warning/error/critical no bloco."""
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ("warning", "error", "critical", "exception", "info"):
                    return True
            elif isinstance(node.func, ast.Name):
                if node.func.id in ("log", "logger"):
                    return True
    return False


def has_reraise_in_body(body: list[ast.stmt]) -> bool:
    """Verifica se há raise no bloco."""
    for node in ast.walk(ast.Module(body=body, type_ignores=[])):
        if isinstance(node, ast.Raise):
            return True
    return False


def is_cleanup_body(body: list[ast.stmt], source_lines: list[str]) -> bool:
    """Verifica se o body é um cleanup legítimo (rollback, close, etc.)."""
    # Se o único statement é pass — pode ser silencioso, mas verificar contexto
    if len(body) == 1 and isinstance(body[0], ast.Pass):
        return False  # `pass` puro é potencialmente silencioso

    # Se contém apenas operações de cleanup
    body_source = "\n".join(
        source_lines[body[0].lineno - 1: body[-1].end_lineno]
    ) if body else ""
    if CLEANUP_BODY_PATTERNS.search(body_source):
        return True

    return False


def is_pure_pass_except(handler: ast.ExceptHandler) -> bool:
    """Retorna True apenas para `except Exception: pass` puro (o anti-pattern mais crítico)."""
    if handler.type is None:
        exc_type = "bare"
    elif isinstance(handler.type, ast.Name):
        exc_type = handler.type.id
    elif isinstance(handler.type, ast.Attribute):
        exc_type = handler.type.attr
    else:
        return False

    if exc_type not in ("Exception", "BaseException", "bare"):
        return False

    # Apenas `pass` no body — definitivamente silencioso
    if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
        return True

    return False


def check_file(path: Path) -> list[tuple[int, str]]:
    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    violations = []

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return [(0, f"Erro de parse: {e}")]

    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        for handler in node.handlers:
            if not is_pure_pass_except(handler):
                continue

            lineno = handler.lineno
            start = max(0, lineno - 3)
            surrounding = "\n".join(lines[start:lineno])

            if EXEMPT_MARKER in surrounding:
                continue

            # Verificar se está em contexto de cleanup (aninhado em try-except superior)
            body_line = lines[lineno] if lineno < len(lines) else ""
            if CLEANUP_BODY_PATTERNS.search(body_line):
                continue

            violations.append((
                lineno,
                f"Broad except: pass silencioso em path compliance-critical: {lines[lineno - 1].strip()!r}",
            ))

    return violations


def main() -> int:
    blocking = "--blocking" in sys.argv
    all_violations: list[tuple[Path, int, str]] = []

    for search_root in (DOMAINS_ROOT, SHARED_ROOT):
        if not search_root.exists():
            continue
        for path in sorted(search_root.rglob("*.py")):
            if "__pycache__" in str(path):
                continue
            if not is_compliance_file(path):
                continue
            for lineno, msg in check_file(path):
                rel = path.relative_to(REPO_ROOT)
                all_violations.append((rel, lineno, msg))

    if not all_violations:
        print(f"[check_no_broad_except_in_compliance_paths] ✅ 0 violations — nenhum broad except:pass silencioso detectado.")
        return 0

    tag = "⚠️" if not blocking else "❌"
    print(f"[check_no_broad_except_in_compliance_paths] {tag} {len(all_violations)} violation(s) [warn-only — baseline tech debt]:\n")
    for rel_path, lineno, msg in all_violations:
        print(f"  [{rel_path}:{lineno}] {msg}")
        print(f"    → Fix: adicionar logger.warning() ou # REGRA-4-EXEMPT: <razão> para documentar intenção.")
        print()

    print(f"[check_no_broad_except_in_compliance_paths] Sensor em warn-only. "
          f"Use --blocking para promover após triagem das violations.")

    if blocking:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
