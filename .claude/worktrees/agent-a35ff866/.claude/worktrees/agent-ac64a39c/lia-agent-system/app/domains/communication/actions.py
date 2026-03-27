"""Communication Domain - Action definitions."""
from app.domains.base import DomainAction

COMMUNICATION_ACTIONS = [
    DomainAction(
        action_id="send_email",
        name="Enviar Email",
        description="Enviar email individual para candidato ou stakeholder",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="send_bulk_email",
        name="Enviar Email em Massa",
        description="Enviar email para múltiplos destinatários simultaneamente",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="send_candidate_report",
        name="Enviar Parecer ao Gestor",
        description="Enviar relatório/parecer do candidato para o gestor contratante",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="send_progress_report",
        name="Relatório de Progresso",
        description="Enviar relatório de andamento da vaga para stakeholders",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="send_kpi_report",
        name="Relatório de KPIs",
        description="Enviar relatório consolidado de indicadores de recrutamento",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="send_feedback",
        name="Enviar Feedback",
        description="Enviar feedback/devolutiva ao candidato sobre o processo seletivo",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="create_template",
        name="Criar Template",
        description="Criar novo template de email para comunicações",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="edit_template",
        name="Editar Template",
        description="Editar template de email existente",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="list_templates",
        name="Listar Templates",
        description="Listar templates de email disponíveis",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="preview_template",
        name="Visualizar Template",
        description="Pré-visualizar template de email com dados do candidato",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="notify_stakeholders",
        name="Notificar Stakeholders",
        description="Enviar notificação para stakeholders sobre eventos do processo",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="send_whatsapp",
        name="Enviar WhatsApp",
        description="Enviar mensagem via WhatsApp para candidato",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="send_teams_message",
        name="Enviar Mensagem Teams",
        description="Enviar mensagem via Microsoft Teams",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="send_sms",
        name="Enviar SMS",
        description="Enviar SMS para candidato",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="get_communication_history",
        name="Histórico de Comunicação",
        description="Consultar histórico de comunicações com candidato",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="send_screening_invite",
        name="Convite de Triagem",
        description="Enviar convite para triagem ao candidato",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="send_interview_invite",
        name="Convite de Entrevista",
        description="Enviar convite para entrevista ao candidato",
        requires_confirmation=True,
    ),
    DomainAction(
        action_id="update_preferences",
        name="Preferências de Comunicação",
        description="Atualizar preferências de comunicação e canal preferido do candidato",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="manage_webhook",
        name="Gerenciar Webhook",
        description="Configurar e gerenciar webhooks de comunicação",
        requires_confirmation=False,
    ),
    DomainAction(
        action_id="handle_data_request",
        name="Solicitação de Dados",
        description="Processar solicitações de dados (LGPD) do candidato",
        requires_confirmation=True,
    ),
]
