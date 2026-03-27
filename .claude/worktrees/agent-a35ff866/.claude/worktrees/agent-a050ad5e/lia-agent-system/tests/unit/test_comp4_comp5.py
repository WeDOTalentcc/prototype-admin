"""
COMP-4: PolicyEngine apply_industry_defaults
COMP-5: Bias Audit baseline golden dataset
"""
import pytest


class TestPolicyEngineIndustryDefaults:
    """COMP-4: apply_industry_defaults()."""

    def test_tech_sector_defaults(self):
        """Setor tech deve ter limites mais altos."""
        from app.orchestrator.policy_engine import PolicyEngine
        engine = PolicyEngine()
        policies = engine.apply_industry_defaults("tech")
        assert policies["max_pearch_searches_per_day"] >= 50
        assert policies["require_approval_for_bulk_email"] is False

    def test_financeiro_restricts_global_search(self):
        """Setor financeiro deve restringir busca global (BCB 498)."""
        from app.orchestrator.policy_engine import PolicyEngine
        engine = PolicyEngine()
        policies = engine.apply_industry_defaults("financeiro")
        assert policies["allow_global_search"] is False

    def test_rpo_highest_limits(self):
        """Setor RPO deve ter maiores limites (multi-cliente)."""
        from app.orchestrator.policy_engine import PolicyEngine
        engine = PolicyEngine()
        policies = engine.apply_industry_defaults("rpo")
        assert policies["max_voice_screenings_per_day"] >= 2000

    def test_unknown_sector_returns_defaults(self):
        """Setor desconhecido deve retornar DEFAULT_POLICIES sem erro."""
        from app.orchestrator.policy_engine import PolicyEngine
        engine = PolicyEngine()
        policies = engine.apply_industry_defaults("unknown_sector_xyz")
        assert isinstance(policies, dict)
        assert "max_pearch_searches_per_day" in policies

    def test_case_insensitive(self):
        """Setor deve ser case-insensitive."""
        from app.orchestrator.policy_engine import PolicyEngine
        engine = PolicyEngine()
        policies_lower = engine.apply_industry_defaults("tech")
        engine2 = PolicyEngine()
        policies_upper = engine2.apply_industry_defaults("TECH")
        assert policies_lower == policies_upper

    def test_varejo_high_volume(self):
        """Varejo deve suportar alto volume (triagem em massa)."""
        from app.orchestrator.policy_engine import PolicyEngine
        engine = PolicyEngine()
        policies = engine.apply_industry_defaults("varejo")
        assert policies["max_voice_screenings_per_day"] >= 500
        assert policies["max_concurrent_requests"] >= 20

    def test_logistica_highest_screening_volume(self):
        """Logística deve ter maior volume de screening."""
        from app.orchestrator.policy_engine import PolicyEngine
        engine = PolicyEngine()
        policies = engine.apply_industry_defaults("logistica")
        assert policies["max_voice_screenings_per_day"] >= 1000


class TestBiasAuditGoldenDataset:
    """COMP-5: Golden dataset e Four-Fifths Rule."""

    def test_dataset_returns_200_candidates(self):
        """Dataset sintético deve retornar 200 candidatos."""
        from tests.fixtures.golden_dataset_bias import get_balanced_baseline_candidates
        candidates = get_balanced_baseline_candidates()
        assert len(candidates) == 200

    def test_all_candidates_marked_synthetic(self):
        """Todos os candidatos devem ser marcados como sintéticos."""
        from tests.fixtures.golden_dataset_bias import get_balanced_baseline_candidates
        candidates = get_balanced_baseline_candidates()
        assert all(c.get("synthetic") is True for c in candidates)

    def test_four_fifths_rule_passes_all_dimensions(self):
        """Dataset balanceado deve passar Four-Fifths Rule em todas as dimensões."""
        from tests.fixtures.golden_dataset_bias import (
            get_balanced_baseline_candidates, assert_four_fifths_rule
        )
        candidates = get_balanced_baseline_candidates()
        result = assert_four_fifths_rule(candidates)
        assert result["all_passed"] is True, f"Four-Fifths falhou: {result['dimensions']}"

    def test_four_fifths_covers_all_dimensions(self):
        """Resultado deve cobrir gender, age_group, disability, region."""
        from tests.fixtures.golden_dataset_bias import (
            get_balanced_baseline_candidates, assert_four_fifths_rule
        )
        candidates = get_balanced_baseline_candidates()
        result = assert_four_fifths_rule(candidates)
        dims = result["dimensions"]
        assert "gender" in dims
        assert "age_group" in dims
        assert "disability" in dims
        assert "region" in dims

    def test_gender_ratio_above_threshold(self):
        """Ratio gênero deve ser >= 0.80 (Four-Fifths Rule)."""
        from tests.fixtures.golden_dataset_bias import (
            get_balanced_baseline_candidates, assert_four_fifths_rule
        )
        candidates = get_balanced_baseline_candidates()
        result = assert_four_fifths_rule(candidates)
        gender_groups = result["dimensions"]["gender"]
        for group, stats in gender_groups.items():
            assert stats["air"] >= 0.80, f"Gender group {group} failed AIR={stats['air']}"

    def test_admin_endpoint_exists(self):
        """Admin endpoint deve existir."""
        from app.api.v1.admin_bias_audit import router
        routes = [r.path for r in router.routes]
        assert any("baseline" in r for r in routes)
