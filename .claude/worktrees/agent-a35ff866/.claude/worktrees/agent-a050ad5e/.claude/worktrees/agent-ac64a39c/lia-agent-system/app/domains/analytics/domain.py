"""Analytics & Reporting Domain - Data analytics, KPIs, and predictive insights."""
from typing import Dict, Any, Optional, List
import re
import logging

from app.domains.base import DomainPrompt, DomainContext, DomainAction, IntentResult, DomainResponse
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: Dict[str, str] = {
    "relatório kpi": "generate_kpi_report",
    "relatório de kpi": "generate_kpi_report",
    "kpi report": "generate_kpi_report",
    "gerar kpi": "generate_kpi_report",
    "indicadores kpi": "generate_kpi_report",

    "funil conversão": "analyze_funnel",
    "funil de conversão": "analyze_funnel",
    "analyze funnel": "analyze_funnel",
    "métricas funil": "analyze_funnel",
    "métricas do funil": "analyze_funnel",

    "saúde vaga": "job_health_check",
    "saúde da vaga": "job_health_check",
    "job health": "job_health_check",
    "health check": "job_health_check",
    "verificar saúde": "job_health_check",

    "detectar anomalia": "detect_anomalies",
    "anomalia": "detect_anomalies",
    "detect anomalies": "detect_anomalies",
    "alerta anomalia": "detect_anomalies",

    "comparar período": "compare_periods",
    "comparar períodos": "compare_periods",
    "compare periods": "compare_periods",
    "comparação mensal": "compare_periods",
    "comparação de períodos": "compare_periods",

    "previsão": "forecast",
    "previsão de métricas": "forecast",
    "forecast": "forecast",
    "projeção": "forecast",
    "tendência": "forecast",

    "sugerir estratégia": "suggest_strategy",
    "estratégia recrutamento": "suggest_strategy",
    "estratégia de recrutamento": "suggest_strategy",
    "sugestão estratégica": "suggest_strategy",
    "recomendação": "suggest_strategy",

    "pergunta dados": "answer_data_question",
    "pergunta sobre dados": "answer_data_question",
    "data question": "answer_data_question",
    "consulta dados": "answer_data_question",
    "consulta de dados": "answer_data_question",

    "insights vaga": "get_job_insights",
    "insights da vaga": "get_job_insights",
    "job insights": "get_job_insights",
    "benchmark salarial": "get_job_insights",
    "benchmark": "get_job_insights",
    "salário médio": "get_job_insights",

    "relatório vaga": "generate_job_report",
    "relatório da vaga": "generate_job_report",
    "job report": "generate_job_report",
    "gerar relatório": "generate_job_report",

    "relatório candidato": "generate_candidate_report",
    "relatório de candidato": "generate_candidate_report",
    "relatório comparativo": "generate_candidate_report",
    "comparar candidatos": "generate_candidate_report",

    "analytics busca": "get_search_analytics",
    "analytics de busca": "get_search_analytics",
    "search analytics": "get_search_analytics",
    "desempenho busca": "get_search_analytics",
    "desempenho de busca": "get_search_analytics",

    "analytics wizard": "get_wizard_analytics",
    "analytics do wizard": "get_wizard_analytics",
    "wizard analytics": "get_wizard_analytics",
    "uso do wizard": "get_wizard_analytics",

    "probabilidade contratação": "predict_hiring_probability",
    "probabilidade de contratação": "predict_hiring_probability",
    "hiring probability": "predict_hiring_probability",
    "chance de contratar": "predict_hiring_probability",

    "tempo preenchimento": "predict_time_to_fill",
    "tempo de preenchimento": "predict_time_to_fill",
    "time to fill": "predict_time_to_fill",
    "prazo da vaga": "predict_time_to_fill",

    "risco desistência": "predict_dropout_risk",
    "risco de desistência": "predict_dropout_risk",
    "dropout risk": "predict_dropout_risk",
    "candidato desistir": "predict_dropout_risk",

    "dashboard": "get_dashboard_data",
    "dados dashboard": "get_dashboard_data",
    "dados do dashboard": "get_dashboard_data",
    "painel indicadores": "get_dashboard_data",
    "painel de indicadores": "get_dashboard_data",

    "monitoramento agentes": "get_agent_monitoring",
    "monitoramento de agentes": "get_agent_monitoring",
    "agent monitoring": "get_agent_monitoring",
    "performance agentes": "get_agent_monitoring",
    "performance dos agentes": "get_agent_monitoring",
}


@register_domain
class AnalyticsDomain(DomainPrompt):
    domain_id = "analytics"
    domain_name = "Analytics & Reporting"

    def __init__(self):
        from app.domains.analytics.actions import ANALYTICS_ACTIONS
        self._actions = ANALYTICS_ACTIONS

    def get_allowed_actions(self) -> List[DomainAction]:
        from app.domains.analytics.actions import ANALYTICS_ACTIONS
        return ANALYTICS_ACTIONS

    def get_system_prompt(self) -> str:
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower().strip()
        best_action = "get_dashboard_data"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"analytics.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )

    _ACTION_TOOL_MAP: Dict[str, str] = {
        "generate_kpi_report": "analytics_generate_kpi",
        "analyze_funnel": "analytics_analyze_funnel",
        "job_health_check": "analytics_job_health",
        "detect_anomalies": "analytics_detect_anomalies",
        "get_job_insights": "analytics_get_insights",
        "generate_job_report": "analytics_generate_report",
        "generate_candidate_report": "analytics_generate_report",
        "get_search_analytics": "analytics_search_analytics",
        "predict_hiring_probability": "analytics_predict",
        "predict_time_to_fill": "analytics_predict",
        "predict_dropout_risk": "analytics_predict",
        "get_dashboard_data": "analytics_dashboard",
        "get_agent_monitoring": "analytics_monitoring",
    }

    async def execute_action(self, action_id: str, params: Dict[str, Any], context: DomainContext) -> DomainResponse:
        action = None
        for a in self.get_allowed_actions():
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de analytics."
            )

        logger.info(f"Routing analytics action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.analytics.tools import ANALYTICS_TOOLS, execute_analytics_tool

        tool_ids = {t["tool_id"] for t in ANALYTICS_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_analytics_tool(mapped_tool, params, context)
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        return DomainResponse.success_response(
            message=f"Ação '{action.name}' encaminhada para o agente de analytics.",
            data={"action_id": action_id, "params": params, "delegate_to_agent": True},
            domain_id=self.domain_id,
            action_id=action_id,
        )
