export interface GoalTemplate {
  id: string
  name: string
  description: string
  formula: string
  category: 'recruitment' | 'quality' | 'efficiency' | 'satisfaction'
  defaultTarget: number
  unit: string
  period: 'monthly' | 'quarterly' | 'yearly'
  isActive: boolean
}

export interface UserGoal {
  id: string
  userId: string
  templateId: string
  name: string
  description: string
  target: number
  current: number
  unit: string
  period: 'monthly' | 'quarterly' | 'yearly'
  startDate: string
  endDate: string
  status: 'pending' | 'in_progress' | 'achieved' | 'overdue'
  progress: number
  category: 'recruitment' | 'quality' | 'efficiency' | 'satisfaction'
  isCustom: boolean
}

export interface MonthlyGoalValue {
  userId: string
  templateId: string
  month: number
  year: number
  target: number
  current: number
}

export interface CustomGoalForm {
  name: string
  description: string
  target: number
  unit: string
  period: 'monthly' | 'quarterly' | 'yearly'
  category: 'recruitment' | 'quality' | 'efficiency' | 'satisfaction'
  startDate: string
  endDate: string
  userId: string
}

export interface GoalsUser {
  id: string
  name: string
  email?: string
  role?: string
  department?: string
  isActive?: boolean
  avatar?: string
}

export const goalTemplates: GoalTemplate[] = [
  { id: 'hires-monthly', name: 'Contratações (Placements)', description: 'Número de contratações efetivadas no mês', formula: 'Contagem de candidatos que mudaram para status "Contratado"', category: 'recruitment', defaultTarget: 5, unit: 'contratações', period: 'monthly', isActive: true },
  { id: 'interviews-monthly', name: 'Entrevistas Realizadas', description: 'Número total de entrevistas realizadas no período', formula: 'Total de entrevistas agendadas e confirmadas', category: 'recruitment', defaultTarget: 40, unit: 'entrevistas', period: 'monthly', isActive: true },
  { id: 'candidates-sourced', name: 'Candidatos Sourced', description: 'Número de candidatos prospectados ativamente', formula: 'Candidatos adicionados via sourcing ativo', category: 'recruitment', defaultTarget: 100, unit: 'candidatos', period: 'monthly', isActive: true },
  { id: 'screening-calls', name: 'Triagens Realizadas', description: 'Número de entrevistas de triagem', formula: 'Ligações de triagem registradas no sistema', category: 'recruitment', defaultTarget: 60, unit: 'triagens', period: 'monthly', isActive: true },
  { id: 'vacancies-closed', name: 'Vagas Fechadas', description: 'Número de vagas preenchidas e encerradas', formula: 'Vagas com status "Fechada" ou "Preenchida"', category: 'recruitment', defaultTarget: 8, unit: 'vagas', period: 'monthly', isActive: true },
  { id: 'offers-sent', name: 'Propostas Enviadas', description: 'Número de ofertas enviadas', formula: 'Candidatos com status "Proposta Enviada"', category: 'recruitment', defaultTarget: 10, unit: 'propostas', period: 'monthly', isActive: true },
  { id: 'offers-accepted', name: 'Propostas Aceitas', description: 'Número de ofertas aceitas', formula: 'Propostas com status "Aceita"', category: 'quality', defaultTarget: 8, unit: 'aceitas', period: 'monthly', isActive: true },
  { id: 'offers-declined', name: 'Propostas Recusadas', description: 'Número de ofertas recusadas', formula: 'Propostas com status "Recusada"', category: 'quality', defaultTarget: 2, unit: 'recusadas', period: 'monthly', isActive: true },
  { id: 'offer-acceptance-rate', name: 'Taxa de Aceitação', description: 'Percentual de ofertas aceitas', formula: '(Propostas Aceitas ÷ Total) × 100', category: 'quality', defaultTarget: 85, unit: '%', period: 'quarterly', isActive: true },
  { id: 'time-to-fill', name: 'Tempo de Preenchimento', description: 'Tempo médio para preenchimento', formula: 'Média de dias entre abertura e aceite', category: 'efficiency', defaultTarget: 30, unit: 'dias', period: 'monthly', isActive: true },
  { id: 'time-to-hire', name: 'Time to Hire', description: 'Tempo desde 1ª entrevista até contratação', formula: 'Média de dias entre 1ª entrevista e início', category: 'efficiency', defaultTarget: 21, unit: 'dias', period: 'monthly', isActive: true },
  { id: 'conversion-rate', name: 'Taxa de Conversão', description: 'Percentual convertido em contratações', formula: '(Contratações ÷ Total no Funil) × 100', category: 'efficiency', defaultTarget: 2.5, unit: '%', period: 'quarterly', isActive: true },
  { id: 'candidate-response', name: 'Taxa de Resposta', description: 'Percentual de candidatos que respondem', formula: '(Responderam ÷ Contatados) × 100', category: 'efficiency', defaultTarget: 75, unit: '%', period: 'monthly', isActive: true },
  { id: 'pipeline-velocity', name: 'Velocidade do Pipeline', description: 'Tempo médio para avançar entre etapas', formula: 'Média de dias por etapa', category: 'efficiency', defaultTarget: 5, unit: 'dias', period: 'monthly', isActive: true },
  { id: 'quality-score', name: 'Score de Qualidade', description: 'Avaliação média das contratações', formula: 'Média das avaliações (1-5) após experiência', category: 'quality', defaultTarget: 4.0, unit: 'pontos', period: 'yearly', isActive: true },
  { id: 'retention-90days', name: 'Retenção 90 Dias', description: 'Percentual retido após 90 dias', formula: '(Ativos após 90 dias ÷ Total) × 100', category: 'quality', defaultTarget: 90, unit: '%', period: 'quarterly', isActive: true },
  { id: 'hiring-manager-satisfaction', name: 'Satisfação do Gestor', description: 'Avaliação do gestor sobre qualidade', formula: 'Média das notas (1-5) dos gestores', category: 'quality', defaultTarget: 4.5, unit: 'pontos', period: 'quarterly', isActive: true },
  { id: 'nps-candidates', name: 'NPS dos Candidatos', description: 'Score de satisfação dos candidatos', formula: '% promotores - % detratores', category: 'satisfaction', defaultTarget: 85, unit: 'pontos', period: 'quarterly', isActive: true },
  { id: 'nps-hiring-managers', name: 'NPS dos Gestores', description: 'Score de satisfação dos gestores', formula: '% promotores - % detratores', category: 'satisfaction', defaultTarget: 80, unit: 'pontos', period: 'quarterly', isActive: true },
  { id: 'candidate-experience', name: 'Experiência do Candidato', description: 'Avaliação da experiência no processo', formula: 'Média das notas de feedback (1-5)', category: 'satisfaction', defaultTarget: 4.0, unit: 'pontos', period: 'monthly', isActive: true }
]

