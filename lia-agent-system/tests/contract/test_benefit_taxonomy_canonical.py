"""
Sensor canonical para a taxonomia v2 de beneficios (categories, value_types, waiting_periods).

Aplica:
- canonical-fix: garante 1 fonte de verdade (BENEFIT_CATEGORIES em benefits_service.py)
- harness-engineering: detecta drift (frontend hardcoded ≠ canonical, endpoint hardcoded ≠ canonical)
- compliance: legacy aliases mantidos pra backward-compat com dados antigos no banco

Background:
Pre-2026-05-24 existiam 3 listas divergentes:
- benefits_service.BENEFIT_CATEGORIES (8 itens)
- /v1/company_benefits/categories/list endpoint (9 itens hardcoded inline)
- BenefitFormModal.tsx BENEFIT_CATEGORIES (11 itens hardcoded)
+ templates seed usavam "wellness" e "flexibility" que NAO existiam em BENEFIT_CATEGORIES
→ LIA recebia string crua no prompt quando renderizava esses beneficios.

Fix canonical 2026-05-24: BENEFIT_CATEGORIES v2 com 14 categorias canonical
+ BENEFIT_CATEGORY_LEGACY_ALIASES pra backward-compat.
"""
import pytest

from app.domains.company.services.benefits_service import (
    BENEFIT_CATEGORIES,
    BENEFIT_CATEGORY_ICONS,
    BENEFIT_CATEGORY_LEGACY_ALIASES,
    BENEFIT_VALUE_TYPES,
    BENEFIT_VALUE_TYPE_ICONS,
    BENEFIT_WAITING_PERIODS,
    resolve_benefit_category,
)


class TestBenefitCategoriesV2:
    """Taxonomia v2 canonical — 14 categorias."""

    EXPECTED_V2_KEYS = {
        "health", "wellness", "food", "transport", "education",
        "financial", "retirement", "family", "parental", "flexibility",
        "equipment", "culture", "recognition", "other",
    }

    def test_has_exactly_14_canonical_categories(self):
        assert set(BENEFIT_CATEGORIES.keys()) == self.EXPECTED_V2_KEYS, (
            f"BENEFIT_CATEGORIES drift. Expected v2 taxonomy of 14 keys: "
            f"{self.EXPECTED_V2_KEYS}. Got: {set(BENEFIT_CATEGORIES.keys())}"
        )

    def test_all_labels_are_non_empty_strings(self):
        for k, v in BENEFIT_CATEGORIES.items():
            assert isinstance(v, str) and v.strip(), f"Empty label for category '{k}'"

    def test_all_categories_have_icon(self):
        missing = self.EXPECTED_V2_KEYS - set(BENEFIT_CATEGORY_ICONS.keys())
        assert not missing, f"Categories without icon: {missing}"

    def test_no_duplicate_labels(self):
        labels = list(BENEFIT_CATEGORIES.values())
        assert len(labels) == len(set(labels)), (
            f"Duplicate labels in BENEFIT_CATEGORIES: "
            f"{[l for l in labels if labels.count(l) > 1]}"
        )

    def test_legacy_aliases_map_to_canonical(self):
        # Categorias da v1 que foram absorvidas — devem resolver pra canonical
        assert "quality_life" in BENEFIT_CATEGORY_LEGACY_ALIASES
        assert "security" in BENEFIT_CATEGORY_LEGACY_ALIASES
        for legacy, canonical in BENEFIT_CATEGORY_LEGACY_ALIASES.items():
            assert canonical in BENEFIT_CATEGORIES, (
                f"Legacy alias '{legacy}' aponta para '{canonical}' que nao existe na v2"
            )

    def test_resolve_benefit_category_handles_canonical(self):
        assert resolve_benefit_category("health") == "health"
        assert resolve_benefit_category("retirement") == "retirement"

    def test_resolve_benefit_category_handles_legacy(self):
        # quality_life → flexibility, security → financial
        assert resolve_benefit_category("quality_life") == "flexibility"
        assert resolve_benefit_category("security") == "financial"

    def test_resolve_benefit_category_handles_unknown(self):
        # Categoria desconhecida retorna "other" (fail-soft pra dados sujos no banco)
        assert resolve_benefit_category("unknown_xyz") == "other"
        assert resolve_benefit_category(None) == "other"
        assert resolve_benefit_category("") == "other"


