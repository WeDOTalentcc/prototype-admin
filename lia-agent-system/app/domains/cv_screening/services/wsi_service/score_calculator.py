"""
WSI Score Calculator - Weighted average scoring and percentile ranking.
"""
import logging

from .models import ResponseAnalysis, WSIResult

logger = logging.getLogger(__name__)

class WSIScoreCalculator:
    """Calculadora de WSI (média ponderada) e ranking."""
    
    def calculate(
        self,
        candidate_id: str,
        job_vacancy_id: str,
        responses: list[ResponseAnalysis],
        weights: dict[str, float],
        tech_weight: float = 0.70,
        behav_weight: float = 0.30,
    ) -> WSIResult:
        """
        Calcula WSI final usando média ponderada.

        Fórmula: WSI = (technical × tech_weight) + (behavioral × behav_weight)

        Args:
            tech_weight: Peso da dimensão técnica (default 0.70, CalibrationWeight override).
            behav_weight: Peso da dimensão comportamental (default 0.30, CalibrationWeight override).

        Classificação WSI:
        - 4.5-5.0: Excelente
        - 4.0-4.4: Alto
        - 3.0-3.9: Médio
        - 2.0-2.9: Regular
        - < 2.0: Baixo
        """
        
        # Separar respostas por tipo de competência
        technical_responses = [r for r in responses if r.competency in weights and "python" in r.competency.lower() or "javascript" in r.competency.lower() or "sql" in r.competency.lower() or "docker" in r.competency.lower() or "aws" in r.competency.lower()]
        
        # Se não conseguiu detectar técnicas por nome, assume proporção tech_weight
        if not technical_responses:
            technical_count = int(len(responses) * tech_weight)
            technical_responses = responses[:technical_count]
        
        behavioral_responses = [r for r in responses if r not in technical_responses]
        
        # Calcular WSI Técnico
        technical_wsi = 0.0
        technical_weight_sum = 0.0
        
        for response in technical_responses:
            weight = weights.get(response.competency, 0.15)  # Default 15%
            technical_wsi += response.final_score * weight
            technical_weight_sum += weight
        
        if technical_weight_sum > 0:
            technical_wsi = technical_wsi / technical_weight_sum
        else:
            technical_wsi = 0.0
        
        # Calcular WSI Comportamental
        behavioral_wsi = 0.0
        behavioral_weight_sum = 0.0
        
        for response in behavioral_responses:
            weight = weights.get(response.competency, 0.10)  # Default 10%
            behavioral_wsi += response.final_score * weight
            behavioral_weight_sum += weight
        
        if behavioral_weight_sum > 0:
            behavioral_wsi = behavioral_wsi / behavioral_weight_sum
        elif len(behavioral_responses) > 0:
            # Se não tem weights, usa média simples
            behavioral_wsi = sum(r.final_score for r in behavioral_responses) / len(behavioral_responses)
        else:
            # Se não tem respostas comportamentais, usa tech_weight do técnico
            behavioral_wsi = technical_wsi * tech_weight

        # Calcular WSI Geral (pesos vindos de CalibrationWeight ou defaults)
        overall_wsi = (technical_wsi * tech_weight) + (behavioral_wsi * behav_weight)
        
        # Classificação
        if overall_wsi >= 4.5:
            classification = "excelente"
        elif overall_wsi >= 4.0:
            classification = "alto"
        elif overall_wsi >= 3.0:
            classification = "medio"
        elif overall_wsi >= 2.0:
            classification = "regular"
        else:
            classification = "baixo"
        
        return WSIResult(
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            technical_wsi=round(technical_wsi, 2),
            behavioral_wsi=round(behavioral_wsi, 2),
            overall_wsi=round(overall_wsi, 2),
            classification=classification,
            percentile=None,  # Será calculado depois comparando com outros candidatos
            response_analyses=responses
        )
    
    def calculate_percentiles(
        self,
        results: list[WSIResult]
    ) -> list[WSIResult]:
        """
        Calcula percentis para um grupo de candidatos.
        
        Exemplo: Candidato com WSI 4.2 que está no top 10%
        terá percentile = 90.
        """
        if not results:
            return results
        
        # Ordenar por overall_wsi descendente
        sorted_results = sorted(results, key=lambda r: r.overall_wsi, reverse=True)
        total = len(sorted_results)
        
        # Atribuir percentis e ranking
        for idx, result in enumerate(sorted_results):
            result.percentile = int(((total - idx) / total) * 100)
            # Note: percentile seria melhor salvar no banco, não mutar aqui
            # Mas para simplificar o exemplo, estamos mutando
        
        return sorted_results


