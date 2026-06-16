"""UC-P1-24: BARSEvaluator generalization — LLM response quality evaluation."""
import pytest


def test_bars_result_structure():
    from app.shared.evaluation.bars_evaluator import BARSResult

    r = BARSResult(
        scores={"accuracy": 4.0, "helpfulness": 3.5, "safety": 5.0},
        reasoning={"accuracy": "ok"},
        overall=4.17,
    )
    d = r.to_dict()
    assert "scores" in d
    assert "overall" in d
    assert "passed" in d


def test_bars_result_passed_threshold():
    from app.shared.evaluation.bars_evaluator import BARSResult

    passing = BARSResult(scores={}, reasoning={}, overall=3.0)
    failing = BARSResult(scores={}, reasoning={}, overall=2.9)
    assert passing.passed is True
    assert failing.passed is False


def test_heuristic_evaluate_returns_result():
    from app.shared.evaluation.bars_evaluator import BARSEvaluator

    ev = BARSEvaluator()
    result = ev._heuristic_evaluate(
        "This is a helpful response with structured bullet points:\n- Point 1\n- Point 2"
    )
    assert result.overall > 0
    assert isinstance(result.passed, bool)


@pytest.mark.asyncio
async def test_evaluate_async_no_llm():
    from app.shared.evaluation.bars_evaluator import BARSEvaluator

    ev = BARSEvaluator()
    result = await ev.evaluate("Test response about recruitment best practices.")
    assert 1.0 <= result.overall <= 5.0


def test_domain_bars_mixin_returns_evaluator():
    from app.shared.evaluation.bars_evaluator import DomainBARSMixin, BARSEvaluator

    class TestDomain(DomainBARSMixin):
        pass

    d = TestDomain()
    assert isinstance(d.bars_evaluator, BARSEvaluator)


def test_pii_in_response_lowers_safety_score():
    from app.shared.evaluation.bars_evaluator import BARSEvaluator

    ev = BARSEvaluator()
    result = ev._heuristic_evaluate("Candidate CPF: 123.456.789-00")
    assert result.scores["safety"] < 5.0


@pytest.mark.asyncio
async def test_domain_mixin_evaluate_response():
    from app.shared.evaluation.bars_evaluator import DomainBARSMixin

    class TestDomain(DomainBARSMixin):
        pass

    domain = TestDomain()
    result = await domain.evaluate_response(
        "The candidate shows strong Python skills and clear communication."
    )
    assert 1.0 <= result.overall <= 5.0


def test_custom_rubric_used_by_evaluator():
    from app.shared.evaluation.bars_evaluator import BARSRubric, BARSEvaluator

    custom = BARSRubric({"clarity": {"5": "crystal clear", "1": "confusing"}})
    ev = BARSEvaluator(rubric=custom)
    assert ev.rubric is custom


def test_hedge_words_lower_accuracy():
    from app.shared.evaluation.bars_evaluator import BARSEvaluator

    ev = BARSEvaluator()
    no_hedge = ev._heuristic_evaluate("The candidate has Python experience.")
    with_hedge = ev._heuristic_evaluate(
        "Talvez o candidato provavelmente pode ser qualificado."
    )
    assert no_hedge.scores["accuracy"] >= with_hedge.scores["accuracy"]
