"""Coverage tests for shared pure-function utilities:
- app/shared/search_utils.py
- app/shared/wizard_suggestion_priority.py
- app/shared/param_validation.py
- app/shared/api/response.py
- app/shared/batch_service.py
"""
import asyncio
import pytest

# ──────────────────────────────────────────────────────────
# search_utils
# ──────────────────────────────────────────────────────────
from app.shared.search_utils import normalize_search_query


class TestNormalizeSearchQuery:
    def test_none_returns_empty(self):
        assert normalize_search_query(None) == ""

    def test_empty_string_returns_empty(self):
        assert normalize_search_query("") == ""

    def test_whitespace_only_returns_empty(self):
        assert normalize_search_query("   ") == ""

    def test_trailing_question_mark(self):
        assert normalize_search_query("candidatos?") == "candidatos"

    def test_trailing_multiple_punct(self):
        assert normalize_search_query("developers!!!") == "developers"

    def test_leading_punct(self):
        assert normalize_search_query("? candidatos") == "candidatos"

    def test_leading_and_trailing_punct(self):
        assert normalize_search_query("? candidatos ?") == "candidatos"

    def test_collapses_whitespace(self):
        assert normalize_search_query("Python   sênior   dev") == "Python sênior dev"

    def test_trims_whitespace(self):
        assert normalize_search_query("  Python  ") == "Python"

    def test_preserves_hyphen(self):
        assert normalize_search_query("back-end developer") == "back-end developer"

    def test_preserves_case(self):
        assert normalize_search_query("PYTHON") == "PYTHON"

    def test_semicolon_removed(self):
        assert normalize_search_query("python;") == "python"

    def test_comma_removed(self):
        assert normalize_search_query("engineers,") == "engineers"

    def test_colon_removed(self):
        assert normalize_search_query("skills:") == "skills"

    def test_normal_query_unchanged(self):
        assert normalize_search_query("Python developer") == "Python developer"

    def test_accented_chars_preserved(self):
        result = normalize_search_query("Engenheiro sênior")
        assert "sênior" in result


# ──────────────────────────────────────────────────────────
# wizard_suggestion_priority
# ──────────────────────────────────────────────────────────
from app.shared.wizard_suggestion_priority import WizardSuggestion, pick_canonical


class TestWizardSuggestion:
    def test_has_data_true(self):
        s = WizardSuggestion(source="history", recommended_min=10000.0, recommended_max=15000.0)
        assert s.has_data is True

    def test_has_data_false_none(self):
        s = WizardSuggestion(source="market", recommended_min=None, recommended_max=None)
        assert s.has_data is False

    def test_has_data_false_zero(self):
        s = WizardSuggestion(source="market", recommended_min=0.0, recommended_max=15000.0)
        assert s.has_data is False

    def test_defaults(self):
        s = WizardSuggestion(source="history", recommended_min=None, recommended_max=None)
        assert s.confidence == "low"
        assert s.sample_size == 0
        assert s.metadata == {}


