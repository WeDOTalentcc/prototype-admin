"""test_conditions_canonical.py — Sprint A.8 sensor.

Pin canonical lists + API shape + fail-CLOSED lookups + endpoint smoke.

Audit ref: AUTOMATIONS_SPRINT_PLAN_ADR.md Sprint A.8.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.shared.automation.conditions_canonical import (
    CONDITION_FIELDS_CATALOG,
    OPERATORS_CATALOG,
    condition_fields_to_api_response,
    get_condition_field,
    get_operator,
    operators_to_api_response,
)


# ---------------------------------------------------------------------------
# Canonical catalogs — pin shape + size
# ---------------------------------------------------------------------------


class TestOperatorsCatalog:
    def test_has_ten_canonical_operators(self):
        assert len(OPERATORS_CATALOG) == 10, (
            "Sprint A.8 canonical: 10 operators (eq/neq/gt/gte/lt/lte/contains/"
            "not_contains/in/is_empty). Mudou? Atualize sensor + frontend types."
        )

    def test_all_operators_have_unique_values(self):
        values = [op.value for op in OPERATORS_CATALOG]
        assert len(values) == len(set(values)), f"Operator values duplicados: {values}"

    def test_all_operators_have_pt_and_en_labels(self):
        for op in OPERATORS_CATALOG:
            assert op.label_pt, f"Operator {op.value} sem label_pt"
            assert op.label_en, f"Operator {op.value} sem label_en"

    def test_applicable_types_only_canonical(self):
        canonical = {"number", "string", "boolean", "list"}
        for op in OPERATORS_CATALOG:
            invalid = set(op.applicable_types) - canonical
            assert not invalid, (
                f"Operator {op.value} declara tipo não-canonical: {invalid}. "
                f"Permitidos: {canonical}."
            )


class TestConditionFieldsCatalog:
    def test_has_at_least_ten_fields(self):
        assert len(CONDITION_FIELDS_CATALOG) >= 10, (
            "Sprint A.8 canonical: 10+ condition fields. "
            f"Atual: {len(CONDITION_FIELDS_CATALOG)}."
        )

    def test_all_fields_have_unique_values(self):
        values = [f.value for f in CONDITION_FIELDS_CATALOG]
        assert len(values) == len(set(values)), f"Field values duplicados: {values}"

    def test_covers_candidate_job_pipeline(self):
        categories = {f.category for f in CONDITION_FIELDS_CATALOG}
        for required in ("candidate", "job", "pipeline"):
            assert required in categories, (
                f"Catalog deve cobrir categoria {required!r}. Atual: {categories}."
            )

    def test_types_canonical(self):
        canonical = {"number", "string", "boolean", "list"}
        for f in CONDITION_FIELDS_CATALOG:
            assert f.type in canonical, (
                f"Field {f.value} type {f.type!r} não-canonical. Permitido: {canonical}."
            )

    def test_value_uses_dotted_path(self):
        """Canonical paths usam dot notation `category.field`."""
        for f in CONDITION_FIELDS_CATALOG:
            assert "." in f.value, (
                f"Field {f.value!r} deve usar dot notation (ex: 'candidate.wsi_score')."
            )


# ---------------------------------------------------------------------------
# API response shape
# ---------------------------------------------------------------------------


class TestApiResponseShape:
    def test_operators_response_shape(self):
        resp = operators_to_api_response()
        assert isinstance(resp, list)
        assert len(resp) == len(OPERATORS_CATALOG)
        for item in resp:
            assert set(item.keys()) >= {
                "value",
                "name",
                "label_pt",
                "label_en",
                "applicable_types",
            }, f"Item operator faltando keys: {item}"

    def test_condition_fields_response_shape(self):
        resp = condition_fields_to_api_response()
        assert isinstance(resp, list)
        assert len(resp) == len(CONDITION_FIELDS_CATALOG)
        for item in resp:
            assert set(item.keys()) >= {
                "value",
                "name",
                "label_pt",
                "label_en",
                "type",
                "category",
            }, f"Item condition-field faltando keys: {item}"


# ---------------------------------------------------------------------------
# Fail-CLOSED lookups
# ---------------------------------------------------------------------------


class TestFailClosedLookups:
    def test_get_operator_known(self):
        op = get_operator("eq")
        assert op is not None
        assert op.value == "eq"

    def test_get_operator_unknown_returns_none(self):
        """Fail-CLOSED: unknown operator NUNCA retorna fallback silencioso."""
        assert get_operator("__not_a_real_op__") is None

    def test_get_condition_field_known(self):
        f = get_condition_field("candidate.wsi_score")
        assert f is not None
        assert f.value == "candidate.wsi_score"

    def test_get_condition_field_unknown_returns_none(self):
        assert get_condition_field("__not_a_real_field__") is None


# ---------------------------------------------------------------------------
# Endpoint smoke (FastAPI router-level, sem DB / sem auth real)
# ---------------------------------------------------------------------------


@pytest.fixture
def app_no_auth():
    """App stub que substitui require_company_id pra teste de shape de resposta."""
    from app.api.v1 import automations as automations_module
    from app.shared.security.require_company_id import require_company_id

    app = FastAPI()
    app.include_router(automations_module.router, prefix="/api/v1")

    async def _fake_company_id() -> str:
        return "test-company-id"

    app.dependency_overrides[require_company_id] = _fake_company_id
    return app


class TestOperatorsEndpoint:
    def test_get_operators_returns_200(self, app_no_auth):
        client = TestClient(app_no_auth)
        r = client.get("/api/v1/automations/operators/available")
        assert r.status_code == 200, r.text

    def test_get_operators_canonical_shape(self, app_no_auth):
        client = TestClient(app_no_auth)
        r = client.get("/api/v1/automations/operators/available")
        body = r.json()
        assert body.get("success") is True
        operators = body.get("data", {}).get("operators")
        assert isinstance(operators, list)
        assert len(operators) == len(OPERATORS_CATALOG)
        assert any(op["value"] == "eq" for op in operators)


class TestConditionFieldsEndpoint:
    def test_get_condition_fields_returns_200(self, app_no_auth):
        client = TestClient(app_no_auth)
        r = client.get("/api/v1/automations/condition-fields/available")
        assert r.status_code == 200, r.text

    def test_get_condition_fields_canonical_shape(self, app_no_auth):
        client = TestClient(app_no_auth)
        r = client.get("/api/v1/automations/condition-fields/available")
        body = r.json()
        assert body.get("success") is True
        fields = body.get("data", {}).get("condition_fields")
        assert isinstance(fields, list)
        assert len(fields) == len(CONDITION_FIELDS_CATALOG)
        assert any(f["value"] == "candidate.wsi_score" for f in fields)
