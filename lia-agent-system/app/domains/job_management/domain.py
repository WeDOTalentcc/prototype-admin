from __future__ import annotations
from pathlib import Path

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
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="job_management")



@register_domain
class JobManagementDomain(ComplianceDomainPrompt):
    """Domínio de Job Management & Wizard da LIA."""

    _compliance_config = {'high_impact': False}

    domain_id = "job_management"
    domain_name = "Job Management & Wizard"
    description = "Criação, gestão e otimização de vagas de emprego"

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.job_management.actions import JOB_MANAGEMENT_ACTIONS
        return JOB_MANAGEMENT_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="create_job")
                return IntentResult(
                    intent_id=f"job_management.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="create_job")
            if match.intent_type.value == "info":
                logger.info("[LIA-I03] Info query detected for job_management: %s", query[:60])
            return IntentResult(
                intent_id=f"job_management.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}' (kw='{match.matched_keyword}')",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
        query_lower = query.lower()
        best_action = "create_job"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"job_management.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )


    async def execute_action(
        self, action_id: str, params: dict[str, Any], context: DomainContext
    ) -> DomainResponse:
        action = self.get_action_by_id(action_id)
        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de job management."
            )

        logger.info(f"Routing job management action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.job_management.tools import JOB_MANAGEMENT_TOOLS, execute_job_management_tool

        tool_ids = {t["tool_id"] for t in JOB_MANAGEMENT_TOOLS}

        _ACTION_TOOL_MAP: dict[str, str] = {
            "create_job": "create_job_vacancy",
            "update_job": "update_job_vacancy",
            "close_job": "close_job_vacancy",
            "pause_job": "pause_job_vacancy",
            "duplicate_job": "duplicate_job_vacancy",
            "clone_job": "duplicate_job_vacancy",
            "generate_jd": "generate_job_description",
            "enrich_jd": "enrich_job_description",
            "import_jd": "import_job_description",
            "search_templates": "search_job_templates",
            "create_from_template": "search_job_templates",
            "apply_template": "search_job_templates",
            "health_check": "get_job_health",
            "advance_wizard_step": "advance_wizard",
            "get_wizard_step_data": "get_wizard_step",
            "guided_wizard": "get_wizard_step",
            "job_analytics": "get_job_analytics",
        }

        mapped_tool = _ACTION_TOOL_MAP.get(action_id)
        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_job_management_tool(
                tool_id=mapped_tool,
                params=params,
                tenant_id=context.tenant_id,
            )
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        from app.shared.delegation_fallback import DelegationFallbackHandler
        fallback_data = DelegationFallbackHandler.handle(
            action_id=action_id,
            domain_id=self.domain_id,
            params=params,
            context={"user_id": context.user_id, "tenant_id": context.tenant_id},
        )
        return DomainResponse.success_response(
            message=fallback_data["message"],
            data=fallback_data,
            domain_id=self.domain_id,
            action_id=action_id,
        )
