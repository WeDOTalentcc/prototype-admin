"""Unit tests for WSI Camada 2 consumption no scorer determinístico
(audit M04+M05+M06 rev. 19, spec WeDOTalent §F8.3).

Cobre:
- M04 — penalidades semânticas (paráfrase, idioma, R-ausente, sem 1ª pessoa, word-bands)
- M04 — override absoluto de prompt-injection (final_score = 0)
- M05 — ajustes spec (no_trait_signals, dreyfus<esp-1, bloom>esp, quantif, traits>esp, dreyfus>esp)
- M06 — detecção de inflação semântica via Layer2 (prioritária sobre lexical)
- Regressão: Camada 1 SEM Layer2 mantém comportamento idêntico (rev. 17/18)
"""
import pytest

from app.domains.cv_screening.constants.wsi_scale import (
    BONUS_BLOOM_EXCEEDS,
    BONUS_DREYFUS_EXCEEDS,
    BONUS_QUANTIFICATION,
    BONUS_TRAIT_SIGNALS_EXCEED,
    PENALTY_DREYFUS_BELOW,
    PENALTY_LANGUAGE_MISMATCH,
    PENALTY_MISSING_R_OUTCOME,
    PENALTY_NO_FIRST_PERSON,
    PENALTY_NO_TRAIT_SIGNALS,
    PENALTY_PARAPHRASE,
    PENALTY_WORD_BAND_SHORT,
    PENALTY_WORD_BAND_VERY_SHORT,
    PROMPT_INJECTION_OVERRIDE_SCORE,
)
from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    calculate_bonus,
    calculate_penalty,
    calculate_wsi_deterministic,
    detect_red_flags,
)
from app.domains.cv_screening.services.wsi_service.models import Layer2Signals


# Resposta longa, neutra, em pt-BR — base para isolar o efeito da Layer2.
LONG_RESPONSE = (
    "Liderei um time de cinco pessoas durante seis meses em um projeto interno. "
    "Defini os marcos, distribuí responsabilidades e revisei o progresso semanalmente. "
    "Conseguimos reduzir o tempo de processamento em vinte por cento e entregar dentro do prazo."
)


def _signals(**overrides) -> Layer2Signals:
    """Layer2Signals exemplar — neutro (sem penalidade nem bônus por default)."""
    base = dict(
        is_paraphrase=False,
        is_first_person=True,
        has_R_outcome=True,
        language_consistency=True,
        prompt_injection_detected=False,
        word_count_band="50-150",
        trait_signals_count=2,
        has_quantification=False,
        semantic_inflation=False,
        bloom_demonstrated=3,
        dreyfus_demonstrated=3,
        confidence=0.9,
        extraction_warnings=[],
    )
    base.update(overrides)
    return Layer2Signals(**base)


# ---------------------------------------------------------------------------
# M04 — penalidades semânticas em calculate_penalty
# ---------------------------------------------------------------------------

