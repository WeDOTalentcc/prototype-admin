"""
Unit tests for the ToneFilter class.

Tests cover:
- Informal language filtering
- Formal greeting enforcement
- Professional tone validation
- Emoji normalization
- Edge cases
- Performance
"""
import pytest
import time
from app.shared.robustness.response_filter import (
    ToneFilter,
    filter_response,
    validate_response,
    INFORMAL_TERMS,
    FORBIDDEN_PATTERNS,
    PROFESSIONAL_INDICATORS,
)


class TestFilterInformalLanguage:
    """Tests for filter_informal_language method."""
    
    def setup_method(self):
        self.filter = ToneFilter()
    
    def test_replace_vc_with_voce(self):
        text = "Vc pode me ajudar?"
        result = self.filter.filter_informal_language(text)
        assert "você" in result.lower()
        assert "vc" not in result.lower()
    
    def test_replace_pra_with_para(self):
        text = "Isso é pra você"
        result = self.filter.filter_informal_language(text)
        assert "para" in result.lower()
        assert "pra" not in result.lower()
    
    def test_replace_ta_with_esta(self):
        text = "Tá tudo bem?"
        result = self.filter.filter_informal_language(text)
        assert "está" in result.lower()
    
    def test_replace_blz_with_ok(self):
        text = "blz, vamos fazer isso"
        result = self.filter.filter_informal_language(text)
        assert "ok" in result.lower()
        assert "blz" not in result.lower()
    
    def test_remove_tmj(self):
        text = "Combinado, tmj!"
        result = self.filter.filter_informal_language(text)
        assert "tmj" not in result.lower()
    
    def test_remove_rs_laughter(self):
        text = "Isso foi engraçado rs"
        result = self.filter.filter_informal_language(text)
        assert "rs" not in result.lower()
    
    def test_remove_rsrs_laughter(self):
        text = "Muito bom rsrs"
        result = self.filter.filter_informal_language(text)
        assert "rsrs" not in result.lower()
    
    def test_remove_kk_laughter(self):
        text = "Adorei kkk"
        result = self.filter.filter_informal_language(text)
        assert "kk" not in result.lower()
    
    def test_remove_multiple_k_laughter(self):
        text = "Incrível kkkkkkk"
        result = self.filter.filter_informal_language(text)
        assert "kk" not in result.lower()
    
    def test_multiple_informal_terms(self):
        text = "Vc tá ok? Pra mim tá blz tmj"
        result = self.filter.filter_informal_language(text)
        assert "vc" not in result.lower()
        assert "pra" not in result.lower()
        assert "tmj" not in result.lower()
    
    def test_empty_string(self):
        assert self.filter.filter_informal_language("") == ""
    
    def test_none_input(self):
        assert self.filter.filter_informal_language(None) is None
    
    def test_no_informal_language(self):
        text = "Olá, como posso ajudá-lo hoje?"
        result = self.filter.filter_informal_language(text)
        assert result == text


class TestEmojiNormalization:
    """Tests for emoji normalization."""
    
    def setup_method(self):
        self.filter = ToneFilter(max_emojis=1)
    
    def test_single_emoji_kept(self):
        text = "Olá! 😊"
        result = self.filter.filter_informal_language(text)
        assert "😊" in result
    
    def test_excess_emojis_removed(self):
        text = "Olá! 😊😊😊😊"
        result = self.filter.filter_informal_language(text)
        assert result.count("😊") <= 1
    
    def test_zero_max_emojis(self):
        filter_no_emoji = ToneFilter(max_emojis=0)
        text = "Olá! 😊"
        result = filter_no_emoji.filter_informal_language(text)
        assert "😊" not in result
    
    def test_two_max_emojis(self):
        filter_two = ToneFilter(max_emojis=2)
        text = "Olá! 😊😎🎉"
        result = filter_two.filter_informal_language(text)
        emoji_count = result.count("😊") + result.count("😎") + result.count("🎉")
        assert emoji_count <= 2


