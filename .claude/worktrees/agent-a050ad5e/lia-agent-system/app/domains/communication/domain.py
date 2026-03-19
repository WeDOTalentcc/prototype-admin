"""Communication Domain - Multi-channel communication management."""
from typing import Dict, Any, Optional, List
import re
import logging

from app.domains.base import DomainPrompt, DomainContext, DomainAction, IntentResult, DomainResponse
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: Dict[str, str] = {
    "enviar email": "send_email",
    "send email": "send_email",
    "disparar email": "send_email",
    "email candidato": "send_email",
    "email em massa": "send_bulk_email",
    "bulk email": "send_bulk_email",
    "envio massa": "send_bulk_email",
    "envio em lote": "send_bulk_email",
    "enviar parecer": "send_candidate_report",
    "parecer gestor": "send_candidate_report",
    "relatório candidato": "send_candidate_report",
    "report gestor": "send_candidate_report",
    "relatório progresso": "send_progress_report",
    "relatório de progresso": "send_progress_report",
    "progress report": "send_progress_report",
    "andamento da vaga": "send_progress_report",
    "progresso da vaga": "send_progress_report",
    "relatório kpi": "send_kpi_report",
    "relatório de kpi": "send_kpi_report",
    "kpi report": "send_kpi_report",
    "relatório consolidado": "send_kpi_report",
    "indicadores": "send_kpi_report",
    "feedback candidato": "send_feedback",
    "enviar feedback": "send_feedback",
    "devolutiva candidato": "send_feedback",
    "retorno candidato": "send_feedback",
    "criar template": "create_template",
    "template email": "create_template",
    "novo template": "create_template",
    "editar template": "edit_template",
    "atualizar template": "edit_template",
    "listar template": "list_templates",
    "templates disponíveis": "list_templates",
    "visualizar template": "preview_template",
    "preview template": "preview_template",
    "preview do template": "preview_template",
    "notificar stakeholder": "notify_stakeholders",
    "notificação": "notify_stakeholders",
    "avisar gestor": "notify_stakeholders",
    "alertar equipe": "notify_stakeholders",
    "enviar whatsapp": "send_whatsapp",
    "whatsapp candidato": "send_whatsapp",
    "mensagem whatsapp": "send_whatsapp",
    "whatsapp": "send_whatsapp",
    "enviar teams": "send_teams_message",
    "mensagem teams": "send_teams_message",
    "teams": "send_teams_message",
    "notificar teams": "send_teams_message",
    "enviar sms": "send_sms",
    "sms candidato": "send_sms",
    "sms": "send_sms",
    "histórico comunicação": "get_communication_history",
    "histórico de comunicação": "get_communication_history",
    "communication history": "get_communication_history",
    "histórico email": "get_communication_history",
    "histórico mensagem": "get_communication_history",
    "convite triagem": "send_screening_invite",
    "convite de triagem": "send_screening_invite",
    "convidar triagem": "send_screening_invite",
    "screening invite": "send_screening_invite",
    "convite entrevista": "send_interview_invite",
    "convite de entrevista": "send_interview_invite",
    "convidar entrevista": "send_interview_invite",
    "interview invite": "send_interview_invite",
    "preferência comunicação": "update_preferences",
    "preferências de comunicação": "update_preferences",
    "opt-out": "update_preferences",
    "preferências candidato": "update_preferences",
    "canal preferido": "update_preferences",
    "webhook": "manage_webhook",
    "configurar webhook": "manage_webhook",
    "registrar webhook": "manage_webhook",
    "solicitação dados": "handle_data_request",
    "solicitação de dados": "handle_data_request",
    "data request": "handle_data_request",
    "lgpd solicitação": "handle_data_request",
    "lgpd": "handle_data_request",
}


@register_domain
class CommunicationDomain(DomainPrompt):
    domain_id = "communication"
    domain_name = "Communication & Messaging"

    def __init__(self):
        from app.domains.communication.actions import COMMUNICATION_ACTIONS
        self._actions = COMMUNICATION_ACTIONS

    def get_allowed_actions(self) -> List[DomainAction]:
        from app.domains.communication.actions import COMMUNICATION_ACTIONS
        return COMMUNICATION_ACTIONS

    def get_system_prompt(self) -> str:
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower().strip()
        best_action = "send_email"
        best_confidence = 0.3

        for keyword, action_id in _KEYWORD_ACTION_MAP.items():
            if keyword in query_lower:
                confidence = min(0.95, 0.6 + len(keyword) * 0.02)
                if confidence > best_confidence:
                    best_action = action_id
                    best_confidence = confidence

        return IntentResult(
            intent_id=f"communication.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )

    _ACTION_TOOL_MAP: Dict[str, str] = {
        "send_email": "communication_send_email",
        "send_bulk_email": "communication_send_bulk",
        "send_whatsapp": "communication_send_whatsapp",
        "send_teams_message": "communication_send_teams",
        "create_template": "communication_create_template",
        "list_templates": "communication_list_templates",
        "preview_template": "communication_preview_template",
        "get_communication_history": "communication_get_history",
        "manage_webhook": "communication_manage_webhook",
        "handle_data_request": "communication_data_request",
    }

    async def execute_action(self, action_id: str, params: Dict[str, Any], context: DomainContext) -> DomainResponse:
        action = None
        for a in self.get_allowed_actions():
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de comunicação."
            )

        logger.info(f"Routing communication action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.communication.tools import COMMUNICATION_TOOLS, execute_communication_tool

        tool_ids = {t["tool_id"] for t in COMMUNICATION_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_communication_tool(mapped_tool, params, context)
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        return DomainResponse.success_response(
            message=f"Ação '{action.name}' encaminhada para o agente de comunicação.",
            data={"action_id": action_id, "params": params, "delegate_to_agent": True},
            domain_id=self.domain_id,
            action_id=action_id,
        )
