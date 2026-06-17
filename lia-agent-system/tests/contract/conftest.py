"""Contract tests conftest — env guard contra leak em prod-local.

Sprint 1.B Task 1.B Phase 3 (2026-05-25).

PROBLEMA (incident 2026-05-22 17:06-18:58):
  Sensor `tests/contract/test_jobvacancy_roundtrip.py` rodou contra
  `LIA_BACKEND_URL=http://127.0.0.1:8001` (prod-local Replit) com `DEMO_EMAIL`
  apontando conta real `demo@wedotalent.com`. Resultado: 8 vagas
  "Sensor Harness Roundtrip Test" persistidas em company_id test fixture
  `00000000-0000-4000-a000-000000000001`, visíveis em "Minhas Vagas Ativas"
  do Paulo (mesma company_id resolvida via JWT do demo user).

GUIDE COMPUTACIONAL (harness-engineering Hashimoto):
  Bloquear *na coleção do pytest* — antes de qualquer test rodar — quando
  combinação tóxica é detectada:
    - LIA_BACKEND_URL aponta 127.0.0.1:8001 ou localhost:8001 (prod-local)
    - LIA_ENV não é 'staging', 'ci' ou 'test' (envs intencionais)

  pytest.exit() com mensagem prescritiva para o LLM consumidor — instrui
  como liberar quando for intencional.

NÃO BLOQUEIA:
  - URL apontando staging real (https://staging.lia.wedotalent.cc, etc)
  - URL apontando port diferente (sandbox em :8002, etc)
  - LIA_BACKEND_URL não-definida (testes individuais decidem com skip)
  - LIA_ENV explícito = staging/ci/test
"""
from __future__ import annotations

import os
import sys


_PROD_LOCAL_HOSTS = ("127.0.0.1:8001", "localhost:8001")
_ALLOWED_ENVS = ("staging", "ci", "test")


def _is_prod_local(url: str) -> bool:
    """True se URL aponta backend prod-local Replit (porta canonical 8001)."""
    return any(host in url for host in _PROD_LOCAL_HOSTS)


def assert_safe_contract_env() -> None:
    """Bloqueia contract tests escrevendo em prod-local sem LIA_ENV explícito.

    Chamado em `pytest_configure` (collection time) — antes de qualquer test.
    Exit code 2 = configuração errada (per pytest convention).
    """
    backend_url = os.environ.get("LIA_BACKEND_URL", "")
    if not backend_url:
        return  # Sem URL — testes individuais usam skip natural

    if not _is_prod_local(backend_url):
        return  # URL não-prod-local — OK, libera

    lia_env = os.environ.get("LIA_ENV", "").lower()
    if lia_env in _ALLOWED_ENVS:
        return  # Env intencional — libera

    message = (
        "\n\n"
        "🛑 CONTRACT TEST SAFETY GUARD TRIGGERED\n"
        "\n"
        f"  LIA_BACKEND_URL = {backend_url}\n"
        "    → aponta backend prod-local Replit (porta 8001)\n"
        f"  LIA_ENV = {lia_env or '(unset)'}\n"
        f"    → precisa ser um de {_ALLOWED_ENVS} pra liberar\n"
        "\n"
        "  Razão: contract tests rodando contra prod-local CRIAM ROWS LEAK\n"
        "  (incident 2026-05-22: 8× 'Sensor Harness Roundtrip Test' em\n"
        "   company_id test fixture, visíveis no card 'Minhas Vagas Ativas').\n"
        "\n"
        "  Como liberar:\n"
        "    Local dev contra staging (recomendado):\n"
        "      export LIA_ENV=staging\n"
        "      export LIA_BACKEND_URL=<staging URL real>\n"
        "\n"
        "    Local dev contra prod-local (intencional, e.g. iterando refactor):\n"
        "      export LIA_ENV=test\n"
        "      # mantém LIA_BACKEND_URL=http://127.0.0.1:8001\n"
        "\n"
        "    CI pipeline:\n"
        "      export LIA_ENV=ci\n"
    )
    # SystemExit com code 2 = pytest collection error (per pytest convention).
    # Não usar pytest.exit() aqui pois esta função roda também em test cases
    # com unittest.mock.patch — pytest.exit() em fixture causa abort do
    # próprio módulo de teste do guard.
    raise SystemExit(message if False else 2)


def pytest_configure(config):  # type: ignore[no-untyped-def]
    """Hook pytest — roda 1× na coleção, antes de qualquer test."""
    # Permitir bypass durante run do próprio test_env_guard.py
    if "PYTEST_GUARD_BYPASS" in os.environ:
        return
    try:
        assert_safe_contract_env()
    except SystemExit as exc:
        # Print mensagem completa + abort collection
        if isinstance(exc.code, int):
            # Re-fetch mensagem porque SystemExit(2) só carrega code
            print(_format_guard_message(), file=sys.stderr)
            raise
        else:
            print(exc.code, file=sys.stderr)
            raise SystemExit(2)


def _format_guard_message() -> str:
    """Formata mensagem completa pra stderr (versão sem raise)."""
    backend_url = os.environ.get("LIA_BACKEND_URL", "")
    lia_env = os.environ.get("LIA_ENV", "(unset)")
    return (
        "\n\n"
        "🛑 CONTRACT TEST SAFETY GUARD TRIGGERED\n"
        "\n"
        f"  LIA_BACKEND_URL = {backend_url}\n"
        "    → aponta backend prod-local Replit (porta 8001)\n"
        f"  LIA_ENV = {lia_env}\n"
        f"    → precisa ser um de {_ALLOWED_ENVS} pra liberar\n"
        "\n"
        "  Razão: contract tests rodando contra prod-local CRIAM ROWS LEAK\n"
        "  (incident 2026-05-22: 8× 'Sensor Harness Roundtrip Test' em\n"
        "   company_id test fixture, visíveis no card 'Minhas Vagas Ativas').\n"
        "\n"
        "  Como liberar:\n"
        "    Local dev contra staging (recomendado):\n"
        "      export LIA_ENV=staging\n"
        "      export LIA_BACKEND_URL=<staging URL real>\n"
        "\n"
        "    Local dev contra prod-local (intencional, e.g. iterando refactor):\n"
        "      export LIA_ENV=test\n"
        "\n"
        "    CI pipeline:\n"
        "      export LIA_ENV=ci\n"
    )
