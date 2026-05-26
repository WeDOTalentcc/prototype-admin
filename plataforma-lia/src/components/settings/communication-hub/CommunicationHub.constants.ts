import type { AlertConfig, EmailTemplate } from './CommunicationHub.types'

export const TEMPLATE_GROUPS: Record<string, { label: string; icon: string; situations: string[] }> = {
  'primeiro_contato': { label: 'Primeiro Contato', icon: '👋', situations: ['contato_inicial', 'follow_up', 'initial_contact', 'contato_rapido'] },
  'triagem': { label: 'Triagem', icon: '📋', situations: ['triagem', 'screening_reminder', 'screening_passed', 'screening_failed', 'screening_completed', 'lembrete'] },
  'entrevista': { label: 'Entrevista', icon: '🎤', situations: ['agendamento', 'interview_scheduled', 'interview_reminder', 'rejection_post_interview'] },
  'feedback': { label: 'Feedback', icon: '💬', situations: ['feedback_positivo', 'feedback_construtivo'] },
  'proposta': { label: 'Proposta', icon: '📝', situations: ['proposta', 'proposta_aceita', 'offer_accepted', 'offer_rejected'] },
  'encerramento': { label: 'Encerramento', icon: '✅', situations: ['vaga_fechada', 'process_closed', 'job_paused', 'job_reactivated'] },
  'alertas': { label: 'Alertas', icon: '🔔', situations: ['critical_alert', 'sla_violated', 'no_show_alert', 'approval_pending', 'approval_expired', 'ats_sync_failed', 'credits_low'] },
  'relatorios': { label: 'Relatórios', icon: '📊', situations: ['briefing', 'end_of_day_summary', 'weekly_summary', 'monthly_summary', 'monthly_report', 'team_report', 'job_executive_report', 'weekly_performance', 'goal_at_risk', 'goal_missed'] },
  'outros': { label: 'Outros', icon: '📌', situations: [] }
}