export const MONTHS = [
  { short: 'Jan', full: 'Janeiro', num: 1 }, { short: 'Fev', full: 'Fevereiro', num: 2 },
  { short: 'Mar', full: 'Março', num: 3 }, { short: 'Abr', full: 'Abril', num: 4 },
  { short: 'Mai', full: 'Maio', num: 5 }, { short: 'Jun', full: 'Junho', num: 6 },
  { short: 'Jul', full: 'Julho', num: 7 }, { short: 'Ago', full: 'Agosto', num: 8 },
  { short: 'Set', full: 'Setembro', num: 9 }, { short: 'Out', full: 'Outubro', num: 10 },
  { short: 'Nov', full: 'Novembro', num: 11 }, { short: 'Dez', full: 'Dezembro', num: 12 },
]

export async function createGoalInBackend(goalData: Partial<UserGoal> & { userId: string }): Promise<UserGoal | null> {
  const response = await fetch('/api/backend-proxy/goals', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: goalData.userId,
      template_id: goalData.templateId || null,
      name: goalData.name,
      description: goalData.description || '',
      target: goalData.target,
      current: goalData.current || 0,
      unit: goalData.unit || '',
      period: goalData.period,
      category: goalData.category,
      start_date: goalData.startDate ? new Date(goalData.startDate).toISOString() : null,
      end_date: goalData.endDate ? new Date(goalData.endDate).toISOString() : null,
      is_custom: goalData.isCustom || false
    })
  })
  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || 'Erro ao criar meta')
  }
  const created = await response.json()
  return {
    id: created.id, userId: created.user_id, templateId: created.template_id || '',
    name: created.name, description: created.description || '', target: created.target,
    current: created.current, unit: created.unit || '', period: created.period,
    startDate: created.start_date, endDate: created.end_date, status: created.status,
    progress: created.progress, category: created.category, isCustom: created.is_custom
  }
}

export async function updateGoalInBackend(goalId: string, updates: Partial<UserGoal>): Promise<boolean> {
  const response = await fetch(`/api/backend-proxy/goals/${goalId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: updates.name, description: updates.description, target: updates.target, current: updates.current, unit: updates.unit, period: updates.period, category: updates.category, status: updates.status })
  })
  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || 'Erro ao atualizar meta')
  }
  return true
}

export async function deleteGoalInBackend(goalId: string): Promise<boolean> {
  const response = await fetch(`/api/backend-proxy/goals/${goalId}`, { method: 'DELETE' })
  if (!response.ok) {
    const errorData = await response.json()
    throw new Error(errorData.error || 'Erro ao deletar meta')
  }
  return true
}

export function calculateEndDate(period: string): string {
  const now = new Date()
  const end = new Date(now)
  if (period === 'monthly') end.setMonth(end.getMonth() + 1)
  else if (period === 'quarterly') end.setMonth(end.getMonth() + 3)
  else end.setFullYear(end.getFullYear() + 1)
  return end.toISOString().split('T')[0]
}
