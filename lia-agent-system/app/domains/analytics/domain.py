from pathlib import Path
"""Analytics & Reporting Domain - Data analytics, KPIs, and predictive insights."""
import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher
import yaml as _yaml_imp  # Fase 5

logger = logging.getLogger(__name__)

# Fase 5: _KEYWORD_ACTION_MAP loaded from capabilities.yaml (LIA-I05)
_capabilities_yaml_path = Path(__file__).parent / 'config' / 'capabilities.yaml'
_KEYWORD_ACTION_MAP: dict[str, str] = (
    _yaml_imp.safe_load(_capabilities_yaml_path.read_text()).get('intent_keywords', {})
    if _capabilities_yaml_path.exists()
    else {}
)
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="analytics")



@register_domain
class AnalyticsDomain(ComplianceDomainPrompt):

    _compliance_config = {'high_impact': False}
    domain_id = "analytics"
    domain_name = "Analytics & Reporting"

    def __init__(self):
        from app.domains.analytics.actions import ANALYTICS_ACTIONS
        self._actions = ANALYTICS_ACTIONS

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.analytics.actions import ANALYTICS_ACTIONS
        return ANALYTICS_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="get_dashboard_data")
                return IntentResult(
                    intent_id=f"analytics.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="get_dashboard_data")
            if match.intent_type.value == "info":
                logger.info("[LIA-I03] Info query detected for analytics: %s", query[:60])
            return IntentResult(
                intent_id=f"analytics.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}' (kw='{match.matched_keyword}')",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
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


    _ACTION_TOOL_MAP: dict[str, str] = {
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

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
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


# ---------------------------------------------------------------------------
# LIA-C06 - Registro de validador domain-specific para analytics
# ---------------------------------------------------------------------------
try:
    from app.shared.compliance.domain_validators import validate_analytics_metric_claim
    from app.shared.compliance.fact_checker import FactChecker
    FactChecker.register_validator("analytics", validate_analytics_metric_claim)
    logger.debug("analytics domain validator registered")
except Exception as _e:
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "Could not register analytics domain validator: %s", _e
    )
