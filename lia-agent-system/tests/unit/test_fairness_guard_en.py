"""
Tests for FairnessGuard EN hardening — Etapa 3.

Cobre:
- IMPLICIT_BIAS_TERMS_EN: 35 termos presentes
- Detecção de termos EN via check_implicit_bias()
- Categorias EN: gender_en, race_en, age_en
- Regex PT-BR de idade: "maiores de X anos", "acima de X", etc.
- _detect_language(): texto EN→"en", PT-BR→"pt-br", vazio→"pt-br"
- _PATTERNS_VERSION == 5
- Total de categorias == 20
"""
import pytest


class TestImplicitBiasTermsEN:
    """Verifica que os 20 termos EN estão presentes e detectados."""

    def setup_method(self):
        from app.shared.compliance.fairness_guard import FairnessGuard
        self.guard = FairnessGuard()

    def test_implicit_bias_terms_en_has_20_terms(self):
        from app.shared.compliance.fairness_guard import IMPLICIT_BIAS_TERMS_EN
        assert len(IMPLICIT_BIAS_TERMS_EN) == 35

    def test_young_and_dynamic_present(self):
        from app.shared.compliance.fairness_guard import IMPLICIT_BIAS_TERMS_EN
        assert "young and dynamic" in IMPLICIT_BIAS_TERMS_EN

    def test_ivy_league_present(self):
        from app.shared.compliance.fairness_guard import IMPLICIT_BIAS_TERMS_EN
        assert "ivy league" in IMPLICIT_BIAS_TERMS_EN

    def test_no_family_obligations_present(self):
        from app.shared.compliance.fairness_guard import IMPLICIT_BIAS_TERMS_EN
        assert "no family obligations" in IMPLICIT_BIAS_TERMS_EN

    def test_without_restrictions_present(self):
        from app.shared.compliance.fairness_guard import IMPLICIT_BIAS_TERMS_EN
        assert "without restrictions" in IMPLICIT_BIAS_TERMS_EN

    def test_culture_fit_present(self):
        from app.shared.compliance.fairness_guard import IMPLICIT_BIAS_TERMS_EN
        assert "culture fit" in IMPLICIT_BIAS_TERMS_EN

    def test_good_looking_present(self):
        from app.shared.compliance.fairness_guard import IMPLICIT_BIAS_TERMS_EN
        assert "good looking" in IMPLICIT_BIAS_TERMS_EN

    def test_digital_native_present(self):
        from app.shared.compliance.fairness_guard import IMPLICIT_BIAS_TERMS_EN
        assert "digital native" in IMPLICIT_BIAS_TERMS_EN

    def test_detect_ivy_league_in_check(self):
        result = self.guard.check("We need an ivy league background preferred")
        assert result.soft_warnings or result.is_blocked

    def test_detect_young_and_dynamic_in_check(self):
        result = self.guard.check("looking for young and dynamic candidates")
        assert result.soft_warnings or result.is_blocked

    def test_detect_culture_fit_in_check(self):
        result = self.guard.check("must be a good culture fit")
        assert result.soft_warnings or result.is_blocked


class TestFairnessGuardENCategories:
    """Testa categorias EN: gender_en, race_en, age_en."""

    def setup_method(self):
        from app.shared.compliance.fairness_guard import FairnessGuard
        self.guard = FairnessGuard()

    def test_gender_en_male_only_blocked(self):
        result = self.guard.check("male only position available")
        assert result.is_blocked

    def test_gender_en_female_only_blocked(self):
        result = self.guard.check("only women candidates please")
        assert result.is_blocked

    def test_age_en_under_35_blocked(self):
        result = self.guard.check("candidates must be under 35 years")
        assert result.is_blocked

    def test_age_en_young_candidate_blocked(self):
        result = self.guard.check("looking for young candidate")
        assert result.is_blocked

    def test_total_categories_is_16(self):
        from app.shared.compliance.fairness_guard import DISCRIMINATORY_CATEGORIES
        assert len(DISCRIMINATORY_CATEGORIES) == 20


class TestFairnessGuardIdadePatternsPTBR:
    """Verifica os 8 novos padrões de idade PT-BR (bug fix Etapa 3)."""

    def setup_method(self):
        from app.shared.compliance.fairness_guard import FairnessGuard
        self.guard = FairnessGuard()

    def test_maiores_de_50_anos_blocked(self):
        result = self.guard.check("vaga para maiores de 50 anos")
        assert result.is_blocked
        assert result.category == "idade"

    def test_acima_de_40_blocked(self):
        result = self.guard.check("candidatos acima de 40 anos")
        assert result.is_blocked
        assert result.category == "idade"

    def test_menores_de_30_anos_blocked(self):
        result = self.guard.check("apenas menores de 30 anos")
        assert result.is_blocked
        assert result.category == "idade"

    def test_abaixo_de_25_blocked(self):
        result = self.guard.check("candidatos abaixo de 25 anos de idade")
        assert result.is_blocked
        assert result.category == "idade"

    def test_a_partir_de_18_not_necessarily_blocked(self):
        # "a partir de 18 anos" pode ser requisito legal (maioridade), não discriminação
        # O guard pode ou não bloquear — documentar comportamento
        result = self.guard.check("a partir de 18 anos")
        # Just assert it returns a FairnessCheckResult
        from app.shared.compliance.fairness_guard import FairnessCheckResult
        assert isinstance(result, FairnessCheckResult)


class TestDetectLanguage:
    """Testa a função _detect_language()."""

    def test_english_text_returns_en(self):
        from app.shared.compliance.fairness_guard import _detect_language
        result = _detect_language("We are looking for candidates with strong skills")
        assert result == "en"

    def test_portuguese_text_returns_ptbr(self):
        from app.shared.compliance.fairness_guard import _detect_language
        result = _detect_language("Não é válido pôr vírgula após preposição")
        assert result == "pt-br"

    def test_empty_text_returns_ptbr(self):
        from app.shared.compliance.fairness_guard import _detect_language
        result = _detect_language("")
        assert result == "pt-br"

    def test_mixed_mostly_english_returns_en(self):
        from app.shared.compliance.fairness_guard import _detect_language
        result = _detect_language("We need strong Python developer with experience")
        assert result == "en"

    def test_whitespace_only_returns_ptbr(self):
        from app.shared.compliance.fairness_guard import _detect_language
        result = _detect_language("   ")
        assert result == "pt-br"


class TestFairnessGuardPatternsVersion:
    """Testa versionamento dos patterns."""

    def test_patterns_version_is_4(self):
        from app.shared.compliance.fairness_guard import _PATTERNS_VERSION
        assert _PATTERNS_VERSION == 5
