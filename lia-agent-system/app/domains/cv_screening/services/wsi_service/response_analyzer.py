"""
WSI Response Analyzer - Deterministic response scoring.
"""
import logging
from typing import Any

from app.domains.cv_screening.services.wsi_deterministic_scorer import (
    DeterministicWSIResult,
    calculate_wsi_deterministic,
)

from .models import ResponseAnalysis, WSIQuestion

logger = logging.getLogger(__name__)

class WSIResponseAnalyzer:
    """
    Analisador de respostas com scoring DETERMINÍSTICO baseado em Dreyfus + Bloom.
    
    IMPORTANTE: Os scores são calculados de forma 100% determinística.
    O LLM NÃO participa do cálculo de scores - apenas da extração de informações.
    """
    
    def __init__(self, llm=None, *, enable_layer2: bool = False, layer2_extractor=None):
        self.llm = llm
        self._enable_layer2 = enable_layer2
        self._layer2_extractor = layer2_extractor
    
    async def analyze(
        self,
        question: WSIQuestion,
        response: str
    ) -> ResponseAnalysis:
        """
        Analisa resposta usando cálculos 100% DETERMINÍSTICOS.
        
        Metodologia WSI (scoring determinístico):
        1. Extrai autodeclaração via regex
        2. Calcula contexto via indicadores
        3. Classifica Bloom via keywords
        4. Classifica Dreyfus via anos + contexto
        5. Detecta red flags via regras fixas
        6. Aplica fórmula fixa: Score = (0.6 × Autodec) + (0.4 × Contexto) - Penalty + Bonus
        
        NENHUM LLM é usado para calcular scores.
        """
        try:
            result: DeterministicWSIResult = calculate_wsi_deterministic(
                response_text=response,
                competency_name=question.competency,
                question_framework=question.framework
            )
            
            justification_text = f"{result.justification} | Fórmula: {result.formula_applied}"
            layer2_signals = None
            layer2_degraded_reason = None
            if self._enable_layer2 and self._layer2_extractor is not None:
                try:
                    layer2_signals = await self._layer2_extractor.extract(question, response)
                except Exception as _l2_exc:
                    layer2_degraded_reason = str(_l2_exc)
                    justification_text += " | Camada 2 degradada"
                    logger.warning("Layer2 extraction degraded: %s", _l2_exc)
            return ResponseAnalysis(
                question_id=question.id,
                competency=question.competency,
                response_text=response,
                autodeclaration_score=result.autodeclaracao_score,
                context_score=result.context_score,
                bloom_level=result.bloom_level,
                dreyfus_level=result.dreyfus_level,
                evidences=result.evidences,
                red_flags=result.red_flags,
                consistency_penalty=result.penalty,
                final_score=result.final_score,
                justification=justification_text,
                layer2_signals=layer2_signals,
                layer2_degraded_reason=layer2_degraded_reason,
                # Phase 2.5: forward the BigFive trait of the question so
                # downstream score_calculator can build ocean_traits dict.
                trait_ocean=getattr(question, "big_five_mapping", None),
            )
        except Exception as e:
            logger.error(f"Deterministic analysis failed for {question.competency}: {e}")
            return ResponseAnalysis(
                question_id=question.id,
                competency=question.competency,
                response_text=response,
                autodeclaration_score=3.0,
                context_score=3.0,
                bloom_level=3,
                dreyfus_level=3,
                evidences=[],
                red_flags=["Erro no processamento determinístico"],
                consistency_penalty=0.0,
                final_score=3.0,
                justification=f"Fallback aplicado devido a erro: {str(e)}",
                # Phase 2.5: preserve trait association even in fallback path.
                trait_ocean=getattr(question, "big_five_mapping", None),
            )


