"""
WSI Response Analyzer - Deterministic response scoring (Camada 1) + opcional
Camada 2 LLM-extractor (spec §F8.3, audit M01 rev. 18).
"""
import logging
from typing import Any

from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    DeterministicWSIResult,
    calculate_wsi_deterministic,
)

from .layer2_extractor import Layer2ExtractionError, WSILayer2Extractor
from .models import Layer2Signals, ResponseAnalysis, WSIQuestion

logger = logging.getLogger(__name__)


class WSIResponseAnalyzer:
    """Analisa respostas em duas camadas:

    - **Camada 1 (determinística)** — sempre ativa. `calculate_wsi_deterministic`
      via Dreyfus + Bloom + STAR + heurísticas lexicais.
    - **Camada 2 (LLM-extractor)** — opcional, ativada com `enable_layer2=True`.
      Spec WeDOTalent §F8.3 — extrai sinais semânticos (paráfrase, 1ª pessoa,
      R do STAR, idioma, prompt-injection, contagem de traits, quantificação,
      inflação semântica, Bloom/Dreyfus demonstrados) consumidos pela Camada 1
      em iterações futuras (M04 penalidades, M05 bônus, M06 inflação semântica).

    Camada 2 NUNCA pontua diretamente — apenas alimenta a Camada 1. Isso preserva
    o contrato determinístico do scorer e a auditabilidade SOX/LGPD.

    Falha graciosa: se a Camada 2 falhar (LLM timeout, parse, schema), a análise
    retorna o resultado determinístico puro com `layer2_degraded_reason` setado.
    Nunca raise descontrolado, nunca payload fabricado (lição M12 rev. 15).
    """

    def __init__(
        self,
        llm: Any | None = None,
        *,
        enable_layer2: bool = False,
        layer2_extractor: WSILayer2Extractor | None = None,
    ) -> None:
        """`llm` aceito por compat com o container do `WSIService`.

        Args:
            llm: legado — mantido por compat de assinatura. Ignorado pela
                Camada 1. A Camada 2 usa `llm_service` (singleton) por padrão.
            enable_layer2: ativa extração semântica via LLM (default OFF).
            layer2_extractor: injeção opcional p/ teste (mock).
        """
        self._llm = llm  # noqa: F841 — preservado para futuras subclasses
        self._enable_layer2 = enable_layer2
        if enable_layer2:
            self._layer2_extractor = layer2_extractor or WSILayer2Extractor()
        else:
            self._layer2_extractor = None

    async def _try_extract_layer2(
        self,
        question: WSIQuestion,
        response: str,
    ) -> tuple[Layer2Signals | None, str | None]:
        """Retorna (signals, degraded_reason). Apenas um deles é não-None."""
        if not self._enable_layer2 or not self._layer2_extractor:
            return None, None
        try:
            signals = await self._layer2_extractor.extract(question, response)
            return signals, None
        except Layer2ExtractionError as exc:
            # Falha esperada — degrade graciosamente (EU AI Act §13).
            logger.warning(
                "Layer2 degraded for q=%s competency=%s: %s",
                question.id, question.competency, exc,
            )
            return None, str(exc)
        except Exception as exc:
            # Falha INESPERADA — log com stack mas não derruba a análise.
            logger.exception(
                "Layer2 unexpected failure for q=%s competency=%s",
                question.id, question.competency,
            )
            return None, f"Unexpected error: {exc}"

    async def analyze(
        self,
        question: WSIQuestion,
        response: str,
    ) -> ResponseAnalysis:
        """Analisa resposta. Camada 1 é sempre executada; Camada 2 opcional."""
        # Camada 2 — extração semântica (opcional, falha graciosa).
        layer2_signals, layer2_degraded_reason = await self._try_extract_layer2(
            question, response
        )

        # Camada 1 — determinístico (sempre ativo).
        try:
            # Audit task #510 (M07) — deriva question_type do framework
            # canônico para que o scorer use o ladder Dreyfus correto
            # (técnico vs comportamental) e a fórmula tri-componente certa.
            derived_category = _category_from_framework(question.framework)
            question_type = derived_category if derived_category in ("technical", "behavioral") else "technical"
            # M11 fix (rev. 15) — propaga `bloom_expected` real da pergunta quando
            # disponível. Quando ausente, o scorer aplica default + flag degraded.
            bloom_expected = getattr(question, "bloom_expected", None)
            # M05 (rev. 19) — extrai expecteds adicionais para os ajustes da Camada 2.
            # Scoring_criteria pode trazer dreyfus_expected explicitamente; senão fica None.
            criteria = getattr(question, "scoring_criteria", {}) or {}
            dreyfus_expected = (
                getattr(question, "dreyfus_expected", None)
                or criteria.get("dreyfus_expected")
            )
            # trait_signals_expected — heurística canônica: a quantidade de
            # `expected_signals` declarada na pergunta. Quando vazio, fica None
            # e o scorer NÃO aplica o BONUS_TRAIT_SIGNALS_EXCEED (correto: sem
            # baseline, não há "excesso" comparável).
            expected_signals = getattr(question, "expected_signals", None) or []
            trait_signals_expected = len(expected_signals) if expected_signals else None
            result: DeterministicWSIResult = calculate_wsi_deterministic(
                response_text=response,
                competency_name=question.competency,
                question_framework=question.framework,
                question_type=question_type,
                bloom_expected=bloom_expected,
                dreyfus_expected=dreyfus_expected,
                trait_signals_expected=trait_signals_expected,
                layer2_signals=layer2_signals,
            )

            # M11 fix — concatena selo de qualidade degradada na justificativa
            # (auditável; UI pode renderizar badge "qualidade degradada").
            justification = f"{result.justification} | Fórmula: {result.formula_applied}"
            red_flags = list(result.red_flags)
            if result.degraded_quality:
                reasons = ", ".join(result.degraded_reasons or [])
                justification += f" | ⚠️ Qualidade degradada: {reasons}"
                red_flags.append(f"Qualidade degradada: {reasons}")

            # M01 — anota Camada 2 degradada na justificativa (auditável).
            if layer2_degraded_reason:
                justification += f" | ⚠️ Camada 2 degradada: {layer2_degraded_reason}"

            return ResponseAnalysis(
                question_id=question.id,
                competency=question.competency,
                response_text=response,
                autodeclaration_score=result.autodeclaracao_score,
                context_score=result.context_score,
                bloom_level=result.bloom_level,
                dreyfus_level=result.dreyfus_level,
                evidences=result.evidences,
                red_flags=red_flags,
                consistency_penalty=result.penalty,
                final_score=result.final_score,
                justification=justification,
                category=_category_from_framework(question.framework),
                layer2_signals=layer2_signals,
                layer2_degraded_reason=layer2_degraded_reason,
                # Audit task #528 — transparência (G23-02 + G23-03)
                # Reforça `is_llm_fallback` aqui porque o scorer não conhece
                # `layer2_degraded_reason` (apenas analyzer sabe se a Camada 2
                # foi degradada por timeout, falta de chave ou erro do LLM).
                flags_structured={
                    **(result.flags_structured or {}),
                    "is_llm_fallback": (
                        bool((result.flags_structured or {}).get("is_llm_fallback"))
                        or (layer2_degraded_reason is not None)
                    ),
                },
                degraded_quality=result.degraded_quality,
                degraded_reasons=result.degraded_reasons,
                penalty_breakdown=result.penalty_breakdown,
                bonus_breakdown=result.bonus_breakdown,
            )
        except Exception as e:
            logger.error(f"Deterministic analysis failed for {question.competency}: {e}")
            return ResponseAnalysis(
                question_id=question.id,
                competency=question.competency,
                response_text=response,
                autodeclaration_score=6.0,
                context_score=6.0,
                bloom_level=3,
                dreyfus_level=3,
                evidences=[],
                red_flags=["Erro no processamento determinístico"],
                consistency_penalty=0.0,
                final_score=6.0,
                justification=f"Fallback aplicado devido a erro: {str(e)}",
                category=_category_from_framework(question.framework),
                layer2_signals=layer2_signals,
                layer2_degraded_reason=layer2_degraded_reason,
            )


def _category_from_framework(framework: str) -> str | None:
    """Audit task #498 — mapeia framework canônico WSI → categoria de competência.

    Bloom (taxonomia cognitiva) e Dreyfus (níveis de maestria de skill)
    são frameworks técnicos. CBI (Competency-Based Interview) e BigFive
    (traços OCEAN) são comportamentais. Mantém o split determinístico no
    scorer mesmo quando todos os pesos são iguais.
    """
    if framework in ("Bloom", "Dreyfus"):
        return "technical"
    if framework in ("CBI", "BigFive"):
        return "behavioral"
    return None
