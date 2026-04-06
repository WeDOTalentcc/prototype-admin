"""
Tests for the 3 policy gaps fixed:
  1. salary_expectation_filter + salary_tolerance_percent enforcement in batch screening
  2. manager_approval_for_offer added to warnings (not just metadata)
  3. governance_collector reads company policy defaults (tested via unit logic)
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ─────────────────────────────────────────────────────────────────
# Gap 1 — Salary filter (_check_salary_compatibility)
# ─────────────────────────────────────────────────────────────────
from app.domains.cv_screening.services.cv_screening_batch_service import (
    _check_salary_compatibility,
)


class TestCheckSalaryCompatibility:
    def test_no_salary_range_always_compatible(self):
        candidate = {"salary_expectation_clt": 20000}
        assert _check_salary_compatibility(candidate, None, 15) is True

    def test_salary_range_without_max_always_compatible(self):
        candidate = {"salary_expectation_clt": 20000}
        assert _check_salary_compatibility(candidate, {"min": 5000}, 15) is True

    def test_salary_range_max_zero_always_compatible(self):
        candidate = {"salary_expectation_clt": 20000}
        assert _check_salary_compatibility(candidate, {"max": 0}, 15) is True

    def test_candidate_without_expectations_always_compatible(self):
        salary_range = {"min": 5000, "max": 10000}
        assert _check_salary_compatibility({}, salary_range, 15) is True

    def test_candidate_with_none_expectations_always_compatible(self):
        candidate = {
            "salary_expectation_clt": None,
            "salary_expectation_pj": None,
            "salary_expectation_freelance": None,
        }
        assert _check_salary_compatibility(candidate, {"max": 10000}, 15) is True

    def test_clt_within_tolerance_is_compatible(self):
        # max=10000, tolerance=15% => ceiling=11500
        candidate = {"salary_expectation_clt": 11000}
        assert _check_salary_compatibility(candidate, {"max": 10000}, 15) is True

    def test_clt_exactly_at_ceiling_is_compatible(self):
        # max=10000, tolerance=15% => ceiling=11500
        candidate = {"salary_expectation_clt": 11500}
        assert _check_salary_compatibility(candidate, {"max": 10000}, 15) is True

    def test_clt_above_tolerance_is_incompatible(self):
        # max=10000, tolerance=15% => ceiling=11500; expectation=12000 > 11500
        candidate = {"salary_expectation_clt": 12000}
        assert _check_salary_compatibility(candidate, {"max": 10000}, 15) is False

    def test_uses_minimum_expectation_across_types(self):
        # pj=15000 but clt=9000 — lowest is 9000 which is <= ceiling(11500)
        candidate = {
            "salary_expectation_clt": 9000,
            "salary_expectation_pj": 15000,
        }
        assert _check_salary_compatibility(candidate, {"max": 10000}, 15) is True

    def test_zero_tolerance_uses_exact_max(self):
        # tolerance=0 => ceiling=10000
        candidate = {"salary_expectation_clt": 10001}
        assert _check_salary_compatibility(candidate, {"max": 10000}, 0) is False

    def test_zero_tolerance_at_exact_max_is_compatible(self):
        candidate = {"salary_expectation_clt": 10000}
        assert _check_salary_compatibility(candidate, {"max": 10000}, 0) is True

    def test_zero_expectations_treated_as_missing(self):
        # 0 values should be treated as "not informed" → compatible
        candidate = {"salary_expectation_clt": 0}
        assert _check_salary_compatibility(candidate, {"max": 10000}, 15) is True


# ─────────────────────────────────────────────────────────────────
# Gap 2 — manager_approval_for_offer in warnings
# ─────────────────────────────────────────────────────────────────

import asyncio


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestPipelinePolicyManagerApprovalWarning:
    """
    Validates that pipeline_policy.validate_transition includes manager approval
    in the warnings list (so the amber box is shown in the Kanban modal).
    """

    def _make_mock_db(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalar=MagicMock(return_value=5)))
        return db

    @patch("app.api.v1.pipeline_policy.get_policy_for_company")
    def test_manager_approval_appears_in_warnings(self, mock_policy):
        mock_policy.return_value = {
            "id": "policy-1",
            "pipeline_rules": {
                "min_interviews_before_offer": 1,
                "manager_approval_for_offer": True,
            },
        }
        from app.api.v1.pipeline_policy import validate_transition

        result = _run(
            validate_transition(
                company_id="company-1",
                candidate_id="cand-1",
                target_stage="proposta",
                db=self._make_mock_db(),
            )
        )

        assert result["metadata"]["requires_manager_approval"] is True
        assert any("gestor" in w.lower() for w in result["warnings"]), (
            "Expected manager approval warning in warnings list"
        )

    @patch("app.api.v1.pipeline_policy.get_policy_for_company")
    def test_no_manager_approval_no_warning(self, mock_policy):
        mock_policy.return_value = {
            "id": "policy-1",
            "pipeline_rules": {
                "min_interviews_before_offer": 1,
                "manager_approval_for_offer": False,
            },
        }
        from app.api.v1.pipeline_policy import validate_transition

        result = _run(
            validate_transition(
                company_id="company-1",
                candidate_id="cand-1",
                target_stage="proposta",
                db=self._make_mock_db(),
            )
        )

        assert result["metadata"].get("requires_manager_approval") is None
        assert not any("gestor" in w.lower() for w in result["warnings"])

    @patch("app.api.v1.pipeline_policy.get_policy_for_company")
    def test_non_offer_stage_no_warnings(self, mock_policy):
        mock_policy.return_value = {
            "id": "policy-1",
            "pipeline_rules": {"manager_approval_for_offer": True},
        }
        from app.api.v1.pipeline_policy import validate_transition

        result = _run(
            validate_transition(
                company_id="company-1",
                candidate_id="cand-1",
                target_stage="triagem",
                db=self._make_mock_db(),
            )
        )

        assert result["warnings"] == []
        assert result["blockers"] == []


# ─────────────────────────────────────────────────────────────────
# Gap 3 — get_screening_policy exposes salary filter fields
# ─────────────────────────────────────────────────────────────────

class TestGetScreeningPolicySalaryFields:
    @pytest.mark.asyncio
    @patch("app.domains.cv_screening.services.wsi_screening_pipeline.get_policy_for_company")
    async def test_returns_salary_filter_fields_when_policy_exists(self, mock_policy):
        mock_policy.return_value = {
            "screening_rules": {
                "salary_expectation_filter": True,
                "salary_tolerance_percent": 20,
                "experience_policy": "per_job",
                "default_screening_questions": [],
            }
        }
        from app.domains.cv_screening.services.wsi_screening_pipeline import (
            wsi_screening_pipeline,
        )

        result = await wsi_screening_pipeline.get_screening_policy(
            company_id="company-1", db=AsyncMock()
        )

        assert result["salary_expectation_filter"] is True
        assert result["salary_tolerance_percent"] == 20

    @pytest.mark.asyncio
    async def test_returns_salary_filter_defaults_when_no_db(self):
        from app.domains.cv_screening.services.wsi_screening_pipeline import (
            wsi_screening_pipeline,
        )

        result = await wsi_screening_pipeline.get_screening_policy(
            company_id="company-1", db=None
        )

        assert result["salary_expectation_filter"] is False
        assert result["salary_tolerance_percent"] == 15

    @pytest.mark.asyncio
    @patch("app.domains.cv_screening.services.wsi_screening_pipeline.get_policy_for_company")
    async def test_returns_defaults_when_policy_missing_salary_fields(self, mock_policy):
        mock_policy.return_value = {
            "screening_rules": {
                "experience_policy": "global",
            }
        }
        from app.domains.cv_screening.services.wsi_screening_pipeline import (
            wsi_screening_pipeline,
        )

        result = await wsi_screening_pipeline.get_screening_policy(
            company_id="company-1", db=AsyncMock()
        )

        assert result["salary_expectation_filter"] is False
        assert result["salary_tolerance_percent"] == 15
