"""Interview & Scheduling Domain - Interview management and WSI methodology."""
import logging
from typing import Any


from app.domains.base import DomainAction, DomainContext, DomainResponse, IntentResult
from app.domains.compliance_base import ComplianceDomainPrompt
from app.domains.interview_scheduling.agents.interview_graph import interview_graph
from app.domains.registry import register_domain
from app.services.interview_session_store import interview_session_store

# Prefixo separado do WSIInterviewGraph para evitar colisão de chaves no Redis
_SCHEDULING_SESSION_PREFIX = "scheduling:"

# Actions delegadas ao InterviewGraph (LangGraph conversacional)
_GRAPH_ACTIONS = {"schedule_interview"}

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: dict[str, str] = {
    "agendar entrevista": "schedule_interview",
    "marcar entrevista": "schedule_interview",
    "schedule interview": "schedule_interview",
    "agendar reunião": "schedule_interview",

    "reagendar entrevista": "reschedule_interview",
    "reagendar": "reschedule_interview",
    "remarcar entrevista": "reschedule_interview",
    "reschedule": "reschedule_interview",
    "mudar horário entrevista": "reschedule_interview",
    "mudar horário da entrevista": "reschedule_interview",

    "cancelar entrevista": "cancel_interview",
    "cancel interview": "cancel_interview",
    "desmarcar entrevista": "cancel_interview",

    "verificar disponibilidade": "check_availability",
    "checar disponibilidade": "check_availability",
    "check availability": "check_availability",
    "disponibilidade calendário": "check_availability",
    "disponibilidade do calendário": "check_availability",
    "horários disponíveis": "check_availability",
    "horários livres": "check_availability",

    "link agendamento": "generate_self_scheduling_link",
    "link de agendamento": "generate_self_scheduling_link",
    "auto-agendamento": "generate_self_scheduling_link",
    "self scheduling": "generate_self_scheduling_link",
    "link para candidato agendar": "generate_self_scheduling_link",

    "horários comuns": "find_common_slots",
    "slots comuns": "find_common_slots",
    "encontrar horários": "find_common_slots",
    "common slots": "find_common_slots",

    "enviar lembrete": "send_reminder",
    "lembrete entrevista": "send_reminder",
    "lembrete de entrevista": "send_reminder",
    "reminder": "send_reminder",

    "agendar lembretes": "schedule_reminders",
    "programar lembretes": "schedule_reminders",
    "lembretes automáticos": "schedule_reminders",

    "entrevistas hoje": "list_today_interviews",
    "entrevistas de hoje": "list_today_interviews",
    "agenda hoje": "list_today_interviews",
    "agenda de hoje": "list_today_interviews",
    "today interviews": "list_today_interviews",
    "entrevistas do dia": "list_today_interviews",

    "conflito agenda": "resolve_conflict",
    "conflito de agenda": "resolve_conflict",
    "resolver conflito": "resolve_conflict",
    "scheduling conflict": "resolve_conflict",

    "entrevista wsi": "start_wsi_interview",
    "iniciar entrevista wsi": "start_wsi_interview",
    "wsi interview": "start_wsi_interview",
    "entrevista completa": "start_wsi_interview",

    "enviar pergunta": "send_question",
    "fazer pergunta": "send_question",
    "próxima pergunta": "send_question",
    "send question": "send_question",

    "analisar resposta": "analyze_response",
    "avaliar resposta": "analyze_response",
    "analyze response": "analyze_response",
    "análise de resposta": "analyze_response",

    "transcrever áudio": "transcribe_audio",
    "transcrição": "transcribe_audio",
    "transcribe": "transcribe_audio",
    "transcrever entrevista": "transcribe_audio",

    "analisar voz": "analyze_voice",
    "análise de voz": "analyze_voice",
    "análise vocal": "analyze_voice",
    "voice analysis": "analyze_voice",

    "resposta evasiva": "detect_evasive",
    "detectar evasiva": "detect_evasive",
    "candidato evadindo": "detect_evasive",
    "evasive answer": "detect_evasive",

    "pergunta follow-up": "generate_followup",
    "pergunta de follow-up": "generate_followup",
    "follow-up": "generate_followup",
    "gerar follow-up": "generate_followup",
    "aprofundar resposta": "generate_followup",

    "finalizar entrevista": "complete_interview",
    "encerrar entrevista": "complete_interview",
    "complete interview": "complete_interview",
    "concluir entrevista": "complete_interview",
    "resumo da entrevista": "complete_interview",

    "dúvida entrevista": "interview_qa",
    "dúvida sobre entrevista": "interview_qa",
    "pergunta sobre entrevista": "interview_qa",
    "interview qa": "interview_qa",

    "triagem rápida": "start_quick_screening",
    "quick screening": "start_quick_screening",
    "triagem inicial": "start_quick_screening",
    "screening rápido": "start_quick_screening",
    "iniciar triagem": "start_quick_screening",
}


