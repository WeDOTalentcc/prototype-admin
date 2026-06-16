// Shared constants for goals planning workforce subsection.
// Consumed by useGoalsPlanningHub hook + WorkforceHubContent + WorkforceSection.
// (Original GoalsPlanningHub.tsx component foi deletado 2026-05-26 como dead code;
// constants extraidas viraram canonical pra hook funcional.)

export interface AlertConfig {
  id: string
  name: string
  description: string
  enabled: boolean
  channel: 'email' | 'teams' | 'both'
}

export const DEFAULT_ALERTS: AlertConfig[] = [
  { id: '1', name: 'SLA Próximo do Vencimento', description: 'Alerta quando um candidato está há 80% do SLA na mesma etapa', enabled: true, channel: 'both' },
  { id: '2', name: 'Meta Mensal em Risco', description: 'Notifica quando a meta de contratações do mês pode não ser atingida', enabled: true, channel: 'email' },
  { id: '3', name: 'Candidato Sem Interação', description: 'Alerta para candidatos sem contato há mais de 5 dias', enabled: true, channel: 'teams' },
  { id: '4', name: 'Entrevista Não Confirmada', description: 'Lembrete 24h antes de entrevistas sem confirmação', enabled: true, channel: 'both' },
  { id: '5', name: 'Feedback Pendente', description: 'Solicita feedback após 48h de entrevista realizada', enabled: false, channel: 'email' },
]

export interface WorkforceEntry {
  month: string
  department: string
  planned: number
  actual: number
  aiSuggestion?: number
}

export const MOCK_WORKFORCE: WorkforceEntry[] = [
  { month: 'Jan', department: 'Tecnologia', planned: 5, actual: 4, aiSuggestion: 6 },
  { month: 'Fev', department: 'Tecnologia', planned: 4, actual: 5 },
  { month: 'Mar', department: 'Tecnologia', planned: 6, actual: 0, aiSuggestion: 5 },
  { month: 'Jan', department: 'Comercial', planned: 3, actual: 3 },
  { month: 'Fev', department: 'Comercial', planned: 2, actual: 2 },
  { month: 'Mar', department: 'Comercial', planned: 4, actual: 0, aiSuggestion: 3 },
  { month: 'Jan', department: 'RH', planned: 1, actual: 1 },
  { month: 'Fev', department: 'RH', planned: 1, actual: 0 },
  { month: 'Mar', department: 'RH', planned: 2, actual: 0, aiSuggestion: 1 },
]

export const DEPARTMENT_NAMES = ['Tecnologia', 'Comercial', 'RH', 'Financeiro', 'Marketing']
export const MONTH_LABELS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

export interface MonthlyPlanning {
  jan: number; feb: number; mar: number; apr: number; may: number; jun: number
  jul: number; aug: number; sep: number; oct: number; nov: number; dec: number
}

export interface Position {
  id: string
  name: string
  salary_min?: number
  salary_max?: number
  monthlyPlanned: MonthlyPlanning
}

export interface DepartmentData {
  id: string
  name: string
  positions: Position[]
  expanded: boolean
}

const EMPTY_MONTHLY: MonthlyPlanning = { jan: 0, feb: 0, mar: 0, apr: 0, may: 0, jun: 0, jul: 0, aug: 0, sep: 0, oct: 0, nov: 0, dec: 0 }

export const INITIAL_DEPARTMENTS: DepartmentData[] = [
  { id: '1', name: 'Tecnologia', positions: [
    { id: '1a', name: 'Backend Developer', salary_min: 8000, salary_max: 15000, monthlyPlanned: { ...EMPTY_MONTHLY, jan: 1, feb: 1, apr: 1, jun: 1, sep: 1 } },
    { id: '1b', name: 'Frontend Developer', salary_min: 7000, salary_max: 14000, monthlyPlanned: { ...EMPTY_MONTHLY, feb: 1, may: 1, aug: 1 } }
  ], expanded: true },
  { id: '2', name: 'Comercial', positions: [
    { id: '2a', name: 'Account Executive', salary_min: 6000, salary_max: 12000, monthlyPlanned: { ...EMPTY_MONTHLY, jan: 1, mar: 1, jun: 1 } }
  ], expanded: true },
  { id: '3', name: 'RH', positions: [
    { id: '3a', name: 'Recrutador', salary_min: 4000, salary_max: 8000, monthlyPlanned: { ...EMPTY_MONTHLY, mar: 1, sep: 1 } }
  ], expanded: false },
  { id: '4', name: 'Financeiro', positions: [
    { id: '4a', name: 'Controller', salary_min: 12000, salary_max: 20000, monthlyPlanned: { ...EMPTY_MONTHLY, may: 1 } }
  ], expanded: false }
]