class TestBenefitValueTypesV2:
    """Tipos de valor v2 — 6 tipos."""

    EXPECTED_V2_KEYS = {
        "monetary", "percentage", "match", "reimbursement", "coverage", "informative",
    }

    def test_has_exactly_6_value_types(self):
        assert set(BENEFIT_VALUE_TYPES.keys()) == self.EXPECTED_V2_KEYS, (
            f"BENEFIT_VALUE_TYPES drift. Expected 6 types: {self.EXPECTED_V2_KEYS}. "
            f"Got: {set(BENEFIT_VALUE_TYPES.keys())}"
        )

    def test_all_value_types_have_icon(self):
        missing = self.EXPECTED_V2_KEYS - set(BENEFIT_VALUE_TYPE_ICONS.keys())
        assert not missing, f"Value types without icon: {missing}"


class TestBenefitWaitingPeriodsV2:
    """Periodos de carencia v2 — 9 opcoes."""

    def test_has_at_least_9_waiting_periods(self):
        assert len(BENEFIT_WAITING_PERIODS) >= 9, (
            f"Expected at least 9 waiting periods (0/exp/30/60/90/180/365/540/730). "
            f"Got: {len(BENEFIT_WAITING_PERIODS)}"
        )

    def test_includes_immediate_and_after_experience(self):
        ids = [p["id"] for p in BENEFIT_WAITING_PERIODS]
        assert 0 in ids, "Missing 'Imediato' (id=0)"
        # -1 sinaliza 'apos periodo de experiencia' (variavel)
        assert -1 in ids, "Missing 'Apos periodo de experiencia' (id=-1)"

    def test_includes_long_tenure_periods(self):
        ids = [p["id"] for p in BENEFIT_WAITING_PERIODS]
        assert 540 in ids, "Missing 18 meses (id=540)"
        assert 730 in ids, "Missing 24 meses (id=730)"

    def test_all_have_label_and_id(self):
        for p in BENEFIT_WAITING_PERIODS:
            assert "id" in p and isinstance(p["id"], int)
            assert "label" in p and isinstance(p["label"], str) and p["label"].strip()


class TestSingleSourceOfTruth:
    """Garante que nao ha drift entre fontes (canonical-fix principio 2)."""

    def test_endpoint_helper_returns_canonical_data(self):
        """Endpoint /categories/list deve retornar EXATAMENTE BENEFIT_CATEGORIES."""
        from app.domains.company.services.benefits_service import (
            build_categories_response,
        )
        response = build_categories_response()
        assert isinstance(response, list)
        assert len(response) == len(BENEFIT_CATEGORIES)
        for item in response:
            assert "id" in item and "name" in item and "icon" in item
            assert item["id"] in BENEFIT_CATEGORIES
            assert item["name"] == BENEFIT_CATEGORIES[item["id"]]
            assert item["icon"] == BENEFIT_CATEGORY_ICONS[item["id"]]

    def test_endpoint_helper_value_types(self):
        from app.domains.company.services.benefits_service import (
            build_value_types_response,
        )
        response = build_value_types_response()
        assert len(response) == len(BENEFIT_VALUE_TYPES)
        for item in response:
            assert item["id"] in BENEFIT_VALUE_TYPES

    def test_endpoint_helper_waiting_periods(self):
        from app.domains.company.services.benefits_service import (
            build_waiting_periods_response,
        )
        response = build_waiting_periods_response()
        assert response == BENEFIT_WAITING_PERIODS