class TestM04Penalties:
    def test_paraphrase_adds_penalty(self):
        baseline = calculate_penalty(LONG_RESPONSE, autodeclaracao=7.0, context_score=7.0, layer2=_signals())
        with_para = calculate_penalty(
            LONG_RESPONSE, autodeclaracao=7.0, context_score=7.0,
            layer2=_signals(is_paraphrase=True),
        )
        assert with_para == pytest.approx(baseline + PENALTY_PARAPHRASE, abs=0.01)

    def test_language_mismatch_adds_penalty(self):
        baseline = calculate_penalty(LONG_RESPONSE, 7.0, 7.0, layer2=_signals())
        diff_lang = calculate_penalty(
            LONG_RESPONSE, 7.0, 7.0,
            layer2=_signals(language_consistency=False),
        )
        assert diff_lang == pytest.approx(baseline + PENALTY_LANGUAGE_MISMATCH, abs=0.01)

    def test_missing_R_outcome_adds_penalty(self):
        baseline = calculate_penalty(LONG_RESPONSE, 7.0, 7.0, layer2=_signals())
        no_r = calculate_penalty(
            LONG_RESPONSE, 7.0, 7.0,
            layer2=_signals(has_R_outcome=False),
        )
        assert no_r == pytest.approx(baseline + PENALTY_MISSING_R_OUTCOME, abs=0.01)

    def test_no_first_person_only_in_behavioral(self):
        # Em contexto técnico (expects_first_person=False) — sem penalty.
        tech = calculate_penalty(
            LONG_RESPONSE, 7.0, 7.0,
            layer2=_signals(is_first_person=False),
            expects_first_person=False,
        )
        baseline = calculate_penalty(LONG_RESPONSE, 7.0, 7.0, layer2=_signals())
        assert tech == pytest.approx(baseline, abs=0.01)

        # Em contexto comportamental (expects_first_person=True) — aplica.
        behav = calculate_penalty(
            LONG_RESPONSE, 7.0, 7.0,
            layer2=_signals(is_first_person=False),
            expects_first_person=True,
        )
        assert behav == pytest.approx(baseline + PENALTY_NO_FIRST_PERSON, abs=0.01)

    def test_word_band_30_50_penalty(self):
        baseline = calculate_penalty(LONG_RESPONSE, 7.0, 7.0, layer2=_signals())
        short = calculate_penalty(
            LONG_RESPONSE, 7.0, 7.0,
            layer2=_signals(word_count_band="30-50"),
        )
        assert short == pytest.approx(baseline + PENALTY_WORD_BAND_SHORT, abs=0.01)

    def test_word_band_lt30_does_not_double_charge_with_no_context(self):
        """Se a resposta já tem <20 palavras (gate PENALTY_NO_CONTEXT lexical),
        a band <30 não soma de novo. Para evitar double-charging."""
        short_text = "ok foi bom"  # 3 palavras, gate <20 disparado
        # Este texto também marcaria PENALTY_NO_CONTEXT lexical sozinho.
        with_band = calculate_penalty(
            short_text, autodeclaracao=7.0, context_score=7.0,
            layer2=_signals(word_count_band="<30"),
        )
        without_band = calculate_penalty(
            short_text, autodeclaracao=7.0, context_score=7.0,
            layer2=_signals(word_count_band="50-150"),
        )
        # Mesma penalty — band <30 NÃO adiciona quando no_context lexical já cobriu.
        assert with_band == pytest.approx(without_band, abs=0.01)

    def test_word_band_lt30_charges_when_above_lexical_gate(self):
        """20-30 palavras: lexical no_context não dispara (gate é <20),
        mas band <30 SIM. Garante cobertura do range 20-29."""
        # Texto com 22 palavras (acima de 20, abaixo de 30).
        text_22 = " ".join(["palavra"] * 22)
        with_band = calculate_penalty(
            text_22, 7.0, 7.0,
            layer2=_signals(word_count_band="<30"),
        )
        without_band = calculate_penalty(
            text_22, 7.0, 7.0,
            layer2=_signals(word_count_band="50-150"),
        )
        assert with_band == pytest.approx(without_band + PENALTY_WORD_BAND_VERY_SHORT, abs=0.01)


# ---------------------------------------------------------------------------
# M04 — override prompt-injection em calculate_wsi_deterministic
# ---------------------------------------------------------------------------

class TestPromptInjectionOverride:
    def test_prompt_injection_zeros_score(self):
        result = calculate_wsi_deterministic(
            response_text=LONG_RESPONSE,
            competency_name="Liderança",
            question_framework="CBI",
            question_type="behavioral",
            bloom_expected=3,
            layer2_signals=_signals(prompt_injection_detected=True),
        )
        assert result.final_score == PROMPT_INJECTION_OVERRIDE_SCORE
        assert "prompt_injection_override" in result.formula_applied

    def test_prompt_injection_marked_in_red_flags(self):
        result = calculate_wsi_deterministic(
            response_text=LONG_RESPONSE,
            competency_name="Liderança",
            question_framework="CBI",
            question_type="behavioral",
            bloom_expected=3,
            layer2_signals=_signals(prompt_injection_detected=True),
        )
        assert any("prompt-injection" in f.lower() for f in result.red_flags)

    def test_prompt_injection_marked_in_flags_structured(self):
        result = calculate_wsi_deterministic(
            response_text=LONG_RESPONSE,
            competency_name="Liderança",
            question_framework="CBI",
            question_type="behavioral",
            bloom_expected=3,
            layer2_signals=_signals(prompt_injection_detected=True),
        )
        assert result.flags_structured.get("is_prompt_injection") is True


