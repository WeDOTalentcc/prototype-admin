"""
PredictionActionBridge - Connects predictions to actionable suggestions.

Maps OutcomePredictor results into ProactiveActions:
- High success probability → suggest advancing candidate
- Dropout risk → suggest preventive action (contact, schedule interview)
- Time-to-fill risk → suggest sourcing expansion
- Salary mismatch → suggest adjustment
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


class PredictionActionBridge:
    """
    Bridge between OutcomePredictor/PredictiveAnalytics and actionable ProactiveActions.
    Converts prediction results into suggestions the recruiter can act on.
    """

    THRESHOLDS = {
        "high_success_score": 0.8,
        "dropout_risk_score": 0.7,
        "time_to_fill_risk_percent": 120,
        "salary_mismatch_percent": 20,
    }

    def __init__(self):
        self._outcome_predictor = None
        self._autonomous_service = None

    def _get_outcome_predictor(self):
        if self._outcome_predictor is None:
            try:
                from app.services.ml.outcome_predictor import OutcomePredictor
                self._outcome_predictor = OutcomePredictor()
            except Exception as e:
                logger.warning(f"Could not load OutcomePredictor: {e}")
        return self._outcome_predictor

    def _get_autonomous_service(self):
        if self._autonomous_service is None:
            try:
                from app.domains.automation.services.autonomous_agent_service import AutonomousAgentService
                self._autonomous_service = AutonomousAgentService()
            except Exception as e:
                logger.warning(f"Could not load AutonomousAgentService: {e}")
        return self._autonomous_service

    async def analyze_and_suggest(
        self,
        db,
        company_id: str,
        job_data: dict[str, Any],
        candidate_data: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Run predictions and generate actionable suggestions.
        Returns list of suggestion dicts (not yet persisted).
        """
        suggestions = []
        predictor = self._get_outcome_predictor()
        if not predictor:
            return suggestions

        try:
            ttf = await predictor.predict_time_to_fill(db, job_data, company_id)
            if ttf.predicted_days > 60 and ttf.confidence >= 0.5:
                suggestions.append({
                    "type": "time_to_fill_risk",
                    "title": f"Risco de Tempo: vaga pode levar {ttf.predicted_days} dias",
                    "description": (
                        f"A previsão indica {ttf.predicted_days} dias para preencher esta vaga "
                        f"({ttf.comparison_to_market}). Considere ampliar sourcing ou revisar requisitos."
                    ),
                    "severity": "warning",
                    "confidence": ttf.confidence,
                    "suggested_action": {
                        "handler": "expand_sourcing",
                        "params": {"vacancy_id": job_data.get("id")},
                    },
                    "action_label": "Ampliar Sourcing",
                    "data": ttf.to_dict(),
                })
        except Exception as e:
            logger.error(f"Error in time-to-fill prediction: {e}")

        try:
            insights = await predictor.get_hiring_insights(db, company_id, role=job_data.get("role"))
            for rec in insights.get("recommendations", []):
                suggestions.append({
                    "type": f"insight_{rec['type']}",
                    "title": f"Insight: {rec['message'][:60]}",
                    "description": rec["message"],
                    "severity": "info" if rec["type"] == "optimization" else "warning",
                    "confidence": insights.get("confidence", 0.5),
                    "suggested_action": {
                        "handler": "review_criteria",
                        "params": {"company_id": company_id},
                    },
                    "action_label": "Revisar Critérios",
                    "data": {"insight": rec},
                })
        except Exception as e:
            logger.error(f"Error getting hiring insights: {e}")

        if candidate_data:
            try:
                wsi_score = candidate_data.get("wsi_score", 0)
                if wsi_score >= self.THRESHOLDS["high_success_score"] * 100:
                    suggestions.append({
                        "type": "high_success_candidate",
                        "title": f"Candidato promissor: score WSI {wsi_score}",
                        "description": (
                            f"{candidate_data.get('name', 'Candidato')} tem score WSI de {wsi_score}, "
                            f"indicando alta compatibilidade. Recomenda-se avançar para entrevista."
                        ),
                        "severity": "info",
                        "confidence": 0.85,
                        "suggested_action": {
                            "handler": "advance_candidate",
                            "params": {
                                "candidate_id": candidate_data.get("id"),
                                "vacancy_id": job_data.get("id"),
                            },
                        },
                        "action_label": "Avançar para Entrevista",
                        "data": {"wsi_score": wsi_score},
                    })
            except Exception as e:
                logger.error(f"Error analyzing candidate success: {e}")

        return suggestions

    async def create_proactive_actions(
        self,
        company_id: str,
        suggestions: list[dict[str, Any]],
        vacancy_id: str | None = None,
        candidate_id: str | None = None,
    ) -> list[str]:
        """
        Persist suggestions as ProactiveActions via AutonomousAgentService.
        Returns list of created action IDs.
        """
        service = self._get_autonomous_service()
        if not service:
            return []

        created_ids = []
        for suggestion in suggestions:
            try:
                action = await service.create_proactive_action(
                    company_id=company_id,
                    action_type="prediction_suggestion",
                    title=suggestion["title"],
                    description=suggestion["description"],
                    suggested_action=suggestion.get("suggested_action", {}),
                    priority="high" if suggestion.get("severity") == "urgent" else "normal",
                    related_job_id=vacancy_id,
                    related_candidate_id=candidate_id,
                    trigger_reason=f"prediction:{suggestion['type']}",
                    auto_executable=False,
                    expires_in_hours=48,
                )
                created_ids.append(str(action.id))
            except Exception as e:
                logger.error(f"Error creating proactive action: {e}")

        logger.info(f"PredictionActionBridge created {len(created_ids)} proactive actions for company {company_id}")
        return created_ids


prediction_action_bridge = PredictionActionBridge()
