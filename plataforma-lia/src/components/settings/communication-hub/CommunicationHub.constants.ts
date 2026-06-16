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