@register_domain
class InterviewSchedulingDomain(ComplianceDomainPrompt):

    _compliance_config = {'high_impact': False}
    domain_id = "interview_scheduling"
    domain_name = "Interview & Scheduling"

    def __init__(self):
        from app.domains.interview_scheduling.actions import INTERVIEW_SCHEDULING_ACTIONS
        self._actions = INTERVIEW_SCHEDULING_ACTIONS

    def get_allowed_actions(self) -> list[DomainAction]:
        from app.domains.interview_scheduling.actions import INTERVIEW_SCHEDULING_ACTIONS
        return INTERVIEW_SCHEDULING_ACTIONS

    def get_system_prompt(self) -> str:
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
        query_lower = query.lower().strip()
        best_action = "list_today_interviews"
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
            intent_id=f"interview_scheduling.{best_action}",
            action_id=best_action,
            confidence=best_confidence,
            extracted_params={"raw_query": query},
            reasoning=f"Keyword heuristic matched action '{best_action}'",
        )

    _ACTION_TOOL_MAP: dict[str, str] = {
        "schedule_interview": "scheduling_schedule_interview",
        "reschedule_interview": "scheduling_reschedule",
        "cancel_interview": "scheduling_cancel",
        "check_availability": "scheduling_check_availability",
        "generate_self_scheduling_link": "scheduling_self_scheduling_link",
        "find_common_slots": "scheduling_find_slots",
        "send_reminder": "scheduling_send_reminder",
        "list_today_interviews": "scheduling_list_today",
        "transcribe_audio": "scheduling_transcribe_audio",
        "analyze_voice": "scheduling_analyze_voice",
    }

    async def execute_action(self, action_id: str, params: dict[str, Any], context: DomainContext) -> DomainResponse:
        action = None
        for a in self.get_allowed_actions():
            if a.action_id == action_id:
                action = a
                break

        if not action:
            return DomainResponse.error_response(
                error=f"Ação '{action_id}' não encontrada no domínio de entrevistas & agendamento."
            )

        logger.info(f"Routing interview_scheduling action '{action_id}' (tenant={context.tenant_id})")

        from app.domains.interview_scheduling.tools import INTERVIEW_SCHEDULING_TOOLS, execute_interview_scheduling_tool

        tool_ids = {t["tool_id"] for t in INTERVIEW_SCHEDULING_TOOLS}
        mapped_tool = self._ACTION_TOOL_MAP.get(action_id)

        # Schedule_interview → InterviewGraph (LangGraph conversacional)
        if action_id in _GRAPH_ACTIONS:
            return await self._run_interview_graph(action_id, params, context)

        if mapped_tool and mapped_tool in tool_ids:
            result = await execute_interview_scheduling_tool(mapped_tool, params, context)
            return DomainResponse.success_response(
                message=f"Ferramenta '{mapped_tool}' executada para ação '{action.name}'.",
                data={"action_id": action_id, "tool_id": mapped_tool, "result": result},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        return DomainResponse.success_response(
            message=f"Ação '{action.name}' encaminhada para o agente de entrevistas.",
            data={"action_id": action_id, "params": params, "delegate_to_agent": True},
            domain_id=self.domain_id,
            action_id=action_id,
        )

    async def _run_interview_graph(
        self,
        action_id: str,
        params: dict[str, Any],
        context: DomainContext,
    ) -> DomainResponse:
        """Delega agendamento conversacional ao InterviewGraph (LangGraph).
        Usa a variável module-level `interview_graph` para ser patchável em testes.
        """
        raw_query = params.get("raw_query", "")

        # Mensagem compatível com a interface esperada pelos nós do graph
        class _Msg:
            def __init__(self, content: str):
                self.content = content

        # Persiste workflow_data entre requisições HTTP via InterviewSessionStore (Redis/fallback).
        # 1) Tenta carregar do store (recupera turno anterior da conversa).
        # 2) Params podem sobrepor (cliente enviou workflow_data explicitamente).
        session_key = _SCHEDULING_SESSION_PREFIX + (context.session_id or "no-session")
        stored_workflow = await interview_session_store.get(session_key) or {}
        workflow_data = {**stored_workflow, **params.get("workflow_data", {})}

        state: dict[str, Any] = {
            "messages": [_Msg(raw_query)],
            "workflow_data": workflow_data,
            "entities": {k: v for k, v in params.items() if k not in ("raw_query", "workflow_data")},
            "session_id": context.session_id,
            "company_id": context.tenant_id,
            "user_id": context.user_id,
        }

        try:
            # interview_graph é a variável module-level — patchável via
            # patch("app.domains.interview_scheduling.domain.interview_graph")
            final_state = await interview_graph.invoke(state)
        except Exception as exc:
            logger.error(f"InterviewGraph falhou para action '{action_id}': {exc}", exc_info=True)
            return DomainResponse.error_response(
                error=str(exc),
                message="Erro ao processar agendamento de entrevista.",
                domain_id=self.domain_id,
                action_id=action_id,
            )

        workflow_data_out = final_state.get("workflow_data", {})

        # Persiste o estado atualizado para o próximo turno da conversa
        if context.session_id:
            await interview_session_store.set(session_key, workflow_data_out)

        response_data = workflow_data_out.get("response_data", {})
        status = response_data.get("status", "collecting")

        # Campos pendentes → pede ao usuário
        if status == "collecting":
            next_field = response_data.get("next_field")
            field_labels = {
                "candidate_name": "nome do candidato",
                "candidate_email": "e-mail do candidato",
                "job_title": "cargo/vaga",
                "interview_type": "tipo de entrevista (técnica, comportamental, cultural, RH, gerencial)",
                "interviewer_email": "e-mail do entrevistador",
                "preferred_date": "data preferida (ex: 15/03/2026)",
                "preferred_time": "horário preferido (ex: 14:00 ou tarde)",
            }
            question = (
                f"Para agendar a entrevista, preciso saber: **{field_labels.get(next_field, next_field)}**."
                if next_field else "Qual informação adicional você deseja fornecer?"
            )
            return DomainResponse.clarification_response(
                question=question,
                data={
                    "action_id": action_id,
                    "graph_status": status,
                    "progress": response_data.get("progress", {}),
                    "workflow_data": workflow_data_out,
                },
                domain_id=self.domain_id,
                action_id=action_id,
            )

        # Erro no graph
        if status == "error":
            return DomainResponse.error_response(
                error=response_data.get("error", "Erro desconhecido no agendamento"),
                message="Não foi possível agendar a entrevista.",
                data={"workflow_data": workflow_data_out},
                domain_id=self.domain_id,
                action_id=action_id,
            )

        # Concluído — limpa sessão do store (conversa encerrada)
        if context.session_id:
            await interview_session_store.delete(session_key)

        return DomainResponse.success_response(
            message=response_data.get("message", "Entrevista agendada com sucesso!"),
            data={
                "action_id": action_id,
                "interview_id": response_data.get("interview_id"),
                "meeting_url": response_data.get("meeting_url"),
                "graph_status": status,
                "workflow_data": workflow_data_out,
            },
            domain_id=self.domain_id,
            action_id=action_id,
        )