# ---------------------------------------------------------------------------
# M05 — ajustes spec em calculate_bonus
# ---------------------------------------------------------------------------

class TestM05BonusAdjustments:
    def test_quantification_adds_bonus(self):
        baseline = calculate_bonus(LONG_RESPONSE, layer2=_signals())
        with_q = calculate_bonus(LONG_RESPONSE, layer2=_signals(has_quantification=True))
        assert with_q == pytest.approx(baseline + BONUS_QUANTIFICATION, abs=0.01)

    def test_bloom_exceeds_expected_adds_bonus(self):
        baseline = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(bloom_demonstrated=3),
            bloom_expected=3,
        )
        higher = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(bloom_demonstrated=5),
            bloom_expected=3,
        )
        assert higher == pytest.approx(baseline + BONUS_BLOOM_EXCEEDS, abs=0.01)

    def test_trait_signals_exceed_expected_adds_bonus(self):
        baseline = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(trait_signals_count=2),
            trait_signals_expected=2,
        )
        higher = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(trait_signals_count=5),
            trait_signals_expected=2,
        )
        assert higher == pytest.approx(baseline + BONUS_TRAIT_SIGNALS_EXCEED, abs=0.01)

    def test_dreyfus_exceeds_expected_adds_bonus(self):
        baseline = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(dreyfus_demonstrated=3),
            dreyfus_expected=3,
        )
        higher = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(dreyfus_demonstrated=5),
            dreyfus_expected=3,
        )
        assert higher == pytest.approx(baseline + BONUS_DREYFUS_EXCEEDS, abs=0.01)

    def test_dreyfus_below_minus_one_subtracts(self):
        baseline = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(dreyfus_demonstrated=4),
            dreyfus_expected=4,
        )
        below = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(dreyfus_demonstrated=2),  # 2 < 4-1=3
            dreyfus_expected=4,
        )
        assert below == pytest.approx(baseline + PENALTY_DREYFUS_BELOW, abs=0.01)

    def test_no_trait_signals_in_behavioral_subtracts(self):
        with_traits = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(trait_signals_count=2),
            is_behavioral=True,
        )
        zero_traits = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(trait_signals_count=0),
            is_behavioral=True,
        )
        assert zero_traits == pytest.approx(with_traits + PENALTY_NO_TRAIT_SIGNALS, abs=0.01)

    def test_no_trait_signals_in_technical_does_nothing(self):
        with_traits = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(trait_signals_count=2),
            is_behavioral=False,
        )
        zero_traits = calculate_bonus(
            LONG_RESPONSE,
            layer2=_signals(trait_signals_count=0),
            is_behavioral=False,
        )
        assert zero_traits == pytest.approx(with_traits, abs=0.01)

    def test_bonus_clamped_at_max(self):
        """Soma máxima de bônus não passa de BONUS_MAX (cap defensivo)."""
        from app.domains.cv_screening.constants.wsi_scale import BONUS_MAX
        result = calculate_bonus(
            "ainda estou aprendendo, contribuí com open source, palestrei",  # +humility +exceptional
            layer2=_signals(
                has_quantification=True,
                bloom_demonstrated=6,
                trait_signals_count=10,
                dreyfus_demonstrated=5,
            ),
            bloom_expected=2,
            dreyfus_expected=2,
            trait_signals_expected=1,
        )
        assert result <= BONUS_MAX


# ---------------------------------------------------------------------------
# M06 — detecção de inflação semântica em detect_red_flags
# ---------------------------------------------------------------------------

