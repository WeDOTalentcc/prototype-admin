"""Automation & Tasks Domain - Task management, automations and proactive alerts."""
from typing import Dict, Any, Optional, List
import re
import logging

from app.domains.base import DomainPrompt, DomainContext, DomainAction, IntentResult, DomainResponse
from app.domains.registry import register_domain

logger = logging.getLogger(__name__)

_KEYWORD_ACTION_MAP: Dict[str, str] = {
    "criar tarefa": "create_task",
    "nova tarefa": "create_task",
    "create task": "create_task",
    "adicionar tarefa": "create_task",

    "listar tarefas": "list_tasks",
    "minhas tarefas": "list_tasks",
    "list tasks": "list_tasks",
    "tarefas pendentes": "list_tasks",
    "ver tarefas": "list_tasks",

    "concluir tarefa": "complete_task",
    "completar tarefa": "complete_task",
    "tarefa concluída": "complete_task",
    "complete task": "complete_task",
    "finalizar tarefa": "complete_task",

    "cancelar tarefa": "cancel_task",
    "cancel task": "cancel_task",
    "remover tarefa": "cancel_task",

    "decompor tarefa": "decompose_task",
    "quebrar tarefa": "decompose_task",
    "decompose task": "decompose_task",
    "dividir tarefa": "decompose_task",
    "subtarefas": "decompose_task",

    "planejar execução": "plan_execution",
    "plano de execução": "plan_execution",
    "plan execution": "plan_execution",
    "criar plano": "plan_execution",
    "planejamento": "plan_execution",

    "próximas tarefas": "get_next_tasks",
    "próxima tarefa": "get_next_tasks",
    "next tasks": "get_next_tasks",
    "o que fazer agora": "get_next_tasks",
    "tarefas prioritárias": "get_next_tasks",

    "criar automação": "create_automation",
    "nova automação": "create_automation",
    "create automation": "create_automation",
    "configurar automação": "create_automation",
    "adicionar automação": "create_automation",

    "listar automações": "list_automations",
    "ver automações": "list_automations",
    "list automations": "list_automations",
    "automações configuradas": "list_automations",
    "automações ativas": "list_automations",

    "ativar automação": "enable_automation",
    "enable automation": "enable_automation",
    "habilitar automação": "enable_automation",
    "ligar automação": "enable_automation",

    "desativar automação": "disable_automation",
    "disable automation": "disable_automation",
    "desabilitar automação": "disable_automation",
    "pausar automação": "disable_automation",
    "desligar automação": "disable_automation",

    "disparar automação": "trigger_automation",
    "trigger automation": "trigger_automation",
    "executar automação": "trigger_automation",
    "rodar automação": "trigger_automation",

    "log automação": "view_automation_log",
    "log de automação": "view_automation_log",
    "histórico automação": "view_automation_log",
    "histórico de automação": "view_automation_log",
    "automation log": "view_automation_log",

    "automação de etapa": "configure_stage_automation",
    "automação de estágio": "configure_stage_automation",
    "stage automation": "configure_stage_automation",
    "transição automática": "configure_stage_automation",
    "automatizar etapa": "configure_stage_automation",
    "automatizar transição": "configure_stage_automation",

    "prever sub-status": "predict_substatus",
    "prever substatus": "predict_substatus",
    "predict substatus": "predict_substatus",
    "próximo status": "predict_substatus",
    "previsão de status": "predict_substatus",

    "alertas proativos": "check_proactive_alerts",
    "verificar alertas": "check_proactive_alerts",
    "proactive alerts": "check_proactive_alerts",
    "alertas pendentes": "check_proactive_alerts",
    "meus alertas": "check_proactive_alerts",

    "configurar alerta": "configure_alert",
    "criar alerta": "configure_alert",
    "configure alert": "configure_alert",
    "novo alerta": "configure_alert",

    "tarefa recorrente": "schedule_recurring",
    "agendar recorrente": "schedule_recurring",
    "recurring task": "schedule_recurring",
    "automação periódica": "schedule_recurring",
    "tarefa programada": "schedule_recurring",

    "dependências tarefa": "view_task_dependencies",
    "dependências de tarefa": "view_task_dependencies",
    "ver dependências": "view_task_dependencies",
    "task dependencies": "view_task_dependencies",
    "grafo de tarefas": "view_task_dependencies",

    "verificação autônoma": "run_autonomous_check",
    "autonomous check": "run_autonomous_check",
    "verificação automática": "run_autonomous_check",
    "background check": "run_autonomous_check",
    "agente autônomo": "run_autonomous_check",
}


@register_domain
class AutomationDomain(DomainPrompt):
    domain_id = "automation"
    domain_name = "Automation & Tasks"

    def __init__(self):
        from app.domains.automation.actions import AUTOMATION_ACTIONS
        self._actions = AUTOMATION_ACTIONS

    def get_allowed_actions(self) -> List[DomainAction]:
        from app.domains.automation.actions import AUTOMATION_ACTIONS
        return AUTOMATION_ACTIONS

    def get_system_prompt(self) -> str:
        from app.prompts import PromptLoader
        return PromptLoader.get_domain_prompt(self.domain_id)

    async def process_intent(self, query: str, context: DomainContext) -> IntentResult:
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

    _ACTION_TOOL_MAP: Dict[str, str] = {
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

    async def execute_action(self, action_id: str, params: Dict[str, Any], context: DomainContext) -> DomainResponse:
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
