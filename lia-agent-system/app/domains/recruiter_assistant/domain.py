"""Recruiter Assistant Domain - Personal assistant for recruiters."""
from typing import Dict, Any, Optional, List
import re
import logging

from app.domains.base import DomainPrompt, DomainContext, DomainAction, IntentResult, DomainResponse
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: Dict[str, str] = {
    "briefing diário": "daily_briefing",
    "briefing do dia": "daily_briefing",
    "daily briefing": "daily_briefing",
    "bom dia lia": "daily_briefing",
    "resumo matinal": "daily_briefing",
    "como está meu dia": "daily_briefing",

    "resumo do dia": "end_of_day_summary",
    "resumo final": "end_of_day_summary",
    "end of day": "end_of_day_summary",
    "encerrar dia": "end_of_day_summary",
    "fim do dia": "end_of_day_summary",

    "pergunta rápida": "quick_question",
    "dúvida rápida": "quick_question",
    "quick question": "quick_question",
    "me ajuda com": "quick_question",

    "planejar dia": "plan_day",
    "planejar meu dia": "plan_day",
    "plan day": "plan_day",
    "organizar agenda": "plan_day",
    "organizar minha agenda": "plan_day",

    "saúde do pipeline": "pipeline_health",
    "saúde pipeline": "pipeline_health",
    "pipeline health": "pipeline_health",
    "como está o pipeline": "pipeline_health",
    "status do pipeline": "pipeline_health",

    "candidatos parados": "stale_candidates",
    "candidatos estão parados": "stale_candidates",
    "candidatos inativos": "stale_candidates",
    "stale candidates": "stale_candidates",
    "candidatos sem movimento": "stale_candidates",
    "candidatos esquecidos": "stale_candidates",

    "mover candidato": "move_candidate",
    "mover para etapa": "move_candidate",
    "move candidate": "move_candidate",
    "mudar etapa": "move_candidate",
    "trocar etapa": "move_candidate",
    "avançar candidato": "move_candidate",

    "sugerir ação": "suggest_action",
    "próxima ação": "suggest_action",
    "suggest action": "suggest_action",
    "o que fazer com": "suggest_action",
    "recomendação de ação": "suggest_action",

    "buscar contexto": "search_context",
    "histórico conversa": "search_context",
    "histórico de conversa": "search_context",
    "search context": "search_context",
    "buscar no histórico": "search_context",

    "salvar memória": "save_memory",
    "lembrar disso": "save_memory",
    "save memory": "save_memory",
    "guardar informação": "save_memory",
    "anotar": "save_memory",

    "recuperar memória": "recall_memory",
    "o que eu disse sobre": "recall_memory",
    "recall memory": "recall_memory",
    "lembrar de": "recall_memory",
    "buscar memória": "recall_memory",

    "resumo da conversa": "conversation_summary",
    "resumir conversa": "conversation_summary",
    "conversation summary": "conversation_summary",
    "resumo do chat": "conversation_summary",

    "análise do kanban": "kanban_analysis",
    "análise kanban": "kanban_analysis",
    "kanban analysis": "kanban_analysis",
    "analisar kanban": "kanban_analysis",
    "visão do kanban": "kanban_analysis",

    "ranking": "kanban_analysis",
    "rankear": "kanban_analysis",
    "rankear candidatos": "kanban_analysis",
    "ranking de candidatos": "kanban_analysis",
    "melhores candidatos": "kanban_analysis",
    "quem são os melhores": "kanban_analysis",
    "top candidatos": "kanban_analysis",
    "ordenar candidatos": "kanban_analysis",
    "classificar candidatos": "kanban_analysis",
    "performance do funil": "kanban_analysis",
    "como está o funil": "kanban_analysis",
    "métricas do funil": "kanban_analysis",
    "gargalos": "kanban_analysis",
    "gargalo no processo": "kanban_analysis",
    "taxa de conversão": "kanban_analysis",
    "tempo médio": "kanban_analysis",
    "candidatos parados": "kanban_analysis",

    "calibrar perfil": "calibrate_profile",
    "calibrar candidato ideal": "calibrate_profile",
    "calibrate profile": "calibrate_profile",
    "perfil ideal": "calibrate_profile",
    "ajustar perfil": "calibrate_profile",

    "enviar notificação": "send_notification",
    "notificar": "send_notification",
    "send notification": "send_notification",
    "alerta para mim": "send_notification",

    "acompanhar metas": "track_goals",
    "minhas metas": "track_goals",
    "track goals": "track_goals",
    "progresso das metas": "track_goals",
    "metas de recrutamento": "track_goals",

    "gerar insights": "generate_insights",
    "insights de busca": "generate_insights",
    "generate insights": "generate_insights",
    "análise proativa": "generate_insights",
    "sugestões proativas": "generate_insights",

    "comparar candidatos": "compare_candidates",
    "compare candidates": "compare_candidates",
    "comparação de candidatos": "compare_candidates",
    "candidato vs candidato": "compare_candidates",

    "recomendar etapa": "stage_recommendation",
    "qual próxima etapa": "stage_recommendation",
    "stage recommendation": "stage_recommendation",
    "sugerir etapa": "stage_recommendation",
    "recomendação de etapa": "stage_recommendation",

    "ajuda": "help_command",
    "help": "help_command",
    "comandos disponíveis": "help_command",
    "o que você pode fazer": "help_command",
    "funcionalidades": "help_command",
}


@register_domain
class RecruiterAssistantDomain(ComplianceDomainPrompt):

    _compliance_config = {'high_impact': False}
    domain_id = "recruiter_assistant"
    domain_name = "Recruiter Assistant"

    def __init__(self):
        from app.domains.recruiter_assistant.actions import RECRUITER_ASSISTANT_ACTIONS
        self._actions = RECRUITER_ASSISTANT_ACTIONS

    def get_allowed_actions(self) -> List[DomainAction]:
        from app.domains.recruiter_assistant.actions import RECRUITER_ASSISTANT_ACTIONS
        return RECRUITER_ASSISTANT_ACTIONS

    def get_system_prompt(self) -> str:
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower().strip()
        best_action = "quick_question"
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
            intent_id=f"recruiter_assistant.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )

    _ACTION_TOOL_MAP: Dict[str, str] = {
        "pipeline_health": "assistant_pipeline_health",
        "stale_candidates": "assistant_stale_candidates",
        "move_candidate": "assistant_move_candidate",
        "search_context": "assistant_search_context",
        "save_memory": "assistant_save_memory",
        "recall_memory": "assistant_recall_memory",
        "conversation_summary": "assistant_conversation_summary",
        "kanban_analysis": "assistant_kanban_analysis",
        "send_notification": "assistant_send_notification",
        "track_goals": "assistant_track_goals",
    }

    async def execute_action(self, action_id: str, params: Dict[str, Any], context: DomainContext) -> DomainResponse:
        action = None
        for a in self.get_allowed_actions():
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de assistente do recrutador."
            )

        logger.info(f"Routing recruiter_assistant action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.recruiter_assistant.tools import RECRUITER_ASSISTANT_TOOLS, execute_recruiter_assistant_tool

        tool_ids = {t["tool_id"] for t in RECRUITER_ASSISTANT_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_recruiter_assistant_tool(mapped_tool, params, context)
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        return DomainResponse.success_response(
            message=f"Ação '{action.name}' encaminhada para o agente assistente.",
            data={"action_id": action_id, "params": params, "delegate_to_agent": True},
            domain_id=self.domain_id,
            action_id=action_id,
        )
