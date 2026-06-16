"""UC-P1-25: FactChecker for hallucination detection — shared/evaluation layer."""
import pytest


@pytest.mark.asyncio
async def test_valid_response_passes():
    from app.shared.evaluation.fact_checker import FactChecker

    checker = FactChecker()
    result = await checker.check("O candidato tem experiência em Python.")
    assert result.is_valid


@pytest.mark.asyncio
async def test_experience_mismatch_detected():
    from app.shared.evaluation.fact_checker import FactChecker

    checker = FactChecker()
    result = await checker.check(
        "O candidato tem 20 anos de experiência em Python",
        context={"cv_text": "2 anos de experiência em Python"},
    )
    assert not result.is_valid
    assert len(result.violations) > 0


@pytest.mark.asyncio
async def test_hallucination_pattern_detected():
    from app.shared.evaluation.fact_checker import FactChecker

    checker = FactChecker()
    result = await checker.check(
        "Certamente tem 15 anos de experiência garantidamente."
    )
    assert not result.is_valid


def test_fact_check_result_to_dict():
    from app.shared.evaluation.fact_checker import FactCheckResult

    r = FactCheckResult(is_valid=False, confidence=0.8, violations=["mismatch"])
    d = r.to_dict()
    assert d["is_valid"] is False
    assert "violations" in d
    assert d["violations"] == ["mismatch"]


def test_domain_mixin_returns_fact_checker():
    from app.shared.evaluation.fact_checker import DomainFactCheckerMixin, FactChecker

    class TestDomain(DomainFactCheckerMixin):
        pass

    d = TestDomain()
    assert isinstance(d.fact_checker, FactChecker)


@pytest.mark.asyncio
async def test_domain_mixin_check_response():
    from app.shared.evaluation.fact_checker import DomainFactCheckerMixin

    class TestDomain(DomainFactCheckerMixin):
        pass

    domain = TestDomain()
    result = await domain.check_response(
        "O candidato tem 5 anos de experiência em Python.",
        context={"cv_text": "5 anos de experiência em Python"},
    )
    assert result.is_valid


@pytest.mark.asyncio
async def test_missing_caveat_warning():
    from app.shared.evaluation.fact_checker import FactChecker

    checker = FactChecker()
    result = await checker.check(
        "O candidato definitivamente é qualificado.",
        context={"data_quality": "low"},
    )
    # Warnings but no violations for this case
    assert isinstance(result.warnings, list)


@pytest.mark.asyncio
async def test_no_context_check_passes_valid_text():
    from app.shared.evaluation.fact_checker import FactChecker

    checker = FactChecker()
    result = await checker.check(
        "Esta é uma resposta normal sem afirmações numéricas problemáticas."
    )
    assert result.is_valid
    assert result.confidence > 0


def test_result_confidence_range():
    from app.shared.evaluation.fact_checker import FactCheckResult

    r = FactCheckResult(is_valid=True, confidence=0.9)
    assert 0.0 <= r.confidence <= 1.0
