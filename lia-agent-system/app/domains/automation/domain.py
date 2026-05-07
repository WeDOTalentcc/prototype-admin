from pathlib import Path
"""Automation & Tasks Domain - Task management, automations and proactive alerts."""
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

# LIA-I03: Shared KeywordIntentMatcher singleton
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="automation")


@register_domain
class AutomationDomain(ComplianceDomainPrompt):

    _compliance_config = {'high_impact': False}
    domain_id = "automation"
    domain_name = "Automation & Tasks"

    def __init__(self):
        from app.domains.automation.actions import AUTOMATION_ACTIONS
        self._actions = AUTOMATION_ACTIONS

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.automation.actions import AUTOMATION_ACTIONS
        return AUTOMATION_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="list_tasks")
                return IntentResult(
                    intent_id=f"automation.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="list_tasks")
            return IntentResult(
                intent_id=f"automation.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}'",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            query_lower = query.lower().strip()
            best_action = "list_tasks"
            best_confidence = 0.3
            best_keyword = ""
            for keyword, action_id in _KEYWORD_ACTION_MAP.items():
                if keyword in query_lower:
                    confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                    if confidence > best_confidence or (confidence == best_confidence and len(keyword) > len(best_keyword)):
                        best_action = action_id
                        best_confidence = confidence
                        best_keyword = keyword
            return IntentResult(
                intent_id=f"automation.{best_action}",
                action_id=best_action,
                confidence=best_confidence,
                extracted_params={"raw_query": query},
                reasoning=f"Keyword heuristic matched action '{best_action}'",
            )

    _ACTION_TOOL_MAP: dict[str, str] = {
        "create_task": "automation_create_task",
        "list_tasks": "automation_list_tasks",
        "complete_task": "automation_complete_task",
        "cancel_task": "automation_cancel_task",
        "create_automation": "automation_create_rule",
        "list_automations": "automation_list_rules",
        "enable_automation": "automation_enable_rule",
        "disable_automation": "automation_disable_rule",
        "trigger_automation": "automation_trigger",
        "view_automation_log": "automation_view_log",
    }

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = None
        for a in self.get_allowed_actions():
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de automação & tarefas."
            )

        logger.info(f"Routing automation action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.automation.tools import AUTOMATION_TOOLS, execute_automation_tool

        tool_ids = {t["tool_id"] for t in AUTOMATION_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_automation_tool(mapped_tool, params, context)
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        return DomainResponse.success_response(
            message=f"Ação '{action.name}' encaminhada para o agente de automação.",
            data={"action_id": action_id, "params": params, "delegate_to_agent": True},
            domain_id=self.domain_id,
            action_id=action_id,
        )
