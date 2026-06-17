"""
COMP-4: PolicyEngine apply_industry_defaults
COMP-5: Bias Audit baseline golden dataset

WT-2022 Phase 2 prep (2026-05-21): V1 PolicyEngine deprecated, deletion
agendada para Q3 2026. Tests COMP-4 cobrem 
que continua disponivel via PolicyEngineService.apply_industry_defaults
(V2 delega para V1 enquanto V1 vivo; pos-deletion, dados SECTOR_DEFAULTS
serao internalizados em V2). Tests migrados para chamar V2 API canonical.
"""
import pytest


class TestPolicyEngineIndustryDefaults:
    """COMP-4: apply_industry_defaults() — migrado V1 -> V2 (WT-2022 Phase 2 prep)."""

    @pytest.fixture
    def engine(self):
        from app.domains.policy.services.policy_engine_service import PolicyEngineService
        return PolicyEngineService()

    @pytest.mark.asyncio
    async def test_tech_sector_defaults(self, engine):
        """Setor tech deve ter limites mais altos."""
        policies = await engine.apply_industry_defaults("tech")
        assert policies["max_pearch_searches_per_day"] >= 50
        assert policies["require_approval_for_bulk_email"] is False

    @pytest.mark.asyncio
    async def test_financeiro_restricts_global_search(self, engine):
        """Setor financeiro deve restringir busca global (BCB 498)."""
        policies = await engine.apply_industry_defaults("financeiro")
        assert policies["allow_global_search"] is False

    @pytest.mark.asyncio
    async def test_rpo_highest_limits(self, engine):
        """Setor RPO deve ter maiores limites (multi-cliente)."""
        policies = await engine.apply_industry_defaults("rpo")
        assert policies["max_voice_screenings_per_day"] >= 2000

    @pytest.mark.asyncio
    async def test_unknown_sector_returns_defaults(self, engine):
        """Setor desconhecido deve retornar DEFAULT_POLICIES sem erro."""
        policies = await engine.apply_industry_defaults("unknown_sector_xyz")
        assert isinstance(policies, dict)
        assert "max_pearch_searches_per_day" in policies

    @pytest.mark.asyncio
    async def test_case_insensitive(self):
        """Setor deve ser case-insensitive."""
        from app.domains.policy.services.policy_engine_service import PolicyEngineService
        engine1 = PolicyEngineService()
        engine2 = PolicyEngineService()
        policies_lower = await engine1.apply_industry_defaults("tech")
        policies_upper = await engine2.apply_industry_defaults("TECH")
        assert policies_lower == policies_upper

    @pytest.mark.asyncio
    async def test_varejo_high_volume(self, engine):
        """Varejo deve suportar alto volume (triagem em massa)."""
        policies = await engine.apply_industry_defaults("varejo")
        assert policies["max_voice_screenings_per_day"] >= 500
        assert policies["max_concurrent_requests"] >= 20

    @pytest.mark.asyncio
    async def test_logistica_highest_screening_volume(self, engine):
        """Logistica deve ter maior volume de screening."""
        policies = await engine.apply_industry_defaults("logistica")
        assert policies["max_voice_screenings_per_day"] >= 1000


class TestBiasAuditGoldenDataset:
    """COMP-5: Golden dataset e Four-Fifths Rule. (inalterado — nao toca PolicyEngine)"""

    def test_dataset_returns_200_candidates(self):
        """Dataset sintetico deve retornar 200 candidatos."""
        from tests.fixtures.golden_dataset_bias import get_balanced_baseline_candidates
        candidates = get_balanced_baseline_candidates()
        assert len(candidates) == 200

    def test_all_candidates_marked_synthetic(self):
        """Todos os candidatos devem ser marcados como sinteticos."""
        from tests.fixtures.golden_dataset_bias import get_balanced_baseline_candidates
        candidates = get_balanced_baseline_candidates()
        assert all(c.get("synthetic") is True for c in candidates)

    def test_four_fifths_rule_passes_all_dimensions(self):
        """Dataset balanceado deve passar Four-Fifths Rule em todas as dimensoes."""
        from tests.fixtures.golden_dataset_bias import (
            get_balanced_baseline_candidates, assert_four_fifths_rule
        )
        candidates = get_balanced_baseline_candidates()
        result = assert_four_fifths_rule(candidates)
        assert result["all_passed"] is True, f"Four-Fifths falhou: {result[dimensions]}"

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
        """Ratio genero deve ser >= 0.80 (Four-Fifths Rule)."""
        from tests.fixtures.golden_dataset_bias import (
            get_balanced_baseline_candidates, assert_four_fifths_rule
        )
        candidates = get_balanced_baseline_candidates()
        result = assert_four_fifths_rule(candidates)
        gender_groups = result["dimensions"]["gender"]
        for group, stats in gender_groups.items():
            assert stats["air"] >= 0.80, f"Gender group {group} failed AIR={stats[air]}"

    def test_admin_endpoint_exists(self):
        """Admin endpoint deve existir."""
        from app.api.v1.admin_bias_audit import router
        routes = [r.path for r in router.routes]
        assert any("baseline" in r for r in routes)