class TestEnsureFormalGreeting:
    """Tests for ensure_formal_greeting method."""
    
    def setup_method(self):
        self.filter = ToneFilter()
    
    def test_replace_oi_with_ola(self):
        text = "oi, como vai?"
        result = self.filter.ensure_formal_greeting(text)
        assert result.startswith("Olá")
    
    def test_replace_e_ai_with_ola(self):
        text = "e aí, tudo bem?"
        result = self.filter.ensure_formal_greeting(text)
        assert result.startswith("Olá")
    
    def test_replace_eai_with_ola(self):
        text = "eai pessoal"
        result = self.filter.ensure_formal_greeting(text)
        assert result.startswith("Olá")
    
    def test_replace_fala_with_ola(self):
        text = "fala, beleza?"
        result = self.filter.ensure_formal_greeting(text)
        assert result.startswith("Olá")
    
    def test_replace_salve_with_ola(self):
        text = "salve, mano"
        result = self.filter.ensure_formal_greeting(text)
        assert result.startswith("Olá")
    
    def test_formal_greeting_unchanged(self):
        text = "Olá, como posso ajudar?"
        result = self.filter.ensure_formal_greeting(text)
        assert result == text
    
    def test_prezado_greeting_unchanged(self):
        text = "Prezado candidato, agradecemos seu interesse."
        result = self.filter.ensure_formal_greeting(text)
        assert result == text
    
    def test_empty_string(self):
        assert self.filter.ensure_formal_greeting("") == ""
    
    def test_none_input(self):
        assert self.filter.ensure_formal_greeting(None) is None


class TestValidateProfessionalTone:
    """Tests for validate_professional_tone method."""
    
    def setup_method(self):
        self.filter = ToneFilter()
    
    def test_professional_text_valid(self):
        text = "Olá, prezado candidato. Agradeço seu interesse na vaga."
        is_professional, issues = self.filter.validate_professional_tone(text)
        assert is_professional
        assert len(issues) == 0
    
    def test_informal_text_invalid(self):
        text = "vc tá sabendo da vaga? blz pra mim kkkk"
        is_professional, issues = self.filter.validate_professional_tone(text)
        assert not is_professional
        assert len(issues) > 0
    
    def test_detects_vc(self):
        text = "Vc pode confirmar a entrevista?"
        is_professional, issues = self.filter.validate_professional_tone(text)
        assert not is_professional
        assert any("vc" in issue.lower() for issue in issues)
    
    def test_detects_excess_emojis(self):
        text = "Olá! 😊😎🎉🎊🎁"
        is_professional, issues = self.filter.validate_professional_tone(text)
        assert not is_professional
        assert any("emoji" in issue.lower() for issue in issues)
    
    def test_detects_laughter(self):
        text = "Muito bom kkkkk"
        is_professional, issues = self.filter.validate_professional_tone(text)
        assert not is_professional
    
    def test_empty_string_valid(self):
        is_professional, issues = self.filter.validate_professional_tone("")
        assert is_professional
        assert len(issues) == 0
    
    def test_none_input_valid(self):
        is_professional, issues = self.filter.validate_professional_tone(None)
        assert is_professional
        assert len(issues) == 0
    
    def test_suggests_professional_indicators_for_long_text(self):
        text = "A" * 150
        is_professional, issues = self.filter.validate_professional_tone(text)
        assert any("indicador" in issue.lower() for issue in issues)


class TestApplyAllFilters:
    """Tests for apply_all_filters method."""
    
    def setup_method(self):
        self.filter = ToneFilter()
    
    def test_applies_greeting_and_informal_filters(self):
        text = "oi, vc tá bem? pra gente isso é blz tmj kkk"
        result = self.filter.apply_all_filters(text)
        
        assert result.startswith("Olá")
        assert "vc" not in result.lower()
        assert "pra" not in result.lower()
        assert "kk" not in result.lower()
        assert "tmj" not in result.lower()
    
    def test_empty_string(self):
        assert self.filter.apply_all_filters("") == ""
    
    def test_none_input(self):
        assert self.filter.apply_all_filters(None) is None
    
    def test_already_formal_unchanged(self):
        text = "Olá, como posso ajudá-lo?"
        result = self.filter.apply_all_filters(text)
        assert result == text
    
    def test_complex_message(self):
        text = "oi vc, tô querendo saber sobre a vaga pra desenvolvedor. Tá disponível? blz, tmj rsrs 😊😊😊"
        result = self.filter.apply_all_filters(text)
        
        is_professional, issues = self.filter.validate_professional_tone(result)
        assert len(issues) < 5


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_filter_response(self):
        text = "oi vc, blz?"
        result = filter_response(text)
        assert result.startswith("Olá")
        assert "vc" not in result.lower()
    
    def test_validate_response_professional(self):
        text = "Olá, prezado candidato."
        is_professional, issues = validate_response(text)
        assert is_professional
    
    def test_validate_response_informal(self):
        text = "oi vc, tmj kkk"
        is_professional, issues = validate_response(text)
        assert not is_professional


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def setup_method(self):
        self.filter = ToneFilter()
    
    def test_case_insensitivity(self):
        text = "VC tá BLZ?"
        result = self.filter.filter_informal_language(text)
        assert "vc" not in result.lower()
        assert "blz" not in result.lower()
    
    def test_word_boundaries_vc(self):
        text = "serviço está disponível"
        result = self.filter.filter_informal_language(text)
        assert "serviço" in result
    
    def test_word_boundaries_ta(self):
        text = "A fruta está madura"
        result = self.filter.filter_informal_language(text)
        assert "fruta" in result
    
    def test_punctuation_preserved(self):
        text = "Olá! Como vai? Tudo bem."
        result = self.filter.filter_informal_language(text)
        assert "!" in result
        assert "?" in result
        assert "." in result
    
    def test_newlines_preserved(self):
        text = "Olá,\n\nComo posso ajudar?"
        result = self.filter.filter_informal_language(text)
        assert "\n" in result
    
    def test_urls_preserved(self):
        text = "Acesse https://example.com para mais informações"
        result = self.filter.filter_informal_language(text)
        assert "https://example.com" in result
    
    def test_email_preserved(self):
        text = "Envie para contato@empresa.com"
        result = self.filter.filter_informal_language(text)
        assert "contato@empresa.com" in result
    
    def test_numbers_preserved(self):
        text = "O salário é R$ 5.000,00"
        result = self.filter.filter_informal_language(text)
        assert "5.000,00" in result
    
    def test_special_characters(self):
        text = "Olá! @#$%^&*()"
        result = self.filter.filter_informal_language(text)
        assert "@#$%^&*()" in result
    
    def test_very_long_text(self):
        text = "vc " * 1000
        result = self.filter.filter_informal_language(text)
        assert "vc" not in result.lower()
    
    def test_unicode_characters(self):
        text = "Olá, café está pronto ☕"
        result = self.filter.filter_informal_language(text)
        assert "café" in result


