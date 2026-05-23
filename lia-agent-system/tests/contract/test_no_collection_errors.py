"""
Contract sensor — pytest collection must succeed for the entire test suite.

WHY THIS SENSOR EXISTS
======================
Audit Recovery 2026-05-23 (Recovery #2 — tenant.py) descobriu que o test
`app/tests/test_dev_auto_login_tenant.py` ficou com ``ImportError`` há 22 dias
(desde commit 02361f41c em 2026-05-01) sem ninguém notar. O test importava
`normalize_demo_company_id` que foi removido do `app/core/tenant.py` e isso
NUNCA quebrou CI.

Significa que ou:
1. CI não rodou esse path em 22 dias
2. OU ImportError em collection foi silenciado em algum gate

Esse sensor é **defesa em profundidade**: roda `pytest --collect-only` e
falha se qualquer test file tiver erro de import/collection. Garante que
nenhum test fica orphan silenciosamente de novo.

Pattern: BLOCKING (não warn-only). Test orphans são red flag claro de
código removido sem cleanup de tests — sempre bloquear.

Se houver test legitimo que falha em collection (raríssimo — talvez fixture
condicional), adicionar ao `_EXPECTED_COLLECTION_FAILURES` abaixo com
justificativa.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

# Empty pós-Recovery #9 — orphan resolvido (W2-010-B canonical merge).
# Cada exceção futura DEVE ter:
#   - Path do test file
#   - TODO indicando qual Recovery/PR vai limpar
#   - Comentário com investigação preliminar
_EXPECTED_COLLECTION_FAILURES: set[str] = set()


def test_pytest_collect_only_has_no_errors():
    """
    Roda `pytest --collect-only -q` na suite inteira e verifica que não
    há ERROR durante collection (ImportError, SyntaxError, etc).

    Se falhar:
    - Olhar output do pytest pra identificar test file com problema
    - Decidir: corrigir o import OU deletar o test orphan
    - Se for exceção legítima (raríssimo), adicionar a _EXPECTED_COLLECTION_FAILURES
    """
    repo_root = Path(__file__).resolve().parents[2]  # tests/contract/foo.py → repo
    result = subprocess.run(
        ["python3", "-m", "pytest", "--collect-only", "-q", "--no-cov"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr

    # `pytest --collect-only` reporta ERRORS no end summary linhas tipo:
    # "===== ERROR tests/path/test_foo.py ====="
    # "ERROR tests/path/test_foo.py"
    error_lines = [
        line for line in output.split("\n")
        if "ERROR " in line and ".py" in line and "Interrupted" not in line
    ]

    # Filtrar exceções esperadas (se houver)
    unexpected_errors = [
        line for line in error_lines
        if not any(expected in line for expected in _EXPECTED_COLLECTION_FAILURES)
    ]

    assert not unexpected_errors, (
        "pytest --collect-only encontrou ERROR(s) inesperados:\n"
        + "\n".join(unexpected_errors)
        + "\n\n"
        + "Provável causa: test file referencia código removido (orphan).\n"
        + "Fix: corrigir import OU deletar test orphan.\n"
        + "\n=== Output completo ===\n"
        + output[-2000:]  # últimos 2000 chars pra ajudar debugging
    )
