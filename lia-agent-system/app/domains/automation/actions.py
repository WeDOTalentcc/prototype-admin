"""Automation & Tasks Domain - Action definitions."""
from app.domains.base import DomainAction

AUTOMATION_ACTIONS = [
    DomainAction(
        action_id="create_task",
        name="Criar Tarefa",
        description="Create a new task for execution",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="list_tasks",
        name="Listar Tarefas",
        description="List current tasks and their status",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="complete_task",
        name="Concluir Tarefa",
        description="Mark task as completed",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="cancel_task",
        name="Cancelar Tarefa",
        description="Cancel a pending task",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="decompose_task",
        name="Decompor Tarefa",
        description="Break complex task into subtasks using AI",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="plan_execution",
        name="Planejar Execução",
        description="Create execution plan with dependencies",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="get_next_tasks",
        name="Próximas Tarefas",
        description="Get next tasks ready for execution",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="create_automation",
        name="Criar Automação",
        description="Create a new automation rule",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="list_automations",
        name="Listar Automações",
        description="List configured automation rules",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="enable_automation",
        name="Ativar Automação",
        description="Enable an automation rule",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="disable_automation",
        name="Desativar Automação",
        description="Disable an automation rule",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="trigger_automation",
        name="Disparar Automação",
        description="Manually trigger an automation",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="view_automation_log",
        name="Ver Log de Automação",
        description="View automation execution history",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="configure_stage_automation",
        name="Configurar Automação de Etapa",
        description="Set up stage transition automation",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="predict_substatus",
        name="Prever Sub-status",
        description="AI-predict next sub-status for candidate",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="check_proactive_alerts",
        name="Verificar Alertas Proativos",
        description="Check proactive alerts for recruiter",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="configure_alert",
        name="Configurar Alerta",
        description="Configure proactive alert rules",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="schedule_recurring",
        name="Agendar Tarefa Recorrente",
        description="Schedule a recurring automation task",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="view_task_dependencies",
        name="Ver Dependências",
        description="View task dependency graph",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="run_autonomous_check",
        name="Executar Verificação Autônoma",
        description="Run autonomous agent background check",
        requires_confirmation=True,
    ),
]
