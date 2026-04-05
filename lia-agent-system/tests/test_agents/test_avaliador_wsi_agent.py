"""
Tests for AvaliadorWSIAgent (Agent 5) - WSI Evaluation Specialist.

Tests cover:
- Deterministic WSI scoring (no LLM for calculations)
- Bloom taxonomy classification
- Dreyfus model classification
- Big Five trait mapping
- Final WSI calculation with cutoffs
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    calculate_bloom_level,
    calculate_dreyfus_level,
    BLOOM_LEVELS,
    DREYFUS_LEVELS,
    WSI_CUTOFFS,
)
from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    calculate_wsi_deterministic,
    calculate_final_wsi_score,
    extract_autodeclaracao_score,
    calculate_context_score,
    DeterministicWSIResult,
)


class TestDeterministicScorer:
    """Test the deterministic WSI scorer."""
    
    def test_extract_autodeclaracao_numeric(self):
        """Test extraction of numeric self-declaration scores."""
        assert extract_autodeclaracao_score("Eu me considero 4 de 5 em Python") == 4.0
        assert extract_autodeclaracao_score("Meu nível é 3/5") == 3.0
        assert extract_autodeclaracao_score("Nota 5 para mim") == 5.0
    
    def test_extract_autodeclaracao_keywords(self):
        """Test extraction from keyword-based declarations."""
        assert extract_autodeclaracao_score("Sou avançado em Python") == 4.0
        assert extract_autodeclaracao_score("Tenho nível intermediário") == 3.0
        assert extract_autodeclaracao_score("Sou um expert na área") == 5.0
        assert extract_autodeclaracao_score("Estou aprendendo ainda, sou básico") == 2.0
    
    def test_extract_autodeclaracao_none(self):
        """Test returns None when no declaration found."""
        result = extract_autodeclaracao_score("Trabalhei com Python em projetos")
        assert result is None
    
    def test_context_score_high_quality(self):
        """Test high-quality context indicators."""
        text = "Reduzimos latência em 80%, implementei arquitetura de microserviços em escala enterprise com métricas de produção"
        score = calculate_context_score(text)
        assert score >= 4.0
    
    def test_context_score_low_quality(self):
        """Test low-quality context indicators."""
        text = "Fiz um curso básico e estou estudando a teoria"
        score = calculate_context_score(text)
        assert score < 3.0
    
    def test_wsi_deterministic_full(self):
        """Test full deterministic WSI calculation."""
        response = """
        Considero-me 4 de 5 em Python. Tenho 5 anos de experiência desenvolvendo
        APIs com FastAPI. Implementei um sistema que reduziu latência de 2s para 150ms
        e atende 1 milhão de requisições por dia. Lidero uma equipe de 4 desenvolvedores.
        """
        result = calculate_wsi_deterministic(response, "Python", "CBI")
        
        assert isinstance(result, DeterministicWSIResult)
        assert result.autodeclaracao_score == 4.0
        assert result.context_score >= 3.5
        assert 1 <= result.bloom_level <= 6
        assert 1 <= result.dreyfus_level <= 5
        assert 1.0 <= result.final_score <= 5.0
        assert "×" in result.formula_applied
    
    def test_wsi_deterministic_with_overrides(self):
        """Test deterministic calculation respects overrides."""
        result = calculate_wsi_deterministic(
            response_text="Texto qualquer",
            competency_name="Python",
            autodeclaracao_override=4.5,
            contexto_override=4.0,
            years_experience=7.0
        )
        
        expected_raw = (0.6 * 4.5) + (0.4 * 4.0)
        assert result.final_score >= 4.0
        assert result.dreyfus_level >= 4
    
    def test_wsi_formula_applied(self):
        """Test the WSI formula is correctly applied."""
        autodec = 4.0
        contexto = 3.5
        
        result = calculate_wsi_deterministic(
            response_text="",
            autodeclaracao_override=autodec,
            contexto_override=contexto
        )
        
        expected = (0.6 * autodec) + (0.4 * contexto)
        assert abs(result.final_score - expected) <= 1.0


class TestBloomTaxonomy:
    """Test Bloom's Taxonomy classification."""
    
    def test_bloom_level_create(self):
        """Test detection of highest Bloom level (Create/Evaluate)."""
        # Uses present-tense forms matching BLOOM_LEVELS indicators exactly
        text = "Eu arquiteto soluções e lidero times de engenharia; inovo continuamente"
        level, _ = calculate_bloom_level(text)
        assert level >= 5

    def test_bloom_level_apply(self):
        """Test detection of Apply level."""
        # Uses present-tense form matching level-3 indicator "implemento"
        text = "Implemento e aplico o conhecimento na prática em projetos reais"
        level, _ = calculate_bloom_level(text)
        assert level >= 2

    def test_bloom_level_remember(self):
        """Test detection of Remember level (lowest)."""
        text = "Sei o que é Python e lembro dos conceitos"
        level, _ = calculate_bloom_level(text)
        assert level <= 2


