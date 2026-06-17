"""
WSI Score Calculator - Weighted average scoring and percentile ranking.
"""
import logging

from .models import ResponseAnalysis, WSIResult
# P1-2 canonical fix: single source of truth for OCEAN trait whitelist
from app.shared.ocean_constants import ALLOWED_TRAITS

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
        
        # Phase 2.5: aggregate per-trait OCEAN scores from responses that
        # carry trait_ocean (propagated from WSIQuestion.big_five_mapping).
        # Strategy: group by trait, compute mean of final_score (1-5),
        # normalize to 0-1 via (mean - 1) / 4. Skip responses without
        # trait_ocean (technical / non-BigFive). Returns {} when no
        # BigFive-tagged responses exist — degrades graceful (record_hire
        # accepts partial dict per ALLOWED_TRAITS whitelist).
        ocean_traits = self._aggregate_ocean_traits(responses)

        return WSIResult(
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            technical_wsi=round(technical_wsi, 2),
            behavioral_wsi=round(behavioral_wsi, 2),
            overall_wsi=round(overall_wsi, 2),
            classification=classification,
            percentile=None,  # Será calculado depois comparando com outros candidatos
            response_analyses=responses,
            ocean_traits=ocean_traits,
        )

    @staticmethod
    def _aggregate_ocean_traits(responses: list) -> dict[str, float]:
        """Group responses by trait_ocean, mean final_score, normalize 1-5 -> 0-1.

        Phase 2.5 helper. Responses without trait_ocean are skipped
        entirely. Only OCEAN-whitelisted traits contribute (defends
        against accidental non-OCEAN strings that would later fail
        BigFiveDepartmentService.record_hire's ALLOWED_TRAITS guard).
        """
        buckets: dict[str, list[float]] = {}
        for r in responses:
            trait = getattr(r, "trait_ocean", None)
            if trait is None or trait not in ALLOWED_TRAITS:
                continue
            score = getattr(r, "final_score", None)
            if score is None:
                continue
            buckets.setdefault(trait, []).append(float(score))

        out: dict[str, float] = {}
        for trait, scores in buckets.items():
            if not scores:
                continue
            mean_score = sum(scores) / len(scores)  # 1..5
            normalized = (mean_score - 1.0) / 4.0    # 0..1
            out[trait] = round(max(0.0, min(1.0, normalized)), 4)
        return out
    
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


