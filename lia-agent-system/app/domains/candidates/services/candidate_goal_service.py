"""
CandidateGoalService — Pure business logic extracted from RecruiterAssistantAgent.

Covers:
  - check_vacancy_candidate_goal: goal-progress math for a vacancy
  - analyze_calibration_patterns_for_session: pattern extraction from like/dislike feedbacks
"""
from collections import Counter
from datetime import datetime
from typing import Any



class CandidateGoalService:
    """Stateless service; all methods are pure calculations."""

    # ------------------------------------------------------------------
    # Vacancy candidate goal
    # ------------------------------------------------------------------

    async def check_vacancy_candidate_goal(
        self,
        vacancy_id: str,
        current_count: int,
        target_min: int = 50,
        target_max: int = 70,
    ) -> dict[str, Any]:
        """Return goal-progress assessment for a vacancy."""
        if current_count < target_min:
            status = "below_target"
            deficit = target_min - current_count
            surplus = 0

            if current_count == 0:
                recommendation = "Iniciar sourcing imediatamente com busca ampla"
                message = f"A vaga não tem candidatos ainda. Meta mínima: {target_min} candidatos."
            elif current_count < target_min * 0.3:
                recommendation = "Intensificar busca - considere usar Pearch para ampliar pool"
                message = (
                    f"A vaga tem apenas {current_count} candidatos. "
                    f"Faltam {deficit} para a meta mínima de {target_min}."
                )
            elif current_count < target_min * 0.6:
                recommendation = "Expandir critérios de busca ou adicionar fontes externas"
                message = (
                    f"A vaga tem {current_count} candidatos. "
                    f"Faltam {deficit} para atingir a meta mínima."
                )
            else:
                recommendation = "Continuar sourcing - quase atingindo a meta"
                message = f"Bom progresso! {current_count} candidatos, faltam apenas {deficit} para a meta."

        elif current_count <= target_max:
            status = "on_target"
            deficit = 0
            surplus = 0
            recommendation = "Meta atingida! Focar em triagem e qualificação"
            message = (
                f"Excelente! A vaga tem {current_count} candidatos, "
                f"dentro da meta de {target_min}-{target_max}."
            )

        else:
            status = "above_target"
            deficit = 0
            surplus = current_count - target_max
            recommendation = "Considere aplicar filtros mais rigorosos na triagem"
            message = (
                f"A vaga tem {current_count} candidatos, "
                f"{surplus} acima do máximo recomendado de {target_max}."
            )

        progress_percentage = min(100, int((current_count / target_min) * 100))

        suggested_actions: list[dict[str, str]] = []
        if status == "below_target":
            suggested_actions = [
                {"id": "expand_search", "label": "Expandir busca", "priority": "high"},
                {"id": "add_sources", "label": "Adicionar fontes", "priority": "medium"},
                {"id": "review_criteria", "label": "Revisar critérios", "priority": "low"},
            ]
        elif status == "on_target":
            suggested_actions = [
                {"id": "start_screening", "label": "Iniciar triagem", "priority": "high"},
                {"id": "schedule_interviews", "label": "Agendar entrevistas", "priority": "medium"},
            ]
        else:
            suggested_actions = [
                {"id": "apply_filters", "label": "Aplicar filtros", "priority": "high"},
                {"id": "rank_candidates", "label": "Ranquear candidatos", "priority": "medium"},
                {"id": "archive_low_score", "label": "Arquivar baixo score", "priority": "low"},
            ]

        return {
            "status": status,
            "vacancy_id": vacancy_id,
            "current_count": current_count,
            "target_range": [target_min, target_max],
            "deficit": deficit,
            "surplus": surplus,
            "progress_percentage": progress_percentage,
            "recommendation": recommendation,
            "message": message,
            "suggested_actions": suggested_actions,
        }

    # ------------------------------------------------------------------
    # Calibration pattern analysis
    # ------------------------------------------------------------------

    def _analyze_calibration_patterns(
        self, feedbacks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Extract skill/company/experience patterns from like/dislike feedbacks."""
        if not feedbacks:
            return {}

        liked = [f for f in feedbacks if f["feedback"] == "like"]
        disliked = [f for f in feedbacks if f["feedback"] == "dislike"]

        patterns: dict[str, Any] = {
            "preferred_skills": [],
            "avoided_skills": [],
            "preferred_companies": [],
            "avoided_companies": [],
            "experience_range": None,
            "seniority_preference": None,
            "location_preference": None,
        }

        liked_skills: list[str] = []
        disliked_skills: list[str] = []
        liked_companies: list[str] = []
        liked_experience: list[float] = []

        for f in liked:
            snapshot = f.get("candidate_snapshot", {}) or {}
            skills = snapshot.get("skills", [])
            if isinstance(skills, list):
                liked_skills.extend(skills[:5])
            company = snapshot.get("current_company")
            if company:
                liked_companies.append(company)
            exp = snapshot.get("total_experience_years")
            if exp is not None:
                liked_experience.append(float(exp))

        for f in disliked:
            snapshot = f.get("candidate_snapshot", {}) or {}
            skills = snapshot.get("skills", [])
            if isinstance(skills, list):
                disliked_skills.extend(skills[:5])

        if liked_skills:
            patterns["preferred_skills"] = [s for s, _ in Counter(liked_skills).most_common(5)]

        if disliked_skills:
            patterns["avoided_skills"] = [s for s, _ in Counter(disliked_skills).most_common(3)]

        if liked_companies:
            patterns["preferred_companies"] = list(set(liked_companies))[:3]

        if liked_experience:
            patterns["experience_range"] = {
                "min": min(liked_experience),
                "max": max(liked_experience),
                "average": sum(liked_experience) / len(liked_experience),
            }

        return patterns

    async def analyze_calibration_patterns_for_session(
        self,
        session_id: str,
        feedbacks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyse calibration feedbacks and return patterns + confidence + message.

        Returns:
            {
                "patterns": {...},
                "confidence": float,
                "confirmation_message": str,
                "ready_to_source": True
            }
        """
        patterns = self._analyze_calibration_patterns(feedbacks)

        likes = sum(1 for f in feedbacks if f.get("feedback") == "like")
        dislikes = sum(1 for f in feedbacks if f.get("feedback") == "dislike")
        total = len(feedbacks)

        base_confidence = min(0.9, 0.3 + (total * 0.12))
        diversity_bonus = 0.1 if likes >= 2 and dislikes >= 2 else 0
        confidence = min(0.95, base_confidence + diversity_bonus)

        preferred_skills = patterns.get("preferred_skills", [])
        exp_range = patterns.get("experience_range") or {}
        avg_exp = exp_range.get("average", 0)

        message_parts = ["Entendi seu perfil ideal!"]

        if preferred_skills:
            message_parts.append(f"Você valoriza candidatos com: {', '.join(preferred_skills[:3])}.")

        if avg_exp > 0:
            if avg_exp >= 7:
                message_parts.append("Perfil sênior com bastante experiência é prioridade.")
            elif avg_exp >= 4:
                message_parts.append("Experiência plena a sênior é ideal para você.")
            else:
                message_parts.append("Perfis mais júnior também são bem-vindos.")

        avoided_skills = patterns.get("avoided_skills", [])
        if avoided_skills:
            message_parts.append(f"Vou evitar perfis focados em: {', '.join(avoided_skills[:2])}.")

        message_parts.append("\nAgora posso iniciar o sourcing automático com esse perfil!")

        patterns["session_id"] = session_id
        patterns["likes_count"] = likes
        patterns["dislikes_count"] = dislikes
        patterns["total_feedbacks"] = total
        patterns["calibrated_at"] = datetime.now().isoformat()

        return {
            "patterns": patterns,
            "confidence": round(confidence, 2),
            "confirmation_message": " ".join(message_parts),
            "ready_to_source": True,
        }


candidate_goal_service = CandidateGoalService()