class TestGetFilterStats:
    """Tests for get_filter_stats method."""
    
    def setup_method(self):
        self.filter = ToneFilter()
    
    def test_stats_for_filtered_text(self):
        original = "oi vc, blz? kkkk"
        filtered = self.filter.apply_all_filters(original)
        stats = self.filter.get_filter_stats(original, filtered)
        
        assert "original_length" in stats
        assert "filtered_length" in stats
        assert "characters_changed" in stats
        assert "original_issues_count" in stats
        assert "filtered_issues_count" in stats
        assert "issues_fixed" in stats
        assert "is_now_professional" in stats
    
    def test_stats_issues_fixed(self):
        original = "vc tá blz?"
        filtered = self.filter.apply_all_filters(original)
        stats = self.filter.get_filter_stats(original, filtered)
        
        assert stats["issues_fixed"] > 0


class TestPerformance:
    """Performance tests for the ToneFilter."""
    
    def setup_method(self):
        self.filter = ToneFilter()
    
    def test_filter_performance_short_text(self):
        text = "oi vc, tá blz? pra mim tmj kkkk"
        
        start = time.time()
        for _ in range(1000):
            self.filter.apply_all_filters(text)
        duration = time.time() - start
        
        assert duration < 1.0
    
    def test_filter_performance_medium_text(self):
        text = "oi vc, " * 100
        
        start = time.time()
        for _ in range(100):
            self.filter.apply_all_filters(text)
        duration = time.time() - start
        
        assert duration < 1.0
    
    def test_filter_performance_long_text(self):
        text = "oi vc, tá blz? " * 500
        
        start = time.time()
        for _ in range(10):
            self.filter.apply_all_filters(text)
        duration = time.time() - start
        
        assert duration < 2.0
    
    def test_validation_performance(self):
        text = "vc tá blz? pra mim tmj kkk 😊😊😊"
        
        start = time.time()
        for _ in range(1000):
            self.filter.validate_professional_tone(text)
        duration = time.time() - start
        
        assert duration < 1.0


class TestConstants:
    """Tests to verify constants are properly defined."""
    
    def test_informal_terms_not_empty(self):
        assert len(INFORMAL_TERMS) > 0
    
    def test_forbidden_patterns_not_empty(self):
        assert len(FORBIDDEN_PATTERNS) > 0
    
    def test_professional_indicators_not_empty(self):
        assert len(PROFESSIONAL_INDICATORS) > 0
    
    def test_informal_terms_has_required_mappings(self):
        patterns = list(INFORMAL_TERMS.keys())
        patterns_str = " ".join(patterns)
        assert "vc" in patterns_str
        assert "pra" in patterns_str
        assert "blz" in patterns_str
        assert "tmj" in patterns_str
    
    def test_professional_indicators_include_greetings(self):
        assert "olá" in PROFESSIONAL_INDICATORS