export const TRIGGER_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  'automatic': { label: 'Automático', color: 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary' },
  'manual': { label: 'Manual', color: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' },
  'both': { label: 'Ambos', color: 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary' }
}

export const PRIORITY_COLORS: Record<string, string> = {
  'high': 'bg-status-error',
  'medium': 'bg-status-warning',
  'low': 'bg-lia-border-medium'
}

export const CATEGORY_LABELS: Record<string, { label: string; color: string }> = {
  approval: { label: 'Aprovação', color: 'bg-status-success/10 text-status-success dark:bg-status-success/20 dark:text-status-success' },
  rejection: { label: 'Rejeição', color: 'bg-status-error/10 text-status-error dark:bg-status-error/20 dark:text-status-error' },
  scheduling: { label: 'Agendamento', color: 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary' },
  followup: { label: 'Follow-up', color: 'bg-status-warning/10 text-status-warning dark:bg-status-warning/20 dark:text-status-warning' },
  feedback: { label: 'Feedback', color: 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary' }
}

/**
 * @deprecated Sprint 3 F6 (2026-05-21) — usar useAlertRuleTemplates hook canonical.
 *
 * Status: PRESERVADO como fallback transitorio (seed durante loading do hook
 * canonical). Hook tem isLoading state; usuario nao deve ver catalogo vazio
 * durante fetch inicial. Quando hook resolve, substitui este seed pelos
 * items per-tenant (ver useCommunicationHub.ts:47).
 *
 * Decisao F6 2026-05-21: NAO deletar agora. Runtime warning abaixo informa
 * status deprecated quando arquivo eh importado em dev mode.
 *
 * Migracao canonical: src/hooks/communication/use-alert-rule-templates.ts
 * + flattenTemplates() para shape AlertConfig.
 *
 * Para criar templates per-tenant via wizard agent:
 *   tool: create_custom_alert_rule_template (communication agent)
 *   ou POST /api/backend-proxy/alert-rule-templates
 */

// Sprint 3 F6: runtime deprecation warning (dev only — silenciado em prod
// para evitar noise nos logs). Fire-once via module-scope IIFE.
let _deprecationWarningEmitted = false
function _warnDeprecation() {
  if (_deprecationWarningEmitted) return
  _deprecationWarningEmitted = true
  if (typeof process !== 'undefined' && process.env?.NODE_ENV !== 'production') {
     
    console.warn(
      '[DEPRECATED Sprint 3 F6] DEFAULT_ALERTS hardcoded — ' +
      'usar useAlertRuleTemplates() canonical per-tenant. ' +
      'Fallback preservado apenas como seed durante loading.'
    )
  }
}
_warnDeprecation()

export const DEFAULT_ALERTS: AlertConfig[] = [
  { id: '1', name: 'SLA Próximo do Vencimento', description: 'Alerta quando um candidato está há 80% do SLA na mesma etapa', enabled: true, channel: 'both' },
  { id: '2', name: 'Meta Mensal em Risco', description: 'Notifica quando a meta de contratações do mês pode não ser atingida', enabled: true, channel: 'email' },
  { id: '3', name: 'Candidato Sem Interação', description: 'Alerta para candidatos sem contato há mais de 5 dias', enabled: true, channel: 'teams' },
  { id: '4', name: 'Entrevista Não Confirmada', description: 'Lembrete 24h antes de entrevistas sem confirmação', enabled: true, channel: 'both' },
  { id: '5', name: 'Feedback Pendente', description: 'Solicita feedback após 48h de entrevista realizada', enabled: false, channel: 'email' }
]

export const DEFAULT_TEMPLATES: EmailTemplate[] = [
  // Email Templates
  {
    id: '1',
    name: 'Contato Inicial (Email)',
    category: 'followup',
    subject: 'Oportunidade - {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

Identificamos seu perfil e gostaríamos de conversar sobre uma excelente oportunidade para a posição de {{vaga}}.

Sua experiência e qualificações são muito alinhadas com o que buscamos.

Podemos agendar uma conversa?

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'contato_inicial',
    trigger_type: 'manual',
    used_in: ['Sourcing', 'Pipeline'],
    priority: 'high'
  },
  {
    id: '2',
    name: 'Follow-up (Email)',
    category: 'followup',
    subject: 'Acompanhamento - {{vaga}}',
    body: `Olá {{candidato_nome}},

Espero que esteja bem! Gostaria de fazer um acompanhamento sobre sua candidatura para a posição de {{vaga}}.

Tem alguma dúvida sobre o processo ou a vaga?

Fico à disposição.

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'follow_up',
    trigger_type: 'automatic',
    used_in: ['Pipeline'],
    priority: 'medium'
  },
  {
    id: '3',
    name: 'Convite Triagem (Email)',
    category: 'scheduling',
    subject: 'Próximo passo: Avaliação - {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

Estamos avançando em nosso processo seletivo para a posição de {{vaga}} e gostaríamos de convidá-lo(a) para a próxima etapa: uma triagem rápida com a nossa assistente LIA.

📋 Sobre a triagem:
• Duração estimada: 15-20 minutos
• Formato: Conversa por chat ou WhatsApp com a LIA
• Objetivo: Conhecer melhor sua forma de pensar e resolver problemas

🔗 Para iniciar, escolha uma das opções:
• INICIAR VIA CHAT WEB - Clique aqui para conversar pelo navegador
• INICIAR VIA WHATSAPP - Clique aqui para conversar pelo WhatsApp

⚠️ Ao iniciar, você será apresentado aos termos de uso e política de privacidade (LGPD).

Essa avaliação nos ajuda a entender melhor seu perfil e garantir que a vaga seja compatível com suas habilidades e expectativas.

Qualquer dúvida, estamos à disposição!

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome', 'link_triagem', 'duracao_triagem'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'triagem',
    trigger_type: 'automatic',
    used_in: ['Triagem Automática', 'Pipeline'],
    priority: 'high'
  },
  {
    id: '4',
    name: 'Convite Entrevista (Email)',
    category: 'scheduling',
    subject: 'Convite para Entrevista - {{vaga}}',
    body: `Olá {{candidato_nome}},

Parabéns por avançar no processo seletivo para {{vaga}}! 🎉

Gostaríamos de convidá-lo(a) para a próxima etapa: uma entrevista {{formato_entrevista}}.

📅 Detalhes da Entrevista:
• Tipo: Entrevista {{formato_entrevista}}
• Duração: {{duracao_entrevista}} minutos
• Plataforma: {{link_entrevista}}
• Entrevistador: {{entrevistador_nome}}

🗓️ Escolha o melhor horário:
Clique no link abaixo para visualizar as disponibilidades e escolher o horário que melhor funciona para você:

{{link_calendario}}

Após a confirmação, você receberá:
✅ Email de confirmação com todos os detalhes
✅ Convite do Outlook/Google Calendar
✅ Link da plataforma de vídeo (se aplicável)

Qualquer dúvida, estamos à disposição!

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'formato_entrevista', 'duracao_entrevista', 'entrevistador_nome', 'link_entrevista', 'link_calendario', 'data_entrevista', 'horario_entrevista'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'agendamento',
    trigger_type: 'both',
    used_in: ['Agendamento', 'Calendário'],
    priority: 'high'
  },
  {
    id: '5',
    name: 'Feedback Positivo (Email)',
    category: 'feedback',
    subject: 'Atualização - Processo Seletivo {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

É com grande satisfação que compartilhamos o feedback sobre sua participação no processo seletivo para {{vaga}}.

✅ Pontos Positivos:
• Sua experiência e conhecimento técnico impressionaram nossa equipe
• Demonstrou excelente comunicação e clareza nas respostas
• Alinhamento com os valores e cultura da empresa

📈 Próximos Passos:
{{proximos_passos}}

Agradecemos seu interesse e dedicação ao processo!

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'pontos_positivos', 'proximos_passos', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'feedback_positivo',
    trigger_type: 'manual',
    used_in: ['Entrevistas', 'Feedback'],
    priority: 'medium'
  },
  {
    id: '6',
    name: 'Feedback Construtivo (Email)',
    category: 'feedback',
    subject: 'Retorno - Processo Seletivo {{vaga}}',
    body: `Olá {{candidato_nome}},

Agradecemos sua participação no processo seletivo para {{vaga}}.

Gostaríamos de compartilhar nosso feedback:

📝 Observações:
{{areas_desenvolvimento}}

Agradecemos seu tempo e interesse. Mantemos seu perfil em nosso banco de talentos para futuras oportunidades que sejam mais alinhadas com seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
Equipe de Recrutamento`,
    variables: ['candidato_nome', 'vaga', 'areas_desenvolvimento', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'email',
    situation: 'feedback_construtivo',
    trigger_type: 'manual',
    used_in: ['Rejeição', 'Feedback'],
    priority: 'low'
  },
  // WhatsApp Templates
  {
    id: '7',
    name: 'Contato Rápido (WhatsApp)',
    category: 'followup',
    subject: '',
    body: `Olá {{candidato_nome}}! 👋

Sou da equipe de recrutamento. Temos uma oportunidade que pode interessar você.

Podemos conversar? 😊`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'whatsapp',
    situation: 'contato_rapido',
    trigger_type: 'manual',
    used_in: ['Sourcing', 'WhatsApp'],
    priority: 'high'
  },
  {
    id: '8',
    name: 'Lembrete (WhatsApp)',
    category: 'followup',
    subject: '',
    body: `Olá {{candidato_nome}}! 📅

Passando para confirmar nossa conversa de hoje.

Nos vemos em breve! 🚀`,
    variables: ['candidato_nome', 'vaga'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'whatsapp',
    situation: 'lembrete',
    trigger_type: 'automatic',
    used_in: ['Agendamento', 'Lembretes'],
    priority: 'medium'
  },
  {
    id: '9',
    name: 'Convite Triagem (WhatsApp)',
    category: 'scheduling',
    subject: '',
    body: `Olá {{candidato_nome}}! 👋

Esperamos que esteja bem!

Estamos avançando no processo seletivo para {{vaga}} e gostaríamos de convidá-lo(a) para uma triagem rápida.

📋 *Sobre a triagem:*
• Duração: 15-20 min
• Formato: Conversa com a LIA, nossa assistente

⚠️ *Aviso LGPD*
Antes de iniciar, você receberá informações sobre como seus dados serão tratados e os termos de uso do processo.

Podemos começar? Ao confirmar, a LIA iniciará a conversa! 🎯

Responda "SIM" para começar 😊`,
    variables: ['candidato_nome', 'vaga', 'link_triagem'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'whatsapp',
    situation: 'triagem',
    trigger_type: 'automatic',
    used_in: ['Triagem', 'WhatsApp'],
    priority: 'high'
  },
  {
    id: '10',
    name: 'Convite Entrevista (WhatsApp)',
    category: 'scheduling',
    subject: '',
    body: `Olá {{candidato_nome}}! 🎉

Parabéns por avançar no processo seletivo para {{vaga}}!

Gostaríamos de agendar uma entrevista {{formato_entrevista}} com você.

📅 *Detalhes:*
• Duração: {{duracao_entrevista}} min
• Formato: {{link_entrevista}}

🗓️ *Escolha seu horário preferido:*
A LIA vai te mostrar as opções disponíveis!

✅ Após confirmar:
• Você receberá email de confirmação
• Convite para calendário
• Link da videochamada

Vamos agendar? 😊`,
    variables: ['candidato_nome', 'vaga', 'formato_entrevista', 'duracao_entrevista', 'link_entrevista'],
    isActive: true,
    lastUpdated: '2025-01-01',
    channel: 'whatsapp',
    situation: 'agendamento',
    trigger_type: 'both',
    used_in: ['Agendamento', 'WhatsApp'],
    priority: 'high'
  }
]
