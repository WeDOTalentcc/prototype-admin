"""
Tests for FactChecker - post-response validation.
"""
import pytest
from app.shared.compliance.fact_checker import FactChecker, FactCheckResult


class TestFactCheckerSalary:
    def setup_method(self):
        self.checker = FactChecker()

    def test_valid_salary_range(self):
        result = self.checker.check_response("A faixa salarial é R$ 8.000 a R$ 12.000")
        assert result.total_claims >= 1
        salary_claims = [c for c in result.claims if c.claim_type == "salary"]
        assert len(salary_claims) >= 1
        assert salary_claims[0].is_accurate

    def test_invalid_salary_too_low(self):
        result = self.checker.check_response("Salário de R$ 500")
        salary_claims = [c for c in result.claims if c.claim_type == "salary"]
        assert len(salary_claims) >= 1
        assert not salary_claims[0].is_accurate

    def test_invalid_salary_too_high(self):
        result = self.checker.check_response("Salário de R$ 500.000")
        salary_claims = [c for c in result.claims if c.claim_type == "salary"]
        assert len(salary_claims) >= 1
        assert not salary_claims[0].is_accurate

    def test_salary_deviation_from_context(self):
        context = {"expected_salary_range": {"min": 10000, "max": 15000}}
        result = self.checker.check_response("Faixa de R$ 50.000", context)
        salary_claims = [c for c in result.claims if c.claim_type == "salary"]
        assert len(salary_claims) >= 1
        assert salary_claims[0].deviation_pct is not None


class TestFactCheckerCandidateCount:
    def setup_method(self):
        self.checker = FactChecker()

    def test_valid_count(self):
        result = self.checker.check_response("Encontramos 25 candidatos")
        count_claims = [c for c in result.claims if c.claim_type == "candidate_count"]
        assert len(count_claims) >= 1
        assert count_claims[0].is_accurate

    def test_invalid_count_too_high(self):
        result = self.checker.check_response("Temos 100000 candidatos")
        count_claims = [c for c in result.claims if c.claim_type == "candidate_count"]
        assert len(count_claims) >= 1
        assert not count_claims[0].is_accurate

    def test_zero_count(self):
        result = self.checker.check_response("0 candidatos encontrados")
        count_claims = [c for c in result.claims if c.claim_type == "candidate_count"]
        assert len(count_claims) >= 1
        assert count_claims[0].is_accurate


class TestFactCheckerPercentage:
    def setup_method(self):
        self.checker = FactChecker()

    def test_valid_percentage(self):
        result = self.checker.check_response("Match de 85%")
        pct_claims = [c for c in result.claims if c.claim_type == "percentage"]
        assert len(pct_claims) >= 1
        assert pct_claims[0].is_accurate

    def test_invalid_percentage(self):
        result = self.checker.check_response("Taxa de 150%")
        pct_claims = [c for c in result.claims if c.claim_type == "percentage"]
        assert len(pct_claims) >= 1
        assert not pct_claims[0].is_accurate


class TestFactCheckerDate:
    def setup_method(self):
        self.checker = FactChecker()

    def test_valid_date(self):
        result = self.checker.check_response("Data: 15/03/2026")
        date_claims = [c for c in result.claims if c.claim_type == "date"]
        assert len(date_claims) >= 1
        assert date_claims[0].is_accurate

    def test_unreasonable_date_year(self):
        result = self.checker.check_response("Contratado em 01/01/2015")
        date_claims = [c for c in result.claims if c.claim_type == "date"]
        assert len(date_claims) >= 1
        assert not date_claims[0].is_accurate


class TestFactCheckerMetadata:
    def setup_method(self):
        self.checker = FactChecker()

    def test_no_claims_response(self):
        result = self.checker.check_response("Olá, como posso ajudar?")
        assert result.total_claims == 0
        assert result.overall_accuracy == 1.0

    def test_to_metadata_format(self):
        result = self.checker.check_response("25 candidatos com R$ 8.000")
        metadata = result.to_metadata()
        assert "fact_check" in metadata
        assert "confidence_verified" in metadata["fact_check"]
        assert "total_claims" in metadata["fact_check"]

    def test_mixed_claims(self):
        result = self.checker.check_response("25 candidatos, salário R$ 10.000, match 85%")
        assert result.total_claims >= 3
