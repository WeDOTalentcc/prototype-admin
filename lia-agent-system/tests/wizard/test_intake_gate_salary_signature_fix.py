"""TDD bug fix — _safe_fetch_salary deve usar a assinatura canônica de
search_salary_benchmark (role, seniority, location).

Bug (regressão do P0-B, commit e060f184d): intake_gate chamava com kwargs
`work_model=` e `company_id=` que a assinatura `(role, seniority, location)`
NÃO aceita → TypeError engolido pelo fail-open → benchmark salarial NUNCA
retornava no intake conversacional.

Red: com autospec enforçando a assinatura real, a chamada atual quebra e
_safe_fetch_salary retorna None.
Green: após alinhar ao contrato canônico, retorna o benchmark.

Run:
    cd lia-agent-system && python -m pytest tests/wizard/test_intake_gate_salary_signature_fix.py -v --no-cov
"""
from __future__ import annotations
import sys
from pathlib import Path
from unittest import mock

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


class TestSafeFetchSalaryCanonicalSignature:
    def _run_with_autospec(self, state):
        from app.domains.job_creation.nodes import intake_gate
        from app.domains.analytics.services.market_benchmark_service import (
            MarketBenchmarkService,
        )

        captured = {}

        # autospec=True enforça a assinatura REAL (role, seniority, location);
        # kwargs inválidos (work_model/company_id) levantam TypeError.
        async def fake_search(self, role, seniority=None, location=None):
            captured["role"] = role
            captured["seniority"] = seniority
            captured["location"] = location
            return {"min": 10000, "max": 15000, "currency": "BRL"}

        with mock.patch.object(
            MarketBenchmarkService,
            "search_salary_benchmark",
            autospec=True,
            side_effect=fake_search,
        ):
            result = intake_gate._safe_fetch_salary(
                state, "Desenvolvedor Python", "senior",
            )
        return result, captured

    def test_returns_benchmark_not_none(self):
        """Após o fix, o benchmark deve retornar (hoje retorna None pelo TypeError)."""
        state = {"parsed_location": "São Paulo", "workspace_id": "cid-1"}
        result, _ = self._run_with_autospec(state)
        assert result is not None, (
            "benchmark deve retornar; None indica TypeError engolido pelo fail-open"
        )
        assert result.get("min") == 10000

    def test_passes_role_and_seniority(self):
        state = {"parsed_location": "São Paulo"}
        _, captured = self._run_with_autospec(state)
        assert captured.get("role") == "Desenvolvedor Python"
        assert captured.get("seniority") == "senior"

    def test_passes_location_from_state(self):
        """location deve vir de parsed_location (uso correto do param canônico)."""
        state = {"parsed_location": "Rio de Janeiro"}
        _, captured = self._run_with_autospec(state)
        assert captured.get("location") == "Rio de Janeiro"

    def test_no_location_in_state_passes_none(self):
        """Sem parsed_location → location=None (mercado nacional)."""
        state = {}
        result, captured = self._run_with_autospec(state)
        assert result is not None
        assert captured.get("location") is None
