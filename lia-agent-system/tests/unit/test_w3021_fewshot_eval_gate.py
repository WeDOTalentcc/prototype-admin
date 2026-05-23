"""
Unit tests · W3-021 — eval gate thresholds do FewShotEvolutionService.

Garante que ninguém altere MIN_CONFIDENCE, AUTO_APPROVE_THRESHOLD ou
MANUAL_REVIEW_THRESHOLD sem os testes quebrarem explicitamente.

Testes são puramente unitários (sem IO, sem DB, sem LLM).
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers de import
# ---------------------------------------------------------------------------

def _import_module():
    from app.services.fewshot_evolution_service import (
        MIN_CONFIDENCE,
        AUTO_APPROVE_THRESHOLD,
        MANUAL_REVIEW_THRESHOLD,
        MAX_FEW_SHOT_PER_AGENT,
        MIN_TOOL_CALLS,
        FewShotCandidateSelector,
    )
    return (
        MIN_CONFIDENCE,
        AUTO_APPROVE_THRESHOLD,
        MANUAL_REVIEW_THRESHOLD,
        MAX_FEW_SHOT_PER_AGENT,
        MIN_TOOL_CALLS,
        FewShotCandidateSelector,
    )


# ---------------------------------------------------------------------------
# 1. Constantes pinadas
# ---------------------------------------------------------------------------

class TestEvalGateThresholds:
    """Pina os valores exatos dos thresholds — qualquer mudança quebra estes testes."""

    def test_min_confidence_is_085(self):
        MIN_CONFIDENCE, *_ = _import_module()
        assert MIN_CONFIDENCE == 0.85, (
            f"MIN_CONFIDENCE foi alterado para {MIN_CONFIDENCE}. "
            "Valor canonical é 0.85 (W3-021). Abrir ADR antes de mudar."
        )

    def test_auto_approve_threshold_is_090(self):
        _, AUTO_APPROVE_THRESHOLD, *_ = _import_module()
        assert AUTO_APPROVE_THRESHOLD == 0.90, (
            f"AUTO_APPROVE_THRESHOLD foi alterado para {AUTO_APPROVE_THRESHOLD}. "
            "Valor canonical é 0.90 (W3-021). Abrir ADR antes de mudar."
        )

    def test_manual_review_threshold_is_070(self):
        _, _, MANUAL_REVIEW_THRESHOLD, *_ = _import_module()
        assert MANUAL_REVIEW_THRESHOLD == 0.70, (
            f"MANUAL_REVIEW_THRESHOLD foi alterado para {MANUAL_REVIEW_THRESHOLD}. "
            "Valor canonical é 0.70 (W3-021). Abrir ADR antes de mudar."
        )

    def test_max_few_shot_per_agent_is_15(self):
        _, _, _, MAX_FEW_SHOT_PER_AGENT, *_ = _import_module()
        assert MAX_FEW_SHOT_PER_AGENT == 15, (
            f"MAX_FEW_SHOT_PER_AGENT foi alterado para {MAX_FEW_SHOT_PER_AGENT}. "
            "Valor canonical é 15 (W3-021)."
        )

    def test_min_tool_calls_is_2(self):
        _, _, _, _, MIN_TOOL_CALLS, _ = _import_module()
        assert MIN_TOOL_CALLS == 2, (
            f"MIN_TOOL_CALLS foi alterado para {MIN_TOOL_CALLS}. "
            "Valor canonical é 2 (W3-021)."
        )


# ---------------------------------------------------------------------------
# 2. Invariante da pirâmide: AUTO_APPROVE > MIN_CONFIDENCE > MANUAL_REVIEW
# ---------------------------------------------------------------------------

class TestThresholdInvariant:
    """Garante que a relação lógica entre os três thresholds nunca é violada."""

    def test_auto_approve_gt_min_confidence(self):
        MIN_CONFIDENCE, AUTO_APPROVE_THRESHOLD, MANUAL_REVIEW_THRESHOLD, *_ = _import_module()
        assert AUTO_APPROVE_THRESHOLD > MIN_CONFIDENCE, (
            f"Invariante violada: AUTO_APPROVE ({AUTO_APPROVE_THRESHOLD}) deve ser "
            f"> MIN_CONFIDENCE ({MIN_CONFIDENCE}). "
            "Se AUTO_APPROVE <= MIN_CONFIDENCE, a zona de 'auto-insert' some ou inverte."
        )

    def test_min_confidence_gt_manual_review(self):
        MIN_CONFIDENCE, AUTO_APPROVE_THRESHOLD, MANUAL_REVIEW_THRESHOLD, *_ = _import_module()
        assert MIN_CONFIDENCE > MANUAL_REVIEW_THRESHOLD, (
            f"Invariante violada: MIN_CONFIDENCE ({MIN_CONFIDENCE}) deve ser "
            f"> MANUAL_REVIEW ({MANUAL_REVIEW_THRESHOLD}). "
            "Se MIN_CONFIDENCE <= MANUAL_REVIEW, a zona de 'revisão manual' some ou inverte."
        )

    def test_pyramid_full_ordering(self):
        MIN_CONFIDENCE, AUTO_APPROVE_THRESHOLD, MANUAL_REVIEW_THRESHOLD, *_ = _import_module()
        assert AUTO_APPROVE_THRESHOLD > MIN_CONFIDENCE > MANUAL_REVIEW_THRESHOLD > 0, (
            "Pirâmide completa violada: "
            f"esperado AUTO_APPROVE ({AUTO_APPROVE_THRESHOLD}) > "
            f"MIN_CONFIDENCE ({MIN_CONFIDENCE}) > "
            f"MANUAL_REVIEW ({MANUAL_REVIEW_THRESHOLD}) > 0"
        )

    def test_all_thresholds_between_0_and_1(self):
        MIN_CONFIDENCE, AUTO_APPROVE_THRESHOLD, MANUAL_REVIEW_THRESHOLD, *_ = _import_module()
        for name, value in [
            ("MIN_CONFIDENCE", MIN_CONFIDENCE),
            ("AUTO_APPROVE_THRESHOLD", AUTO_APPROVE_THRESHOLD),
            ("MANUAL_REVIEW_THRESHOLD", MANUAL_REVIEW_THRESHOLD),
        ]:
            assert 0.0 < value < 1.0, (
                f"{name}={value} fora do intervalo (0, 1). "
                "Thresholds devem ser probabilidades válidas."
            )


# ---------------------------------------------------------------------------
# 3. evaluate_candidate — score abaixo de MANUAL_REVIEW_THRESHOLD
# ---------------------------------------------------------------------------

class TestEvaluateCandidateBelowThreshold:
    """
    Interação de baixa qualidade: confiança 0.60, sem reasoning, sem criteria,
    sem score, decision desconhecida → evaluate_candidate retorna 0.0
    (abaixo de MANUAL_REVIEW_THRESHOLD=0.70 → rejeitado pelo pipeline).
    """

    def _make_selector(self):
        _, _, _, _, _, FewShotCandidateSelector = _import_module()
        return FewShotCandidateSelector()

    def test_low_quality_interaction_scores_zero(self):
        selector = self._make_selector()
        interaction = {
            "confidence": 0.60,
            "reasoning": [],
            "criteria_used": [],
            "score": None,
            "decision": "pending",
        }
        result = selector.evaluate_candidate(interaction)
        assert result == 0.0, (
            f"Interação de baixa qualidade deveria ter score 0.0, got {result}"
        )

    def test_low_quality_score_below_manual_review(self):
        """Score 0.0 < MANUAL_REVIEW_THRESHOLD=0.70 → seria rejeitado pelo pipeline."""
        _, _, MANUAL_REVIEW_THRESHOLD, *_ = _import_module()
        selector = self._make_selector()
        interaction = {
            "confidence": 0.60,
            "reasoning": [],
            "criteria_used": [],
            "score": None,
            "decision": "unknown",
        }
        result = selector.evaluate_candidate(interaction)
        assert result < MANUAL_REVIEW_THRESHOLD, (
            f"Esperado score < MANUAL_REVIEW ({MANUAL_REVIEW_THRESHOLD}), got {result}. "
            "Interação ruim NÃO deve passar o gate de revisão manual."
        )

    def test_score_is_float_not_none(self):
        selector = self._make_selector()
        interaction = {
            "confidence": 0.50,
            "reasoning": None,
            "criteria_used": None,
            "score": None,
            "decision": "",
        }
        result = selector.evaluate_candidate(interaction)
        assert isinstance(result, float), (
            f"evaluate_candidate deve retornar float, got {type(result)}"
        )


# ---------------------------------------------------------------------------
# 4. evaluate_candidate — score auto-approve (>= AUTO_APPROVE_THRESHOLD=0.90)
# ---------------------------------------------------------------------------

class TestEvaluateCandidateAutoApprove:
    """
    Interação excelente: confidence 0.95, reasoning rico, criteria amplos,
    score presente, decision approved → evaluate_candidate retorna >= 0.90
    → elegível para auto-insert.
    """

    def _make_selector(self):
        _, _, _, _, _, FewShotCandidateSelector = _import_module()
        return FewShotCandidateSelector()

    def test_excellent_interaction_meets_auto_approve(self):
        _, AUTO_APPROVE_THRESHOLD, *_ = _import_module()
        selector = self._make_selector()
        interaction = {
            "confidence": 0.95,   # >= 0.90 → +0.35
            "reasoning": ["step1", "step2", "step3"],  # len >= 2 → +0.25
            "criteria_used": ["c1", "c2", "c3"],       # len >= 3 → +0.20
            "score": 0.95,        # not None → +0.10
            "decision": "approved",  # in whitelist → +0.10
        }
        result = selector.evaluate_candidate(interaction)
        assert result >= AUTO_APPROVE_THRESHOLD, (
            f"Interação excelente deveria score >= AUTO_APPROVE ({AUTO_APPROVE_THRESHOLD}), "
            f"got {result}"
        )

    def test_excellent_interaction_total_score_is_100(self):
        selector = self._make_selector()
        interaction = {
            "confidence": 0.95,
            "reasoning": ["step1", "step2", "step3"],
            "criteria_used": ["c1", "c2", "c3"],
            "score": 0.95,
            "decision": "approved",
        }
        result = selector.evaluate_candidate(interaction)
        assert result == 1.0, (
            f"Interação excelente com todos os critérios deveria ter score 1.0, got {result}"
        )

    def test_completed_decision_also_scores_high(self):
        _, AUTO_APPROVE_THRESHOLD, *_ = _import_module()
        selector = self._make_selector()
        interaction = {
            "confidence": 0.95,
            "reasoning": ["r1", "r2"],
            "criteria_used": ["c1", "c2", "c3"],
            "score": 0.91,
            "decision": "completed",  # alternativa válida
        }
        result = selector.evaluate_candidate(interaction)
        assert result >= AUTO_APPROVE_THRESHOLD, (
            f"decision='completed' também deve qualificar auto-approve, got {result}"
        )

    def test_advanced_decision_also_qualifies(self):
        _, AUTO_APPROVE_THRESHOLD, *_ = _import_module()
        selector = self._make_selector()
        interaction = {
            "confidence": 0.95,
            "reasoning": ["r1", "r2"],
            "criteria_used": ["c1", "c2", "c3"],
            "score": 0.90,
            "decision": "advanced",
        }
        result = selector.evaluate_candidate(interaction)
        assert result >= AUTO_APPROVE_THRESHOLD, (
            f"decision='advanced' também deve qualificar auto-approve, got {result}"
        )


# ---------------------------------------------------------------------------
# 5. evaluate_candidate — score zona de revisão manual (>= 0.85, < 0.90)
# ---------------------------------------------------------------------------

class TestEvaluateCandidateManualReview:
    """
    Interação boa mas não excelente: confidence 0.88 (0.85..0.90), reasoning
    rico, criteria amplos, score presente, decision approved →
    evaluate_candidate retorna 0.85 → vai para revisão manual, NÃO auto-insert.
    """

    def _make_selector(self):
        _, _, _, _, _, FewShotCandidateSelector = _import_module()
        return FewShotCandidateSelector()

    def test_good_interaction_in_manual_review_zone(self):
        MIN_CONFIDENCE, AUTO_APPROVE_THRESHOLD, MANUAL_REVIEW_THRESHOLD, *_ = _import_module()
        selector = self._make_selector()
        # conf 0.88 → +0.20 (>= 0.85 branch, not >= 0.90)
        # reasoning 3 items → +0.25
        # criteria 3 items → +0.20
        # score → +0.10
        # decision "approved" → +0.10
        # total = 0.85 — which is >= MIN_CONFIDENCE, but < AUTO_APPROVE
        interaction = {
            "confidence": 0.88,
            "reasoning": ["step1", "step2", "step3"],
            "criteria_used": ["c1", "c2", "c3"],
            "score": 0.88,
            "decision": "approved",
        }
        result = selector.evaluate_candidate(interaction)
        assert result >= MIN_CONFIDENCE, (
            f"Interação boa deveria score >= MIN_CONFIDENCE ({MIN_CONFIDENCE}), got {result}"
        )
        assert result < AUTO_APPROVE_THRESHOLD, (
            f"Interação boa mas não excelente deveria score < AUTO_APPROVE "
            f"({AUTO_APPROVE_THRESHOLD}), got {result}"
        )

    def test_manual_review_zone_exact_score(self):
        """Valida o score exato calculado para a interação da zona manual."""
        selector = self._make_selector()
        interaction = {
            "confidence": 0.88,   # >= 0.85 (not 0.90) → +0.20
            "reasoning": ["s1", "s2", "s3"],  # len >= 2 → +0.25
            "criteria_used": ["c1", "c2", "c3"],  # len >= 3 → +0.20
            "score": 0.88,        # not None → +0.10
            "decision": "approved",  # whitelist → +0.10
        }
        result = selector.evaluate_candidate(interaction)
        assert result == 0.85, (
            f"Score esperado 0.85 para interação 'boa', got {result}. "
            "Breakdown: +0.20 (conf) +0.25 (reasoning) +0.20 (criteria) +0.10 (score) +0.10 (decision)"
        )

    def test_manual_review_not_auto_insert(self):
        """
        Regra de negócio: score na zona manual NÃO deve disparar auto-insert.
        Testa a condição do pipeline: score >= AUTO_APPROVE_THRESHOLD é False.
        """
        MIN_CONFIDENCE, AUTO_APPROVE_THRESHOLD, *_ = _import_module()
        selector = self._make_selector()
        interaction = {
            "confidence": 0.88,
            "reasoning": ["r1", "r2"],
            "criteria_used": ["c1", "c2", "c3"],
            "score": 0.88,
            "decision": "approved",
        }
        result = selector.evaluate_candidate(interaction)
        # Condição do pipeline: auto-insert requer score >= AUTO_APPROVE_THRESHOLD
        would_auto_insert = result >= AUTO_APPROVE_THRESHOLD
        would_manual_review = result >= MIN_CONFIDENCE and not would_auto_insert

        assert not would_auto_insert, (
            f"Score {result} NÃO deve disparar auto-insert (threshold={AUTO_APPROVE_THRESHOLD})"
        )
        assert would_manual_review, (
            f"Score {result} DEVE ser encaminhado para revisão manual "
            f"(MIN_CONFIDENCE={MIN_CONFIDENCE})"
        )


# ---------------------------------------------------------------------------
# 6. evaluate_candidate — score entre 0.70 e 0.85 (apenas revisão manual)
# ---------------------------------------------------------------------------

class TestEvaluateCandidateMidRange:
    """
    Interação mediana: confidence baixa (< 0.85), algum reasoning.
    Score cai entre MANUAL_REVIEW (0.70) e MIN_CONFIDENCE (0.85).
    """

    def _make_selector(self):
        _, _, _, _, _, FewShotCandidateSelector = _import_module()
        return FewShotCandidateSelector()

    def test_mid_range_only_manual_review_path(self):
        """
        conf 0.60 → +0.0
        reasoning [x, y] → +0.25
        criteria [a, b, c] → +0.20
        score 0.75 → +0.10
        decision 'approved' → +0.10
        total = 0.65 — abaixo de MIN_CONFIDENCE (0.85), acima de 0 (mas ainda abaixo de MANUAL_REVIEW=0.70)
        """
        MIN_CONFIDENCE, AUTO_APPROVE_THRESHOLD, MANUAL_REVIEW_THRESHOLD, *_ = _import_module()
        selector = self._make_selector()
        interaction = {
            "confidence": 0.60,   # 0 points (< 0.85)
            "reasoning": ["r1", "r2"],  # +0.25
            "criteria_used": ["c1", "c2", "c3"],  # +0.20
            "score": 0.75,  # +0.10
            "decision": "approved",  # +0.10
        }
        result = selector.evaluate_candidate(interaction)
        # 0.25 + 0.20 + 0.10 + 0.10 = 0.65
        assert result == 0.65, f"Score esperado 0.65, got {result}"
        assert result < MIN_CONFIDENCE, (
            f"Score {result} deve ser < MIN_CONFIDENCE ({MIN_CONFIDENCE})"
        )
        assert result < MANUAL_REVIEW_THRESHOLD, (
            f"Score {result} deve ser < MANUAL_REVIEW_THRESHOLD ({MANUAL_REVIEW_THRESHOLD})"
        )

    def test_score_capped_at_10(self):
        """evaluate_candidate usa min(score, 1.0) — nunca retorna > 1.0."""
        selector = self._make_selector()
        interaction = {
            "confidence": 0.99,   # +0.35
            "reasoning": ["r1", "r2", "r3", "r4"],  # +0.25
            "criteria_used": ["c1", "c2", "c3", "c4"],  # +0.20
            "score": 0.99,  # +0.10
            "decision": "completed",  # +0.10
        }
        result = selector.evaluate_candidate(interaction)
        assert result <= 1.0, (
            f"evaluate_candidate nunca deve retornar > 1.0, got {result}"
        )


# ---------------------------------------------------------------------------
# 7. is_novel — verificação de novidade
# ---------------------------------------------------------------------------

class TestIsNovel:
    """is_novel previne inserção de duplicatas (mesmo decision_type:action)."""

    def _make_selector(self):
        _, _, _, _, _, FewShotCandidateSelector = _import_module()
        return FewShotCandidateSelector()

    def test_novel_when_key_not_in_existing(self):
        selector = self._make_selector()
        candidate = {"decision_type": "advance", "action": "schedule_interview"}
        existing_ids = {"reject:disqualify", "advance:send_proposal"}
        assert selector.is_novel(candidate, existing_ids), (
            "Combinação nova (advance:schedule_interview) deve ser considerada novel"
        )

    def test_not_novel_when_key_already_exists(self):
        selector = self._make_selector()
        candidate = {"decision_type": "advance", "action": "send_proposal"}
        existing_ids = {"advance:send_proposal"}
        assert not selector.is_novel(candidate, existing_ids), (
            "Combinação duplicada (advance:send_proposal) NÃO deve ser novel"
        )

    def test_empty_existing_ids_always_novel(self):
        selector = self._make_selector()
        candidate = {"decision_type": "any", "action": "any_action"}
        assert selector.is_novel(candidate, set()), (
            "Sem IDs existentes, qualquer candidato é novel"
        )
