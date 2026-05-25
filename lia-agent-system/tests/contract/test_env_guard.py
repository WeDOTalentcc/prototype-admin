"""Sensor harness — Env guard de contract tests vs prod-local Replit.

Sprint 1.B Task 1.B Phase 3 (2026-05-25): prevenir regressão do leak
"Sensor Harness Roundtrip Test" (8 vagas criadas em 2026-05-22 17:06-18:58
em company_id de teste 00000000-0000-4000-a000-000000000001 quando
test_jobvacancy_roundtrip.py rodou contra LIA_BACKEND_URL default :8001).

Princípio (harness-engineering): Guide computacional > Guide inferencial.
Bloquear contract test em prod-local é mais barato que limpar dados leaked.

Este teste valida que o helper `assert_safe_contract_env()` em
tests/contract/conftest.py detecta a combinação tóxica:
  - LIA_BACKEND_URL aponta :8001 (prod-local)
  - LIA_ENV não é "staging" / "ci" / "test"

E gera pytest.exit() ANTES de qualquer test rodar.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from tests.contract.conftest import assert_safe_contract_env


class TestEnvGuard:
    """Guard contract tests don't write to prod-local backend."""

    def test_blocks_prod_local_default_url_without_lia_env(self):
        """LIA_BACKEND_URL=:8001 (default) + LIA_ENV unset → exit."""
        with patch.dict(
            os.environ,
            {"LIA_BACKEND_URL": "http://127.0.0.1:8001", "LIA_ENV": ""},
            clear=False,
        ):
            with pytest.raises(SystemExit) as exc_info:
                assert_safe_contract_env()
            assert exc_info.value.code == 2

    def test_blocks_localhost_alias_too(self):
        """localhost:8001 deve ser bloqueado igual a 127.0.0.1:8001."""
        with patch.dict(
            os.environ,
            {"LIA_BACKEND_URL": "http://localhost:8001", "LIA_ENV": ""},
            clear=False,
        ):
            with pytest.raises(SystemExit):
                assert_safe_contract_env()

    def test_allows_when_lia_env_is_staging(self):
        """LIA_ENV=staging libera prod-local URL (ambiente intencional)."""
        with patch.dict(
            os.environ,
            {"LIA_BACKEND_URL": "http://127.0.0.1:8001", "LIA_ENV": "staging"},
            clear=False,
        ):
            # Deve passar sem exit
            assert_safe_contract_env()

    def test_allows_when_lia_env_is_ci(self):
        """LIA_ENV=ci também libera (rodando em pipeline CI explícito)."""
        with patch.dict(
            os.environ,
            {"LIA_BACKEND_URL": "http://127.0.0.1:8001", "LIA_ENV": "ci"},
            clear=False,
        ):
            assert_safe_contract_env()

    def test_allows_non_prod_local_url(self):
        """URL pointing a staging real (não :8001) é liberada."""
        with patch.dict(
            os.environ,
            {
                "LIA_BACKEND_URL": "https://staging.lia.wedotalent.cc",
                "LIA_ENV": "",
            },
            clear=False,
        ):
            assert_safe_contract_env()

    def test_allows_when_url_unset(self):
        """Sem LIA_BACKEND_URL nenhum, deixa passar (tests podem skip naturally)."""
        with patch.dict(os.environ, {"LIA_BACKEND_URL": ""}, clear=False):
            assert_safe_contract_env()