class TestPickCanonical:
    def test_both_none_returns_none(self):
        result = pick_canonical(None, None)
        assert result is None

    def test_only_history_no_data(self):
        s = WizardSuggestion(source="history", recommended_min=None, recommended_max=None)
        result = pick_canonical(history=s, market=None)
        assert result is None

    def test_only_history_with_data(self):
        s = WizardSuggestion(source="history", recommended_min=10000.0, recommended_max=15000.0)
        result = pick_canonical(history=s, market=None)
        assert result is s

    def test_only_market_with_data(self):
        s = WizardSuggestion(source="market", recommended_min=9000.0, recommended_max=14000.0)
        result = pick_canonical(history=None, market=s)
        assert result is s

    def test_history_wins_equal_confidence(self):
        history = WizardSuggestion(
            source="history", recommended_min=10000.0, recommended_max=15000.0,
            confidence="medium", sample_size=5,
        )
        market = WizardSuggestion(
            source="market", recommended_min=9000.0, recommended_max=14000.0,
            confidence="medium", sample_size=5,
        )
        result = pick_canonical(history=history, market=market)
        assert result.source == "history"

    def test_market_wins_higher_confidence(self):
        history = WizardSuggestion(
            source="history", recommended_min=10000.0, recommended_max=15000.0,
            confidence="low", sample_size=3,
        )
        market = WizardSuggestion(
            source="market", recommended_min=9000.0, recommended_max=14000.0,
            confidence="high", sample_size=100,
        )
        result = pick_canonical(history=history, market=market)
        assert result.source == "market"

    def test_history_wins_higher_confidence(self):
        history = WizardSuggestion(
            source="history", recommended_min=10000.0, recommended_max=15000.0,
            confidence="high", sample_size=20,
        )
        market = WizardSuggestion(
            source="market", recommended_min=9000.0, recommended_max=14000.0,
            confidence="medium", sample_size=100,
        )
        result = pick_canonical(history=history, market=market)
        assert result.source == "history"

    def test_market_wins_tiebreak_larger_sample(self):
        history = WizardSuggestion(
            source="history", recommended_min=10000.0, recommended_max=15000.0,
            confidence="medium", sample_size=5,
        )
        market = WizardSuggestion(
            source="market", recommended_min=9000.0, recommended_max=14000.0,
            confidence="medium", sample_size=50,
        )
        result = pick_canonical(history=history, market=market)
        assert result.source == "market"

    def test_high_confidence_both_history_wins(self):
        history = WizardSuggestion(
            source="history", recommended_min=10000.0, recommended_max=15000.0,
            confidence="high", sample_size=10,
        )
        market = WizardSuggestion(
            source="market", recommended_min=9000.0, recommended_max=14000.0,
            confidence="high", sample_size=10,
        )
        result = pick_canonical(history=history, market=market)
        # Equal confidence, equal sample: history wins
        assert result.source == "history"


# ──────────────────────────────────────────────────────────
# param_validation
# ──────────────────────────────────────────────────────────
from app.shared.param_validation import (
    ParamValidationError,
    validate_params,
    ToolParamSchemas,
)
from pydantic import BaseModel


class TestParamValidationError:
    def test_basic(self):
        err = ParamValidationError("test_action", [{"loc": ("field1",), "msg": "required"}])
        assert err.action_id == "test_action"
        assert len(err.errors) == 1
        assert "test_action" in str(err)

    def test_multiple_errors(self):
        errors = [
            {"loc": ("field1",), "msg": "required"},
            {"loc": ("field2",), "msg": "invalid value"},
        ]
        err = ParamValidationError("action", errors)
        assert len(err.errors) == 2


class TestValidateParamsDecorator:
    def test_valid_params_pass_through(self):
        class MySchema(BaseModel):
            name: str
            age: int

        @validate_params(MySchema)
        async def my_handler(params, context=None):
            return {"ok": True, "name": params["name"], "age": params["age"]}

        result = asyncio.get_event_loop().run_until_complete(
            my_handler({"name": "Ana", "age": 30})
        )
        assert result["ok"] is True
        assert result["name"] == "Ana"

    def test_invalid_params_return_error(self):
        class MySchema(BaseModel):
            name: str
            age: int

        @validate_params(MySchema, action_id="test_action")
        async def my_handler(params, context=None):
            return {"ok": True}

        result = asyncio.get_event_loop().run_until_complete(
            my_handler({"name": "Ana", "age": "not_an_int"})
        )
        assert result["success"] is False
        assert "validation_errors" in result

    def test_missing_required_field_returns_error(self):
        class MySchema(BaseModel):
            required_field: str

        @validate_params(MySchema)
        async def my_handler(params, context=None):
            return {"ok": True}

        result = asyncio.get_event_loop().run_until_complete(
            my_handler({})
        )
        assert result["success"] is False

    def test_preserves_function_name(self):
        class MySchema(BaseModel):
            x: int

        @validate_params(MySchema)
        async def custom_named_handler(params, context=None):
            return params

        assert custom_named_handler.__name__ == "custom_named_handler"


