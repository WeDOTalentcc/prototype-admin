"""
KanbanAssistantService - Generates proactive suggestions for the recruiter's Kanban view.
Uses candidate context and pipeline state to suggest next actions.
"""
import logging
from typing import Dict, Any, List, Optional

from app.shared.providers.llm_client import llm_complete, is_llm_available

logger = logging.getLogger(__name__)


class KanbanAssistantService:
    """Provides AI-powered suggestions for the Kanban pipeline view."""

    @staticmethod
    async def get_suggestions(
        candidates_in_stage: List[Dict[str, Any]],
        stage_name: str,
        action_behavior: str,
        company_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        suggestions = []

        try:
            for candidate in candidates_in_stage[:10]:
                days_in_stage = candidate.get("days_in_stage", 0)

                if days_in_stage > 7 and action_behavior in ("screening", "scheduling"):
                    suggestions.append({
                        "type": "stale_candidate",
                        "severity": "warning",
                        "candidate_id": candidate.get("id"),
                        "candidate_name": candidate.get("name", "Candidato"),
                        "message": f"{candidate.get('name', 'Candidato')} está há {days_in_stage} dias nesta etapa",
                        "suggested_action": "Considere avançar ou dar feedback",
                        "stage": stage_name,
                    })

                wsi_score = candidate.get("wsi_score")
                if wsi_score and isinstance(wsi_score, (int, float)):
                    if wsi_score >= 80 and action_behavior == "screening":
                        suggestions.append({
                            "type": "high_score",
                            "severity": "info",
                            "candidate_id": candidate.get("id"),
                            "candidate_name": candidate.get("name", "Candidato"),
                            "message": f"{candidate.get('name', 'Candidato')} tem score WSI alto ({wsi_score})",
                            "suggested_action": "Considere avançar para entrevista",
                            "stage": stage_name,
                        })
                    elif wsi_score < 40 and action_behavior == "screening":
                        suggestions.append({
                            "type": "low_score",
                            "severity": "attention",
                            "candidate_id": candidate.get("id"),
                            "candidate_name": candidate.get("name", "Candidato"),
                            "message": f"{candidate.get('name', 'Candidato')} tem score WSI baixo ({wsi_score})",
                            "suggested_action": "Avaliar se candidato deve permanecer no processo",
                            "stage": stage_name,
                        })
        except Exception as e:
            logger.error(f"[KANBAN-ASSISTANT] Error generating suggestions: {e}", exc_info=True)

        return suggestions

    @staticmethod
    async def generate_stage_summary(
        stage_name: str,
        candidate_count: int,
        action_behavior: str,
        avg_days_in_stage: float = 0,
    ) -> Optional[str]:
        if not is_llm_available():
            return None

        try:
            prompt = f"""Gere um resumo CURTO (máx 1 frase) sobre o estado desta etapa do pipeline:
- Etapa: {stage_name}
- Candidatos: {candidate_count}
- Tipo de ação: {action_behavior}
- Tempo médio na etapa: {avg_days_in_stage:.1f} dias

Responda apenas com a frase de resumo em português, sem formatação."""

            result = await llm_complete(prompt=prompt, max_tokens=100, temperature=0.3)
            return result.strip() if result else None
        except Exception as e:
            logger.warning(f"[KANBAN-ASSISTANT] Stage summary generation failed: {e}")
            return None