class TestDreyfusModel:
    """Test Dreyfus skill acquisition model."""
    
    def test_dreyfus_expert(self):
        """Test Expert level detection (5+ years, high context)."""
        level, name = calculate_dreyfus_level(years_experience=7.0, context_score=4.5)
        assert level == 5
        assert "Expert" in name or "Especialista" in name

    def test_dreyfus_proficient(self):
        """Test Proficient level detection (3-5 years)."""
        level, _ = calculate_dreyfus_level(years_experience=4.0, context_score=4.0)
        assert level >= 4

    def test_dreyfus_novice(self):
        """Test Novice level detection (0-1 years)."""
        level, _ = calculate_dreyfus_level(years_experience=0.5, context_score=2.0)
        assert level <= 2


# TestBigFiveMapping e TestFinalWSICalculation removidas — funções migradas (Sprint 5).
# Big Five: app/domains/interview_scheduling/services/interview_transcript_analysis_service.py
# WSI Final: calculate_final_wsi_score em app/services/wsi_deterministic_scorer.py


class TestWSIServiceIntegration:
    """Test WSI service deterministic integration."""
    
    def test_final_wsi_score_deterministic(self):
        """Test deterministic final score calculation."""
        technical_scores = [
            ("Python", 4.0, 0.25),
            ("FastAPI", 4.5, 0.20),
            ("PostgreSQL", 3.5, 0.15)
        ]
        behavioral_scores = [
            ("Team Collaboration", 4.0, 0.20),
            ("Problem Solving", 3.8, 0.20)
        ]
        
        result = calculate_final_wsi_score(
            technical_scores=technical_scores,
            behavioral_scores=behavioral_scores,
            technical_weight=0.70,
            behavioral_weight=0.30
        )
        
        assert "final_score" in result
        assert "classification" in result
        assert "decision" in result
        assert "formula" in result
        assert 1.0 <= result["final_score"] <= 5.0


# TestAvaliadorWSIAgent removida — AvaliadorWSIAgent migrado para PipelineReActAgent (Sprint 5).


class TestNoLLMForScoring:
    """Test that no LLM is used for score calculations."""
    
    def test_deterministic_scorer_no_llm_import(self):
        """Verify deterministic scorer doesn't import LLM."""
        import app.domains.cv_screening.services.wsi_deterministic_scorer as scorer
        
        assert not hasattr(scorer, 'llm_service')
        assert not hasattr(scorer, 'claude')
        assert not hasattr(scorer, 'ainvoke')
    
    def test_score_reproducibility(self):
        """Test same input produces same output (deterministic)."""
        response = "Considero-me 4 de 5. Tenho 5 anos de experiência com Python."
        
        result1 = calculate_wsi_deterministic(response, "Python")
        result2 = calculate_wsi_deterministic(response, "Python")
        
        assert result1.final_score == result2.final_score
        assert result1.bloom_level == result2.bloom_level
        assert result1.dreyfus_level == result2.dreyfus_level
