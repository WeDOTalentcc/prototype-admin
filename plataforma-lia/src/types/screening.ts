export type ScreeningStatus = 'not_configured' | 'not_started' | 'active' | 'paused' | 'completed'

export const SCREENING_STATUS_LABELS: Record<ScreeningStatus, string> = {
  not_configured: 'Configurar',
  not_started: 'Iniciar',
  active: 'Ativa',
  paused: 'Pausada',
  completed: 'Concluída',
}
