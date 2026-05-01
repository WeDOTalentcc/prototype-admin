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
    
    def __init__(self, llm):
        self.llm = llm
    
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
                justification=f"{result.justification} | Fórmula: {result.formula_applied}"
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
                justification=f"Fallback aplicado devido a erro: {str(e)}"
            )


