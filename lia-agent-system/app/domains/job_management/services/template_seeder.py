"""
Template Seeder Service for creating default system templates.
Creates templates for all channels: email, whatsapp, bell, chat_lia, briefing, parecer, report.
"""
import time
import logging
import uuid
from typing import Any, Dict, Final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.template_channels import (
    CHANNEL_BELL,
    CHANNEL_BRIEFING,
    CHANNEL_EMAIL,
    CHANNEL_PARECER,
    CHANNEL_REPORT,
    CHANNEL_TEAMS,
    CHANNEL_WHATSAPP,
)
from app.models.email_template import EmailTemplate

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES: list[dict[str, Any]] = [
    {
        "situation": "goal_at_risk",
        "name": "Meta em Risco",
        "channel": CHANNEL_EMAIL,
        "category": "alerts",
        "subject": "⚠️ Alerta: Meta em Risco - {{goal_name}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #f39c12;">⚠️ Alerta: Meta em Risco</h2>
    <p>Olá {{user_name}},</p>
    <p>A meta <strong>{{goal_name}}</strong> está em risco de não ser atingida.</p>
    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Progresso Atual:</strong> {{current_progress}}%</p>
        <p><strong>Meta:</strong> {{target_value}}</p>
        <p><strong>Prazo:</strong> {{deadline}}</p>
    </div>
    <p>Recomendamos ações imediatas para evitar o descumprimento.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "goal_name", "current_progress", "target_value", "deadline"],
        "trigger_type": "automatic",
        "used_in": ["automation", "alerts"],
        "priority": "medium",
    },
    {
        "situation": "goal_missed",
        "name": "Meta Não Atingida",
        "channel": CHANNEL_EMAIL,
        "category": "alerts",
        "subject": "❌ Meta Não Atingida - {{goal_name}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #e74c3c;">❌ Meta Não Atingida</h2>
    <p>Olá {{user_name}},</p>
    <p>Infelizmente a meta <strong>{{goal_name}}</strong> não foi atingida.</p>
    <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Resultado Final:</strong> {{final_result}}</p>
        <p><strong>Meta Esperada:</strong> {{target_value}}</p>
        <p><strong>Diferença:</strong> {{gap_percentage}}%</p>
    </div>
    <p>Vamos analisar as causas e definir ações corretivas.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "goal_name", "final_result", "target_value", "gap_percentage"],
        "trigger_type": "automatic",
        "used_in": ["automation", "alerts"],
        "priority": "medium",
    },
    {
        "situation": "weekly_performance",
        "name": "Performance Semanal",
        "channel": CHANNEL_EMAIL,
        "category": "reports",
        "subject": "📊 Relatório de Performance Semanal - {{week_period}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #3498db;">📊 Performance Semanal</h2>
    <p>Olá {{user_name}},</p>
    <p>Confira o resumo da performance da semana <strong>{{week_period}}</strong>:</p>
    <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Candidatos Triados:</strong> {{candidates_screened}}</p>
        <p><strong>Entrevistas Realizadas:</strong> {{interviews_conducted}}</p>
        <p><strong>Propostas Enviadas:</strong> {{offers_sent}}</p>
        <p><strong>Contratações:</strong> {{hires}}</p>
    </div>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "week_period", "candidates_screened", "interviews_conducted", "offers_sent", "hires"],
        "trigger_type": "automatic",
        "used_in": ["automation", "reports"],
        "priority": "low",
    },
    {
        "situation": "sla_violated",
        "name": "SLA Violado",
        "channel": CHANNEL_EMAIL,
        "category": "alerts",
        "subject": "🚨 SLA Violado - {{sla_name}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #e74c3c;">🚨 SLA Violado</h2>
    <p>Olá {{user_name}},</p>
    <p>O SLA <strong>{{sla_name}}</strong> foi violado.</p>
    <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Tempo Esperado:</strong> {{expected_time}}</p>
        <p><strong>Tempo Real:</strong> {{actual_time}}</p>
        <p><strong>Vaga Afetada:</strong> {{job_title}}</p>
    </div>
    <p>Por favor, tome as medidas necessárias imediatamente.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "sla_name", "expected_time", "actual_time", "job_title"],
        "trigger_type": "automatic",
        "used_in": ["automation", "alerts"],
        "priority": "medium",
    },
    {
        "situation": "approval_pending",
        "name": "Aprovação Pendente",
        "channel": CHANNEL_EMAIL,
        "category": "workflow",
        "subject": "🔔 Aprovação Pendente - {{item_type}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #f39c12;">🔔 Aprovação Pendente</h2>
    <p>Olá {{approver_name}},</p>
    <p>Você tem uma aprovação pendente do tipo <strong>{{item_type}}</strong>.</p>
    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Item:</strong> {{item_name}}</p>
        <p><strong>Solicitante:</strong> {{requester_name}}</p>
        <p><strong>Data da Solicitação:</strong> {{request_date}}</p>
    </div>
    <p><a href="{{approval_link}}" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Analisar Solicitação</a></p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["approver_name", "item_type", "item_name", "requester_name", "request_date", "approval_link"],
        "trigger_type": "automatic",
        "used_in": ["automation", "alerts"],
        "priority": "medium",
    },
    {
        "situation": "offer_accepted",
        "name": "Proposta Aceita",
        "channel": CHANNEL_EMAIL,
        "category": "offers",
        "subject": "🎉 Proposta Aceita - {{candidate_name}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #27ae60;">🎉 Proposta Aceita!</h2>
    <p>Olá {{recruiter_name}},</p>
    <p>Ótima notícia! <strong>{{candidate_name}}</strong> aceitou a proposta para a vaga de <strong>{{job_title}}</strong>.</p>
    <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Data de Início:</strong> {{start_date}}</p>
        <p><strong>Departamento:</strong> {{department}}</p>
    </div>
    <p>Próximos passos: iniciar processo de onboarding.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["recruiter_name", "candidate_name", "job_title", "start_date", "department"],
        "trigger_type": "manual",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "high",
    },
    {
        "situation": "offer_rejected",
        "name": "Proposta Recusada",
        "channel": CHANNEL_EMAIL,
        "category": "offers",
        "subject": "😔 Proposta Recusada - {{candidate_name}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #e74c3c;">😔 Proposta Recusada</h2>
    <p>Olá {{recruiter_name}},</p>
    <p><strong>{{candidate_name}}</strong> recusou a proposta para a vaga de <strong>{{job_title}}</strong>.</p>
    <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Motivo:</strong> {{rejection_reason}}</p>
    </div>
    <p>Recomendamos entrar em contato com os próximos candidatos na shortlist.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["recruiter_name", "candidate_name", "job_title", "rejection_reason"],
        "trigger_type": "manual",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "high",
    },
    {
        "situation": "monthly_report",
        "name": "Relatório Mensal",
        "channel": CHANNEL_EMAIL,
        "category": "reports",
        "subject": "📈 Relatório Mensal de Recrutamento - {{month_year}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #3498db;">📈 Relatório Mensal</h2>
    <p>Olá {{user_name}},</p>
    <p>Confira o relatório mensal de recrutamento de <strong>{{month_year}}</strong>:</p>
    <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Vagas Abertas:</strong> {{jobs_opened}}</p>
        <p><strong>Vagas Fechadas:</strong> {{jobs_closed}}</p>
        <p><strong>Total de Candidatos:</strong> {{total_candidates}}</p>
        <p><strong>Contratações:</strong> {{total_hires}}</p>
        <p><strong>Tempo Médio de Fechamento:</strong> {{avg_time_to_fill}} dias</p>
    </div>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "month_year", "jobs_opened", "jobs_closed", "total_candidates", "total_hires", "avg_time_to_fill"],
        "trigger_type": "automatic",
        "used_in": ["automation", "reports"],
        "priority": "low",
    },
    {
        "situation": "welcome_user",
        "name": "Boas-vindas Usuário",
        "channel": CHANNEL_EMAIL,
        "category": "onboarding",
        "subject": "🎉 Bem-vindo à Plataforma LIA!",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #27ae60;">🎉 Bem-vindo à LIA!</h2>
    <p>Olá {{user_name}},</p>
    <p>Sua conta foi criada com sucesso na plataforma LIA!</p>
    <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>E-mail:</strong> {{user_email}}</p>
        <p><strong>Empresa:</strong> {{company_name}}</p>
        <p><strong>Perfil:</strong> {{user_role}}</p>
    </div>
    <p><a href="{{login_link}}" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Acessar Plataforma</a></p>
    <p>Atenciosamente,<br>Equipe LIA</p>
</body>
</html>
""",
        "variables": ["user_name", "user_email", "company_name", "user_role", "login_link"],
        "trigger_type": "automatic",
        "used_in": ["automation"],
        "priority": "low",
    },
    {
        "situation": "approval_expired",
        "name": "Aprovação Expirada",
        "channel": CHANNEL_EMAIL,
        "category": "workflow",
        "subject": "⏰ Aprovação Expirada - {{item_name}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #e74c3c;">⏰ Aprovação Expirada</h2>
    <p>Olá {{user_name}},</p>
    <p>A aprovação para <strong>{{item_name}}</strong> expirou sem uma decisão.</p>
    <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Tipo:</strong> {{item_type}}</p>
        <p><strong>Solicitante:</strong> {{requester_name}}</p>
        <p><strong>Prazo Original:</strong> {{deadline}}</p>
    </div>
    <p>Por favor, entre em contato com o solicitante para definir próximos passos.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "item_name", "item_type", "requester_name", "deadline"],
        "trigger_type": "automatic",
        "used_in": ["automation", "alerts"],
        "priority": "medium",
    },
    {
        "situation": "ats_sync_failed",
        "name": "Sync ATS Falhou",
        "channel": CHANNEL_EMAIL,
        "category": "integrations",
        "subject": "❌ Falha na Sincronização do ATS",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #e74c3c;">❌ Falha na Sincronização</h2>
    <p>Olá {{user_name}},</p>
    <p>Houve uma falha na sincronização com o ATS <strong>{{ats_name}}</strong>.</p>
    <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Erro:</strong> {{error_message}}</p>
        <p><strong>Última Sincronização:</strong> {{last_sync}}</p>
    </div>
    <p>Por favor, verifique as credenciais de integração.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "ats_name", "error_message", "last_sync"],
        "trigger_type": "automatic",
        "used_in": ["automation"],
        "priority": "low",
    },
    {
        "situation": "credits_low",
        "name": "Créditos Baixos",
        "channel": CHANNEL_EMAIL,
        "category": "billing",
        "subject": "⚠️ Créditos Baixos - {{credits_remaining}} restantes",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #f39c12;">⚠️ Créditos Baixos</h2>
    <p>Olá {{user_name}},</p>
    <p>Seus créditos estão acabando. Restam apenas <strong>{{credits_remaining}}</strong> créditos.</p>
    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Uso este Mês:</strong> {{credits_used}}</p>
        <p><strong>Limite:</strong> {{credits_limit}}</p>
    </div>
    <p><a href="{{billing_link}}" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Comprar Mais Créditos</a></p>
    <p>Atenciosamente,<br>Equipe LIA</p>
</body>
</html>
""",
        "variables": ["user_name", "credits_remaining", "credits_used", "credits_limit", "billing_link"],
        "trigger_type": "automatic",
        "used_in": ["automation"],
        "priority": "low",
    },
    {
        "situation": "no_show_alert",
        "name": "Alerta No-Show",
        "channel": CHANNEL_EMAIL,
        "category": "interviews",
        "subject": "🚫 No-Show: {{candidate_name}} - {{job_title}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #e74c3c;">🚫 No-Show Registrado</h2>
    <p>Olá {{recruiter_name}},</p>
    <p>O candidato <strong>{{candidate_name}}</strong> não compareceu à entrevista agendada.</p>
    <div style="background: #f8d7da; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Vaga:</strong> {{job_title}}</p>
        <p><strong>Data/Hora:</strong> {{scheduled_datetime}}</p>
        <p><strong>Tipo:</strong> {{interview_type}}</p>
    </div>
    <p>Recomendação: Entrar em contato para reagendamento ou seguir com próximo candidato.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["recruiter_name", "candidate_name", "job_title", "scheduled_datetime", "interview_type"],
        "trigger_type": "automatic",
        "used_in": ["automation", "alerts"],
        "priority": "high",
    },
    {
        "situation": "job_paused",
        "name": "Vaga Pausada",
        "channel": CHANNEL_EMAIL,
        "category": "jobs",
        "subject": "⏸️ Vaga Pausada - {{job_title}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #95a5a6;">⏸️ Vaga Pausada</h2>
    <p>Olá {{user_name}},</p>
    <p>A vaga <strong>{{job_title}}</strong> foi pausada.</p>
    <div style="background: #d6d6d6; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Motivo:</strong> {{pause_reason}}</p>
        <p><strong>Pausada por:</strong> {{paused_by}}</p>
        <p><strong>Candidatos em Pipeline:</strong> {{candidates_in_pipeline}}</p>
    </div>
    <p>Os candidatos serão mantidos no pipeline até a reativação.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "job_title", "pause_reason", "paused_by", "candidates_in_pipeline"],
        "trigger_type": "automatic",
        "used_in": ["automation"],
        "priority": "low",
    },
    {
        "situation": "job_reactivated",
        "name": "Vaga Reativada",
        "channel": CHANNEL_EMAIL,
        "category": "jobs",
        "subject": "▶️ Vaga Reativada - {{job_title}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #27ae60;">▶️ Vaga Reativada</h2>
    <p>Olá {{user_name}},</p>
    <p>A vaga <strong>{{job_title}}</strong> foi reativada!</p>
    <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Reativada por:</strong> {{reactivated_by}}</p>
        <p><strong>Candidatos no Pipeline:</strong> {{candidates_in_pipeline}}</p>
    </div>
    <p>O processo seletivo será retomado.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "job_title", "reactivated_by", "candidates_in_pipeline"],
        "trigger_type": "automatic",
        "used_in": ["automation"],
        "priority": "low",
    },
    {
        "situation": "workforce_variance",
        "name": "Variância Workforce",
        "channel": CHANNEL_EMAIL,
        "category": "workforce",
        "subject": "📉 Variância no Planejamento de Workforce",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #f39c12;">📉 Variância de Workforce</h2>
    <p>Olá {{user_name}},</p>
    <p>Foi detectada uma variância significativa no planejamento de workforce.</p>
    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Departamento:</strong> {{department}}</p>
        <p><strong>Headcount Planejado:</strong> {{planned_headcount}}</p>
        <p><strong>Headcount Atual:</strong> {{current_headcount}}</p>
        <p><strong>Variância:</strong> {{variance_percentage}}%</p>
    </div>
    <p>Recomendamos revisar o planejamento.</p>
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["user_name", "department", "planned_headcount", "current_headcount", "variance_percentage"],
        "trigger_type": "automatic",
        "used_in": ["automation", "alerts"],
        "priority": "medium",
    },
    {
        "situation": "screening_completed",
        "name": "Triagem Concluída",
        "channel": CHANNEL_BELL,
        "category": "screening",
        "subject": "Triagem Concluída",
        "body_html": """
<div>
    <strong>{{candidate_name}}</strong> concluiu a triagem para <strong>{{job_title}}</strong>.
    <br>Score: {{match_score}}% | {{recommendation}}
</div>
""",
        "variables": ["candidate_name", "job_title", "match_score", "recommendation"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "medium",
    },
    {
        "situation": "critical_alert",
        "name": "Alerta Crítico",
        "channel": CHANNEL_BELL,
        "category": "alerts",
        "subject": "Alerta Crítico",
        "body_html": """
<div>
    <strong>🚨 {{alert_type}}</strong>: {{alert_message}}
    <br>Ação requerida: {{required_action}}
</div>
""",
        "variables": ["alert_type", "alert_message", "required_action"],
        "trigger_type": "automatic",
        "used_in": ["automation", "alerts"],
        "priority": "high",
    },
    {
        "situation": "daily_briefing",
        "name": "Briefing Diário",
        "channel": CHANNEL_BRIEFING,
        "category": "briefings",
        "subject": "Briefing Diário - {{date}}",
        "body_html": """
<div style="font-family: Arial, sans-serif;">
    <h3>📋 Briefing Diário - {{date}}</h3>
    <p>Bom dia, {{user_name}}!</p>
    
    <h4>📊 Resumo do Dia</h4>
    <ul>
        <li>Entrevistas agendadas: {{interviews_today}}</li>
        <li>Aprovações pendentes: {{pending_approvals}}</li>
        <li>Tarefas prioritárias: {{priority_tasks}}</li>
    </ul>
    
    <h4>🎯 Foco do Dia</h4>
    <p>{{focus_areas}}</p>
    
    <h4>⚠️ Alertas</h4>
    <p>{{alerts_summary}}</p>
</div>
""",
        "variables": ["date", "user_name", "interviews_today", "pending_approvals", "priority_tasks", "focus_areas", "alerts_summary"],
        "trigger_type": "automatic",
        "used_in": ["automation", "reports"],
        "priority": "low",
    },
    {
        "situation": "end_of_day_summary",
        "name": "Resumo de Fim de Dia",
        "channel": CHANNEL_BRIEFING,
        "category": "briefings",
        "subject": "Resumo do Dia - {{date}}",
        "body_html": """
<div style="font-family: Arial, sans-serif;">
    <h3>🌙 Resumo de Fim de Dia - {{date}}</h3>
    <p>Olá, {{user_name}}!</p>
    
    <h4>✅ Realizações de Hoje</h4>
    <ul>
        <li>Candidatos triados: {{candidates_screened}}</li>
        <li>Entrevistas realizadas: {{interviews_completed}}</li>
        <li>Propostas enviadas: {{offers_sent}}</li>
    </ul>
    
    <h4>📌 Para Amanhã</h4>
    <p>{{tomorrow_priorities}}</p>
    
    <h4>💡 Insights da LIA</h4>
    <p>{{lia_insights}}</p>
</div>
""",
        "variables": ["date", "user_name", "candidates_screened", "interviews_completed", "offers_sent", "tomorrow_priorities", "lia_insights"],
        "trigger_type": "automatic",
        "used_in": ["automation", "reports"],
        "priority": "low",
    },
    {
        "situation": "lia_opinion_compact",
        "name": "Parecer Resumido",
        "channel": CHANNEL_PARECER,
        "category": "parecer",
        "subject": "Parecer LIA - {{candidate_name}}",
        "body_html": """
<div style="font-family: Arial, sans-serif; padding: 15px; border-left: 4px solid #3498db;">
    <h4>Parecer LIA - {{candidate_name}}</h4>
    <p><strong>Vaga:</strong> {{job_title}}</p>
    <p><strong>Match Score:</strong> {{match_score}}%</p>
    <p><strong>Recomendação:</strong> {{recommendation}}</p>
    <p><strong>Resumo:</strong> {{summary}}</p>
</div>
""",
        "variables": ["candidate_name", "job_title", "match_score", "recommendation", "summary"],
        "trigger_type": "automatic",
        "used_in": ["automation"],
        "priority": "medium",
    },
    {
        "situation": "lia_opinion_full",
        "name": "Parecer Completo",
        "channel": CHANNEL_PARECER,
        "category": "parecer",
        "subject": "Parecer Completo LIA - {{candidate_name}}",
        "body_html": """
<div style="font-family: Arial, sans-serif;">
    <h3>📝 Parecer Completo da LIA</h3>
    <h4>Candidato: {{candidate_name}}</h4>
    <p><strong>Vaga:</strong> {{job_title}}</p>
    
    <h4>📊 Scores</h4>
    <ul>
        <li>Match Geral: {{match_score}}%</li>
        <li>Experiência: {{experience_score}}%</li>
        <li>Habilidades: {{skills_score}}%</li>
        <li>Cultural Fit: {{cultural_score}}%</li>
    </ul>
    
    <h4>✅ Pontos Fortes</h4>
    <p>{{strengths}}</p>
    
    <h4>⚠️ Pontos de Atenção</h4>
    <p>{{concerns}}</p>
    
    <h4>💡 Recomendação</h4>
    <p>{{recommendation}}</p>
    
    <h4>🎯 Perguntas Sugeridas para Entrevista</h4>
    <p>{{suggested_questions}}</p>
</div>
""",
        "variables": ["candidate_name", "job_title", "match_score", "experience_score", "skills_score", "cultural_score", "strengths", "concerns", "recommendation", "suggested_questions"],
        "trigger_type": "automatic",
        "used_in": ["automation"],
        "priority": "medium",
    },
    {
        "situation": "weekly_summary",
        "name": "Resumo Semanal",
        "channel": CHANNEL_REPORT,
        "category": "reports",
        "subject": "Resumo Semanal - {{week_period}}",
        "body_html": """
<div style="font-family: Arial, sans-serif;">
    <h3>📊 Resumo Semanal de Recrutamento</h3>
    <p><strong>Período:</strong> {{week_period}}</p>
    
    <h4>Métricas Principais</h4>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #f5f5f5;">
            <td style="padding: 8px; border: 1px solid #ddd;">Novos Candidatos</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{new_candidates}}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Triagens Realizadas</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{screenings_done}}</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 8px; border: 1px solid #ddd;">Entrevistas</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{interviews}}</td>
        </tr>
        <tr>
            <td style="padding: 8px; border: 1px solid #ddd;">Propostas</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{offers}}</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 8px; border: 1px solid #ddd;">Contratações</td>
            <td style="padding: 8px; border: 1px solid #ddd;">{{hires}}</td>
        </tr>
    </table>
</div>
""",
        "variables": ["week_period", "new_candidates", "screenings_done", "interviews", "offers", "hires"],
        "trigger_type": "automatic",
        "used_in": ["automation", "reports"],
        "priority": "low",
    },
    {
        "situation": "monthly_summary",
        "name": "Relatório Mensal",
        "channel": CHANNEL_REPORT,
        "category": "reports",
        "subject": "Relatório Mensal - {{month_year}}",
        "body_html": """
<div style="font-family: Arial, sans-serif;">
    <h3>📈 Relatório Mensal de Recrutamento</h3>
    <p><strong>Período:</strong> {{month_year}}</p>
    
    <h4>Visão Geral</h4>
    <ul>
        <li>Total de Vagas: {{total_jobs}}</li>
        <li>Vagas Fechadas: {{closed_jobs}}</li>
        <li>Taxa de Fechamento: {{close_rate}}%</li>
    </ul>
    
    <h4>Pipeline</h4>
    <ul>
        <li>Candidatos no Mês: {{monthly_candidates}}</li>
        <li>Tempo Médio de Fechamento: {{avg_time_to_fill}} dias</li>
        <li>Custo por Contratação: R$ {{cost_per_hire}}</li>
    </ul>
    
    <h4>Performance por Fonte</h4>
    <p>{{source_performance}}</p>
</div>
""",
        "variables": ["month_year", "total_jobs", "closed_jobs", "close_rate", "monthly_candidates", "avg_time_to_fill", "cost_per_hire", "source_performance"],
        "trigger_type": "automatic",
        "used_in": ["automation", "reports"],
        "priority": "low",
    },
    {
        "situation": "team_report",
        "name": "Relatório de Equipe",
        "channel": CHANNEL_REPORT,
        "category": "reports",
        "subject": "Relatório de Equipe - {{team_name}}",
        "body_html": """
<div style="font-family: Arial, sans-serif;">
    <h3>👥 Relatório de Equipe</h3>
    <p><strong>Equipe:</strong> {{team_name}}</p>
    <p><strong>Período:</strong> {{report_period}}</p>
    
    <h4>Performance da Equipe</h4>
    <ul>
        <li>Vagas Gerenciadas: {{jobs_managed}}</li>
        <li>Contratações: {{team_hires}}</li>
        <li>Tempo Médio de Resposta: {{avg_response_time}}</li>
    </ul>
    
    <h4>Performance Individual</h4>
    <p>{{individual_performance}}</p>
    
    <h4>Metas vs Realizado</h4>
    <p>{{goals_vs_actual}}</p>
</div>
""",
        "variables": ["team_name", "report_period", "jobs_managed", "team_hires", "avg_response_time", "individual_performance", "goals_vs_actual"],
        "trigger_type": "automatic",
        "used_in": ["automation", "reports"],
        "priority": "low",
    },
    # ========================================
    # TEMPLATES DE EMAIL PARA CANDIDATOS
    # ========================================
    {
        "situation": "initial_contact",
        "name": "Primeiro Contato com Candidato",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Oportunidade: {{job_title}} - {{company_name}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá {{candidate_name}},</p>
    
    <p>A {{company_name}} está em busca de um(a) <strong>{{job_title}}</strong> para integrar nosso time.</p>
    
    <p>Seu perfil chamou nossa atenção e acreditamos que você pode ser um excelente fit para esta posição.</p>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <strong>O DESAFIO:</strong><br>
        {{job_challenge}}
    </div>
    
    <p><strong>PRÓXIMOS PASSOS:</strong></p>
    <p>Se tiver interesse, convidamos você a participar de uma triagem inicial com a LIA, nossa assistente de recrutamento com inteligência artificial.</p>
    
    <p>A LIA conduz entrevistas de forma:</p>
    <ul>
        <li>✅ Profissional e isenta (sem viés)</li>
        <li>✅ Humanizada e respeitosa</li>
        <li>✅ Com feedback construtivo ao final</li>
    </ul>
    
    <p style="text-align: center;">
        <a href="{{screening_link}}" style="background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">👉 CLIQUE AQUI PARA INICIAR</a>
    </p>
    
    <p style="font-size: 13px; color: #6b7280; margin-top: 20px;">
        📋 Ao participar, você concorda com nossa <a href="{{privacy_policy_url}}" style="color: #3498db;">Política de Privacidade</a>. Caso não deseje participar do processo, basta responder este email informando.
    </p>
    
    <p>Atenciosamente,<br>{{recruiter_name}}<br>{{company_name}}</p>
</body>
</html>
""",
        "variables": ["candidate_name", "job_title", "company_name", "job_challenge", "recruiter_name", "screening_link", "privacy_policy_url"],
        "trigger_type": "manual",
        "used_in": ["communication_modal"],
        "priority": "medium",
    },
    {
        "situation": "screening_reminder",
        "name": "Lembrete de Triagem Pendente",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Lembrete: Triagem pendente - {{job_title}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá {{candidate_name}},</p>
    
    <p>Notei que você ainda não completou a triagem para a posição de <strong>{{job_title}}</strong>.</p>
    
    <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p>⏰ Você tem mais <strong>{{hours_remaining}} horas</strong> para finalizar a conversa.</p>
    </div>
    
    <p style="text-align: center;">
        <a href="{{screening_link}}" style="background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">👉 CLIQUE AQUI PARA CONTINUAR</a>
    </p>
    
    <p>Se tiver qualquer dificuldade ou dúvida, é só responder este email.</p>
    
    <p>Atenciosamente,<br>LIA - Assistente de Recrutamento</p>
</body>
</html>
""",
        "variables": ["candidate_name", "job_title", "hours_remaining", "screening_link"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "medium",
    },
    {
        "situation": "screening_passed",
        "name": "Aprovação na Triagem",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "🎉 Parabéns! Você avançou no processo - {{job_title}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #27ae60;">🎉 Parabéns, {{candidate_name}}!</h2>
    
    <p>Temos uma ótima notícia: você foi <strong>aprovado(a)</strong> na triagem para a vaga de <strong>{{job_title}}</strong>!</p>
    
    <div style="background: #d4edda; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Próxima Etapa:</strong> {{next_step}}</p>
        <p><strong>Prazo:</strong> {{deadline}}</p>
    </div>
    
    <p>Em breve entraremos em contato com mais detalhes sobre os próximos passos.</p>
    
    <p>Atenciosamente,<br>{{recruiter_name}}<br>{{company_name}}</p>
</body>
</html>
""",
        "variables": ["candidate_name", "job_title", "next_step", "deadline", "recruiter_name", "company_name"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "medium",
    },
    {
        "situation": "screening_failed",
        "name": "Rejeição na Triagem",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Atualização sobre sua candidatura - {{job_title}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá {{candidate_name}},</p>
    
    <p>Agradecemos muito seu interesse na posição de <strong>{{job_title}}</strong> e o tempo que dedicou ao nosso processo seletivo.</p>
    
    <p>Após uma análise cuidadosa do seu perfil, decidimos não prosseguir com sua candidatura neste momento.</p>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Feedback:</strong></p>
        <p>{{feedback}}</p>
    </div>
    
    <p>Isso não significa que você não seja um excelente profissional - apenas que para esta vaga específica, outros perfis estão mais alinhados com as necessidades atuais.</p>
    
    <p>Desejamos muito sucesso em sua trajetória profissional!</p>
    
    <p>Atenciosamente,<br>{{recruiter_name}}<br>{{company_name}}</p>
</body>
</html>
""",
        "variables": ["candidate_name", "job_title", "feedback", "recruiter_name", "company_name"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "medium",
    },
    {
        "situation": "interview_scheduled",
        "name": "Entrevista Agendada",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "📅 Entrevista Agendada - {{job_title}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h2 style="color: #3498db;">📅 Entrevista Agendada</h2>
    
    <p>Olá {{candidate_name}},</p>
    
    <p>Sua entrevista para a vaga de <strong>{{job_title}}</strong> está confirmada!</p>
    
    <div style="background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>📅 Data:</strong> {{interview_date}}</p>
        <p><strong>⏰ Horário:</strong> {{interview_time}}</p>
        <p><strong>📍 Local/Link:</strong> {{interview_location}}</p>
        <p><strong>👤 Entrevistador:</strong> {{interviewer_name}}</p>
    </div>
    
    <p><strong>Dicas para a entrevista:</strong></p>
    <ul>
        <li>Teste sua conexão com antecedência (para entrevistas online)</li>
        <li>Prepare perguntas sobre a empresa e a posição</li>
        <li>Tenha em mãos exemplos de projetos e realizações</li>
    </ul>
    
    <p style="text-align: center;">
        <a href="{{calendar_link}}" style="background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">📅 Adicionar ao Calendário</a>
    </p>
    
    <p>Atenciosamente,<br>{{recruiter_name}}<br>{{company_name}}</p>
</body>
</html>
""",
        "variables": ["candidate_name", "job_title", "interview_date", "interview_time", "interview_location", "interviewer_name", "calendar_link", "recruiter_name", "company_name"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "high",
    },
    {
        "situation": "rejection_post_interview",
        "name": "Rejeição Pós-Entrevista",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Atualização sobre seu processo seletivo - {{job_title}}",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá {{candidate_name}},</p>
    
    <p>Primeiramente, gostaríamos de agradecer pelo tempo e esforço que você dedicou ao nosso processo seletivo para a vaga de <strong>{{job_title}}</strong>.</p>
    
    <p>Após uma análise cuidadosa, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades específicas desta posição no momento.</p>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Feedback da Entrevista:</strong></p>
        <p>{{interview_feedback}}</p>
        
        <p><strong>Pontos Positivos Observados:</strong></p>
        <p>{{positive_points}}</p>
        
        <p><strong>Sugestões de Desenvolvimento:</strong></p>
        <p>{{development_suggestions}}</p>
    </div>
    
    <p>Ficamos muito impressionados com sua trajetória e manteremos seu perfil em nosso banco de talentos para futuras oportunidades.</p>
    
    <p>Desejamos muito sucesso em sua carreira!</p>
    
    <p>Atenciosamente,<br>{{recruiter_name}}<br>{{company_name}}</p>
</body>
</html>
""",
        "variables": ["candidate_name", "job_title", "interview_feedback", "positive_points", "development_suggestions", "recruiter_name", "company_name"],
        "trigger_type": "manual",
        "used_in": ["communication_modal", "close_vacancy_modal"],
        "priority": "high",
    },
    {
        "situation": "process_closed",
        "name": "Processo Encerrado",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Atualização: Vaga {{job_title}} encerrada",
        "body_html": """
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <p>Olá {{candidate_name}},</p>
    
    <p>Gostaríamos de informar que o processo seletivo para a vaga de <strong>{{job_title}}</strong> foi encerrado.</p>
    
    <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
        <p><strong>Motivo:</strong> {{close_reason}}</p>
    </div>
    
    <p>Agradecemos muito seu interesse e participação no processo. Seu perfil permanecerá em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades compatíveis.</p>
    
    <p>Atenciosamente,<br>{{recruiter_name}}<br>{{company_name}}</p>
</body>
</html>
""",
        "variables": ["candidate_name", "job_title", "close_reason", "recruiter_name", "company_name"],
        "trigger_type": "automatic",
        "used_in": ["close_vacancy_modal", "automation"],
        "priority": "high",
    },
    # ========================================
    # TEMPLATES DE WHATSAPP
    # ========================================
    {
        "situation": "initial_contact_wa",
        "name": "Primeiro Contato via WhatsApp",
        "channel": CHANNEL_WHATSAPP,
        "category": "candidates",
        "subject": "Primeiro Contato",
        "body_html": """Olá {{candidate_name}}, tudo bem?
Estamos fazendo uma triagem inicial para a vaga de {{job_title}}.
Gostaríamos de confirmar seu interesse e seguir com algumas perguntas conduzidas pela LIA, nossa assistente de recrutamento com inteligência artificial.
Ao continuar, voce concorda com nossa Politica de Privacidade em {{privacy_policy_url}}. Responda 'NAO' se nao deseja participar.
Você pode responder agora?""",
        "variables": ["candidate_name", "job_title", "privacy_policy_url"],
        "trigger_type": "manual",
        "used_in": ["communication_modal"],
        "priority": "medium",
    },
    {
        "situation": "screening_reminder_wa",
        "name": "Lembrete de Triagem (WhatsApp)",
        "channel": CHANNEL_WHATSAPP,
        "category": "candidates",
        "subject": "Lembrete de Triagem",
        "body_html": """
Oi {{candidate_name}}! 👋

Notei que você iniciou a triagem para *{{job_title}}* mas ainda não finalizou.

⏰ Você tem mais {{hours_remaining}} horas para completar.

É rapidinho! Clique aqui para continuar:
{{screening_link}}

Qualquer dúvida, estou por aqui! 😊
""",
        "variables": ["candidate_name", "job_title", "hours_remaining", "screening_link"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "medium",
    },
    {
        "situation": "interview_reminder_wa",
        "name": "Lembrete de Entrevista (WhatsApp)",
        "channel": CHANNEL_WHATSAPP,
        "category": "candidates",
        "subject": "Lembrete de Entrevista",
        "body_html": """
Oi {{candidate_name}}! 👋

Passando para lembrar da sua entrevista que está chegando:

📅 *{{interview_date}}*
⏰ *{{interview_time}}*
📍 {{interview_location}}

Algumas dicas:
✅ Teste sua conexão antes
✅ Prepare perguntas sobre a vaga
✅ Tenha exemplos de projetos

Boa sorte! 🍀

{{calendar_link}}
""",
        "variables": ["candidate_name", "interview_date", "interview_time", "interview_location", "calendar_link"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "high",
    },
    # ========================================
    # TEMPLATES DE TEAMS
    # ========================================
    {
        "situation": "critical_alert_teams",
        "name": "Alerta Crítico via Teams",
        "channel": CHANNEL_TEAMS,
        "category": "alerts",
        "subject": "Alerta Crítico",
        "body_html": """
{
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "🚨 {{alert_type}}",
                        "weight": "Bolder",
                        "size": "Large",
                        "color": "Attention"
                    },
                    {
                        "type": "TextBlock",
                        "text": "{{alert_message}}",
                        "wrap": true
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {"title": "Vaga", "value": "{{job_title}}"},
                            {"title": "Candidato", "value": "{{candidate_name}}"},
                            {"title": "Horário", "value": "{{timestamp}}"}
                        ]
                    }
                ],
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "Ver Detalhes",
                        "url": "{{action_link}}"
                    }
                ]
            }
        }
    ]
}
""",
        "variables": ["alert_type", "alert_message", "job_title", "candidate_name", "timestamp", "action_link"],
        "trigger_type": "automatic",
        "used_in": ["automation", "alerts"],
        "priority": "high",
    },
    {
        "situation": "screening_completed_teams",
        "name": "Triagem Concluída via Teams",
        "channel": CHANNEL_TEAMS,
        "category": "screening",
        "subject": "Triagem Concluída",
        "body_html": """
{
    "type": "message",
    "attachments": [
        {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "🎯 Triagem Concluída",
                        "weight": "Bolder",
                        "size": "Large"
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {"title": "Candidato", "value": "{{candidate_name}}"},
                            {"title": "Vaga", "value": "{{job_title}}"},
                            {"title": "Score WSI", "value": "{{wsi_score}}%"},
                            {"title": "Recomendação", "value": "{{recommendation}}"}
                        ]
                    },
                    {
                        "type": "TextBlock",
                        "text": "**Pontos Fortes:** {{strengths}}",
                        "wrap": true
                    }
                ],
                "actions": [
                    {"type": "Action.OpenUrl", "title": "Agendar Entrevista", "url": "{{schedule_link}}"},
                    {"type": "Action.OpenUrl", "title": "Ver Parecer", "url": "{{parecer_link}}"}
                ]
            }
        }
    ]
}
""",
        "variables": ["candidate_name", "job_title", "wsi_score", "recommendation", "strengths", "schedule_link", "parecer_link"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "medium",
    },
    # ========================================
    # RELATÓRIO EXECUTIVO DA VAGA
    # ========================================
    {
        "situation": "job_executive_report",
        "name": "Relatório Executivo da Vaga",
        "channel": CHANNEL_REPORT,
        "category": "reports",
        "subject": "Relatório Executivo - {{job_title}}",
        "body_html": """
<div style="font-family: Arial, sans-serif;">
    <h2>📄 Relatório Executivo da Vaga</h2>
    <p><strong>{{job_title}}</strong> | {{department}} | {{location}}</p>
    <p>Gerado: {{generated_date}} às {{generated_time}}</p>
    
    <hr>
    
    <h3>📊 RESUMO EXECUTIVO</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr style="background: #f5f5f5;">
            <td style="padding: 10px; text-align: center;"><strong>👥 Total</strong><br>{{total_candidates}} candidatos</td>
            <td style="padding: 10px; text-align: center;"><strong>✅ Contratados</strong><br>{{hired_count}}</td>
            <td style="padding: 10px; text-align: center;"><strong>⏱️ Tempo</strong><br>{{avg_time_to_hire}} dias</td>
            <td style="padding: 10px; text-align: center;"><strong>💰 Custo</strong><br>R$ {{cost_per_hire}}</td>
        </tr>
    </table>
    
    <h3>🔄 ANÁLISE DO FUNIL</h3>
    <ul>
        <li>Candidatos: {{total_candidates}} (100%)</li>
        <li>Triagem: {{screening_count}} ({{screening_rate}}%)</li>
        <li>Entrevista: {{interview_count}} ({{interview_rate}}%)</li>
        <li>Final: {{final_count}} ({{final_rate}}%)</li>
        <li>Contratados: {{hired_count}} ({{conversion_rate}}%)</li>
    </ul>
    
    <h3>🌐 PERFORMANCE POR CANAL</h3>
    <p>{{channel_performance}}</p>
    
    <h3>🏆 TOP 5 CANDIDATOS</h3>
    <p>{{top_candidates}}</p>
    
    <h3>💰 ANÁLISE DE CUSTOS</h3>
    <ul>
        <li>Orçamento Total: R$ {{total_budget}}</li>
        <li>Gasto: R$ {{spent_budget}}</li>
        <li>Restante: R$ {{remaining_budget}}</li>
    </ul>
    
    <h3>💡 RECOMENDAÇÕES DA LIA</h3>
    <p>{{lia_recommendations}}</p>
</div>
""",
        "variables": ["job_title", "department", "location", "generated_date", "generated_time", "total_candidates", "hired_count", "avg_time_to_hire", "cost_per_hire", "screening_count", "screening_rate", "interview_count", "interview_rate", "final_count", "final_rate", "conversion_rate", "channel_performance", "top_candidates", "total_budget", "spent_budget", "remaining_budget", "lia_recommendations"],
        "trigger_type": "automatic",
        "used_in": ["automation", "reports"],
        "priority": "low",
    },
    # ========================================
    # TEMPLATES DE COMUNICAÇÃO (PT-BR situations)
    # Usados pelo UnifiedCommunicationModal e CloseVacancyModal
    # ========================================
    {
        "situation": "contato_inicial",
        "name": "Contato Inicial",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Oportunidade - {{vaga}}",
        "body_html": """<p>Olá {{candidato_nome}},</p>
<p>Esperamos que esteja bem!</p>
<p>Identificamos seu perfil e gostaríamos de conversar sobre uma excelente oportunidade para a posição de <strong>{{vaga}}</strong>.</p>
<p>Sua experiência e qualificações são muito alinhadas com o que buscamos.</p>
<p>Podemos agendar uma conversa?</p>
<p>Atenciosamente,<br>{{recrutador_nome}}<br>{{empresa_nome}}</p>""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "manual",
        "used_in": ["communication_modal"],
        "priority": "medium",
    },
    {
        "situation": "follow_up",
        "name": "Follow-up",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Acompanhamento - {{vaga}}",
        "body_html": """<p>Olá {{candidato_nome}},</p>
<p>Espero que esteja bem! Gostaria de fazer um acompanhamento sobre sua candidatura para a posição de <strong>{{vaga}}</strong>.</p>
<p>Tem alguma dúvida sobre o processo ou a vaga?</p>
<p>Fico à disposição.</p>
<p>Atenciosamente,<br>{{recrutador_nome}}<br>{{empresa_nome}}</p>""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "manual",
        "used_in": ["communication_modal"],
        "priority": "medium",
    },
    {
        "situation": "triagem",
        "name": "Convite Triagem",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Oportunidade: {{vaga}} — {{empresa_nome}}",
        "body_html": """<html>
<body style="margin:0; padding:0; background-color:#f1f5f9; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">
<table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#f1f5f9;">
<tr><td align="center" style="padding:20px 0;">
<table cellpadding="0" cellspacing="0" border="0" width="600" style="max-width:600px; background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.08);">

<tr><td style="background-color:#1e293b; padding:24px 40px; text-align:center;">
<h1 style="margin:0; color:#ffffff; font-size:20px; font-weight:700; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">{{empresa_nome}}</h1>
</td></tr>

<tr><td style="height:3px; background:linear-gradient(90deg, #0ea5e9, #06b6d4);"></td></tr>

<tr><td style="padding:32px 40px 12px 40px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size:15px; line-height:1.75; color:#334155;">

<p style="margin:0 0 20px 0;">Olá, <strong>{{candidato_nome}}</strong>.</p>

<p style="margin:0 0 16px 0;">Meu nome é <strong>{{recrutador_nome}}</strong> e faço parte do time de recrutamento da <strong>{{empresa_nome}}</strong>. Identificamos seu perfil e gostaríamos de conversar sobre a vaga de <strong>{{vaga}}</strong>.</p>

<p style="margin:0 0 16px 0;">Para dar início ao processo, convidamos você a uma conversa com a <strong>LIA</strong> — nossa assistente de inteligência artificial. É uma etapa breve e assíncrona, criada para que possamos conhecer sua trajetória e expectativas antes de qualquer entrevista formal.</p>

<p style="margin:0 0 6px 0; font-weight:600; color:#1e293b; font-size:16px;">Sobre a conversa</p>

<p style="margin:0 0 16px 0;">A LIA abordará sua experiência, motivações e expectativas em relação à posição. Não há respostas certas ou erradas — o objetivo é simplesmente compreender melhor o seu perfil.</p>

<table cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 20px 0;">
<tr>
<td width="50%" style="padding:8px 8px 8px 0; vertical-align:top;">
<p style="margin:0 0 2px 0; font-weight:600; color:#1e293b; font-size:13px;">Canal</p>
<p style="margin:0; color:#64748b; font-size:13px;">Chat na web ou WhatsApp — texto ou áudio</p>
</td>
<td width="50%" style="padding:8px 0 8px 8px; vertical-align:top;">
<p style="margin:0 0 2px 0; font-weight:600; color:#1e293b; font-size:13px;">Duração</p>
<p style="margin:0; color:#64748b; font-size:13px;">Aproximadamente 15 a 20 minutos</p>
</td>
</tr>
<tr>
<td width="50%" style="padding:8px 8px 8px 0; vertical-align:top;">
<p style="margin:0 0 2px 0; font-weight:600; color:#1e293b; font-size:13px;">Flexibilidade</p>
<p style="margin:0; color:#64748b; font-size:13px;">Assíncrono — pause e retome conforme sua disponibilidade</p>
</td>
<td width="50%" style="padding:8px 0 8px 8px; vertical-align:top;">
<p style="margin:0 0 2px 0; font-weight:600; color:#1e293b; font-size:13px;">Dispositivo</p>
<p style="margin:0; color:#64748b; font-size:13px;">Celular ou computador</p>
</td>
</tr>
</table>

<p style="margin:0 0 6px 0; font-weight:600; color:#1e293b; font-size:16px;">Próximos passos</p>

<p style="margin:0 0 24px 0;">Ao concluir, você receberá um retorno com observações sobre sua participação. As respostas serão analisadas por mim, e darei seguimento com os próximos passos do processo. A decisão final é sempre humana — a LIA existe para tornar o processo mais ágil e equânime para todos os candidatos.</p>

<table cellpadding="0" cellspacing="0" border="0" width="100%">
<tr><td align="center" style="padding:0 0 12px 0;">
<a href="{{screening_link}}" style="background-color:#1e293b; color:#ffffff; padding:14px 40px; text-decoration:none; border-radius:6px; font-weight:600; font-size:15px; display:inline-block; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">Iniciar Conversa</a>
</td></tr>
<tr><td align="center" style="padding:0 0 24px 0;">
<a href="mailto:{{recrutador_email}}?subject=Não tenho interesse — {{vaga}}" style="color:#64748b; font-size:13px; text-decoration:underline; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">Não tenho interesse</a>
</td></tr>
</table>

<p style="margin:0 0 20px 0; color:#64748b; font-size:13px;">Para melhor experiência, escolha um momento tranquilo e verifique sua conexão à internet. Compatível com Chrome, Firefox e Edge.</p>

<p style="margin:0 0 0 0;"><strong>{{recrutador_nome}}</strong><br><span style="color:#64748b;">Recrutador(a) · {{empresa_nome}}</span></p>

</td></tr>

<tr><td style="padding:0 40px;"><table cellpadding="0" cellspacing="0" border="0" width="100%"><tr><td style="border-top:1px solid #e2e8f0;"></td></tr></table></td></tr>

<tr><td style="padding:20px 40px 24px 40px; text-align:center;">
<p style="margin:0 0 4px 0; color:#64748b; font-size:13px; font-weight:600; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">WeDO Talent</p>
<p style="margin:0 0 10px 0; color:#94a3b8; font-size:12px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">Recrutamento mais humano, com inteligência artificial.</p>
<p style="margin:0; color:#cbd5e1; font-size:11px; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;">Ao iniciar, você concorda com o tratamento de seus dados conforme nossa <a href="{{privacy_policy_url}}" style="color:#94a3b8; text-decoration:underline;">Política de Privacidade</a>.</p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome", "recrutador_email", "screening_link", "privacy_policy_url"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "medium",
    },
    {
        "situation": "agendamento",
        "name": "Convite Entrevista",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Convite para Entrevista - {{vaga}}",
        "body_html": """<p>Olá {{candidato_nome}},</p>
<p>Parabéns por avançar no processo seletivo para <strong>{{vaga}}</strong>! 🎉</p>
<p>Gostaríamos de convidá-lo(a) para a próxima etapa: uma entrevista.</p>
<p><strong>📅 Detalhes da Entrevista:</strong></p>
<ul>
<li>Tipo: Entrevista</li>
<li>Duração estimada: 30-45 minutos</li>
</ul>
<p>Após a confirmação, você receberá:</p>
<ul>
<li>✅ Email de confirmação com todos os detalhes</li>
<li>✅ Convite do calendário</li>
<li>✅ Link da plataforma de vídeo (se aplicável)</li>
</ul>
<p>Qualquer dúvida, estamos à disposição!</p>
<p>Atenciosamente,<br>{{recrutador_nome}}<br>{{empresa_nome}}</p>""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "high",
    },
    {
        "situation": "feedback_positivo",
        "name": "Feedback Positivo",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Atualização - Processo Seletivo {{vaga}}",
        "body_html": """<p>Olá {{candidato_nome}},</p>
<p>Esperamos que esteja bem!</p>
<p>Temos uma ótima notícia: você foi <strong>aprovado(a)</strong> na etapa atual do processo seletivo para <strong>{{vaga}}</strong>!</p>
<p>Em breve entraremos em contato com os próximos passos.</p>
<p>Parabéns pelo excelente desempenho!</p>
<p>Atenciosamente,<br>{{recrutador_nome}}<br>{{empresa_nome}}</p>""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "manual",
        "used_in": ["communication_modal", "close_vacancy_modal"],
        "priority": "high",
    },
    {
        "situation": "feedback_construtivo",
        "name": "Feedback Construtivo",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Atualização sobre sua candidatura - {{vaga}}",
        "body_html": """<p>Olá {{candidato_nome}},</p>
<p>Esperamos que esteja bem.</p>
<p>Agradecemos seu interesse na posição de <strong>{{vaga}}</strong> e o tempo dedicado ao nosso processo seletivo.</p>
<p>Após cuidadosa análise, decidimos seguir com outros candidatos cujos perfis estão mais alinhados com as necessidades específicas desta posição no momento.</p>
<p>Esta decisão não diminui o valor de suas qualificações. O mercado é dinâmico e novas oportunidades surgem constantemente.</p>
<p>Manteremos seu perfil em nosso banco de talentos para futuras oportunidades.</p>
<p>Desejamos sucesso em sua jornada profissional!</p>
<p>Atenciosamente,<br>{{recrutador_nome}}<br>{{empresa_nome}}</p>""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "manual",
        "used_in": ["communication_modal", "close_vacancy_modal"],
        "priority": "high",
    },
    {
        "situation": "proposta",
        "name": "Proposta de Trabalho",
        "channel": CHANNEL_EMAIL,
        "category": "offers",
        "subject": "Proposta de Trabalho - {{vaga}}",
        "body_html": """<p>Olá {{candidato_nome}},</p>
<p>Parabéns! 🎉</p>
<p>Após passar por todas as etapas do processo seletivo, temos o prazer de formalizar nossa <strong>proposta de trabalho</strong> para a posição de <strong>{{vaga}}</strong>.</p>
<p>Você demonstrou competências e valores alinhados com nossa cultura organizacional.</p>
<p>Os detalhes da proposta serão enviados em anexo ou discutidos em nossa próxima conversa.</p>
<p>Estamos muito animados com a possibilidade de tê-lo(a) em nossa equipe!</p>
<p>Atenciosamente,<br>{{recrutador_nome}}<br>{{empresa_nome}}</p>""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "manual",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "high",
    },
    {
        "situation": "proposta_aceita",
        "name": "Proposta Aceita - Parabéns",
        "channel": CHANNEL_EMAIL,
        "category": "offers",
        "subject": "Bem-vindo(a) à equipe! 🎉 - {{vaga}}",
        "body_html": """<p>Olá {{candidato_nome}},</p>
<p>É com grande alegria que confirmamos: você agora faz parte da nossa equipe! 🎉</p>
<p>Estamos muito felizes com sua aceitação da proposta para a posição de <strong>{{vaga}}</strong>.</p>
<p>Em breve você receberá todas as informações sobre:</p>
<ul>
<li>📅 Data de início</li>
<li>📋 Documentação necessária</li>
<li>👋 Processo de onboarding</li>
</ul>
<p>Seja bem-vindo(a)!</p>
<p>Atenciosamente,<br>{{recrutador_nome}}<br>{{empresa_nome}}</p>""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome", "data_inicio"],
        "trigger_type": "manual",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "high",
    },
    {
        "situation": "vaga_fechada",
        "name": "Vaga Encerrada",
        "channel": CHANNEL_EMAIL,
        "category": "candidates",
        "subject": "Atualização sobre o processo seletivo - {{vaga}}",
        "body_html": """<p>Olá {{candidato_nome}},</p>
<p>Esperamos que esteja bem.</p>
<p>Gostaríamos de informar que o processo seletivo para a posição de <strong>{{vaga}}</strong> foi encerrado.</p>
<p>Agradecemos seu interesse e participação. Seu perfil ficará em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades compatíveis.</p>
<p>Desejamos sucesso em sua jornada profissional!</p>
<p>Atenciosamente,<br>{{recrutador_nome}}<br>{{empresa_nome}}</p>""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "automatic",
        "used_in": ["close_vacancy_modal", "automation"],
        "priority": "high",
    },
    # WhatsApp versions
    {
        "situation": "contato_inicial",
        "name": "Contato Inicial (WhatsApp)",
        "channel": CHANNEL_WHATSAPP,
        "category": "candidates",
        "subject": "",
        "body_html": """Olá {{candidato_nome}}! 👋

Sou {{recrutador_nome}} da {{empresa_nome}}.

Encontrei seu perfil e gostaria de conversar sobre uma oportunidade para *{{vaga}}*.

Posso te contar mais sobre a posição?""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "manual",
        "used_in": ["communication_modal"],
        "priority": "medium",
    },
    {
        "situation": "triagem",
        "name": "Convite Triagem (WhatsApp)",
        "channel": CHANNEL_WHATSAPP,
        "category": "candidates",
        "subject": "",
        "body_html": """Olá {{candidato_nome}}, tudo bem?

Meu nome é {{recrutador_nome}}, do time de recrutamento da *{{empresa_nome}}*. Identificamos seu perfil e gostaríamos de conversar sobre a vaga de *{{vaga}}*.

Para dar início, convidamos você a uma conversa com a *LIA* — nossa assistente de inteligência artificial. É uma etapa breve e assíncrona, criada para conhecer sua trajetória e expectativas antes de qualquer entrevista formal.

📋 *Sobre a conversa:*
• Canal: aqui pelo WhatsApp mesmo — texto ou áudio
• Duração: ~15 a 20 minutos
• Flexibilidade: assíncrono — pause e retome quando quiser
• Dispositivo: celular ou computador

Ao concluir, você receberá um retorno sobre sua participação. A decisão final é sempre humana — a LIA existe para tornar o processo mais ágil e equânime.

Ao continuar, você concorda com o tratamento de seus dados conforme nossa Política de Privacidade em {{privacy_policy_url}}.

Responda *INICIAR* para começar ou *NÃO* se não tiver interesse.

{{recrutador_nome}} · {{empresa_nome}}""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome", "privacy_policy_url"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "medium",
    },
    {
        "situation": "agendamento",
        "name": "Convite Entrevista (WhatsApp)",
        "channel": CHANNEL_WHATSAPP,
        "category": "candidates",
        "subject": "",
        "body_html": """Olá {{candidato_nome}}! 🎉

Parabéns por avançar no processo para *{{vaga}}*!

Gostaríamos de agendar sua entrevista.

Qual sua disponibilidade nos próximos dias?

{{recrutador_nome}} - {{empresa_nome}}""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "both",
        "used_in": ["communication_modal", "pipeline_transition"],
        "priority": "high",
    },
    {
        "situation": "feedback_construtivo",
        "name": "Feedback Construtivo (WhatsApp)",
        "channel": CHANNEL_WHATSAPP,
        "category": "candidates",
        "subject": "",
        "body_html": """Olá {{candidato_nome}},

Obrigado por participar do processo para *{{vaga}}*.

Após análise, decidimos seguir com outros candidatos neste momento.

Seu perfil fica em nosso banco de talentos para futuras oportunidades.

Desejamos sucesso! 🍀

{{recrutador_nome}} - {{empresa_nome}}""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "manual",
        "used_in": ["communication_modal", "close_vacancy_modal"],
        "priority": "high",
    },
    {
        "situation": "vaga_fechada",
        "name": "Vaga Encerrada (WhatsApp)",
        "channel": CHANNEL_WHATSAPP,
        "category": "candidates",
        "subject": "",
        "body_html": """Olá {{candidato_nome}},

O processo seletivo para *{{vaga}}* foi encerrado.

Agradecemos sua participação! Seu perfil fica em nosso banco de talentos.

Sucesso na sua jornada! 🍀

{{recrutador_nome}} - {{empresa_nome}}""",
        "variables": ["candidato_nome", "vaga", "empresa_nome", "recrutador_nome"],
        "trigger_type": "automatic",
        "used_in": ["close_vacancy_modal", "automation"],
        "priority": "high",
    },
    # ========================================
    # TEMPLATES DE COMPARTILHAMENTO COM GESTOR
    # ========================================
    {
        "situation": "share_with_manager",
        "name": "Compartilhamento com Gestor",
        "channel": CHANNEL_EMAIL,
        "category": "sharing",
        "subject": "{{recruiter_name}} compartilhou candidatos para {{job_title}}",
        "body_html": """<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f9fafb; margin: 0; padding: 0;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
        <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); padding: 30px; text-align: center;">
            <h1 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: 600;">Candidatos Compartilhados</h1>
        </div>
        <div style="padding: 30px;">
            <p>Olá,</p>
            <p><strong>{{recruiter_name}}</strong> da <strong>{{company_name}}</strong> compartilhou <strong>{{candidate_count}} candidato(s)</strong> para a posição de <strong>{{job_title}}</strong> com você.</p>

            <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1f2937;">Mensagem do Recrutador:</h3>
                <p style="margin-bottom: 0;">{{message}}</p>
            </div>

            <div style="background-color: #eff6ff; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb;">
                <p style="margin: 0;"><strong>Código de Acesso (OTP):</strong> {{otp_code}}</p>
                <p style="margin: 5px 0 0 0; font-size: 13px; color: #6b7280;">Válido até {{expiry_date}}</p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{{share_link}}" style="background-color: #2563eb; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    Acessar Candidatos
                </a>
            </div>

            <p style="color: #6b7280; font-size: 13px;">Use o código OTP acima ao acessar o link para verificar sua identidade.</p>
        </div>
        <div style="background-color: #f9fafb; padding: 20px 30px; text-align: center; border-top: 1px solid #e5e7eb;">
            <p style="margin: 0; color: #9ca3af; font-size: 12px;">Este é um email automático enviado pela plataforma WEDOTALENT.</p>
        </div>
    </div>
</body>
</html>""",
        "variables": ["recruiter_name", "job_title", "candidate_count", "share_link", "otp_code", "expiry_date", "message", "company_name"],
        "trigger_type": "manual",
        "used_in": ["share_search_modal"],
        "priority": "high",
    },
    {
        "situation": "share_with_manager",
        "name": "Compartilhamento com Gestor (WhatsApp)",
        "channel": CHANNEL_WHATSAPP,
        "category": "sharing",
        "subject": "",
        "body_html": """Olá! 👋

*{{recruiter_name}}* da *{{company_name}}* compartilhou *{{candidate_count}} candidato(s)* para a vaga de *{{job_title}}* com você.

{{message}}

🔗 Acesse os candidatos:
{{share_link}}

🔑 Código de acesso: *{{otp_code}}*
📅 Válido até: {{expiry_date}}""",
        "variables": ["recruiter_name", "job_title", "candidate_count", "share_link", "otp_code", "expiry_date", "message", "company_name"],
        "trigger_type": "manual",
        "used_in": ["share_search_modal"],
        "priority": "high",
    },
]


def determine_template_visibility(template_data: dict[str, Any]) -> str:
    """
    Determine template visibility based on channel, category, and name.
    
    Returns:
        'admin' - For system templates, alerts, reports, internal notifications
        'recruiter' - For candidate communication templates
        'all' - For templates usable by both
    """
    channel = template_data.get("channel", "")
    category = template_data.get("category", "")
    name = template_data.get("name", "")
    
    if channel in [CHANNEL_BELL, CHANNEL_TEAMS, CHANNEL_BRIEFING, CHANNEL_PARECER, CHANNEL_REPORT]:
        return "admin"
    
    if category in ["alerts", "reports", "workflow", "integrations", "billing", "onboarding", "briefings", "parecer", "workforce"]:
        return "admin"
    
    admin_template_names = [
        "Meta em Risco", "Meta Não Atingida", "SLA Violado", "Aprovação Pendente",
        "Aprovação Expirada", "Alerta No-Show", "Variância Workforce", "Alerta Crítico",
        "Performance Semanal", "Relatório Mensal", "Resumo Semanal", "Relatório de Equipe",
        "Relatório Executivo da Vaga", "Sync ATS Falhou", "Créditos Baixos",
        "Boas-vindas Usuário", "Briefing Diário", "Resumo de Fim de Dia",
        "Parecer Resumido", "Parecer Completo", "Vaga Pausada", "Vaga Reativada",
        "Triagem Concluída", "Alerta Crítico via Teams", "Triagem Concluída via Teams"
    ]
    
    if name in admin_template_names:
        return "admin"
    
    recruiter_template_names = [
        "Primeiro Contato", "Contato Inicial", "Follow-up", "Convite Triagem",
        "Convite Entrevista", "Feedback Positivo", "Feedback Construtivo",
        "Proposta de Trabalho", "Proposta Aceita", "Proposta Recusada",
        "Vaga Encerrada", "Lembrete de Triagem", "Lembrete de Entrevista",
        "Entrevista Agendada", "Aprovação na Triagem", "Rejeição na Triagem",
        "Rejeição Pós-Entrevista", "Processo Encerrado",
        "Contato Inicial (WhatsApp)", "Convite Triagem (WhatsApp)",
        "Convite Entrevista (WhatsApp)", "Feedback Construtivo (WhatsApp)",
        "Vaga Encerrada (WhatsApp)", "Lembrete de Triagem (WhatsApp)",
        "Lembrete de Entrevista (WhatsApp)", "Screening Invite",
        "Screening Reminder", "Interview Reminder",
        "Compartilhamento com Gestor", "Compartilhamento com Gestor (WhatsApp)"
    ]
    
    if name in recruiter_template_names:
        return "recruiter"
    
    if category == "candidates" and channel in [CHANNEL_EMAIL, CHANNEL_WHATSAPP]:
        return "recruiter"
    
    if category in ["offers", "sharing"]:
        return "recruiter"
    
    return "recruiter"


async def seed_default_templates(db: AsyncSession) -> dict[str, Any]:
    """
    Seed default system templates.
    Creates templates with company_id=NULL and is_system_template=True.
    
    Returns:
        Dict with created count and list of template names
    """
    created_templates = []
    skipped_templates = []
    
    for template_data in DEFAULT_TEMPLATES:
        existing = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.situation == template_data["situation"],
                EmailTemplate.channel == template_data["channel"],
                EmailTemplate.is_system_template == True,
                EmailTemplate.company_id.is_(None)
            )
        )
        existing_template = existing.scalar_one_or_none()
        
        if existing_template:
            skipped_templates.append(template_data["name"])
            continue
        
        visibility = determine_template_visibility(template_data)
        
        template = EmailTemplate(
            id=uuid.uuid4(),
            name=template_data["name"],
            subject=template_data.get("subject"),
            body_html=template_data["body_html"].strip(),
            body_text=None,
            category=template_data.get("category"),
            channel=template_data["channel"],
            situation=template_data["situation"],
            variables=template_data.get("variables", []),
            trigger_type=template_data.get("trigger_type", "manual"),
            used_in=template_data.get("used_in", []),
            priority=template_data.get("priority", "medium"),
            is_active=True,
            company_id=None,
            is_system_template=True,
            visibility=visibility,
            version=1,
            created_by="system",
        )
        
        db.add(template)
        created_templates.append(template_data["name"])
    
    await db.commit()
    
    logger.info(f"Template seeder: Created {len(created_templates)} templates, skipped {len(skipped_templates)}")
    
    return {
        "created": len(created_templates),
        "skipped": len(skipped_templates),
        "created_templates": created_templates,
        "skipped_templates": skipped_templates,
    }


async def clone_templates_for_client(db: AsyncSession, client_id: str, auto_commit: bool = True) -> dict[str, Any]:
    """
    Clone all system templates for a new client.
    
    Works with the provided session and can optionally skip commit to allow
    the caller to control the transaction.
    
    Args:
        db: Database session (existing session, works within caller's transaction)
        client_id: The company_id for the new client
        auto_commit: If True (default), commits after cloning. Set to False to let caller control transaction.
        
    Returns:
        Dict with count of cloned templates
        
    Raises:
        Any database errors are propagated to the caller (not swallowed)
    """
    result = await db.execute(
        select(EmailTemplate).where(
            EmailTemplate.is_system_template == True,
            EmailTemplate.company_id.is_(None),
            EmailTemplate.is_active == True
        )
    )
    system_templates = result.scalars().all()
    
    cloned_templates = []
    
    for template in system_templates:
        existing = await db.execute(
            select(EmailTemplate).where(
                EmailTemplate.company_id == client_id,
                EmailTemplate.situation == template.situation,
                EmailTemplate.channel == template.channel
            )
        )
        if existing.scalar_one_or_none():
            continue
        
        cloned = EmailTemplate(
            id=uuid.uuid4(),
            name=template.name,
            subject=template.subject,
            body_html=template.body_html,
            body_text=template.body_text,
            category=template.category,
            channel=template.channel,
            situation=template.situation,
            variables=template.variables,
            is_active=True,
            company_id=client_id,
            is_system_template=False,
            visibility=template.visibility,
            origin_template_id=template.id,
            version=1,
            created_by="system_clone",
        )
        
        db.add(cloned)
        cloned_templates.append(template.name)
    
    if auto_commit:
        await db.commit()
    
    logger.info(f"Cloned {len(cloned_templates)} templates for client {client_id}")
    
    return {
        "client_id": client_id,
        "cloned_count": len(cloned_templates),
        "cloned_templates": cloned_templates,
    }
