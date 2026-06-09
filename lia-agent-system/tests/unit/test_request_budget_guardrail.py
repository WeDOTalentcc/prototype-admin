"""
Tests for per-request token budget guardrail (Fase 3 — Task #129).
"""
import pytest

from app.domains.credits.services.token_budget_service import (
    AGENT_TYPE_REQUEST_OVERRIDES,
    DEFAULT_REQUEST_LIMIT,
    PLAN_REQUEST_LIMITS,
    RequestBudgetExceededError,
    check_request_budget,
    check_request_budget_before_llm,
    estimate_request_tokens,
    get_request_limit,
)


class TestGetRequestLimit:
    def test_starter_plan(self):
        assert get_request_limit("starter") == 2_000

    def test_pro_plan(self):
        assert get_request_limit("pro") == 10_000

    def test_business_plan(self):
        assert get_request_limit("business") == 25_000

    def test_enterprise_plan(self):
        assert get_request_limit("enterprise") == 50_000

    def test_unknown_plan_returns_default(self):
        assert get_request_limit("mystery_plan") == DEFAULT_REQUEST_LIMIT

    def test_none_plan_returns_default(self):
        assert get_request_limit(None) == DEFAULT_REQUEST_LIMIT

    def test_case_insensitive(self):
        assert get_request_limit("PRO") == 10_000
        assert get_request_limit("  Business  ") == 25_000

    def test_agent_type_override_multiplier(self):
        base = PLAN_REQUEST_LIMITS["pro"]
        result = get_request_limit("pro", agent_type="DeepAnalysisAgent")
        assert result == int(base * 2.0)

    def test_agent_type_no_override(self):
        assert get_request_limit("pro", agent_type="UnknownAgent") == 10_000

    def test_rag_agent_override(self):
        base = PLAN_REQUEST_LIMITS["business"]
        result = get_request_limit("business", agent_type="RAGAgent")
        assert result == int(base * 1.5)


class TestEstimateRequestTokens:
    def test_simple_prompt(self):
        prompt = "Hello world"
        result = estimate_request_tokens(prompt)
        assert result > 0

    def test_prompt_with_system(self):
        prompt = "Hello"
        system = "You are a helpful assistant."
        with_system = estimate_request_tokens(prompt, system)
        without_system = estimate_request_tokens(prompt)
        assert with_system > without_system

    def test_explicit_output_tokens(self):
        prompt = "Hello"
        result = estimate_request_tokens(prompt, expected_output_tokens=500)
        assert result > 500

    def test_empty_prompt(self):
        result = estimate_request_tokens("")
        assert result > 0

    def test_large_prompt_proportional(self):
        small = estimate_request_tokens("a" * 100)
        large = estimate_request_tokens("a" * 10000)
        assert large > small


class TestCheckRequestBudget:
    def test_allowed_small_request(self):
        allowed, estimated, ceiling = check_request_budget(
            "pro", 500, company_id="c1", user_id="u1"
        )
        assert allowed is True
        assert estimated == 500
        assert ceiling == 10_000

    def test_blocked_large_request(self):
        allowed, estimated, ceiling = check_request_budget(
            "starter", 5_000, company_id="c1", user_id="u1"
        )
        assert allowed is False
        assert estimated == 5_000
        assert ceiling == 2_000

    def test_exact_ceiling_allowed(self):
        allowed, _, ceiling = check_request_budget("starter", 2_000)
        assert allowed is True
        assert ceiling == 2_000

    def test_one_over_ceiling_blocked(self):
        allowed, _, _ = check_request_budget("starter", 2_001)
        assert allowed is False

    def test_agent_type_override_allows_larger(self):
        allowed, _, ceiling = check_request_budget(
            "pro", 15_000, agent_type="DeepAnalysisAgent"
        )
        assert allowed is True
        assert ceiling == 20_000

    def test_enterprise_high_ceiling(self):
        allowed, _, ceiling = check_request_budget("enterprise", 49_000)
        assert allowed is True
        assert ceiling == 50_000

    def test_none_plan_uses_default(self):
        allowed, _, ceiling = check_request_budget(None, 3_000)
        assert allowed is False
        assert ceiling == DEFAULT_REQUEST_LIMIT


class TestCheckRequestBudgetBeforeLLM:
    def test_passes_for_small_prompt(self):


        check_request_budget_before_llm(
            "Hello",
            plan_code="pro",
            company_id="c1",
        )

    def test_raises_for_huge_prompt(self):


        huge_prompt = "x" * 100_000
        with pytest.raises(RequestBudgetExceededError) as exc_info:
            check_request_budget_before_llm(
                huge_prompt,
                plan_code="starter",
                company_id="c1",
            )
        assert exc_info.value.ceiling == 2_000
        assert exc_info.value.estimated_tokens > 2_000
        assert exc_info.value.company_id == "c1"

    def test_negative_expected_output_tokens_clamped(self):
        est_neg = estimate_request_tokens("Hello", expected_output_tokens=-100)
        est_default = estimate_request_tokens("Hello")
        assert est_neg == est_default

    def test_zero_expected_output_tokens_clamped(self):
        est_zero = estimate_request_tokens("Hello", expected_output_tokens=0)
        est_default = estimate_request_tokens("Hello")
        assert est_zero == est_default

    def test_exception_has_structured_fields(self):


        with pytest.raises(RequestBudgetExceededError) as exc_info:
            check_request_budget_before_llm(
                "x" * 100_000,
                plan_code="starter",
                agent_type="TestAgent",
                company_id="c1",
            )
        err = exc_info.value
        assert err.plan_code == "starter"
        assert err.agent_type == "TestAgent"
        assert err.company_id == "c1"

    def test_agent_override_relaxes_ceiling(self):


        medium_prompt = "x" * 30_000
        check_request_budget_before_llm(
            medium_prompt,
            plan_code="pro",
            agent_type="DeepAnalysisAgent",
            company_id="c1",
        )

    def test_none_plan_enforces_default_ceiling(self):


        large_prompt = "x" * 100_000
        with pytest.raises(RequestBudgetExceededError) as exc_info:
            check_request_budget_before_llm(
                large_prompt,
                plan_code=None,
                company_id=None,
            )
        assert exc_info.value.ceiling == DEFAULT_REQUEST_LIMIT

    def test_none_plan_allows_small(self):


        check_request_budget_before_llm(
            "Hello",
            plan_code=None,
            company_id=None,
        )

    def test_known_plan_blocks_large(self):
        allowed, _, ceiling = check_request_budget("starter", 5_000)
        assert allowed is False
        assert ceiling == 2_000
