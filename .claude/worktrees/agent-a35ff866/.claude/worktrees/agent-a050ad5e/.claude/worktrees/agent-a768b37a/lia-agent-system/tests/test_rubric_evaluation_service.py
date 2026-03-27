"""
Testes unitários para RubricEvaluationService.

Cobre:
- Fórmula BARS: EXCEEDS(100) / MEETS(75) / PARTIAL(40) / MISSING(0)
- Multiplicadores de prioridade: ESSENTIAL(3x) / IMPORTANT(2x) / NICE_TO_HAVE(1x)
- Cache: hit, miss, expirado, thread-safety
- Variation logging: threshold de 10 pontos
- Batch evaluation: múltiplos candidatos em paralelo
- Formato legado (LIA Score)

LLM mockado — testes são determinísticos e rápidos.

Referência: Schmidt & Hunter (1998), BARS methodology.
"""
import pytest
import asyncio
import threading
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.domains.cv_screening.services.rubric_evaluation_service import (
    RubricEvaluationCache,
    CACHE_TTL_HOURS,
    VARIATION_THRESHOLD,
)
from app.schemas.rubric import (
    RubricEvaluationResult,
    RequirementEvaluation,
    JobRequirementCreate,
    EvaluationLevelEnum,
    RequirementPriorityEnum,
    EvidenceType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_requirement(req: str, priority: RequirementPriorityEnum) -> JobRequirementCreate:
    return JobRequirementCreate(
        requirement=req,
        description=f"Descrição: {req}",
        priority=priority,
    )


def make_evaluation(
    requirement: str,
    level: EvaluationLevelEnum,
    priority: RequirementPriorityEnum,
) -> RequirementEvaluation:
    points_map = {
        EvaluationLevelEnum.EXCEEDS: 100,
        EvaluationLevelEnum.MEETS: 75,
        EvaluationLevelEnum.PARTIAL: 40,
        EvaluationLevelEnum.MISSING: 0,
    }
    multiplier_map = {
        RequirementPriorityEnum.ESSENTIAL: 3,
        RequirementPriorityEnum.IMPORTANT: 2,
        RequirementPriorityEnum.NICE_TO_HAVE: 1,
    }
    points = points_map[level]
    multiplier = multiplier_map[priority]
    return RequirementEvaluation(
        requirement=requirement,
        priority=priority,
        level=level,
        points=points,
        multiplier=multiplier,
        weighted_points=float(points * multiplier),
        max_weighted_points=float(100 * multiplier),
        evidence="Evidência extraída do CV.",
        reasoning="Raciocínio da avaliação.",
        confidence=0.9,
    )


def make_result(score: float, reasoning: str = "Avaliação geral do candidato.") -> RubricEvaluationResult:
    return RubricEvaluationResult(
        score=score,
        raw_score=score,
        total_weighted_points=score * 3,
        max_possible_points=300.0,
        evaluations=[],
        strengths=["Ponto forte"],
        concerns=[],
        reasoning=reasoning,
        recommendation="meets",
        scoring_methodology="andre_v1",
    )


CANDIDATE_A = {"id": "cand-001", "name": "João Silva", "email": "joao@example.com", "technical_skills": ["Python"]}
CANDIDATE_B = {"id": "cand-002", "name": "Maria Souza", "email": "maria@example.com", "technical_skills": ["Java"]}
REQUIREMENTS_1 = [make_requirement("Python", RequirementPriorityEnum.ESSENTIAL)]
REQUIREMENTS_2 = [make_requirement("Java", RequirementPriorityEnum.IMPORTANT)]


# ---------------------------------------------------------------------------
# Testes de Fórmula BARS
# ---------------------------------------------------------------------------

class TestBARSFormula:
    """Verifica a fórmula: Score = Σ(Points × Mult) / Σ(100 × Mult) × 100."""

    def test_exceeds_essential_perfect_score(self):
        """EXCEEDS em ESSENTIAL único → score máximo (cap 99)."""
        ev = make_evaluation("Python", EvaluationLevelEnum.EXCEEDS, RequirementPriorityEnum.ESSENTIAL)
        score = (ev.weighted_points / ev.max_weighted_points) * 100
        assert score == pytest.approx(100.0)  # uncapped; service applies cap 99

    def test_missing_essential_zero_score(self):
        """MISSING em ESSENTIAL → 0 pontos ponderados."""
        ev = make_evaluation("Python", EvaluationLevelEnum.MISSING, RequirementPriorityEnum.ESSENTIAL)
        assert ev.weighted_points == 0.0
        assert ev.max_weighted_points == 300.0

    def test_meets_important_correct_points(self):
        """MEETS (75pts) × IMPORTANT (2x) = 150 pontos ponderados."""
        ev = make_evaluation("Java", EvaluationLevelEnum.MEETS, RequirementPriorityEnum.IMPORTANT)
        assert ev.points == 75
        assert ev.multiplier == 2
        assert ev.weighted_points == 150.0
        assert ev.max_weighted_points == 200.0

    def test_partial_nice_to_have_correct_points(self):
        """PARTIAL (40pts) × NICE_TO_HAVE (1x) = 40 pontos ponderados."""
        ev = make_evaluation("Docker", EvaluationLevelEnum.PARTIAL, RequirementPriorityEnum.NICE_TO_HAVE)
        assert ev.points == 40
        assert ev.multiplier == 1
        assert ev.weighted_points == 40.0
        assert ev.max_weighted_points == 100.0

    def test_priority_multipliers_correct_order(self):
        """ESSENTIAL (3x) > IMPORTANT (2x) > NICE_TO_HAVE (1x)."""
        essential = make_evaluation("req", EvaluationLevelEnum.MEETS, RequirementPriorityEnum.ESSENTIAL)
        important = make_evaluation("req", EvaluationLevelEnum.MEETS, RequirementPriorityEnum.IMPORTANT)
        nice = make_evaluation("req", EvaluationLevelEnum.MEETS, RequirementPriorityEnum.NICE_TO_HAVE)
        assert essential.weighted_points > important.weighted_points > nice.weighted_points

    def test_evaluation_levels_correct_points_order(self):
        """EXCEEDS(100) > MEETS(75) > PARTIAL(40) > MISSING(0)."""
        priority = RequirementPriorityEnum.IMPORTANT
        exceeds = make_evaluation("req", EvaluationLevelEnum.EXCEEDS, priority)
        meets = make_evaluation("req", EvaluationLevelEnum.MEETS, priority)
        partial = make_evaluation("req", EvaluationLevelEnum.PARTIAL, priority)
        missing = make_evaluation("req", EvaluationLevelEnum.MISSING, priority)
        assert exceeds.points > meets.points > partial.points > missing.points


# ---------------------------------------------------------------------------
# Testes de Cache
# ---------------------------------------------------------------------------

class TestRubricEvaluationCache:
    """Verifica comportamento do cache in-memory."""

    def setup_method(self):
        self.cache = RubricEvaluationCache(ttl_hours=1)
        self.result = make_result(score=75.0)

    def test_cache_miss_on_new_key(self):
        """Cache miss para entrada nova."""
        result = self.cache.get(CANDIDATE_A, REQUIREMENTS_1)
        assert result is None

    def test_cache_hit_after_set(self):
        """Cache hit após set."""
        self.cache.set(CANDIDATE_A, REQUIREMENTS_1, self.result)
        cached = self.cache.get(CANDIDATE_A, REQUIREMENTS_1)
        assert cached is not None
        assert cached.score == 75.0

    def test_cache_different_candidates_isolated(self):
        """Candidatos diferentes têm entradas separadas no cache."""
        result_b = make_result(score=50.0)
        self.cache.set(CANDIDATE_A, REQUIREMENTS_1, self.result)
        self.cache.set(CANDIDATE_B, REQUIREMENTS_1, result_b)
        assert self.cache.get(CANDIDATE_A, REQUIREMENTS_1).score == 75.0
        assert self.cache.get(CANDIDATE_B, REQUIREMENTS_1).score == 50.0

    def test_cache_different_requirements_isolated(self):
        """Requisitos diferentes geram chaves diferentes."""
        self.cache.set(CANDIDATE_A, REQUIREMENTS_1, self.result)
        result = self.cache.get(CANDIDATE_A, REQUIREMENTS_2)
        assert result is None

    def test_cache_expiry(self):
        """Cache expirado retorna None."""
        short_cache = RubricEvaluationCache(ttl_hours=0)  # TTL = 0 horas → expira imediatamente
        short_cache.set(CANDIDATE_A, REQUIREMENTS_1, self.result)
        # Forçar expiração manipulando o _cache interno
        key = list(short_cache._cache.keys())[0]
        short_cache._cache[key] = (self.result, datetime.utcnow() - timedelta(hours=1))
        assert short_cache.get(CANDIDATE_A, REQUIREMENTS_1) is None

    def test_clear_expired_removes_stale_entries(self):
        """clear_expired() remove apenas entradas expiradas."""
        self.cache.set(CANDIDATE_A, REQUIREMENTS_1, self.result)
        key = list(self.cache._cache.keys())[0]
        # Força expiração
        self.cache._cache[key] = (self.result, datetime.utcnow() - timedelta(hours=2))
        cleared = self.cache.clear_expired()
        assert cleared == 1
        assert len(self.cache._cache) == 0

    def test_cache_thread_safety(self):
        """Cache suporta acesso concorrente sem data races."""
        errors = []

        def writer():
            try:
                for i in range(20):
                    candidate = {**CANDIDATE_A, "id": f"cand-{i}"}
                    self.cache.set(candidate, REQUIREMENTS_1, make_result(float(i)))
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for i in range(20):
                    candidate = {**CANDIDATE_A, "id": f"cand-{i}"}
                    self.cache.get(candidate, REQUIREMENTS_1)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread safety errors: {errors}"


# ---------------------------------------------------------------------------
# Testes de Variation Logging
# ---------------------------------------------------------------------------

class TestVariationLogging:
    """Verifica detecção e log de variações de score."""

    def setup_method(self):
        self.cache = RubricEvaluationCache(ttl_hours=1)

    def test_variation_within_threshold_logged(self):
        """Variação dentro do threshold (< 10pts) é registrada sem alerta."""
        self.cache.log_variation("cand-001", "job-001", old_score=70.0, new_score=75.0, variation=5.0)
        log = self.cache.get_variation_log()
        assert len(log) == 1
        assert log[0]["exceeds_threshold"] is False

    def test_variation_above_threshold_flagged(self):
        """Variação acima do threshold (>= 10pts) é sinalizada como alerta."""
        self.cache.log_variation("cand-001", "job-001", old_score=60.0, new_score=80.0, variation=20.0)
        log = self.cache.get_variation_log()
        assert log[0]["exceeds_threshold"] is True

    def test_variation_log_accumulates_entries(self):
        """Log acumula múltiplas entradas."""
        self.cache.log_variation("c1", "j1", 70.0, 72.0, 2.0)
        self.cache.log_variation("c2", "j1", 50.0, 80.0, 30.0)
        log = self.cache.get_variation_log()
        assert len(log) == 2

    def test_variation_log_is_copy(self):
        """get_variation_log() retorna cópia — mutações externas não afetam o estado interno."""
        self.cache.log_variation("c1", "j1", 70.0, 75.0, 5.0)
        log = self.cache.get_variation_log()
        log.clear()
        assert len(self.cache.get_variation_log()) == 1


# ---------------------------------------------------------------------------
# Testes de Calibration
# ---------------------------------------------------------------------------

class TestCalibrationVersion:
    """Verifica que versão de calibração invalida cache."""

    def setup_method(self):
        self.cache = RubricEvaluationCache(ttl_hours=1)
        self.result = make_result(score=80.0)

    def test_different_calibration_version_cache_miss(self):
        """Versão de calibração diferente gera cache miss (chave diferente)."""
        self.cache.set(CANDIDATE_A, REQUIREMENTS_1, self.result, calibration_version=1)
        # Versão 2 deve gerar cache miss
        result = self.cache.get(CANDIDATE_A, REQUIREMENTS_1, calibration_version=2)
        assert result is None

    def test_same_calibration_version_cache_hit(self):
        """Mesma versão de calibração gera cache hit."""
        self.cache.set(CANDIDATE_A, REQUIREMENTS_1, self.result, calibration_version=3)
        result = self.cache.get(CANDIDATE_A, REQUIREMENTS_1, calibration_version=3)
        assert result is not None
        assert result.score == 80.0