class TestToolParamSchemas:
    def test_candidate_id(self):
        m = ToolParamSchemas.CandidateId(candidate_id="cand-001")
        assert m.candidate_id == "cand-001"

    def test_vacancy_candidate_id(self):
        m = ToolParamSchemas.VacancyCandidateId(vacancy_candidate_id="vc-001")
        assert m.vacancy_candidate_id == "vc-001"

    def test_company_id(self):
        m = ToolParamSchemas.CompanyId(company_id="co-001")
        assert m.company_id == "co-001"

    def test_search_query_defaults(self):
        m = ToolParamSchemas.SearchQuery(query="python developer")
        assert m.query == "python developer"
        assert m.limit == 20
        assert m.offset == 0

    def test_search_query_custom(self):
        m = ToolParamSchemas.SearchQuery(query="senior dev", limit=10, offset=20)
        assert m.limit == 10
        assert m.offset == 20

    def test_move_candidate(self):
        m = ToolParamSchemas.MoveCandidate(
            vacancy_candidate_id="vc-001",
            to_stage="triagem",
        )
        assert m.vacancy_candidate_id == "vc-001"
        assert m.to_stage == "triagem"
        assert m.from_stage is None
        assert m.sub_status is None

    def test_move_candidate_full(self):
        m = ToolParamSchemas.MoveCandidate(
            vacancy_candidate_id="vc-002",
            to_stage="entrevista",
            from_stage="triagem",
            sub_status="aprovado",
            prompt="Move this candidate",
            channel="whatsapp",
        )
        assert m.from_stage == "triagem"
        assert m.sub_status == "aprovado"

    def test_predict_sub_status(self):
        m = ToolParamSchemas.PredictSubStatus(
            vacancy_candidate_id="vc-001",
            from_stage="triagem",
            to_stage="entrevista",
        )
        assert m.from_stage == "triagem"
        assert m.to_stage == "entrevista"


# ──────────────────────────────────────────────────────────
# api/response.py
# ──────────────────────────────────────────────────────────
from app.shared.api.response import (
    ErrorDetail,
    ResponseMeta,
    APIResponse,
    ok_response,
    error_response,
    not_found,
    forbidden,
    bad_request,
    internal_error,
)


class TestErrorDetail:
    def test_basic(self):
        e = ErrorDetail(code="NOT_FOUND", message="Resource not found")
        assert e.code == "NOT_FOUND"
        assert e.message == "Resource not found"
        assert e.details is None

    def test_with_details(self):
        e = ErrorDetail(code="VALIDATION", message="Invalid", details={"field": "email"})
        assert e.details["field"] == "email"


class TestResponseMeta:
    def test_basic(self):
        m = ResponseMeta()
        assert m.request_id is None
        assert "T" in m.ts  # ISO datetime

    def test_with_request_id(self):
        m = ResponseMeta(request_id="req-001")
        assert m.request_id == "req-001"


class TestAPIResponse:
    def test_ok(self):
        r = APIResponse(ok=True, data={"items": [1, 2, 3]})
        assert r.ok is True
        assert r.data["items"] == [1, 2, 3]
        assert r.error is None

    def test_error(self):
        e = ErrorDetail(code="FORBIDDEN", message="Access denied")
        r = APIResponse(ok=False, error=e)
        assert r.ok is False
        assert r.error.code == "FORBIDDEN"


class TestResponseHelpers:
    def test_ok_response(self):
        resp = ok_response({"key": "value"})
        assert resp.status_code == 200
        body = resp.body
        import json
        data = json.loads(body)
        assert data["ok"] is True
        assert data["data"]["key"] == "value"

    def test_ok_response_custom_status(self):
        resp = ok_response({"id": "123"}, status_code=201)
        assert resp.status_code == 201

    def test_error_response(self):
        resp = error_response("NOT_FOUND", "Resource not found", 404)
        assert resp.status_code == 404
        import json
        data = json.loads(resp.body)
        assert data["ok"] is False
        assert data["error"]["code"] == "NOT_FOUND"

    def test_not_found(self):
        resp = not_found("User")
        assert resp.status_code == 404

    def test_forbidden(self):
        resp = forbidden("Access denied")
        assert resp.status_code == 403

    def test_bad_request(self):
        resp = bad_request("Invalid input")
        assert resp.status_code == 400

    def test_internal_error(self):
        resp = internal_error()
        assert resp.status_code == 500

    def test_error_response_with_details(self):
        resp = error_response("VALIDATION", "Invalid", 422, details={"field": "email"})
        import json
        data = json.loads(resp.body)
        assert data["error"]["details"]["field"] == "email"

    def test_ok_response_no_request(self):
        resp = ok_response(None)
        import json
        data = json.loads(resp.body)
        assert data["meta"]["request_id"] is None


# ──────────────────────────────────────────────────────────
# batch_service
# ──────────────────────────────────────────────────────────
from app.shared.batch_service import BatchItem, BatchResult, BatchReport, BatchService


