from pathlib import Path
"""ATS Integration Domain - Bidirectional sync with external ATS platforms."""
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
_matcher = KeywordIntentMatcher.from_keyword_map(_KEYWORD_ACTION_MAP, domain_id="ats_integration")


@register_domain
class ATSIntegrationDomain(ComplianceDomainPrompt):

    _compliance_config = {'high_impact': False}
    domain_id = "ats_integration"
    domain_name = "ATS Integration"

    def __init__(self):
        from app.domains.ats_integration.actions import ATS_INTEGRATION_ACTIONS
        self._actions = ATS_INTEGRATION_ACTIONS

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.ats_integration.actions import ATS_INTEGRATION_ACTIONS
        return ATS_INTEGRATION_ACTIONS

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        # LIA-I07: Check if query is an info request (e.g., "como funciona X?")
        if _matcher.is_info_query(query):
            try:
                match = _matcher.match(query, default_action="check_sync_status")
                return IntentResult(
                    intent_id=f"ats_integration.{match.action}",
                    action_id=match.action,
                    confidence=match.confidence,
                    extracted_params={"raw_query": query, "is_info_query": True},
                    reasoning=f"[LIA-I07] Info query routed via is_info_query (action='{match.action}')",
                )
            except Exception:
                pass  # Fall through to normal logic

        # LIA-I03: Use shared KeywordIntentMatcher (falls back to loop on error)
        try:
            match = _matcher.match(query, default_action="check_sync_status")
            return IntentResult(
                intent_id=f"ats_integration.{match.action}",
                action_id=match.action,
                confidence=match.confidence,
                extracted_params={"raw_query": query},
                reasoning=f"KeywordIntentMatcher matched action '{match.action}'",
            )
        except Exception as e:
            logger.debug("[LIA-I03] Matcher failed, using fallback: %s", e)
            query_lower = query.lower().strip()
            best_action = "check_sync_status"
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
                intent_id=f"ats_integration.{best_action}",
                action_id=best_action,
                confidence=best_confidence,
                extracted_params={"raw_query": query},
                reasoning=f"Keyword heuristic matched action '{best_action}'",
            )

    _ACTION_TOOL_MAP: dict[str, str] = {
        "sync_candidate": "ats_sync_candidate",
        "sync_job": "ats_sync_job",
        "pull_candidates": "ats_pull_candidates",
        "pull_jobs": "ats_pull_jobs",
        "check_sync_status": "ats_check_status",
        "list_connections": "ats_list_connections",
        "test_connection": "ats_test_connection",
        "view_sync_log": "ats_view_sync_log",
        "update_status_ats": "ats_update_status",
        "send_score_ats": "ats_send_score",
    }

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = None
        for a in self.get_allowed_actions():
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de integração ATS."
            )

        logger.info(f"Routing ats_integration action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.ats_integration.tools import ATS_INTEGRATION_TOOLS, execute_ats_integration_tool

        tool_ids = {t["tool_id"] for t in ATS_INTEGRATION_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_ats_integration_tool(mapped_tool, params, context)
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        return DomainResponse.success_response(
            message=f"Ação '{action.name}' encaminhada para o agente de integração ATS.",
            data={"action_id": action_id, "params": params, "delegate_to_agent": True},
            domain_id=self.domain_id,
            action_id=action_id,
        )
