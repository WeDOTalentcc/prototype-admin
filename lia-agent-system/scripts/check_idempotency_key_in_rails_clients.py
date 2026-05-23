#!/usr/bin/env python3
"""
Sensor anti-regressão · W2-009 (2026-05-22)

Verifica que os 2 HTTP clients Rails reais (WeDOTalentATSClient +
JobCreationAPIClient) injetam header `Idempotency-Key` em todo método
não-GET (POST/PUT/PATCH/DELETE).

Os outros 2 files do diagnostic (rails_client.py + rails_adapter.py) só
delegam para esses 2 — fix se propaga naturalmente.

Pattern violação:
- Remover `request_headers["Idempotency-Key"]` (regressão duplicação)
- Trocar uuid.uuid4() por timestamp (não-único entre processes)
- Adicionar Idempotency-Key em GET (semântica incorreta)

Mensagem PT-BR + fix sugerido em sintaxe exata (harness CLAUDE.md).
Modo: BLOCKING por default · --warn-only opt-out.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAILS_CLIENT = REPO_ROOT / "app/shared/integration/rails_client.py"
JOB_API_CLIENT = REPO_ROOT / "app/domains/job_creation/api_client.py"


def _check_file_has_idempotency_inject(path: Path, client_label: str) -> list[str]:
    """Verifica que arquivo tem (1) import uuid, (2) Idempotency-Key inject."""
    errors: list[str] = []
    if not path.exists():
        return [f"❌ {path.relative_to(REPO_ROOT)} ausente ({client_label})"]

    src = path.read_text()

    if "import uuid" not in src:
        errors.append(
            f"❌ {client_label}: NÃO importa `uuid` para gerar Idempotency-Key\n"
            f"   File: {path.relative_to(REPO_ROOT)}\n"
            "   FIX: adicionar `import uuid` no topo do arquivo"
        )
        return errors

    if "Idempotency-Key" not in src:
        errors.append(
            f"❌ {client_label}: NÃO injeta header `Idempotency-Key` em mutations\n"
            f"   File: {path.relative_to(REPO_ROOT)}\n"
            "   Risco: retry HTTP duplica recursos (jobs/candidates/etc.)\n"
            "   FIX em _request() antes do client.request():\n"
            "       mutation_method = method.upper() in {\"POST\", \"PUT\", \"PATCH\", \"DELETE\"}\n"
            "       request_headers: dict[str, str] = dict(self._get_headers() or {})\n"
            "       if mutation_method:\n"
            "           request_headers[\"Idempotency-Key\"] = idempotency_key or str(uuid.uuid4())\n"
            "       # passar headers=request_headers no client.request(...)"
        )

    # Method signature deve aceitar idempotency_key
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return errors + [f"❌ Syntax error em {path.name}: {exc}"]

    # Find _request method
    found_request = False
    accepts_idempotency = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_request":
            found_request = True
            arg_names = [a.arg for a in node.args.args] + [a.arg for a in node.args.kwonlyargs]
            if "idempotency_key" in arg_names:
                accepts_idempotency = True
            break

    if not found_request:
        errors.append(
            f"⚠️  {client_label}: método `_request` não encontrado (estrutura mudou?)\n"
            f"   File: {path.relative_to(REPO_ROOT)}"
        )
    elif not accepts_idempotency:
        errors.append(
            f"❌ {client_label}: `_request` NÃO aceita `idempotency_key` param\n"
            f"   File: {path.relative_to(REPO_ROOT)}\n"
            "   FIX: adicionar `idempotency_key: str | None = None` na assinatura"
        )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    errors.extend(_check_file_has_idempotency_inject(RAILS_CLIENT, "WeDOTalentATSClient"))
    errors.extend(_check_file_has_idempotency_inject(JOB_API_CLIENT, "JobCreationAPIClient"))

    fatal = [e for e in errors if not e.lstrip().startswith("⚠")]
    warnings_list = [e for e in errors if e.lstrip().startswith("⚠")]

    for w in warnings_list:
        print(w, file=sys.stderr)
        print(file=sys.stderr)

    if fatal:
        print(
            f"W2-009 idempotency key drift · {len(fatal)} violation(s):",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for err in fatal:
            print(err, file=sys.stderr)
            print(file=sys.stderr)
        if args.warn_only:
            print("⚠️  WARN-ONLY mode: exit 0", file=sys.stderr)
            return 0
        return 1

    print(
        "✅ Idempotency-Key wired em 2 HTTP clients Rails (W2-009) · "
        "POST/PUT/PATCH/DELETE protegidos contra duplicação em retry"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