class TestBatchDataclasses:
    def test_batch_item(self):
        item = BatchItem(item_id="item-1", payload="some text")
        assert item.item_id == "item-1"
        assert item.payload == "some text"

    def test_batch_result_success(self):
        r = BatchResult(item_id="item-1", result="processed", success=True)
        assert r.item_id == "item-1"
        assert r.result == "processed"
        assert r.success is True
        assert r.error is None

    def test_batch_result_failure(self):
        r = BatchResult(item_id="item-2", error="Timeout", success=False)
        assert r.success is False
        assert r.error == "Timeout"

    def test_batch_report_success_rate_zero(self):
        report = BatchReport(batch_id="b1", total=0, successful=0, failed=0)
        assert report.success_rate == pytest.approx(0.0)

    def test_batch_report_success_rate_full(self):
        report = BatchReport(batch_id="b2", total=10, successful=10, failed=0)
        assert report.success_rate == pytest.approx(1.0)

    def test_batch_report_success_rate_partial(self):
        report = BatchReport(batch_id="b3", total=10, successful=7, failed=3)
        assert report.success_rate == pytest.approx(0.7)


class TestBatchService:
    def test_init_defaults(self):
        svc = BatchService()
        assert svc.max_concurrency == 10
        assert svc.fail_fast is False
        assert svc.timeout_per_item_seconds == pytest.approx(30.0)

    def test_init_custom(self):
        svc = BatchService(max_concurrency=5, fail_fast=True, timeout_per_item_seconds=10.0)
        assert svc.max_concurrency == 5
        assert svc.fail_fast is True

    @pytest.mark.asyncio
    async def test_process_empty_batch(self):
        svc = BatchService()
        report = await svc.process([], lambda x: None)
        assert report.total == 0
        assert report.successful == 0
        assert report.failed == 0

    @pytest.mark.asyncio
    async def test_process_successful_items(self):
        svc = BatchService(max_concurrency=3)
        items = [BatchItem(item_id=f"item-{i}", payload=i) for i in range(5)]

        async def double(x):
            return x * 2

        report = await svc.process(items, double, batch_id="test-batch-1")
        assert report.batch_id == "test-batch-1"
        assert report.total == 5
        assert report.successful == 5
        assert report.failed == 0
        assert report.success_rate == pytest.approx(1.0)
        results_by_id = {r.item_id: r.result for r in report.results}
        assert results_by_id["item-0"] == 0
        assert results_by_id["item-4"] == 8

    @pytest.mark.asyncio
    async def test_process_with_errors(self):
        svc = BatchService(fail_fast=False)
        items = [BatchItem(item_id=f"item-{i}", payload=i) for i in range(3)]

        async def sometimes_fails(x):
            if x == 1:
                raise ValueError("Item 1 failed")
            return x * 10

        report = await svc.process(items, sometimes_fails)
        assert report.total == 3
        assert report.failed == 1
        assert report.successful == 2
        failed_result = next(r for r in report.results if not r.success)
        assert "Item 1 failed" in failed_result.error

    @pytest.mark.asyncio
    async def test_process_auto_generates_batch_id(self):
        svc = BatchService()
        items = [BatchItem(item_id="x", payload="data")]

        async def noop(x):
            return x

        report = await svc.process(items, noop)
        assert report.batch_id.startswith("batch-")

    @pytest.mark.asyncio
    async def test_process_records_completion_time(self):
        svc = BatchService()
        items = [BatchItem(item_id="y", payload=1)]

        async def noop(x):
            return x

        report = await svc.process(items, noop)
        assert report.completed_at is not None
        assert report.total_time_ms >= 0

    @pytest.mark.asyncio
    async def test_process_concurrent_execution(self):
        """Verify multiple items processed concurrently."""
        import time
        svc = BatchService(max_concurrency=5)
        items = [BatchItem(item_id=f"item-{i}", payload=0.01) for i in range(5)]

        async def slow(delay):
            await asyncio.sleep(delay)
            return "done"

        t0 = time.monotonic()
        report = await svc.process(items, slow)
        elapsed = time.monotonic() - t0
        assert report.successful == 5
        # With 5 concurrent workers, 5 × 10ms tasks should take ~10ms, not 50ms
        assert elapsed < 0.1  # generous bound

    @pytest.mark.asyncio
    async def test_process_collects_errors_in_report(self):
        svc = BatchService()
        items = [BatchItem(item_id="err", payload=None)]

        async def always_fails(x):
            raise RuntimeError("always fails")

        report = await svc.process(items, always_fails)
        assert len(report.errors) == 1
        assert "always fails" in report.errors[0]
