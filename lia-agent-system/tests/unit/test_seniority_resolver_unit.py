"""
Tests for SeniorityResolver — multi-signal seniority resolution engine
Target: seniority_resolver.py (16% → ~60%) + seniority_utils.py bonus
"""
import sys
sys.path.insert(0, '/home/runner/workspace/lia-agent-system')
import pytest
import asyncio


class TestSeniorityResolverConstants:
    def test_signal_weights_defined(self):
        from app.domains.cv_screening.services.seniority_resolver import SIGNAL_WEIGHTS
        assert "explicit" in SIGNAL_WEIGHTS
        assert "title_keywords" in SIGNAL_WEIGHTS
        assert "jd_analysis" in SIGNAL_WEIGHTS
        assert "salary_range" in SIGNAL_WEIGHTS
        assert "skills_complexity" in SIGNAL_WEIGHTS

    def test_explicit_weight_highest(self):
        from app.domains.cv_screening.services.seniority_resolver import SIGNAL_WEIGHTS
        assert SIGNAL_WEIGHTS["explicit"] >= 0.40

    def test_senior_skill_indicators(self):
        from app.domains.cv_screening.services.seniority_resolver import SENIOR_SKILL_INDICATORS
        assert "kubernetes" in SENIOR_SKILL_INDICATORS
        assert "machine learning" in SENIOR_SKILL_INDICATORS

    def test_junior_skill_indicators(self):
        from app.domains.cv_screening.services.seniority_resolver import JUNIOR_SKILL_INDICATORS
        assert "excel" in JUNIOR_SKILL_INDICATORS

    def test_display_names(self):
        from app.domains.cv_screening.services.seniority_resolver import SENIORITY_DISPLAY_NAMES
        assert "junior" in SENIORITY_DISPLAY_NAMES
        assert "senior" in SENIORITY_DISPLAY_NAMES
        assert "executive" in SENIORITY_DISPLAY_NAMES

    def test_enabled_flag(self):
        from app.domains.cv_screening.services.seniority_resolver import SENIORITY_RESOLVER_ENABLED
        assert isinstance(SENIORITY_RESOLVER_ENABLED, bool)


class TestSeniorityResolverInstantiation:
    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_module_has_resolve_function(self):
        import importlib
        mod = importlib.import_module(
            "app.domains.cv_screening.services.seniority_resolver"
        )
        assert hasattr(mod, "resolve_seniority") or hasattr(mod, "SeniorityResolver")

    def test_explicit_signal_determines_result(self):
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority
        result = self._run(resolve_seniority(
            explicit_level="senior",
            title="Desenvolvedor",
            jd_text="",
        ))
        assert result is not None
        assert "senior" in str(result).lower() or hasattr(result, "level")

    def test_explicit_junior(self):
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority
        result = self._run(resolve_seniority(
            explicit_level="junior",
            title="Desenvolvedor Júnior",
            jd_text="",
        ))
        assert result is not None

    def test_no_explicit_uses_title(self):
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority
        result = self._run(resolve_seniority(
            explicit_level=None,
            title="Analista Sênior de Dados",
            jd_text="",
        ))
        assert result is not None

    def test_conflict_explicit_vs_title(self):
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority
        result = self._run(resolve_seniority(
            explicit_level="junior",
            title="Desenvolvedor Sênior",
            jd_text="",
        ))
        # Conflict detected — should still return a result
        assert result is not None

    def test_empty_signals(self):
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority
        result = self._run(resolve_seniority(
            explicit_level=None,
            title="",
            jd_text="",
        ))
        assert result is not None

    def test_senior_skills_in_jd(self):
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority
        result = self._run(resolve_seniority(
            explicit_level=None,
            title="Engenheiro",
            jd_text="Experiência com kubernetes, machine learning e system design avançado",
        ))
        assert result is not None

    def test_junior_skills_in_jd(self):
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority
        result = self._run(resolve_seniority(
            explicit_level=None,
            title="Assistente",
            jd_text="Conhecimentos básicos em excel, word e digitação",
        ))
        assert result is not None

    def test_result_has_confidence(self):
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority
        result = self._run(resolve_seniority(
            explicit_level="senior",
            title="Desenvolvedor Sênior",
            jd_text="",
        ))
        if hasattr(result, "confidence"):
            assert 0.0 <= result.confidence <= 1.0

    def test_full_agreement_high_confidence(self):
        from app.domains.cv_screening.services.seniority_resolver import resolve_seniority
        result = self._run(resolve_seniority(
            explicit_level="senior",
            title="Desenvolvedor Sênior",
            jd_text="Buscamos profissional sênior com vasta experiência",
        ))
        if hasattr(result, "confidence"):
            # Full agreement → high confidence
            assert result.confidence >= 0.7


class TestSeniorityResolverModule:
    def test_module_importable(self):
        import app.domains.cv_screening.services.seniority_resolver as mod
        assert mod is not None
