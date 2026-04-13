"""ATS Integration Domain - Bidirectional sync with external ATS platforms."""
import logging
from typing import Any

from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

from app.shared.services.keyword_intent_matcher import KeywordIntentMatcher

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: dict[str, str] = {
    "sincronizar candidato": "sync_candidate",
    "sync candidato": "sync_candidate",
    "sync candidate": "sync_candidate",
    "enviar candidato para ats": "sync_candidate",
    "enviar candidato para o ats": "sync_candidate",
    "sincronizar com ats": "sync_candidate",

    "sincronizar vaga": "sync_job",
    "sync vaga": "sync_job",
    "sync job": "sync_job",
    "enviar vaga para ats": "sync_job",
    "enviar vaga para o ats": "sync_job",

    "sincronização em massa": "bulk_sync",
    "sync em massa": "bulk_sync",
    "bulk sync": "bulk_sync",
    "sincronizar tudo": "bulk_sync",
    "sincronizar todos": "bulk_sync",

    "importar candidatos": "pull_candidates",
    "pull candidates": "pull_candidates",
    "puxar candidatos": "pull_candidates",
    "importar candidatos do ats": "pull_candidates",
    "buscar candidatos no ats": "pull_candidates",

    "importar vagas": "pull_jobs",
    "pull jobs": "pull_jobs",
    "puxar vagas": "pull_jobs",
    "importar vagas do ats": "pull_jobs",

    "status sincronização": "check_sync_status",
    "status da sincronização": "check_sync_status",
    "verificar sincronização": "check_sync_status",
    "sync status": "check_sync_status",
    "status do sync": "check_sync_status",

    "configurar ats": "configure_ats",
    "config ats": "configure_ats",
    "setup ats": "configure_ats",
    "conectar ats": "configure_ats",
    "configurar integração ats": "configure_ats",

    "listar conexões": "list_connections",
    "conexões ats": "list_connections",
    "list connections": "list_connections",
    "ver conexões": "list_connections",
    "quais ats conectados": "list_connections",

    "testar conexão": "test_connection",
    "test connection": "test_connection",
    "verificar conexão": "test_connection",
    "conexão ats": "test_connection",
    "testar integração": "test_connection",

    "mapear campos": "map_fields",
    "mapeamento de campos": "map_fields",
    "field mapping": "map_fields",
    "configurar campos": "map_fields",
    "map fields": "map_fields",

    "log sincronização": "view_sync_log",
    "log de sincronização": "view_sync_log",
    "histórico sync": "view_sync_log",
    "sync log": "view_sync_log",
    "auditoria ats": "view_sync_log",
    "auditoria do ats": "view_sync_log",

    "conflito dados": "resolve_conflict",
    "conflito de dados": "resolve_conflict",
    "resolver conflito ats": "resolve_conflict",
    "data conflict": "resolve_conflict",
    "conflito sincronização": "resolve_conflict",
    "conflito de sincronização": "resolve_conflict",

    "atualizar status ats": "update_status_ats",
    "atualizar status no ats": "update_status_ats",
    "update status ats": "update_status_ats",
    "enviar status para ats": "update_status_ats",
    "push status": "update_status_ats",

    "enviar score ats": "send_score_ats",
    "enviar score para ats": "send_score_ats",
    "enviar score para o ats": "send_score_ats",
    "send score ats": "send_score_ats",
    "enviar parecer ats": "send_score_ats",
    "enviar parecer para ats": "send_score_ats",
    "enviar parecer para o ats": "send_score_ats",

    "sincronizar resultado entrevista": "sync_interview_result",
    "sincronizar resultado da entrevista": "sync_interview_result",
    "sync interview result": "sync_interview_result",
    "enviar resultado entrevista ats": "sync_interview_result",

    "ativar webhook": "enable_webhook",
    "enable webhook": "enable_webhook",
    "webhook ats": "enable_webhook",
    "configurar webhook": "enable_webhook",

    "desativar webhook": "disable_webhook",
    "disable webhook": "disable_webhook",
    "remover webhook": "disable_webhook",
    "desabilitar webhook": "disable_webhook",

    "ver mapeamento": "view_field_mapping",
    "ver mapeamento de campos": "view_field_mapping",
    "view field mapping": "view_field_mapping",
    "campos mapeados": "view_field_mapping",
}

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

    def get_system_prompt(self) -> str:
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

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