class TestM06SemanticInflation:
    def test_layer2_semantic_inflation_takes_priority(self):
        # Combinação "alta autodec + baixo contexto" SOZINHA dispararia lexical,
        # mas com layer2.semantic_inflation=True a mensagem é a semântica.
        flags = detect_red_flags(
            LONG_RESPONSE,
            autodeclaracao=9.5,  # >= INFLATION_AUTODECLARATION_MIN
            context_score=4.0,   # < INFLATION_CONTEXT_MAX
            layer2=_signals(semantic_inflation=True),
        )
        assert any("Inflação semântica" in f for f in flags)
        # A mensagem lexical NÃO deve aparecer — é uma OU outra.
        assert not any("autodeclaração alta" in f for f in flags)

    def test_lexical_fallback_when_no_layer2(self):
        flags = detect_red_flags(
            LONG_RESPONSE,
            autodeclaracao=9.5,
            context_score=4.0,
            layer2=None,
        )
        assert any("autodeclaração alta" in f for f in flags)

    def test_no_layer2_inflation_no_red_flag_when_layer2_says_no(self):
        """Se Layer2 diz 'sem inflação semântica' e autodec/contexto são neutros,
        não deve haver red flag de inflação."""
        flags = detect_red_flags(
            LONG_RESPONSE,
            autodeclaracao=7.0,
            context_score=7.0,
            layer2=_signals(semantic_inflation=False),
        )
        assert not any("nflação" in f for f in flags)

    def test_semantic_inflation_appears_in_flags_structured(self):
        result = calculate_wsi_deterministic(
            response_text=LONG_RESPONSE,
            competency_name="Performance",
            question_framework="CBI",
            question_type="behavioral",
            bloom_expected=3,
            layer2_signals=_signals(semantic_inflation=True),
        )
        assert result.flags_structured.get("is_semantic_inflation") is True


# ---------------------------------------------------------------------------
# Regressão — sem Layer2, comportamento idêntico ao da rev. 17/18
# ---------------------------------------------------------------------------

class TestRegressionNoLayer2:
    def test_calculate_penalty_without_layer2_unchanged(self):
        """Sem layer2, calculate_penalty produz mesmo valor que rev. 18."""
        # Resposta longa neutra: nenhuma das heurísticas lexicais dispara.
        p = calculate_penalty(LONG_RESPONSE, autodeclaracao=7.0, context_score=7.0)
        assert p == 0.0

    def test_calculate_bonus_without_layer2_unchanged(self):
        """Sem layer2, calculate_bonus produz mesmo valor que rev. 18."""
        b = calculate_bonus(LONG_RESPONSE)
        assert b == 0.0

    def test_calculate_wsi_deterministic_without_layer2_no_override(self):
        """Sem layer2, sem override de prompt-injection. Score normal."""
        result = calculate_wsi_deterministic(
            response_text=LONG_RESPONSE,
            competency_name="Liderança",
            question_framework="CBI",
            question_type="behavioral",
            bloom_expected=3,
        )
        assert result.final_score > 0
        assert "prompt_injection_override" not in result.formula_applied
        # Sem layer2, flags_structured não tem chaves novas
        assert "is_prompt_injection" not in result.flags_structured
        assert "is_semantic_inflation" not in result.flags_structured

    def test_layer2_neutro_nao_altera_score_significativamente(self):
        """Layer2 com payload neutro (todos defaults) não inflaciona/penaliza
        muito além do baseline da Camada 1 (margem ≤ 0.5)."""
        without = calculate_wsi_deterministic(
            response_text=LONG_RESPONSE,
            competency_name="Liderança",
            question_framework="CBI",
            question_type="behavioral",
            bloom_expected=3,
            dreyfus_expected=3,
            trait_signals_expected=2,
        )
        with_neutral = calculate_wsi_deterministic(
            response_text=LONG_RESPONSE,
            competency_name="Liderança",
            question_framework="CBI",
            question_type="behavioral",
            bloom_expected=3,
            dreyfus_expected=3,
            trait_signals_expected=2,
            layer2_signals=_signals(),
        )
        assert abs(with_neutral.final_score - without.final_score) <= 0.5
