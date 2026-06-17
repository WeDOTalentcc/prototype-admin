"""
Unit tests for context_type_override service.

Sprint II.4 of LIA-D06 migration.
Tests garantem comportamento idêntico ao código inline do V1.

Reference: ADR-019 — Sprint II.4
"""
from __future__ import annotations

import pytest

from app.orchestrator.services.context_type_override import (
    CONTEXT_TYPE_DOMAIN_MAPPING,
    OVERRIDE_SOURCE,
    build_override_route,
    get_domain_override,
    try_override_route,
)


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT_TYPE_DOMAIN_MAPPING — canonical mapping
# ─────────────────────────────────────────────────────────────────────────────


class TestMappingCanonical:
    """O mapping canônico não pode mudar sem atualizar tests."""

    def test_company_settings_maps_to_company_settings(self):
        assert CONTEXT_TYPE_DOMAIN_MAPPING["company_settings"] == "company_settings"

    def test_hiring_policy_maps_to_hiring_policy(self):
        assert CONTEXT_TYPE_DOMAIN_MAPPING["hiring_policy"] == "hiring_policy"

    def test_mapping_has_exactly_two_keys(self):
        """V1 tem apenas 2 mappings — tests trava esse contrato."""
        assert len(CONTEXT_TYPE_DOMAIN_MAPPING) == 2

    def test_override_source_is_context_type_override(self):
        """Source string é usada em logs e tracing — NÃO mudar."""
        assert OVERRIDE_SOURCE == "context_type_override"


# ─────────────────────────────────────────────────────────────────────────────
# get_domain_override — pure function
# ─────────────────────────────────────────────────────────────────────────────


class TestGetDomainOverride:
    """Mapping lookup function."""

    def test_company_settings_returns_company_settings(self):
        assert get_domain_override("company_settings") == "company_settings"

    def test_hiring_policy_returns_hiring_policy(self):
        assert get_domain_override("hiring_policy") == "hiring_policy"

    def test_unknown_context_type_returns_none(self):
        assert get_domain_override("unknown_xyz") is None

    def test_empty_string_returns_none(self):
        assert get_domain_override("") is None

    def test_case_sensitive(self):
        """Mapping é case-sensitive (consistente com V1 dict.get)."""
        assert get_domain_override("Company_Settings") is None
        assert get_domain_override("COMPANY_SETTINGS") is None

    def test_returns_str_or_none_only(self):
        """Type contract: str | None, nunca outro tipo."""
        for ctx_type in ["company_settings", "hiring_policy", "unknown", ""]:
            result = get_domain_override(ctx_type)
            assert result is None or isinstance(result, str)


# ─────────────────────────────────────────────────────────────────────────────
# build_override_route — RouteResult constructor
# ─────────────────────────────────────────────────────────────────────────────


class TestBuildOverrideRoute:
    """Constrói RouteResult fake com confidence=1.0."""

    def test_returns_route_result_with_correct_domain(self):
        route = build_override_route("company_settings")
        assert route.domain_id == "company_settings"

    def test_confidence_is_one_point_zero(self):
        route = build_override_route("hiring_policy")
        assert route.confidence == 1.0

    def test_source_is_override_constant(self):
        route = build_override_route("company_settings")
        assert route.source == OVERRIDE_SOURCE
        assert route.source == "context_type_override"

    def test_intent_details_contains_raw_intent(self):
        """V1 popula intent_details.raw_intent com domain_id (mesmo valor)."""
        route = build_override_route("hiring_policy")
        assert route.intent_details == {"raw_intent": "hiring_policy"}


# ─────────────────────────────────────────────────────────────────────────────
# try_override_route — convenience function
# ─────────────────────────────────────────────────────────────────────────────


class TestTryOverrideRoute:
    """Combinação de get_domain_override + build_override_route."""

    def test_with_company_settings_returns_route(self):
        route = try_override_route({"context_type": "company_settings"})
        assert route is not None
        assert route.domain_id == "company_settings"

    def test_with_hiring_policy_returns_route(self):
        route = try_override_route({"context_type": "hiring_policy"})
        assert route is not None
        assert route.domain_id == "hiring_policy"

    def test_with_unknown_context_type_returns_none(self):
        assert try_override_route({"context_type": "unknown_xyz"}) is None

    def test_with_empty_context_type_returns_none(self):
        assert try_override_route({"context_type": ""}) is None

    def test_with_missing_context_type_returns_none(self):
        """Context sem `context_type` key retorna None (não crasha)."""
        assert try_override_route({}) is None

    def test_with_none_context_returns_none(self):
        """None context é tratado (não crasha)."""
        assert try_override_route(None) is None

    def test_extra_context_keys_ignored(self):
        """Outras keys no context não afetam o lookup."""
        ctx = {
            "context_type": "company_settings",
            "company_id": "tenant-a",
            "user_id": "u1",
            "extra": "ignored",
        }
        route = try_override_route(ctx)
        assert route is not None
        assert route.domain_id == "company_settings"


# ─────────────────────────────────────────────────────────────────────────────
# Equivalence with V1 inline behavior
# ─────────────────────────────────────────────────────────────────────────────


class TestEquivalenceWithV1Inline:
    """
    Validação que o service module retorna IDENTICO ao código inline do V1.
    """

    def _v1_inline_logic(self, context: dict | None):
        """Reproduz EXATAMENTE o que V1 process_request faz nas linhas 130-145."""
        ctx = context or {}
        _ctx_type = ctx.get("context_type", "")
        _CONTEXT_TYPE_DOMAIN_OVERRIDE = {
            "company_settings": "company_settings",
            "hiring_policy": "hiring_policy",
        }
        _domain_override = _CONTEXT_TYPE_DOMAIN_OVERRIDE.get(_ctx_type)
        if _domain_override:
            from app.orchestrator.routing.cascaded_router import RouteResult
            return RouteResult(
                domain_id=_domain_override,
                confidence=1.0,
                source="context_type_override",
                intent_details={"raw_intent": _domain_override},
            )
        return None

    @pytest.mark.parametrize(
        "context",
        [
            {"context_type": "company_settings"},
            {"context_type": "hiring_policy"},
            {"context_type": "unknown"},
            {"context_type": ""},
            {},
            None,
            {"context_type": "company_settings", "company_id": "t1"},
        ],
    )
    def test_service_matches_v1_inline(self, context):
        """Service retorna estrutura idêntica ao V1 inline."""
        v1_result = self._v1_inline_logic(context)
        new_result = try_override_route(context)

        # Both None or both not-None
        if v1_result is None:
            assert new_result is None
        else:
            assert new_result is not None
            assert v1_result.domain_id == new_result.domain_id
            assert v1_result.confidence == new_result.confidence
            assert v1_result.source == new_result.source
            assert v1_result.intent_details == new_result.intent_details
