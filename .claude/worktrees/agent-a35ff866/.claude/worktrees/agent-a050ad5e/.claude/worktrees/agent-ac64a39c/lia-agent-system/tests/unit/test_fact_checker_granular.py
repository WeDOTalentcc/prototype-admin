"""
Testes unitários para FactChecker — métodos granulares (Sprint H).

Cobertura:
  - verify_count_claim: sem match, dentro da tolerância, fora da tolerância, excede máximo
  - verify_average_claim: sem match, range válido, inválido, desvio acima da tolerância
  - verify_top_candidates_claim: sem match, top razoável, top irrazoável, top difere do esperado
  - check_response: salary, count, percentage, date (testes de regressão)
"""
import pytest

pytestmark = pytest.mark.easy

from app.shared.compliance.fact_checker import FactChecker, FactCheckClaim, FactCheckResult


@pytest.fixture
def fc():
    return FactChecker()


# ---------------------------------------------------------------------------
# verify_count_claim
# ---------------------------------------------------------------------------

class TestVerifyCountClaim:

    def test_no_match_returns_unverified(self, fc):
        claim = fc.verify_count_claim("Nenhuma informação aqui.")
        assert claim.is_verified is False
        assert claim.original_value is None
        assert "No count claim" in claim.notes

    def test_count_within_tolerance(self, fc):
        claim = fc.verify_count_claim("Encontrei 28 candidatos", expected_count=30, tolerance_pct=10.0)
        assert claim.is_verified is True
        assert claim.is_accurate is True
        assert claim.original_value == 28

    def test_count_exceeds_tolerance(self, fc):
        claim = fc.verify_count_claim("Encontrei 25 candidatos", expected_count=30, tolerance_pct=10.0)
        assert claim.is_verified is True
        assert claim.is_accurate is False
        assert claim.deviation_pct == pytest.approx(16.7, abs=0.1)

    def test_count_exceeds_maximum(self, fc):
        claim = fc.verify_count_claim("Encontrei 99999 candidatos")
        assert claim.is_verified is True
        assert claim.is_accurate is False
        assert "exceeds maximum" in claim.notes

    def test_no_expected_count_defaults_accurate(self, fc):
        claim = fc.verify_count_claim("Encontrei 42 candidatos")
        assert claim.is_verified is True
        assert claim.is_accurate is True
        assert claim.deviation_pct is None

    def test_zero_count_is_valid(self, fc):
        claim = fc.verify_count_claim("0 candidatos encontrados")
        assert claim.is_verified is True
        assert claim.is_accurate is True

    def test_exact_match_accurate(self, fc):
        claim = fc.verify_count_claim("Temos 10 candidatos qualificados", expected_count=10)
        assert claim.is_accurate is True
        assert claim.deviation_pct == 0.0


# ---------------------------------------------------------------------------
# verify_average_claim
# ---------------------------------------------------------------------------

class TestVerifyAverageClaim:

    def test_no_match_returns_unverified(self, fc):
        claim = fc.verify_average_claim("Sem percentual aqui.")
        assert claim.is_verified is False
        assert "No percentage" in claim.notes

    def test_valid_percentage_accurate(self, fc):
        claim = fc.verify_average_claim("Score médio de 75%", expected_average=80.0, tolerance_pct=20.0)
        assert claim.is_verified is True
        assert claim.is_accurate is True  # 75 vs 80 = 6.25% desvio < 20%

    def test_deviation_above_tolerance(self, fc):
        claim = fc.verify_average_claim("Score médio de 50%", expected_average=80.0, tolerance_pct=20.0)
        assert claim.is_accurate is False
        assert claim.deviation_pct == pytest.approx(37.5, abs=0.1)

    def test_percentage_above_100(self, fc):
        claim = fc.verify_average_claim("Taxa de aprovação de 150%")
        assert claim.is_verified is True
        assert claim.is_accurate is False
        assert "0-100" in claim.notes

    def test_percentage_200_above_100(self, fc):
        """Regex não captura sinal negativo; testa valor explicitamente > 100."""
        claim = fc.verify_average_claim("Taxa de 200%")
        assert claim.is_verified is True
        assert claim.is_accurate is False

    def test_custom_claim_type(self, fc):
        claim = fc.verify_average_claim("75% aprovados", claim_type="approval_rate")
        assert claim.claim_type == "approval_rate"

    def test_no_expected_defaults_accurate(self, fc):
        claim = fc.verify_average_claim("Aprovação de 65%")
        assert claim.is_accurate is True
        assert claim.deviation_pct is None


# ---------------------------------------------------------------------------
# verify_top_candidates_claim
# ---------------------------------------------------------------------------

class TestVerifyTopCandidatesClaim:

    def test_no_match_returns_unverified(self, fc):
        claim = fc.verify_top_candidates_claim("Nenhuma informação de ranking.")
        assert claim.is_verified is False
        assert "No top-N" in claim.notes

    def test_top_5_accurate(self, fc):
        claim = fc.verify_top_candidates_claim("Os top 5 candidatos são os mais indicados.")
        assert claim.is_verified is True
        assert claim.is_accurate is True
        assert claim.original_value == 5

    def test_top_n_exceeds_max(self, fc):
        claim = fc.verify_top_candidates_claim("Os top 50 candidatos", max_reasonable_top=20)
        assert claim.is_accurate is False
        assert "outside reasonable range" in claim.notes

    def test_top_matches_expected(self, fc):
        claim = fc.verify_top_candidates_claim("os 3 melhores candidatos", expected_top_n=3)
        assert claim.is_accurate is True

    def test_top_differs_from_expected(self, fc):
        claim = fc.verify_top_candidates_claim("Os top 5 candidatos", expected_top_n=3)
        assert claim.is_accurate is False
        assert "expected top-3" in claim.notes

    def test_primeiros_pattern(self, fc):
        claim = fc.verify_top_candidates_claim("os primeiros 10 candidatos")
        assert claim.is_verified is True
        assert claim.original_value == 10

    def test_zero_top_is_invalid(self, fc):
        claim = fc.verify_top_candidates_claim("os top 0 candidatos")
        assert claim.is_accurate is False


# ---------------------------------------------------------------------------
# check_response (regressão)
# ---------------------------------------------------------------------------

class TestCheckResponseRegression:

    def test_salary_valid(self, fc):
        result = fc.check_response("Salário de R$ 8.000 a R$ 12.000 mensais.")
        assert result.total_claims >= 1
        assert result.accurate_claims >= 1

    def test_candidate_count_valid(self, fc):
        result = fc.check_response("Identificamos 15 candidatos para a vaga.")
        assert result.total_claims >= 1

    def test_percentage_valid(self, fc):
        result = fc.check_response("Taxa de aprovação de 78%.")
        assert result.total_claims >= 1

    def test_date_valid(self, fc):
        result = fc.check_response("Entrevista agendada para 15/06/2026.")
        assert result.total_claims >= 1
        assert result.verified_claims >= 1

    def test_inaccurate_salary_flagged(self, fc):
        result = fc.check_response("Salário de R$ 500 ao mês.")
        inaccurate = [c for c in result.claims if c.is_accurate is False]
        assert len(inaccurate) >= 1

    def test_overall_accuracy_one_when_no_claims(self, fc):
        result = fc.check_response("Texto sem claims verificáveis.")
        assert result.overall_accuracy == 1.0

    def test_to_metadata_structure(self, fc):
        result = fc.check_response("Salário R$ 5.000. 10 candidatos. 80%.")
        meta = result.to_metadata()
        assert "fact_check" in meta
        assert "overall_accuracy" in meta["fact_check"]
        assert "total_claims" in meta["fact_check"]
