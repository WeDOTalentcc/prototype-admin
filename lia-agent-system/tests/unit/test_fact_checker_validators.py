"""
Tests for LIA-C06 — Domain-specific validators and FactChecker registry.

Coverage:
- validate_cv_score_claim: detects discrepancy, passes accurate claim
- validate_analytics_metric_claim: detects wrong days
- register_validator: adds to domain
- check_response_with_domain: calls registered validator
"""
import asyncio
import pytest
import sys
import os

# Ensure project root is in path
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')

from app.shared.compliance.domain_validators import (
    validate_cv_score_claim,
    validate_analytics_metric_claim,
    validate_sourcing_count_claim,
)
from app.shared.compliance.fact_checker import FactChecker, FactCheckResult


# ---------------------------------------------------------------------------
# Helper to run async functions in tests
# ---------------------------------------------------------------------------

def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# test_cv_score_validator_detects_discrepancy
# ---------------------------------------------------------------------------

def test_cv_score_validator_detects_discrepancy():
    """LIA says score 85 but real is 72 — should detect discrepancy."""
    result = run(validate_cv_score_claim(
        claim_text="O candidato obteve score 85 pontos na triagem.",
        context_data={"candidate_score": 72},
    ))
    assert result is not None, "Expected discrepancy message, got None"
    assert "85" in result
    assert "72" in result


def test_cv_score_validator_passes_accurate_claim():
    """LIA says score 73 and real is 72 — within tolerance of 5, should pass."""
    result = run(validate_cv_score_claim(
        claim_text="O candidato obteve score 73 pontos.",
        context_data={"candidate_score": 72},
    ))
    assert result is None, f"Expected None (within tolerance), got: {result}"


def test_cv_score_validator_no_score_in_text():
    """No score mention in text — should return None."""
    result = run(validate_cv_score_claim(
        claim_text="O candidato tem boa experiencia em Python.",
        context_data={"candidate_score": 85},
    ))
    assert result is None


def test_cv_score_validator_no_context():
    """No real score in context — should return None gracefully."""
    result = run(validate_cv_score_claim(
        claim_text="O candidato obteve score 90 pontos.",
        context_data={},
    ))
    assert result is None


def test_cv_score_validator_malformed_context():
    """Malformed score in context — should not raise, return None."""
    result = run(validate_cv_score_claim(
        claim_text="O candidato obteve score 90 pontos.",
        context_data={"candidate_score": "nao_e_numero"},
    ))
    assert result is None


# ---------------------------------------------------------------------------
# test_analytics_metric_validator_detects_wrong_days
# ---------------------------------------------------------------------------

def test_analytics_metric_validator_detects_wrong_days():
    """LIA says 15 dias but real avg is 23 days — should detect discrepancy."""
    result = run(validate_analytics_metric_claim(
        claim_text="O tempo medio de contratacao e de 15 dias.",
        context_data={"avg_time_to_hire": 23},
    ))
    assert result is not None, "Expected discrepancy for 15d vs 23d"
    assert "15" in result
    assert "23" in result


def test_analytics_metric_validator_passes_close_days():
    """LIA says 22 dias and real is 23 days — within tolerance of 3."""
    result = run(validate_analytics_metric_claim(
        claim_text="O processo leva em media 22 dias.",
        context_data={"avg_time_to_hire": 23},
    ))
    assert result is None, f"Expected None (within tolerance), got: {result}"


def test_analytics_metric_validator_no_context():
    """No avg_time_to_hire in context — should return None."""
    result = run(validate_analytics_metric_claim(
        claim_text="O processo leva em media 15 dias.",
        context_data={},
    ))
    assert result is None


# ---------------------------------------------------------------------------
# test_sourcing_count_claim
# ---------------------------------------------------------------------------

def test_sourcing_count_validator_detects_large_exaggeration():
    """LIA says 150 candidatos but real is 23 — far exceeds double."""
    result = run(validate_sourcing_count_claim(
        claim_text="Encontrei 150 candidatos para essa vaga.",
        context_data={"total_candidates": 23},
    ))
    assert result is not None
    assert "150" in result
    assert "23" in result


def test_sourcing_count_validator_skips_large_real_counts():
    """Real count is 500 — validator should skip to avoid false positives."""
    result = run(validate_sourcing_count_claim(
        claim_text="Encontrei 800 candidatos para essa vaga.",
        context_data={"total_candidates": 500},
    ))
    assert result is None, "Should not validate when real count >= 100"


# ---------------------------------------------------------------------------
# test_register_validator_adds_to_domain
# ---------------------------------------------------------------------------

def test_register_validator_adds_to_domain():
    """register_validator should add function to the domain registry."""
    # Clear any existing registrations for test isolation
    FactChecker._domain_validators.pop("test_domain", None)

    async def dummy_validator(text, ctx):
        return None

    FactChecker.register_validator("test_domain", dummy_validator)
    assert "test_domain" in FactChecker._domain_validators
    assert dummy_validator in FactChecker._domain_validators["test_domain"]


def test_register_validator_no_duplicates():
    """Registering the same validator twice should not add duplicates."""
    FactChecker._domain_validators.pop("dedup_domain", None)

    async def my_validator(text, ctx):
        return None

    FactChecker.register_validator("dedup_domain", my_validator)
    FactChecker.register_validator("dedup_domain", my_validator)
    assert len(FactChecker._domain_validators["dedup_domain"]) == 1


# ---------------------------------------------------------------------------
# test_check_response_with_domain_calls_validator
# ---------------------------------------------------------------------------

def test_check_response_with_domain_calls_validator():
    """check_response_with_domain should invoke domain validator and add claim."""
    FactChecker._domain_validators.pop("mock_domain", None)

    call_log = []

    async def tracking_validator(text, ctx):
        call_log.append((text, ctx))
        return "discrepancy detected"

    FactChecker.register_validator("mock_domain", tracking_validator)
    checker = FactChecker()
    result: FactCheckResult = run(checker.check_response_with_domain(
        response_text="Texto de resposta sem claims especiais.",
        context_data={"key": "value"},
        domain_id="mock_domain",
    ))
    assert len(call_log) == 1, "Validator should have been called once"
    assert call_log[0][1] == {"key": "value"}
    # The discrepancy should be reflected as an inaccurate claim
    domain_claims = [c for c in result.claims if c.claim_type == "domain_mock_domain"]
    assert len(domain_claims) == 1
    assert domain_claims[0].is_accurate is False


def test_check_response_with_domain_handles_validator_exception():
    """Validator that raises should not propagate — result should still be returned."""
    FactChecker._domain_validators.pop("error_domain", None)

    async def broken_validator(text, ctx):
        raise RuntimeError("simulated error")

    FactChecker.register_validator("error_domain", broken_validator)
    checker = FactChecker()
    result: FactCheckResult = run(checker.check_response_with_domain(
        response_text="Qualquer texto.",
        context_data={},
        domain_id="error_domain",
    ))
    # Should not raise; result still returned
    assert isinstance(result, FactCheckResult)


def test_check_response_with_domain_unknown_domain():
    """Domain with no registered validators should return result normally."""
    checker = FactChecker()
    result: FactCheckResult = run(checker.check_response_with_domain(
        response_text="Nenhum claim aqui.",
        context_data={},
        domain_id="unknown_domain_xyz",
    ))
    assert isinstance(result, FactCheckResult)
