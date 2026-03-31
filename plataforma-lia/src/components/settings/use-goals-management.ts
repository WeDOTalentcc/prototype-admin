// @ts-nocheck
"use client"

// Camada 1 (hooks): Estado e ações centralizadas do GoalsManagement
// Padrão: { state, actions } — compatível com futura migração Pinia/Vue

import { useState, useMemo, useEffect, useCallback } from "react"

// --- Interfaces exportadas (contrato público inalterado) ---

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

// --- Dados estáticos: templates de metas ---

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
  { id: 'time-to-fill', name: 'Time to Fill', description: 'Tempo médio para preenchimento', formula: 'Média de dias entre abertura e aceite', category: 'efficiency', defaultTarget: 30, unit: 'dias', period: 'monthly', isActive: true },
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

// --- Hook Principal (Camada 1) ---

interface GoalsUser {
  id: string
  name: string
  email?: string
  role?: string
  department?: string
  isActive?: boolean
  avatar?: string
}

export function useGoalsManagement(users: GoalsUser[], onGoalUpdate: (userId: string, goals: UserGoal[]) => void) {
  // UI state
  const [selectedUser, setSelectedUser] = useState<GoalsUser | null>(null)
  const [showTemplates, setShowTemplates] = useState(false)
  const [showCustomGoal, setShowCustomGoal] = useState(false)
  const [editingGoal, setEditingGoal] = useState<UserGoal | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterCategory, setFilterCategory] = useState('all')
  const [filterPeriod, setFilterPeriod] = useState('all')
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [savingTemplateId, setSavingTemplateId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [userGoalsMap, setUserGoalsMap] = useState<Record<string, { monthly: UserGoal[], quarterly: UserGoal[], yearly: UserGoal[] }>>({})
  const [selectedTemplateIds, setSelectedTemplateIds] = useState<Set<string>>(new Set())
  const [templateApplyMode, setTemplateApplyMode] = useState<'all' | 'selected'>('all')
  const [deleteConfirmGoal, setDeleteConfirmGoal] = useState<UserGoal | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<GoalTemplate | null>(null)
  const [templateOverrides, setTemplateOverrides] = useState<Record<string, Partial<GoalTemplate>>>({})
  const [hiddenTemplates, setHiddenTemplates] = useState<Set<string>>(new Set())
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [collapsedGoals, setCollapsedGoals] = useState<Set<string>>(new Set())
  const [monthlyGoals, setMonthlyGoals] = useState<Record<string, MonthlyGoalValue[]>>({})
  const [showApplyAllModal, setShowApplyAllModal] = useState<string | null>(null)
  const [applyAllValue, setApplyAllValue] = useState<number>(0)
  const [applyAllMonths, setApplyAllMonths] = useState(true)
  const [applyAllUsers, setApplyAllUsers] = useState(true)
  const [templateUsersMap, setTemplateUsersMap] = useState<Record<string, string[]>>({})
  const [customGoalForm, setCustomGoalForm] = useState<CustomGoalForm>({
    name: '', description: '', target: 0, unit: '', period: 'monthly',
    category: 'recruitment', startDate: '', endDate: '', userId: ''
  })

  // --- API helpers ---

  const fetchUserGoals = useCallback(async (userId: string) => {
    try {
      const response = await fetch(`/api/backend-proxy/goals/by-user/${userId}`)
      if (response.ok) {
        const data = await response.json()
        setUserGoalsMap(prev => ({ ...prev, [userId]: data }))
        return data
      }
    } catch (error) {}
    return { monthly: [], quarterly: [], yearly: [] }
  }, [])

  const createGoalInBackend = async (goalData: Partial<UserGoal> & { userId: string }): Promise<UserGoal | null> => {
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

  const updateGoalInBackend = async (goalId: string, updates: Partial<UserGoal>): Promise<boolean> => {
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

  const deleteGoalInBackend = async (goalId: string): Promise<boolean> => {
    const response = await fetch(`/api/backend-proxy/goals/${goalId}`, { method: 'DELETE' })
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || 'Erro ao deletar meta')
    }
    return true
  }

  // --- Effects ---

  useEffect(() => {
    if (users.length > 0) {
      const load = async () => {
        setIsLoading(true)
        try { await Promise.all(users.map(u => fetchUserGoals(u.id))) }
        catch (e) {} finally { setIsLoading(false) }
      }
      load()
    }
  }, [users, fetchUserGoals])

  useEffect(() => {
    const newMap: Record<string, string[]> = {}
    Object.entries(userGoalsMap).forEach(([userId, goals]) => {
      const all = [...(goals.monthly || []), ...(goals.quarterly || []), ...(goals.yearly || [])]
      all.forEach(goal => {
        if (goal.templateId) {
          if (!newMap[goal.templateId]) newMap[goal.templateId] = []
          if (!newMap[goal.templateId].includes(userId)) newMap[goal.templateId].push(userId)
        }
      })
    })
    setTemplateUsersMap(newMap)
  }, [userGoalsMap])

  useEffect(() => {
    const newMonthly: Record<string, MonthlyGoalValue[]> = {}
    Object.entries(userGoalsMap).forEach(([userId, goals]) => {
      const all = [...(goals.monthly || []), ...(goals.quarterly || []), ...(goals.yearly || [])]
      all.forEach(goal => {
        if (!goal.templateId) return
        const key = `${goal.templateId}-${userId}`
        if (!newMonthly[key]) newMonthly[key] = []
        const meta = (goal as UserGoal & { goal_metadata?: { monthly_values?: Array<{ month: number; year: number; target?: number; current?: number }> } }).goal_metadata
        if (meta?.monthly_values && Array.isArray(meta.monthly_values)) {
          meta.monthly_values.forEach((mv: { month: number; year: number; target?: number; current?: number }) => {
            newMonthly[key].push({ userId, templateId: goal.templateId, month: mv.month, year: mv.year, target: mv.target || 0, current: mv.current || 0 })
          })
        } else {
          const startDate = goal.startDate ? new Date(goal.startDate) : new Date()
          const goalYear = startDate.getFullYear()
          const monthly = goal.target / 12
          for (let month = 1; month <= 12; month++) {
            if (!newMonthly[key].find(v => v.month === month && v.year === goalYear)) {
              newMonthly[key].push({ userId, templateId: goal.templateId, month, year: goalYear, target: Math.round(monthly * 100) / 100, current: 0 })
            }
          }
        }
      })
    })
    setMonthlyGoals(newMonthly)
  }, [userGoalsMap])

  // --- Computed ---

  const findUserGoal = useCallback((userId: string, templateId: string): UserGoal | null => {
    const goals = userGoalsMap[userId]
    if (!goals) return null
    const all = [...(goals.monthly || []), ...(goals.quarterly || []), ...(goals.yearly || [])]
    return all.find(g => g.templateId === templateId) || null
  }, [userGoalsMap])

  const getEffectiveTemplate = useCallback((template: GoalTemplate): GoalTemplate => {
    const override = templateOverrides[template.id]
    return override ? { ...template, ...override } : template
  }, [templateOverrides])

  const filteredTemplates = useMemo(() => {
    return goalTemplates
      .filter(t => !hiddenTemplates.has(t.id))
      .map(t => getEffectiveTemplate(t))
      .filter(t => {
        const matchesSearch = searchTerm === '' || t.name.toLowerCase().includes(searchTerm.toLowerCase()) || t.description.toLowerCase().includes(searchTerm.toLowerCase())
        return matchesSearch && (filterCategory === 'all' || t.category === filterCategory) && (filterPeriod === 'all' || t.period === filterPeriod) && t.isActive
      })
  }, [searchTerm, filterCategory, filterPeriod, hiddenTemplates, getEffectiveTemplate])

  const activeTemplatesWithUsers = useMemo(() => {
    return goalTemplates
      .filter(t => t.isActive && !hiddenTemplates.has(t.id))
      .map(t => ({ ...getEffectiveTemplate(t), assignedUsers: templateUsersMap[t.id] || [] }))
      .filter(t => t.assignedUsers.length > 0)
  }, [hiddenTemplates, getEffectiveTemplate, templateUsersMap])

  const goalStats = useMemo(() => {
    const all: UserGoal[] = []
    Object.values(userGoalsMap).forEach(goals => {
      all.push(...(goals.monthly || []), ...(goals.quarterly || []), ...(goals.yearly || []))
    })
    return {
      totalTemplates: goalTemplates.filter(t => t.isActive).length,
      totalAssigned: all.length,
      achieved: all.filter(g => g.status === 'achieved').length,
      inProgress: all.filter(g => g.status === 'in_progress').length,
      overdue: all.filter(g => g.status === 'overdue').length
    }
  }, [userGoalsMap])

  const getMonthlyValue = useCallback((templateId: string, userId: string, month: number, year: number): number | null => {
    const key = `${templateId}-${userId}`
    const values = monthlyGoals[key] || []
    const found = values.find(v => v.month === month && v.year === year)
    return found ? found.target : null
  }, [monthlyGoals])

  const calculateRowTotal = useCallback((templateId: string, userId: string, year: number): number => {
    const key = `${templateId}-${userId}`
    return (monthlyGoals[key] || []).filter(v => v.year === year).reduce((sum, v) => sum + (v.target || 0), 0)
  }, [monthlyGoals])

  const calculateColumnTotal = useCallback((templateId: string, month: number, year: number, userIds: string[]): number => {
    return userIds.reduce((sum, userId) => sum + (getMonthlyValue(templateId, userId, month, year) || 0), 0)
  }, [getMonthlyValue])

  const calculateGrandTotal = useCallback((templateId: string, year: number, userIds: string[]): number => {
    return userIds.reduce((sum, userId) => sum + calculateRowTotal(templateId, userId, year), 0)
  }, [calculateRowTotal])

  const isTemplateAppliedToUser = useCallback((templateId: string, userId: string): boolean => {
    const goals = userGoalsMap[userId]
    if (!goals) return false
    const all = [...(goals.monthly || []), ...(goals.quarterly || []), ...(goals.yearly || [])]
    return all.some(g => g.templateId === templateId)
  }, [userGoalsMap])

  const getAppliedTemplatesForUser = useCallback((userId: string): Set<string> => {
    const goals = userGoalsMap[userId]
    if (!goals) return new Set()
    const all = [...(goals.monthly || []), ...(goals.quarterly || []), ...(goals.yearly || [])]
    return new Set(all.filter(g => g.templateId).map(g => g.templateId))
  }, [userGoalsMap])

  const getUserById = (userId: string) => users.find(u => u.id === userId)

  // --- Actions ---

  const showSuccess = (message: string) => {
    setSuccessMessage(message)
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  const showError = (message: string) => {
    setError(message)
    setTimeout(() => setError(null), 5000)
  }

  const calculateEndDate = (period: string) => {
    const now = new Date()
    const end = new Date(now)
    if (period === 'monthly') end.setMonth(end.getMonth() + 1)
    else if (period === 'quarterly') end.setMonth(end.getMonth() + 3)
    else end.setFullYear(end.getFullYear() + 1)
    return end.toISOString().split('T')[0]
  }

  const persistGoalToBackend = useCallback(async (templateId: string, userId: string, updatedMonthlyValues: MonthlyGoalValue[]): Promise<boolean> => {
    const existingGoal = findUserGoal(userId, templateId)
    const template = goalTemplates.find(t => t.id === templateId)
    if (!template) return false

    const totalTarget = updatedMonthlyValues.reduce((sum, v) => sum + (v.target || 0), 0)
    const totalCurrent = updatedMonthlyValues.reduce((sum, v) => sum + (v.current || 0), 0)
    const goalMetadata = { monthly_values: updatedMonthlyValues.map(v => ({ month: v.month, year: v.year, target: v.target, current: v.current })) }

    try {
      if (existingGoal) {
        const response = await fetch(`/api/backend-proxy/goals/${existingGoal.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: existingGoal.name, description: existingGoal.description, target: totalTarget, current: totalCurrent, unit: existingGoal.unit, period: existingGoal.period, category: existingGoal.category, status: existingGoal.status, goal_metadata: goalMetadata })
        })
        if (!response.ok) throw new Error('Erro ao atualizar meta')
        return true
      } else {
        const effectiveTemplate = getEffectiveTemplate(template)
        const response = await fetch('/api/backend-proxy/goals', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, template_id: templateId, name: effectiveTemplate.name, description: effectiveTemplate.description || '', target: totalTarget, current: totalCurrent, unit: effectiveTemplate.unit || '', period: effectiveTemplate.period, category: effectiveTemplate.category, start_date: new Date().toISOString(), end_date: new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString(), is_custom: false, goal_metadata: goalMetadata })
        })
        if (!response.ok) throw new Error('Erro ao criar meta')
        await fetchUserGoals(userId)
        return true
      }
    } catch (error) { return false }
  }, [findUserGoal, getEffectiveTemplate, fetchUserGoals])

  const setMonthlyValue = useCallback(async (templateId: string, userId: string, month: number, year: number, value: number) => {
    const key = `${templateId}-${userId}`
    const previousValues = monthlyGoals[key] ? [...monthlyGoals[key]] : []
    const existing = monthlyGoals[key] || []
    const idx = existing.findIndex(v => v.month === month && v.year === year)
    let updatedValues: MonthlyGoalValue[]
    if (idx >= 0) {
      updatedValues = [...existing]
      updatedValues[idx] = { ...updatedValues[idx], target: value }
    } else {
      updatedValues = [...existing, { userId, templateId, month, year, target: value, current: 0 }]
    }
    setMonthlyGoals(prev => ({ ...prev, [key]: updatedValues }))
    try {
      const success = await persistGoalToBackend(templateId, userId, updatedValues)
      if (!success) {
        setMonthlyGoals(prev => ({ ...prev, [key]: previousValues }))
        showError('Erro ao salvar meta. Valor revertido.')
        return
      }
      await fetchUserGoals(userId)
    } catch (error) {
      setMonthlyGoals(prev => ({ ...prev, [key]: previousValues }))
      showError('Erro ao salvar meta. Valor revertido.')
    }
  }, [monthlyGoals, persistGoalToBackend, fetchUserGoals])

  const applyValueToAll = useCallback(async (templateId: string, value: number, options: { allMonths: boolean, allUsers: boolean }) => {
    const template = goalTemplates.find(t => t.id === templateId)
    if (!template) return

    const targetUsers = options.allUsers ? users.map(u => u.id) : (templateUsersMap[templateId] || [])
    const targetMonths = options.allMonths ? MONTHS.map(m => m.num) : [new Date().getMonth() + 1]
    const previousStates: Record<string, MonthlyGoalValue[]> = {}
    const updatedGoals: Record<string, MonthlyGoalValue[]> = {}

    targetUsers.forEach(userId => {
      const key = `${templateId}-${userId}`
      previousStates[key] = monthlyGoals[key] ? [...monthlyGoals[key]] : []
      const existing = monthlyGoals[key] || []
      const updated = [...existing]
      targetMonths.forEach(month => {
        const idx = updated.findIndex(v => v.month === month && v.year === selectedYear)
        if (idx >= 0) updated[idx] = { ...updated[idx], target: value }
        else updated.push({ userId, templateId, month, year: selectedYear, target: value, current: 0 })
      })
      updatedGoals[key] = updated
    })

    setMonthlyGoals(prev => ({ ...prev, ...updatedGoals }))

    const results = await Promise.allSettled(
      targetUsers.map(async userId => {
        const key = `${templateId}-${userId}`
        const success = await persistGoalToBackend(templateId, userId, updatedGoals[key])
        if (!success) throw new Error('Failed to persist')
        return { userId, success: true }
      })
    )

    const successfulIds: string[] = []
    const failedKeys: string[] = []
    results.forEach((result, index) => {
      const userId = targetUsers[index]
      const key = `${templateId}-${userId}`
      if (result.status === 'fulfilled') successfulIds.push(userId)
      else failedKeys.push(key)
    })

    if (failedKeys.length > 0) {
      setMonthlyGoals(prev => {
        const reverted = { ...prev }
        failedKeys.forEach(key => { reverted[key] = previousStates[key] })
        return reverted
      })
      showError(`${failedKeys.length} usuário(s) não foram atualizados`)
    }

    if (successfulIds.length > 0) {
      await Promise.all(successfulIds.map(userId => fetchUserGoals(userId)))
      if (failedKeys.length === 0) showSuccess(`${successfulIds.length} meta(s) salva(s) com sucesso!`)
      else showSuccess(`${successfulIds.length} usuário(s) atualizado(s)`)
    }
  }, [users, templateUsersMap, selectedYear, monthlyGoals, persistGoalToBackend, fetchUserGoals])

  const toggleGoalCollapse = (templateId: string) => {
    setCollapsedGoals(prev => {
      const next = new Set(prev)
      if (next.has(templateId)) next.delete(templateId)
      else next.add(templateId)
      return next
    })
  }

  const toggleTemplateSelection = (templateId: string) => {
    setSelectedTemplateIds(prev => {
      const next = new Set(prev)
      if (next.has(templateId)) next.delete(templateId)
      else next.add(templateId)
      return next
    })
  }

  const handleApplyTemplate = async (template: GoalTemplate, targetUsers: GoalsUser[]) => {
    setIsSaving(true)
    setSavingTemplateId(template.id)
    setError(null)
    try {
      let applied = 0, skipped = 0
      for (const user of targetUsers) {
        if (isTemplateAppliedToUser(template.id, user.id)) { skipped++; continue }
        await createGoalInBackend({ userId: user.id, templateId: template.id, name: template.name, description: template.description, target: template.defaultTarget, current: 0, unit: template.unit, period: template.period, startDate: new Date().toISOString().split('T')[0], endDate: calculateEndDate(template.period), category: template.category, isCustom: false })
        await fetchUserGoals(user.id)
        applied++
      }
      if (skipped > 0 && applied === 0) showError(`"${template.name}" já está aplicado para todos`)
      else if (skipped > 0) showSuccess(`"${template.name}" aplicado para ${applied} usuário(s). ${skipped} já tinham.`)
      else showSuccess(`"${template.name}" aplicado com sucesso para ${applied} usuário(s)`)
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Erro ao aplicar template')
    } finally {
      setIsSaving(false)
      setSavingTemplateId(null)
    }
  }

  const handleApplySelectedTemplates = async () => {
    if (selectedTemplateIds.size === 0) { showError('Selecione pelo menos um template'); return }
    const targetUsers = templateApplyMode === 'selected' && selectedUser ? [selectedUser] : users
    setIsSaving(true)
    setError(null)
    try {
      const goalsToCreate: Array<Partial<UserGoal> & { userId: string }> = []
      let totalSkipped = 0
      for (const templateId of selectedTemplateIds) {
        const template = filteredTemplates.find(t => t.id === templateId) || goalTemplates.find(t => t.id === templateId)
        if (!template) continue
        for (const user of targetUsers) {
          if (isTemplateAppliedToUser(template.id, user.id)) { totalSkipped++; continue }
          goalsToCreate.push({ userId: user.id, templateId: template.id, name: template.name, description: template.description, target: template.defaultTarget, current: 0, unit: template.unit, period: template.period, startDate: new Date().toISOString().split('T')[0], endDate: calculateEndDate(template.period), category: template.category, isCustom: false })
        }
      }
      const results = await Promise.allSettled(goalsToCreate.map(g => createGoalInBackend(g)))
      const totalApplied = results.filter(r => r.status === 'fulfilled').length
      const totalFailed = results.filter(r => r.status === 'rejected').length
      await Promise.all(targetUsers.map(u => fetchUserGoals(u.id)))
      if (totalFailed > 0) showError(`${totalApplied} aplicada(s), ${totalFailed} falharam`)
      else if (totalSkipped > 0 && totalApplied === 0) showError('Todas já estavam aplicadas')
      else if (totalSkipped > 0) showSuccess(`${totalApplied} meta(s) aplicada(s). ${totalSkipped} duplicata(s) ignorada(s).`)
      else showSuccess(`${totalApplied} meta(s) aplicada(s) com sucesso!`)
      setSelectedTemplateIds(new Set())
      setShowTemplates(false)
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Erro ao aplicar templates')
    } finally { setIsSaving(false) }
  }

  const handleCreateCustomGoal = async () => {
    const targetUserId = customGoalForm.userId || selectedUser?.id
    const isApplyToAll = targetUserId === '__all__'
    if (!targetUserId) { showError('Selecione um usuário ou "Todos"'); return }
    if (!customGoalForm.name) { showError('O nome da meta é obrigatório'); return }
    if (customGoalForm.target <= 0) { showError('A meta deve ter valor maior que zero'); return }
    setIsSaving(true)
    setError(null)
    try {
      const targetUsers = isApplyToAll ? users : [users.find(u => u.id === targetUserId)].filter(Boolean)
      for (const user of targetUsers) {
        await createGoalInBackend({ userId: user.id, templateId: '', name: customGoalForm.name, description: customGoalForm.description, target: customGoalForm.target, current: 0, unit: customGoalForm.unit, period: customGoalForm.period, startDate: customGoalForm.startDate || new Date().toISOString().split('T')[0], endDate: customGoalForm.endDate || calculateEndDate(customGoalForm.period), category: customGoalForm.category, isCustom: true })
        await fetchUserGoals(user.id)
      }
      showSuccess(isApplyToAll ? `Meta "${customGoalForm.name}" criada para ${targetUsers.length} usuários!` : 'Meta criada com sucesso!')
      setShowCustomGoal(false)
      setCustomGoalForm({ name: '', description: '', target: 0, unit: '', period: 'monthly', category: 'recruitment', startDate: '', endDate: '', userId: '' })
      setSelectedUser(null)
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Erro ao criar meta')
    } finally { setIsSaving(false) }
  }

  const handleUpdateGoal = async (goal: UserGoal, updates: Partial<UserGoal>) => {
    setIsSaving(true)
    setError(null)
    try {
      await updateGoalInBackend(goal.id, { ...goal, ...updates })
      await fetchUserGoals(goal.userId)
      showSuccess('Meta atualizada com sucesso!')
      setEditingGoal(null)
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Erro ao atualizar meta')
    } finally { setIsSaving(false) }
  }

  const handleDeleteGoal = (goal: UserGoal) => setDeleteConfirmGoal(goal)

  const confirmDeleteGoal = async () => {
    if (!deleteConfirmGoal) return
    setIsDeleting(true)
    setError(null)
    try {
      await deleteGoalInBackend(deleteConfirmGoal.id)
      await fetchUserGoals(deleteConfirmGoal.userId)
      showSuccess('Meta excluída com sucesso!')
      setDeleteConfirmGoal(null)
    } catch (error: unknown) {
      showError(error instanceof Error ? error.message : 'Erro ao excluir meta')
    } finally { setIsDeleting(false) }
  }

  const handleAddUserToTemplate = async (templateId: string) => {
    const template = goalTemplates.find(t => t.id === templateId)
    if (!template) return
    const available = users.filter(u => !isTemplateAppliedToUser(templateId, u.id))
    if (available.length === 0) { showError('Todos os usuários já possuem esta meta'); return }
    setSelectedUser(available[0])
    await handleApplyTemplate(getEffectiveTemplate(template), [available[0]])
  }

  return {
    state: {
      selectedUser, showTemplates, showCustomGoal, editingGoal, searchTerm,
      filterCategory, filterPeriod, isLoading, isSaving, savingTemplateId, error,
      successMessage, userGoalsMap, selectedTemplateIds, templateApplyMode,
      deleteConfirmGoal, isDeleting, editingTemplate, templateOverrides, hiddenTemplates,
      selectedYear, collapsedGoals, monthlyGoals, showApplyAllModal, applyAllValue,
      applyAllMonths, applyAllUsers, templateUsersMap, customGoalForm,
      // derived
      filteredTemplates, activeTemplatesWithUsers, goalStats
    },
    actions: {
      setSelectedUser, setShowTemplates, setShowCustomGoal, setEditingGoal,
      setSearchTerm, setFilterCategory, setFilterPeriod, setSelectedTemplateIds,
      setTemplateApplyMode, setDeleteConfirmGoal, setEditingTemplate, setTemplateOverrides,
      setHiddenTemplates, setSelectedYear, setCollapsedGoals, setShowApplyAllModal,
      setApplyAllValue, setApplyAllMonths, setApplyAllUsers, setCustomGoalForm,
      // computed helpers
      getMonthlyValue, calculateRowTotal, calculateColumnTotal, calculateGrandTotal,
      getEffectiveTemplate, isTemplateAppliedToUser, getAppliedTemplatesForUser, getUserById,
      findUserGoal, fetchUserGoals,
      // actions
      setMonthlyValue, applyValueToAll, toggleGoalCollapse, toggleTemplateSelection,
      handleApplyTemplate, handleApplySelectedTemplates, handleCreateCustomGoal,
      handleUpdateGoal, handleDeleteGoal, confirmDeleteGoal, handleAddUserToTemplate
    }
  }
}
