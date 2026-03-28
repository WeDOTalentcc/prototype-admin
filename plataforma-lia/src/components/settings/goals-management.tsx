"use client"

import { useState, useMemo, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Plus, Edit, Trash2, Save, X, Target, Users, BarChart3, Calendar,
  TrendingUp, Award, CheckCircle, AlertCircle, Clock, Percent,
  Timer, DollarSign, Star, Heart, Zap, UserCheck, Settings,
  Copy, Download, Upload, FileText, Search, Filter, Loader2,
  ChevronDown, ChevronRight, ChevronUp, User
} from "lucide-react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { typography, textStyles } from "@/lib/design-tokens"

interface GoalTemplate {
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

interface UserGoal {
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

interface MonthlyGoalValue {
  userId: string
  templateId: string
  month: number
  year: number
  target: number
  current: number
}

interface GoalsManagementProps {
  users: any[]
  onGoalUpdate: (userId: string, goals: any) => void
}

const MONTHS = [
  { short: 'Jan', full: 'Janeiro', num: 1 },
  { short: 'Fev', full: 'Fevereiro', num: 2 },
  { short: 'Mar', full: 'Março', num: 3 },
  { short: 'Abr', full: 'Abril', num: 4 },
  { short: 'Mai', full: 'Maio', num: 5 },
  { short: 'Jun', full: 'Junho', num: 6 },
  { short: 'Jul', full: 'Julho', num: 7 },
  { short: 'Ago', full: 'Agosto', num: 8 },
  { short: 'Set', full: 'Setembro', num: 9 },
  { short: 'Out', full: 'Outubro', num: 10 },
  { short: 'Nov', full: 'Novembro', num: 11 },
  { short: 'Dez', full: 'Dezembro', num: 12 },
]

const goalTemplates: GoalTemplate[] = [
  {
    id: 'hires-monthly',
    name: 'Contratações (Placements)',
    description: 'Número de contratações efetivadas no mês',
    formula: 'Contagem de candidatos que mudaram para status "Contratado" no período',
    category: 'recruitment',
    defaultTarget: 5,
    unit: 'contratações',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'interviews-monthly',
    name: 'Entrevistas Realizadas',
    description: 'Número total de entrevistas realizadas no período',
    formula: 'Total de entrevistas agendadas e confirmadas como realizadas',
    category: 'recruitment',
    defaultTarget: 40,
    unit: 'entrevistas',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'candidates-sourced',
    name: 'Candidatos Sourced',
    description: 'Número de candidatos prospectados ativamente',
    formula: 'Candidatos adicionados manualmente ou via sourcing ativo (não aplicações)',
    category: 'recruitment',
    defaultTarget: 100,
    unit: 'candidatos',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'screening-calls',
    name: 'Triagens Realizadas',
    description: 'Número de entrevistas de triagem (phone screening)',
    formula: 'Ligações de triagem inicial registradas no sistema',
    category: 'recruitment',
    defaultTarget: 60,
    unit: 'triagens',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'vacancies-closed',
    name: 'Vagas Fechadas',
    description: 'Número de vagas preenchidas e encerradas',
    formula: 'Vagas com status alterado para "Fechada" ou "Preenchida"',
    category: 'recruitment',
    defaultTarget: 8,
    unit: 'vagas',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'offers-sent',
    name: 'Propostas Enviadas',
    description: 'Número de ofertas de trabalho enviadas a candidatos',
    formula: 'Candidatos que receberam proposta formal (status "Proposta Enviada")',
    category: 'recruitment',
    defaultTarget: 10,
    unit: 'propostas',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'offers-accepted',
    name: 'Propostas Aceitas',
    description: 'Número de ofertas aceitas pelos candidatos',
    formula: 'Propostas com status "Aceita" pelo candidato',
    category: 'quality',
    defaultTarget: 8,
    unit: 'aceitas',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'offers-declined',
    name: 'Propostas Recusadas',
    description: 'Número de ofertas recusadas pelos candidatos',
    formula: 'Propostas com status "Recusada" pelo candidato (quanto menor, melhor)',
    category: 'quality',
    defaultTarget: 2,
    unit: 'recusadas',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'offer-acceptance-rate',
    name: 'Taxa de Aceitação',
    description: 'Percentual de ofertas aceitas pelos candidatos',
    formula: '(Propostas Aceitas ÷ Total de Propostas) × 100',
    category: 'quality',
    defaultTarget: 85,
    unit: '%',
    period: 'quarterly',
    isActive: true
  },
  {
    id: 'time-to-fill',
    name: 'Time to Fill',
    description: 'Tempo médio para preenchimento de vagas em dias',
    formula: 'Média de dias entre abertura da vaga e aceite da proposta',
    category: 'efficiency',
    defaultTarget: 30,
    unit: 'dias',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'time-to-hire',
    name: 'Time to Hire',
    description: 'Tempo médio desde primeira entrevista até contratação',
    formula: 'Média de dias entre 1ª entrevista e início do candidato',
    category: 'efficiency',
    defaultTarget: 21,
    unit: 'dias',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'conversion-rate',
    name: 'Taxa de Conversão',
    description: 'Percentual de candidatos convertidos em contratações',
    formula: '(Contratações ÷ Total de Candidatos no Funil) × 100',
    category: 'efficiency',
    defaultTarget: 2.5,
    unit: '%',
    period: 'quarterly',
    isActive: true
  },
  {
    id: 'candidate-response',
    name: 'Taxa de Resposta',
    description: 'Percentual de candidatos que respondem ao contato inicial',
    formula: '(Candidatos que Responderam ÷ Candidatos Contatados) × 100',
    category: 'efficiency',
    defaultTarget: 75,
    unit: '%',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'pipeline-velocity',
    name: 'Velocidade do Pipeline',
    description: 'Tempo médio para avançar candidato entre etapas',
    formula: 'Média de dias que candidatos ficam em cada etapa do processo',
    category: 'efficiency',
    defaultTarget: 5,
    unit: 'dias',
    period: 'monthly',
    isActive: true
  },
  {
    id: 'quality-score',
    name: 'Score de Qualidade',
    description: 'Avaliação média da qualidade das contratações',
    formula: 'Média das avaliações de desempenho (1-5) dos contratados após período de experiência',
    category: 'quality',
    defaultTarget: 4.0,
    unit: 'pontos',
    period: 'yearly',
    isActive: true
  },
  {
    id: 'retention-90days',
    name: 'Retenção 90 Dias',
    description: 'Percentual de contratados que permanecem após 90 dias',
    formula: '(Contratados ativos após 90 dias ÷ Total Contratados) × 100',
    category: 'quality',
    defaultTarget: 90,
    unit: '%',
    period: 'quarterly',
    isActive: true
  },
  {
    id: 'hiring-manager-satisfaction',
    name: 'Satisfação do Gestor',
    description: 'Avaliação do gestor sobre qualidade do candidato',
    formula: 'Média das notas dadas pelos gestores (1-5) sobre candidatos apresentados',
    category: 'quality',
    defaultTarget: 4.5,
    unit: 'pontos',
    period: 'quarterly',
    isActive: true
  },
  {
    id: 'nps-candidates',
    name: 'NPS dos Candidatos',
    description: 'Score de satisfação dos candidatos no processo',
    formula: 'Pesquisa NPS pós-processo: % promotores - % detratores (escala -100 a 100)',
    category: 'satisfaction',
    defaultTarget: 85,
    unit: 'pontos',
    period: 'quarterly',
    isActive: true
  },
  {
    id: 'nps-hiring-managers',
    name: 'NPS dos Gestores',
    description: 'Score de satisfação dos gestores com o processo',
    formula: 'Pesquisa NPS com gestores: % promotores - % detratores (escala -100 a 100)',
    category: 'satisfaction',
    defaultTarget: 80,
    unit: 'pontos',
    period: 'quarterly',
    isActive: true
  },
  {
    id: 'candidate-experience',
    name: 'Experiência do Candidato',
    description: 'Avaliação da experiência do candidato no processo',
    formula: 'Média das notas de feedback dos candidatos (1-5) sobre comunicação e processo',
    category: 'satisfaction',
    defaultTarget: 4.0,
    unit: 'pontos',
    period: 'monthly',
    isActive: true
  }
]

function EditableCell({ 
  value, 
  onChange, 
  disabled = false,
  placeholder = "-"
}: { 
  value: number | null
  onChange: (value: number) => void
  disabled?: boolean
  placeholder?: string
}) {
  const [isEditing, setIsEditing] = useState(false)
  const [inputValue, setInputValue] = useState(value?.toString() || '')

  const handleClick = () => {
    if (disabled) return
    setIsEditing(true)
    setInputValue(value?.toString() || '')
  }

  const handleSave = () => {
    const numValue = parseFloat(inputValue) || 0
    onChange(numValue)
    setIsEditing(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave()
    } else if (e.key === 'Escape') {
      setIsEditing(false)
      setInputValue(value?.toString() || '')
    }
  }

  if (isEditing) {
    return (
      <input
        type="number"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onBlur={handleSave}
        onKeyDown={handleKeyDown}
        autoFocus
        min={0}
        className="w-10 px-1 py-1 text-xs border border-gray-400 rounded text-center bg-white focus:outline-none focus:ring-1 focus:ring-gray-900 font-['Open_Sans',sans-serif]"
      />
    )
  }

  const displayValue = value !== null && value !== undefined && value !== 0 ? value : placeholder

  return (
    <div
      onClick={handleClick}
      className={`w-10 px-1 py-1 text-xs border border-gray-200 rounded-full text-center bg-white cursor-pointer hover:border-gray-300 transition-colors font-['Open_Sans',sans-serif] ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
    >
      {displayValue}
    </div>
  )
}

export function GoalsManagement({ users, onGoalUpdate }: GoalsManagementProps) {
  const [selectedUser, setSelectedUser] = useState<any | null>(null)
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

  const [customGoalForm, setCustomGoalForm] = useState({
    name: '',
    description: '',
    target: 0,
    unit: '',
    period: 'monthly' as const,
    category: 'recruitment' as const,
    startDate: '',
    endDate: '',
    userId: ''
  })

  const fetchUserGoals = useCallback(async (userId: string) => {
    try {
      const response = await fetch(`/api/backend-proxy/goals/by-user/${userId}`)
      if (response.ok) {
        const data = await response.json()
        setUserGoalsMap(prev => ({
          ...prev,
          [userId]: data
        }))
        return data
      }
    } catch (error) {
    }
    return { monthly: [], quarterly: [], yearly: [] }
  }, [])

  useEffect(() => {
    const loadAllUserGoals = async () => {
      setIsLoading(true)
      try {
        await Promise.all(users.map(user => fetchUserGoals(user.id)))
      } catch (error) {
      } finally {
        setIsLoading(false)
      }
    }

    if (users.length > 0) {
      loadAllUserGoals()
    }
  }, [users, fetchUserGoals])

  useEffect(() => {
    const newTemplateUsersMap: Record<string, string[]> = {}
    
    Object.entries(userGoalsMap).forEach(([userId, goals]) => {
      const allGoals = [...(goals.monthly || []), ...(goals.quarterly || []), ...(goals.yearly || [])]
      allGoals.forEach(goal => {
        if (goal.templateId) {
          if (!newTemplateUsersMap[goal.templateId]) {
            newTemplateUsersMap[goal.templateId] = []
          }
          if (!newTemplateUsersMap[goal.templateId].includes(userId)) {
            newTemplateUsersMap[goal.templateId].push(userId)
          }
        }
      })
    })
    
    setTemplateUsersMap(newTemplateUsersMap)
  }, [userGoalsMap])

  useEffect(() => {
    const newMonthlyGoals: Record<string, MonthlyGoalValue[]> = {}
    
    Object.entries(userGoalsMap).forEach(([userId, goals]) => {
      const allGoals = [...(goals.monthly || []), ...(goals.quarterly || []), ...(goals.yearly || [])]
      
      allGoals.forEach(goal => {
        if (!goal.templateId) return
        
        const key = `${goal.templateId}-${userId}`
        
        if (!newMonthlyGoals[key]) {
          newMonthlyGoals[key] = []
        }
        
        const goalMetadata = (goal as any).goal_metadata
        if (goalMetadata?.monthly_values && Array.isArray(goalMetadata.monthly_values)) {
          goalMetadata.monthly_values.forEach((mv: any) => {
            newMonthlyGoals[key].push({
              userId,
              templateId: goal.templateId,
              month: mv.month,
              year: mv.year,
              target: mv.target || 0,
              current: mv.current || 0
            })
          })
        } else {
          const startDate = goal.startDate ? new Date(goal.startDate) : new Date()
          const goalYear = startDate.getFullYear()
          const monthlyTarget = goal.target / 12
          
          for (let month = 1; month <= 12; month++) {
            const existingEntry = newMonthlyGoals[key].find(
              v => v.month === month && v.year === goalYear
            )
            if (!existingEntry) {
              newMonthlyGoals[key].push({
                userId,
                templateId: goal.templateId,
                month,
                year: goalYear,
                target: Math.round(monthlyTarget * 100) / 100,
                current: 0
              })
            }
          }
        }
      })
    })
    
    setMonthlyGoals(newMonthlyGoals)
  }, [userGoalsMap])

  const findUserGoal = useCallback((userId: string, templateId: string): UserGoal | null => {
    const userGoals = userGoalsMap[userId]
    if (!userGoals) return null
    
    const allGoals = [...(userGoals.monthly || []), ...(userGoals.quarterly || []), ...(userGoals.yearly || [])]
    return allGoals.find(g => g.templateId === templateId) || null
  }, [userGoalsMap])

  const getEffectiveTemplate = useCallback((template: GoalTemplate): GoalTemplate => {
    const override = templateOverrides[template.id]
    if (!override) return template
    return { ...template, ...override }
  }, [templateOverrides])

  const filteredTemplates = useMemo(() => {
    return goalTemplates
      .filter(template => !hiddenTemplates.has(template.id))
      .map(template => getEffectiveTemplate(template))
      .filter(template => {
        const matchesSearch = searchTerm === '' ||
          template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          template.description.toLowerCase().includes(searchTerm.toLowerCase())

        const matchesCategory = filterCategory === 'all' || template.category === filterCategory
        const matchesPeriod = filterPeriod === 'all' || template.period === filterPeriod

        return matchesSearch && matchesCategory && matchesPeriod && template.isActive
      })
  }, [searchTerm, filterCategory, filterPeriod, hiddenTemplates, getEffectiveTemplate])

  const activeTemplatesWithUsers = useMemo(() => {
    return goalTemplates
      .filter(t => t.isActive && !hiddenTemplates.has(t.id))
      .map(template => ({
        ...getEffectiveTemplate(template),
        assignedUsers: templateUsersMap[template.id] || []
      }))
      .filter(t => t.assignedUsers.length > 0)
  }, [hiddenTemplates, getEffectiveTemplate, templateUsersMap])

  const goalStats = useMemo(() => {
    const allGoals: UserGoal[] = []
    Object.values(userGoalsMap).forEach(goals => {
      allGoals.push(...(goals.monthly || []))
      allGoals.push(...(goals.quarterly || []))
      allGoals.push(...(goals.yearly || []))
    })

    return {
      totalTemplates: goalTemplates.filter(t => t.isActive).length,
      totalAssigned: allGoals.length,
      achieved: allGoals.filter(g => g.status === 'achieved').length,
      inProgress: allGoals.filter(g => g.status === 'in_progress').length,
      overdue: allGoals.filter(g => g.status === 'overdue').length
    }
  }, [userGoalsMap])

  const getMonthlyValue = useCallback((templateId: string, userId: string, month: number, year: number): number | null => {
    const key = `${templateId}-${userId}`
    const values = monthlyGoals[key] || []
    const found = values.find(v => v.month === month && v.year === year)
    return found ? found.target : null
  }, [monthlyGoals])

  const persistGoalToBackend = useCallback(async (
    templateId: string, 
    userId: string, 
    updatedMonthlyValues: MonthlyGoalValue[]
  ): Promise<boolean> => {
    const existingGoal = findUserGoal(userId, templateId)
    const template = goalTemplates.find(t => t.id === templateId)
    
    if (!template) return false
    
    const totalTarget = updatedMonthlyValues.reduce((sum, v) => sum + (v.target || 0), 0)
    const totalCurrent = updatedMonthlyValues.reduce((sum, v) => sum + (v.current || 0), 0)
    
    const goalMetadata = {
      monthly_values: updatedMonthlyValues.map(v => ({
        month: v.month,
        year: v.year,
        target: v.target,
        current: v.current
      }))
    }
    
    try {
      if (existingGoal) {
        const response = await fetch(`/api/backend-proxy/goals/${existingGoal.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: existingGoal.name,
            description: existingGoal.description,
            target: totalTarget,
            current: totalCurrent,
            unit: existingGoal.unit,
            period: existingGoal.period,
            category: existingGoal.category,
            status: existingGoal.status,
            goal_metadata: goalMetadata
          })
        })
        
        if (!response.ok) {
          throw new Error('Erro ao atualizar meta')
        }
        
        return true
      } else {
        const effectiveTemplate = getEffectiveTemplate(template)
        const response = await fetch('/api/backend-proxy/goals', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            template_id: templateId,
            name: effectiveTemplate.name,
            description: effectiveTemplate.description || '',
            target: totalTarget,
            current: totalCurrent,
            unit: effectiveTemplate.unit || '',
            period: effectiveTemplate.period,
            category: effectiveTemplate.category,
            start_date: new Date().toISOString(),
            end_date: new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString(),
            is_custom: false,
            goal_metadata: goalMetadata
          })
        })
        
        if (!response.ok) {
          throw new Error('Erro ao criar meta')
        }
        
        await fetchUserGoals(userId)
        return true
      }
    } catch (error) {
      return false
    }
  }, [findUserGoal, getEffectiveTemplate, fetchUserGoals])

  const setMonthlyValue = useCallback(async (templateId: string, userId: string, month: number, year: number, value: number) => {
    const key = `${templateId}-${userId}`
    
    const previousValues = monthlyGoals[key] ? [...monthlyGoals[key]] : []
    
    const newValue: MonthlyGoalValue = {
      userId,
      templateId,
      month,
      year,
      target: value,
      current: 0
    }
    
    const existing = monthlyGoals[key] || []
    const idx = existing.findIndex(v => v.month === month && v.year === year)
    
    let updatedValues: MonthlyGoalValue[]
    if (idx >= 0) {
      updatedValues = [...existing]
      updatedValues[idx] = { ...updatedValues[idx], target: value }
    } else {
      updatedValues = [...existing, newValue]
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

  const calculateRowTotal = useCallback((templateId: string, userId: string, year: number): number => {
    const key = `${templateId}-${userId}`
    const values = monthlyGoals[key] || []
    return values
      .filter(v => v.year === year)
      .reduce((sum, v) => sum + (v.target || 0), 0)
  }, [monthlyGoals])

  const calculateColumnTotal = useCallback((templateId: string, month: number, year: number, userIds: string[]): number => {
    return userIds.reduce((sum, userId) => {
      const value = getMonthlyValue(templateId, userId, month, year)
      return sum + (value || 0)
    }, 0)
  }, [getMonthlyValue])

  const calculateGrandTotal = useCallback((templateId: string, year: number, userIds: string[]): number => {
    return userIds.reduce((sum, userId) => {
      return sum + calculateRowTotal(templateId, userId, year)
    }, 0)
  }, [calculateRowTotal])

  const applyValueToAll = useCallback(async (templateId: string, value: number, options: { allMonths: boolean, allUsers: boolean }) => {
    const template = goalTemplates.find(t => t.id === templateId)
    if (!template) return

    const targetUsers = options.allUsers 
      ? users.map(u => u.id)
      : templateUsersMap[templateId] || []

    const targetMonths = options.allMonths 
      ? MONTHS.map(m => m.num)
      : [new Date().getMonth() + 1]

    const previousStates: Record<string, MonthlyGoalValue[]> = {}
    const updatedGoals: Record<string, MonthlyGoalValue[]> = {}

    targetUsers.forEach(userId => {
      const key = `${templateId}-${userId}`
      previousStates[key] = monthlyGoals[key] ? [...monthlyGoals[key]] : []
      
      const existing = monthlyGoals[key] || []
      const updated = [...existing]
      
      targetMonths.forEach(month => {
        const idx = updated.findIndex(v => v.month === month && v.year === selectedYear)
        const newValue: MonthlyGoalValue = {
          userId,
          templateId,
          month,
          year: selectedYear,
          target: value,
          current: 0
        }
        
        if (idx >= 0) {
          updated[idx] = { ...updated[idx], target: value }
        } else {
          updated.push(newValue)
        }
      })
      
      updatedGoals[key] = updated
    })

    setMonthlyGoals(prev => ({ ...prev, ...updatedGoals }))

    const results = await Promise.allSettled(
      targetUsers.map(async userId => {
        const key = `${templateId}-${userId}`
        const success = await persistGoalToBackend(templateId, userId, updatedGoals[key])
        if (!success) {
          throw new Error('Failed to persist')
        }
        return { userId, success: true }
      })
    )

    const successfulUserIds: string[] = []
    const failedKeys: string[] = []

    results.forEach((result, index) => {
      const userId = targetUsers[index]
      const key = `${templateId}-${userId}`

      if (result.status === 'fulfilled' && result.value.success) {
        successfulUserIds.push(userId)
      } else {
        failedKeys.push(key)
      }
    })

    if (failedKeys.length > 0) {
      setMonthlyGoals(prev => {
        const reverted = { ...prev }
        failedKeys.forEach(key => {
          reverted[key] = previousStates[key]
        })
        return reverted
      })
      showError(`${failedKeys.length} usuário(s) não foram atualizados`)
    }

    if (successfulUserIds.length > 0) {
      await Promise.all(successfulUserIds.map(userId => fetchUserGoals(userId)))
      if (failedKeys.length === 0) {
        showSuccess(`${successfulUserIds.length} meta(s) salva(s) com sucesso!`)
      } else {
        showSuccess(`${successfulUserIds.length} usuário(s) atualizado(s) com sucesso`)
      }
    }
  }, [users, templateUsersMap, selectedYear, monthlyGoals, persistGoalToBackend, fetchUserGoals])

  const toggleGoalCollapse = (templateId: string) => {
    setCollapsedGoals(prev => {
      const newSet = new Set(prev)
      if (newSet.has(templateId)) {
        newSet.delete(templateId)
      } else {
        newSet.add(templateId)
      }
      return newSet
    })
  }

  const showSuccess = (message: string) => {
    setSuccessMessage(message)
    setTimeout(() => setSuccessMessage(null), 3000)
  }

  const showError = (message: string) => {
    setError(message)
    setTimeout(() => setError(null), 5000)
  }

  const createGoalInBackend = async (goalData: any): Promise<UserGoal | null> => {
    try {
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

      const createdGoal = await response.json()
      return {
        id: createdGoal.id,
        userId: createdGoal.user_id,
        templateId: createdGoal.template_id || '',
        name: createdGoal.name,
        description: createdGoal.description || '',
        target: createdGoal.target,
        current: createdGoal.current,
        unit: createdGoal.unit || '',
        period: createdGoal.period,
        startDate: createdGoal.start_date,
        endDate: createdGoal.end_date,
        status: createdGoal.status,
        progress: createdGoal.progress,
        category: createdGoal.category,
        isCustom: createdGoal.is_custom
      }
    } catch (error) {
      throw error
    }
  }

  const updateGoalInBackend = async (goalId: string, updates: any): Promise<boolean> => {
    try {
      const response = await fetch(`/api/backend-proxy/goals/${goalId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: updates.name,
          description: updates.description,
          target: updates.target,
          current: updates.current,
          unit: updates.unit,
          period: updates.period,
          category: updates.category,
          status: updates.status
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Erro ao atualizar meta')
      }

      return true
    } catch (error) {
      throw error
    }
  }

  const deleteGoalInBackend = async (goalId: string): Promise<boolean> => {
    try {
      const response = await fetch(`/api/backend-proxy/goals/${goalId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Erro ao deletar meta')
      }

      return true
    } catch (error) {
      throw error
    }
  }

  const calculateEndDate = (period: string) => {
    const now = new Date()
    const endDate = new Date(now)

    switch (period) {
      case 'monthly':
        endDate.setMonth(endDate.getMonth() + 1)
        break
      case 'quarterly':
        endDate.setMonth(endDate.getMonth() + 3)
        break
      case 'yearly':
        endDate.setFullYear(endDate.getFullYear() + 1)
        break
    }

    return endDate.toISOString().split('T')[0]
  }

  const isTemplateAppliedToUser = useCallback((templateId: string, userId: string): boolean => {
    const userGoals = userGoalsMap[userId]
    if (!userGoals) return false
    const allGoals = [...(userGoals.monthly || []), ...(userGoals.quarterly || []), ...(userGoals.yearly || [])]
    return allGoals.some(g => g.templateId === templateId)
  }, [userGoalsMap])

  const getAppliedTemplatesForUser = useCallback((userId: string): Set<string> => {
    const userGoals = userGoalsMap[userId]
    if (!userGoals) return new Set()
    const allGoals = [...(userGoals.monthly || []), ...(userGoals.quarterly || []), ...(userGoals.yearly || [])]
    return new Set(allGoals.filter(g => g.templateId).map(g => g.templateId))
  }, [userGoalsMap])

  const toggleTemplateSelection = (templateId: string) => {
    setSelectedTemplateIds(prev => {
      const newSet = new Set(prev)
      if (newSet.has(templateId)) {
        newSet.delete(templateId)
      } else {
        newSet.add(templateId)
      }
      return newSet
    })
  }

  const handleApplyTemplate = async (template: GoalTemplate, targetUsers: any[]) => {
    setIsSaving(true)
    setSavingTemplateId(template.id)
    setError(null)

    try {
      let appliedCount = 0
      let skippedCount = 0

      for (const user of targetUsers) {
        if (isTemplateAppliedToUser(template.id, user.id)) {
          skippedCount++
          continue
        }

        const goalData = {
          userId: user.id,
          templateId: template.id,
          name: template.name,
          description: template.description,
          target: template.defaultTarget,
          current: 0,
          unit: template.unit,
          period: template.period,
          startDate: new Date().toISOString().split('T')[0],
          endDate: calculateEndDate(template.period),
          category: template.category,
          isCustom: false
        }

        await createGoalInBackend(goalData)
        await fetchUserGoals(user.id)
        appliedCount++
      }

      if (skippedCount > 0 && appliedCount === 0) {
        showError(`"${template.name}" já está aplicado para todos os usuários selecionados`)
      } else if (skippedCount > 0) {
        showSuccess(`"${template.name}" aplicado para ${appliedCount} usuário(s). ${skippedCount} já tinham essa meta.`)
      } else {
        showSuccess(`"${template.name}" aplicado com sucesso para ${appliedCount} usuário(s)`)
      }
    } catch (error: any) {
      showError(error.message || 'Erro ao aplicar template')
    } finally {
      setIsSaving(false)
      setSavingTemplateId(null)
    }
  }

  const handleApplySelectedTemplates = async () => {
    if (selectedTemplateIds.size === 0) {
      showError('Selecione pelo menos um template')
      return
    }

    const targetUsers = templateApplyMode === 'selected' && selectedUser ? [selectedUser] : users
    
    setIsSaving(true)
    setError(null)

    try {
      const goalsToCreate: any[] = []
      let totalSkipped = 0

      for (const templateId of selectedTemplateIds) {
        const template = filteredTemplates.find(t => t.id === templateId) || goalTemplates.find(t => t.id === templateId)
        if (!template) continue

        for (const user of targetUsers) {
          if (isTemplateAppliedToUser(template.id, user.id)) {
            totalSkipped++
            continue
          }

          goalsToCreate.push({
            userId: user.id,
            templateId: template.id,
            name: template.name,
            description: template.description,
            target: template.defaultTarget,
            current: 0,
            unit: template.unit,
            period: template.period,
            startDate: new Date().toISOString().split('T')[0],
            endDate: calculateEndDate(template.period),
            category: template.category,
            isCustom: false
          })
        }
      }

      const results = await Promise.allSettled(
        goalsToCreate.map(goalData => createGoalInBackend(goalData))
      )

      const totalApplied = results.filter(r => r.status === 'fulfilled').length
      const totalFailed = results.filter(r => r.status === 'rejected').length

      await Promise.all(targetUsers.map(u => fetchUserGoals(u.id)))

      if (totalFailed > 0) {
        showError(`${totalApplied} aplicada(s), ${totalFailed} falharam`)
      } else if (totalSkipped > 0 && totalApplied === 0) {
        showError('Todas as metas selecionadas já estavam aplicadas')
      } else if (totalSkipped > 0) {
        showSuccess(`${totalApplied} meta(s) aplicada(s). ${totalSkipped} duplicata(s) ignorada(s).`)
      } else {
        showSuccess(`${totalApplied} meta(s) aplicada(s) com sucesso!`)
      }

      setSelectedTemplateIds(new Set())
      setShowTemplates(false)
    } catch (error: any) {
      showError(error.message || 'Erro ao aplicar templates')
    } finally {
      setIsSaving(false)
    }
  }

  const handleCreateCustomGoal = async () => {
    const targetUserId = customGoalForm.userId || selectedUser?.id
    const isApplyToAll = targetUserId === '__all__'
    
    if (!targetUserId) {
      showError('Selecione um usuário ou "Todos" para criar a meta')
      return
    }
    
    if (!customGoalForm.name) {
      showError('O nome da meta é obrigatório')
      return
    }

    if (customGoalForm.target <= 0) {
      showError('A meta deve ter um valor maior que zero')
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      const targetUsers = isApplyToAll ? users : [users.find(u => u.id === targetUserId)].filter(Boolean)
      
      for (const user of targetUsers) {
        const goalData = {
          userId: user.id,
          templateId: '',
          name: customGoalForm.name,
          description: customGoalForm.description,
          target: customGoalForm.target,
          current: 0,
          unit: customGoalForm.unit,
          period: customGoalForm.period,
          startDate: customGoalForm.startDate || new Date().toISOString().split('T')[0],
          endDate: customGoalForm.endDate || calculateEndDate(customGoalForm.period),
          category: customGoalForm.category,
          isCustom: true
        }

        await createGoalInBackend(goalData)
        await fetchUserGoals(user.id)
      }

      showSuccess(isApplyToAll 
        ? `Meta "${customGoalForm.name}" criada para ${targetUsers.length} usuários!`
        : 'Meta criada com sucesso!'
      )
      setShowCustomGoal(false)
      setCustomGoalForm({
        name: '',
        description: '',
        target: 0,
        unit: '',
        period: 'monthly',
        category: 'recruitment',
        startDate: '',
        endDate: '',
        userId: ''
      })
      setSelectedUser(null)
    } catch (error: any) {
      showError(error.message || 'Erro ao criar meta')
    } finally {
      setIsSaving(false)
    }
  }

  const handleUpdateGoal = async (goal: UserGoal, updates: Partial<UserGoal>) => {
    setIsSaving(true)
    setError(null)

    try {
      await updateGoalInBackend(goal.id, { ...goal, ...updates })
      await fetchUserGoals(goal.userId)

      showSuccess('Meta atualizada com sucesso!')
      setEditingGoal(null)
    } catch (error: any) {
      showError(error.message || 'Erro ao atualizar meta')
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteGoal = (goal: UserGoal) => {
    setDeleteConfirmGoal(goal)
  }

  const confirmDeleteGoal = async () => {
    if (!deleteConfirmGoal) return

    setIsDeleting(true)
    setError(null)

    try {
      await deleteGoalInBackend(deleteConfirmGoal.id)
      await fetchUserGoals(deleteConfirmGoal.userId)

      showSuccess('Meta excluída com sucesso!')
      setDeleteConfirmGoal(null)
    } catch (error: any) {
      showError(error.message || 'Erro ao excluir meta')
    } finally {
      setIsDeleting(false)
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'recruitment': return <UserCheck className="w-3 h-3 text-gray-500" />
      case 'quality': return <Star className="w-3 h-3 text-gray-500" />
      case 'efficiency': return <Zap className="w-3 h-3 text-gray-500" />
      case 'satisfaction': return <Heart className="w-3 h-3 text-gray-500" />
      default: return <Target className="w-3 h-3 text-gray-500" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'recruitment': return 'bg-gray-100 text-gray-700 border-gray-300'
      case 'quality': return 'bg-status-warning/10 text-status-warning border-status-warning/30'
      case 'efficiency': return 'bg-status-success/10 text-status-success border-status-success/30'
      case 'satisfaction': return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700'
      default: return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'achieved': return 'bg-status-success/15 text-status-success border-status-success/30'
      case 'in_progress': return 'bg-status-warning/10 text-status-warning border-status-warning/30'
      case 'overdue': return 'bg-status-error/15 text-status-error border-status-error/30'
      case 'pending': return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
      default: return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
    }
  }

  const getUserById = (userId: string) => users.find(u => u.id === userId)

  const handleAddUserToTemplate = async (templateId: string) => {
    const template = goalTemplates.find(t => t.id === templateId)
    if (!template) return

    const availableUsers = users.filter(u => !isTemplateAppliedToUser(templateId, u.id))
    if (availableUsers.length === 0) {
      showError('Todos os usuários já possuem esta meta')
      return
    }

    setSelectedUser(availableUsers[0])
    await handleApplyTemplate(getEffectiveTemplate(template), [availableUsers[0]])
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-status-error/10 border border-status-error/30 text-status-error px-4 py-3 rounded-md flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          {error}
        </div>
      )}

      {successMessage && (
        <div className="bg-status-success/10 border border-status-success/30 text-status-success px-4 py-3 rounded-md flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          {successMessage}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h3 className={`${textStyles.titleLarge} flex items-center gap-2`}>
              <Target className="w-5 h-5 text-gray-700 dark:text-gray-300" />
              Gestão de Metas - {selectedYear}
            </h3>
            <p className={textStyles.description}>
              Configure e acompanhe as metas de performance da equipe
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedYear.toString()} onValueChange={(val) => setSelectedYear(parseInt(val))}>
            <SelectTrigger className="w-24 h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024">2024</SelectItem>
              <SelectItem value="2025">2025</SelectItem>
              <SelectItem value="2026">2026</SelectItem>
            </SelectContent>
          </Select>
          <Button 
            variant="outline" 
            onClick={() => setShowTemplates(true)} 
            className="gap-2 h-8 text-xs"
            disabled={users.length === 0 || isLoading}
          >
            <Plus className="w-3.5 h-3.5" />
            Aplicar Template
          </Button>
          <Button 
            onClick={() => {
              setSelectedUser(users.length > 0 ? users[0] : null)
              setCustomGoalForm(prev => ({
                ...prev,
                userId: users.length > 0 ? users[0].id : ''
              }))
              setShowCustomGoal(true)
            }} 
            className="gap-2 h-8 text-xs bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
            disabled={users.length === 0 || isLoading}
          >
            <Target className="w-3.5 h-3.5" />
            Nova Meta
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        <Card className="border border-gray-100 dark:border-gray-800">
          <CardContent className="p-3 text-center">
            <div className={`${textStyles.metricLarge} !text-lg`}>{goalStats.totalTemplates}</div>
            <div className={textStyles.caption}>Templates</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-100 dark:border-gray-800">
          <CardContent className="p-3 text-center">
            <div className={`${textStyles.metricLarge} !text-lg`}>{goalStats.totalAssigned}</div>
            <div className={textStyles.caption}>Atribuídas</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-100 dark:border-gray-800">
          <CardContent className="p-3 text-center">
            <div className={`${textStyles.metricLarge} !text-lg !text-status-success`}>{goalStats.achieved}</div>
            <div className={textStyles.caption}>Atingidas</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-100 dark:border-gray-800">
          <CardContent className="p-3 text-center">
            <div className={`${textStyles.metricLarge} !text-lg !text-status-warning`}>{goalStats.inProgress}</div>
            <div className={textStyles.caption}>Em Progresso</div>
          </CardContent>
        </Card>
        <Card className="border border-gray-100 dark:border-gray-800">
          <CardContent className="p-3 text-center">
            <div className={`${textStyles.metricLarge} !text-lg !text-status-error`}>{goalStats.overdue}</div>
            <div className={textStyles.caption}>Atrasadas</div>
          </CardContent>
        </Card>
      </div>

      <Card className="border border-gray-100 dark:border-gray-800">
        <CardHeader className="py-3 border-b border-gray-100 dark:border-gray-800">
          <CardTitle className={`${textStyles.h4} flex items-center justify-between`}>
            <span>Metas por Categoria</span>
            {isLoading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          {users.length === 0 ? (
            <div className="text-center py-8 text-gray-800 dark:text-gray-200">
              <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className={`${textStyles.titleLarge} mb-2`}>Nenhum usuário cadastrado</h3>
              <p className={textStyles.body}>Primeiro cadastre usuários na aba "Usuários" para poder configurar metas</p>
            </div>
          ) : activeTemplatesWithUsers.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <h3 className={`${textStyles.titleLarge} mb-2 !text-gray-950`}>Nenhuma meta configurada</h3>
              <p className={`${textStyles.body} mb-4`}>
                Clique em "Aplicar Template" para adicionar metas aos usuários
              </p>
              <Button 
                onClick={() => setShowTemplates(true)}
                className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
              >
                <Plus className="w-4 h-4" />
                Aplicar Template
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {activeTemplatesWithUsers.map((template) => {
                const isCollapsed = collapsedGoals.has(template.id)
                const assignedUserObjects = template.assignedUsers
                  .map(uid => getUserById(uid))
                  .filter(Boolean)

                return (
                  <div key={template.id} className="border border-gray-200 dark:border-gray-700 rounded-2xl overflow-hidden">
                    <div 
                      className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors bg-gray-50/50"
                      onClick={() => toggleGoalCollapse(template.id)}
                    >
                      <div className="flex items-center gap-2 flex-1">
                        {isCollapsed ? (
                          <ChevronDown className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronUp className="w-3.5 h-3.5" />
                        )}
                        {getCategoryIcon(template.category)}
                        <div>
                          <h4 className={`${textStyles.label} !text-gray-900 dark:!text-gray-50`}>
                            {template.name}
                          </h4>
                          <p className={textStyles.caption}>
                            {template.description}
                          </p>
                        </div>
                        <Badge className={`text-micro ml-2 ${getCategoryColor(template.category)}`}>
                          {template.category}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-micro gap-1"
                          onClick={() => {
                            setShowApplyAllModal(template.id)
                            const effectiveTemplate = getEffectiveTemplate(template)
                            setApplyAllValue(effectiveTemplate.defaultTarget)
                          }}
                        >
                          <Settings className="w-3 h-3" />
                          Aplicar para Todos
                        </Button>
                      </div>
                    </div>

                    {!isCollapsed && (
                      <div className="border-t border-gray-200 bg-gray-50/50 dark:bg-gray-800/50">
                        <div className="overflow-x-auto">
                        <table className="w-full text-xs font-['Open_Sans',sans-serif]">
                          <thead>
                            <tr className="border-b border-gray-200 dark:border-gray-700">
                              <th className="text-left p-2 min-w-[140px] sticky left-0 bg-gray-50 dark:bg-gray-800 font-medium text-gray-600 dark:text-gray-400 border-r border-gray-200 dark:border-gray-700">
                                Usuário
                              </th>
                              {MONTHS.map((month) => (
                                <th 
                                  key={month.num} 
                                  className="text-center p-2 min-w-10 text-gray-600 font-medium"
                                >
                                  {month.short}
                                </th>
                              ))}
                              <th className="text-center p-2 min-w-[50px] font-semibold text-gray-900 dark:text-gray-50">
                                Total
                              </th>
                            </tr>
                          </thead>
                          <tbody>
                            {assignedUserObjects.map((user: any) => (
                              <tr key={user.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-white dark:hover:bg-gray-800">
                                <td className="p-2 sticky left-0 bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
                                  <div className="flex items-center gap-2">
                                    <Avatar className="w-5 h-5">
                                      <AvatarImage src={user.avatar} alt={user.name} />
                                      <AvatarFallback className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium text-micro">
                                        {user.name.split(' ').map((n: string) => n[0]).join('')}
                                      </AvatarFallback>
                                    </Avatar>
                                    <span className="font-medium text-xs text-gray-800 dark:text-gray-200 truncate">{user.name}</span>
                                  </div>
                                </td>
                                {MONTHS.map((month) => (
                                  <td 
                                    key={month.num} 
                                    className="p-1 text-center"
                                  >
                                    <EditableCell
                                      value={getMonthlyValue(template.id, user.id, month.num, selectedYear)}
                                      onChange={(value) => setMonthlyValue(template.id, user.id, month.num, selectedYear, value)}
                                    />
                                  </td>
                                ))}
                                <td className="p-2 text-center font-semibold text-gray-900 dark:text-gray-50">
                                  {calculateRowTotal(template.id, user.id, selectedYear)}
                                </td>
                              </tr>
                            ))}
                            <tr className="border-t-2 border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800">
                              <td className="p-2 font-semibold text-gray-800 dark:text-gray-200 sticky left-0 bg-gray-100 border-r border-gray-200">
                                TOTAL EQUIPE
                              </td>
                              {MONTHS.map((month) => (
                                <td 
                                  key={month.num} 
                                  className="p-2 text-center font-semibold text-gray-800 dark:text-gray-200"
                                >
                                  {calculateColumnTotal(template.id, month.num, selectedYear, template.assignedUsers)}
                                </td>
                              ))}
                              <td className="p-2 text-center font-bold text-gray-900 dark:text-gray-50">
                                {calculateGrandTotal(template.id, selectedYear, template.assignedUsers)}
                              </td>
                            </tr>
                          </tbody>
                        </table>
                        </div>
                        <div className="p-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleAddUserToTemplate(template.id)}
                            className="text-micro h-6 gap-1.5 rounded-2xl text-gray-700 border-gray-300 hover:bg-gray-100"
                            disabled={isSaving}
                          >
                            <Plus className="w-3 h-3" />
                            Adicionar Usuário
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {showApplyAllModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-md p-6 w-full max-w-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className={textStyles.h4}>
                Aplicar Valor para Todos
              </h3>
              <Button variant="ghost" size="sm" onClick={() => setShowApplyAllModal(null)} className="h-6 w-6 p-0">
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className={`${textStyles.label} block mb-1`}>
                  Valor da Meta
                </label>
                <input
                  type="number"
                  value={applyAllValue}
                  onChange={(e) => setApplyAllValue(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm font-['Open_Sans',sans-serif]"
                />
              </div>

              <div className="space-y-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={applyAllMonths}
                    onChange={(e) => setApplyAllMonths(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 accent-gray-900"
                  />
                  <span className={textStyles.bodySmall}>
                    Aplicar mesmo valor a todos os meses
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={applyAllUsers}
                    onChange={(e) => setApplyAllUsers(e.target.checked)}
                    className="w-4 h-4 rounded border-gray-300 accent-gray-900"
                  />
                  <span className={textStyles.bodySmall}>
                    Aplicar a todos os usuários
                  </span>
                </label>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" size="sm" onClick={() => setShowApplyAllModal(null)}>
                  Cancelar
                </Button>
                <Button 
                  size="sm"
                  onClick={async () => {
                    setShowApplyAllModal(null)
                    await applyValueToAll(showApplyAllModal!, applyAllValue, {
                      allMonths: applyAllMonths,
                      allUsers: applyAllUsers
                    })
                  }}
                  className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                >
                  <Save className="w-3.5 h-3.5 mr-1.5" />
                  Aplicar
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showTemplates && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-md p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h3 className={textStyles.h4}>Templates de Metas</h3>
                <p className={textStyles.caption}>Selecione uma ou mais metas para aplicar</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => {
                setShowTemplates(false)
                setSelectedTemplateIds(new Set())
              }} className="h-6 w-6 p-0">
                <X className="w-3.5 h-3.5" />
              </Button>
            </div>

            {selectedTemplateIds.size > 0 && (
              <div className="border rounded-md px-2.5 py-1.5 mb-3 flex items-center justify-between bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-600">
                <div className="flex items-center gap-1.5">
                  <CheckCircle className="w-3 h-3 text-gray-700 dark:text-gray-300" />
                  <span className={textStyles.caption}>
                    <strong>{selectedTemplateIds.size}</strong> template(s) selecionado(s)
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <select
                    value={templateApplyMode}
                    onChange={(e) => setTemplateApplyMode(e.target.value as 'all' | 'selected')}
                    className="border rounded-full px-1.5 py-0.5 text-micro bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 font-['Open_Sans',sans-serif]"
                  >
                    <option value="all">Aplicar a todos usuários</option>
                    {selectedUser && <option value="selected">Aplicar a {selectedUser.name}</option>}
                  </select>
                  <Button
                    size="sm"
                    onClick={handleApplySelectedTemplates}
                    disabled={isSaving}
                    className="text-micro h-6 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 font-['Open_Sans',sans-serif]"
                  >
                    {isSaving ? <Loader2 className="w-2.5 h-2.5 animate-spin mr-1" /> : <Plus className="w-2.5 h-2.5 mr-1" />}
                    Aplicar Selecionados
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedTemplateIds(new Set())}
                    className="text-micro h-6 font-['Open_Sans',sans-serif]"
                  >
                    Limpar
                  </Button>
                </div>
              </div>
            )}

            <div className="flex gap-2 mb-3">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3 h-3 text-gray-400 dark:text-gray-500" />
                  <input
                    type="text"
                    placeholder="Buscar templates..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-7 pr-2.5 py-1 border border-gray-200 dark:border-gray-700 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-micro font-['Open_Sans',sans-serif]"
                  />
                </div>
              </div>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="border border-gray-200 dark:border-gray-700 rounded-full bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-2 py-1 text-micro font-['Open_Sans',sans-serif]"
              >
                <option value="all">Todas Categorias</option>
                <option value="recruitment">Recrutamento</option>
                <option value="quality">Qualidade</option>
                <option value="efficiency">Eficiência</option>
                <option value="satisfaction">Satisfação</option>
              </select>
              <select
                value={filterPeriod}
                onChange={(e) => setFilterPeriod(e.target.value)}
                className="border border-gray-200 dark:border-gray-700 rounded-full bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 px-2 py-1 text-micro font-['Open_Sans',sans-serif]"
              >
                <option value="all">Todos Períodos</option>
                <option value="monthly">Mensal</option>
                <option value="quarterly">Trimestral</option>
                <option value="yearly">Anual</option>
              </select>
            </div>

            {hiddenTemplates.size > 0 && (
              <div className="bg-status-warning/10 border border-status-warning/30 rounded-md px-3 py-1.5 mb-4 flex items-center justify-between">
                <span className={`${textStyles.bodySmall} !text-status-warning`}>
                  {hiddenTemplates.size} template(s) oculto(s)
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setHiddenTemplates(new Set())}
                  className="text-xs text-status-warning hover:text-status-warning hover:bg-status-warning/15 h-7 font-['Open_Sans',sans-serif]"
                >
                  Restaurar Todos
                </Button>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredTemplates.map((template) => {
                const appliedCount = Object.values(userGoalsMap).reduce((count, periodGoals) => {
                  const allGoals = [...(periodGoals.monthly || []), ...(periodGoals.quarterly || []), ...(periodGoals.yearly || [])]
                  return count + (allGoals.some(g => g.templateId === template.id) ? 1 : 0)
                }, 0)
                const isAppliedToAll = appliedCount === users.length && users.length > 0
                const isPartiallyApplied = appliedCount > 0 && appliedCount < users.length
                const isSelected = selectedTemplateIds.has(template.id)
                const isAppliedToSelectedUser = selectedUser ? isTemplateAppliedToUser(template.id, selectedUser.id) : false
                
                return (
                <div 
                  key={template.id} 
                  onClick={() => !isAppliedToAll && toggleTemplateSelection(template.id)}
                  className={`border rounded-md p-3 transition-all cursor-pointer ${
                    isAppliedToAll 
                      ? 'border-status-success/30 bg-status-success/10 opacity-60 cursor-not-allowed' 
                      : isSelected
                        ? 'border-gray-900 bg-gray-50 ring-2 ring-gray-400'
                        : isPartiallyApplied 
                          ? 'border-status-warning/30 bg-status-warning/10 hover:border-gray-400' 
                          : 'border-gray-200 hover:border-gray-400 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-colors ${
                        isAppliedToAll 
                          ? 'bg-status-success border-status-success/30'
                          : isSelected 
                            ? 'bg-gray-900 border-gray-900 dark:bg-gray-50 dark:border-gray-50' 
                            : 'border-gray-300 bg-white'
                      }`}>
                        {(isSelected || isAppliedToAll) && <CheckCircle className="w-2.5 h-2.5 text-white dark:text-gray-900" />}
                      </div>
                      {getCategoryIcon(template.category)}
                      <div>
                        <h4 className={textStyles.label}>{template.name}</h4>
                        <p className={textStyles.caption}>{template.description}</p>
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-0.5">
                      <Badge className={`text-micro px-1.5 py-0.5 font-['Open_Sans',sans-serif] ${getCategoryColor(template.category)}`}>
                        {template.category}
                      </Badge>
                      {isAppliedToAll && (
                        <Badge className="text-micro px-1.5 py-0.5 bg-status-success/15 text-status-success border-status-success/30 font-['Open_Sans',sans-serif]">
                          <CheckCircle className="w-2.5 h-2.5 mr-0.5" />
                          Aplicado a Todos
                        </Badge>
                      )}
                      {isPartiallyApplied && (
                        <Badge className="text-micro px-1.5 py-0.5 bg-status-warning/15 text-status-warning border-status-warning/30 font-['Open_Sans',sans-serif]">
                          {appliedCount}/{users.length} usuários
                        </Badge>
                      )}
                      {selectedUser && isAppliedToSelectedUser && !isAppliedToAll && (
                        <Badge className="text-micro px-1.5 py-0.5 bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700 font-['Open_Sans',sans-serif]">
                          Já aplicado a {selectedUser.name.split(' ')[0]}
                        </Badge>
                      )}
                    </div>
                  </div>
                  
                  <div className="bg-gray-50 rounded px-1.5 py-1 mb-2 border-l-2 border-gray-400 ml-6">
                    <div className="flex items-start gap-1">
                      <BarChart3 className="w-2.5 h-2.5 text-gray-500 dark:text-gray-400 mt-0.5 flex-shrink-0" />
                      <p className={textStyles.caption}>
                        <span className="font-medium text-gray-600 dark:text-gray-400">Como é calculado:</span>{' '}
                        {template.formula}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-micro ml-6">
                    <span className={textStyles.caption}>
                      Meta: {template.defaultTarget} {template.unit}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <Badge variant="outline" className="text-micro px-1.5 py-0.5 font-['Open_Sans',sans-serif]">
                        {template.period === 'monthly' ? 'Mensal' :
                         template.period === 'quarterly' ? 'Trimestral' : 'Anual'}
                      </Badge>
                      <div className="flex items-center gap-0.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setEditingTemplate(template)
                          }}
                          className="h-5 w-5 p-0 hover:bg-gray-100 hover:text-gray-900"
                          title="Editar template"
                        >
                          <Edit className="w-2.5 h-2.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setHiddenTemplates(prev => new Set([...prev, template.id]))
                          }}
                          className="h-5 w-5 p-0 hover:bg-status-error/10 hover:text-status-error"
                          title="Ocultar template"
                        >
                          <X className="w-2.5 h-2.5" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )})}
            </div>
          </div>
        </div>
      )}

      {showCustomGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-md p-6 w-full max-w-lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Nova Meta Customizada</h3>
              <Button variant="ghost" onClick={() => {
                setShowCustomGoal(false)
                setSelectedUser(null)
              }}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                  Aplicar para *
                </label>
                <Select
                  value={customGoalForm.userId || selectedUser?.id || ''}
                  onValueChange={(value) => {
                    setCustomGoalForm(prev => ({ ...prev, userId: value }))
                    if (value === '__all__') {
                      setSelectedUser(null)
                    } else {
                      setSelectedUser(users.find(u => u.id === value) || null)
                    }
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione usuário ou todos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all__">
                      <span className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-gray-700 dark:text-gray-300" />
                        <span className="font-medium">Todos os Usuários</span>
                      </span>
                    </SelectItem>
                    <div className="border-t border-gray-200 my-1" />
                    {users.map((user) => (
                      <SelectItem key={user.id} value={user.id}>
                        {user.name} - {user.role}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {customGoalForm.userId === '__all__' && (
                  <p className={`${textStyles.caption} mt-1`}>
                    A meta será criada para todos os {users.length} usuários
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                  Nome da Meta *
                </label>
                <input
                  type="text"
                  value={customGoalForm.name}
                  onChange={(e) => setCustomGoalForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  placeholder="Ex: Aumentar taxa de conversão"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                  Descrição
                </label>
                <textarea
                  value={customGoalForm.description}
                  onChange={(e) => setCustomGoalForm(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  rows={2}
                  placeholder="Descreva a meta..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Meta *
                  </label>
                  <input
                    type="number"
                    value={customGoalForm.target}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, target: parseFloat(e.target.value) || 0 }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    min="0"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Unidade
                  </label>
                  <input
                    type="text"
                    value={customGoalForm.unit}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, unit: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    placeholder="Ex: %, dias, contratações"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Período
                  </label>
                  <select
                    value={customGoalForm.period}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, period: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="monthly">Mensal</option>
                    <option value="quarterly">Trimestral</option>
                    <option value="yearly">Anual</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Categoria
                  </label>
                  <select
                    value={customGoalForm.category}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, category: e.target.value as any }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="recruitment">Recrutamento</option>
                    <option value="quality">Qualidade</option>
                    <option value="efficiency">Eficiência</option>
                    <option value="satisfaction">Satisfação</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Data Início
                  </label>
                  <input
                    type="date"
                    value={customGoalForm.startDate}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, startDate: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Data Fim
                  </label>
                  <input
                    type="date"
                    value={customGoalForm.endDate}
                    onChange={(e) => setCustomGoalForm(prev => ({ ...prev, endDate: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button variant="outline" onClick={() => {
                  setShowCustomGoal(false)
                  setSelectedUser(null)
                }}>
                  Cancelar
                </Button>
                <Button onClick={handleCreateCustomGoal} disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Criar Meta
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {editingGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-md p-6 w-full max-w-lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Editar Meta</h3>
              <Button variant="ghost" onClick={() => setEditingGoal(null)}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                  Nome da Meta
                </label>
                <input
                  type="text"
                  value={editingGoal.name}
                  onChange={(e) => setEditingGoal(prev => prev ? { ...prev, name: e.target.value } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Meta
                  </label>
                  <input
                    type="number"
                    value={editingGoal.target}
                    onChange={(e) => setEditingGoal(prev => prev ? { ...prev, target: parseFloat(e.target.value) || 0 } : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    min="0"
                    step="0.1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                    Atual
                  </label>
                  <input
                    type="number"
                    value={editingGoal.current}
                    onChange={(e) => setEditingGoal(prev => prev ? { ...prev, current: parseFloat(e.target.value) || 0 } : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    min="0"
                    step="0.1"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-gray-200 mb-1">
                  Status
                </label>
                <select
                  value={editingGoal.status}
                  onChange={(e) => setEditingGoal(prev => prev ? { ...prev, status: e.target.value as any } : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="pending">Pendente</option>
                  <option value="in_progress">Em Progresso</option>
                  <option value="achieved">Atingida</option>
                  <option value="overdue">Atrasada</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button variant="outline" onClick={() => setEditingGoal(null)}>
                  Cancelar
                </Button>
                <Button 
                  onClick={() => handleUpdateGoal(editingGoal, editingGoal)}
                  disabled={isSaving}
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Salvando...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Salvar Alterações
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {deleteConfirmGoal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-md w-full max-w-md mx-4 overflow-hidden">
            <div className="bg-status-error/10 px-6 py-4 border-b border-status-error/30">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-status-error/15 flex items-center justify-center">
                  <Trash2 className="w-5 h-5 text-status-error" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-950">Excluir Meta</h3>
                  <p className="text-sm text-gray-600">Esta ação não pode ser desfeita</p>
                </div>
              </div>
            </div>

            <div className="p-6">
              <div className="bg-gray-50 rounded-md p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  {getCategoryIcon(deleteConfirmGoal.category)}
                  <span className="font-medium text-gray-950">{deleteConfirmGoal.name}</span>
                </div>
                <p className="text-sm text-gray-600">{deleteConfirmGoal.description}</p>
                <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                  <span>Meta: {deleteConfirmGoal.target} {deleteConfirmGoal.unit}</span>
                  <span>•</span>
                  <span>{deleteConfirmGoal.period === 'monthly' ? 'Mensal' : 
                         deleteConfirmGoal.period === 'quarterly' ? 'Trimestral' : 'Anual'}</span>
                </div>
              </div>

              <p className="text-sm text-gray-600 mb-6">
                Tem certeza que deseja excluir esta meta? O progresso registrado será perdido permanentemente.
              </p>

              <div className="flex justify-end gap-3">
                <Button 
                  variant="outline" 
                  onClick={() => setDeleteConfirmGoal(null)}
                  disabled={isDeleting}
                >
                  Cancelar
                </Button>
                <Button 
                  onClick={confirmDeleteGoal}
                  disabled={isDeleting}
                  className="bg-status-error hover:bg-status-error text-white"
                >
                  {isDeleting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Excluindo...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4 mr-2" />
                      Sim, Excluir
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {editingTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-md w-full max-w-md mx-4 overflow-hidden">
            <div className="bg-gray-50 px-5 py-3 border-b border-gray-100">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-200">
                  <Settings className="w-4 h-4 text-gray-700" />
                </div>
                <div>
                  <h3 className={textStyles.h4}>Editar Template</h3>
                  <p className={textStyles.caption}>Personalize os valores padrão</p>
                </div>
              </div>
            </div>

            <div className="p-5 space-y-3">
              <div>
                <label className={`${textStyles.label} block mb-1`}>Nome da Meta</label>
                <input
                  type="text"
                  value={editingTemplate.name}
                  onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, name: e.target.value } : null)}
                  className="w-full px-2.5 py-1.5 border border-gray-200 rounded-md text-xs font-['Open_Sans',sans-serif]"
                />
              </div>

              <div>
                <label className={`${textStyles.label} block mb-1`}>Descrição</label>
                <input
                  type="text"
                  value={editingTemplate.description}
                  onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, description: e.target.value } : null)}
                  className="w-full px-2.5 py-1.5 border border-gray-200 rounded-md text-xs font-['Open_Sans',sans-serif]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={`${textStyles.label} block mb-1`}>Meta Padrão</label>
                  <input
                    type="number"
                    value={editingTemplate.defaultTarget}
                    onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, defaultTarget: parseFloat(e.target.value) || 0 } : null)}
                    className="w-full px-2.5 py-1.5 border border-gray-200 rounded-md text-xs font-['Open_Sans',sans-serif]"
                  />
                </div>
                <div>
                  <label className={`${textStyles.label} block mb-1`}>Unidade</label>
                  <input
                    type="text"
                    value={editingTemplate.unit}
                    onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, unit: e.target.value } : null)}
                    className="w-full px-2.5 py-1.5 border border-gray-200 rounded-md text-xs font-['Open_Sans',sans-serif]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className={`${textStyles.label} block mb-1`}>Período</label>
                  <select
                    value={editingTemplate.period}
                    onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, period: e.target.value as any } : null)}
                    className="w-full px-2.5 py-1.5 border border-gray-200 rounded-md text-xs font-['Open_Sans',sans-serif]"
                  >
                    <option value="monthly">Mensal</option>
                    <option value="quarterly">Trimestral</option>
                    <option value="yearly">Anual</option>
                  </select>
                </div>
                <div>
                  <label className={`${textStyles.label} block mb-1`}>Categoria</label>
                  <select
                    value={editingTemplate.category}
                    onChange={(e) => setEditingTemplate(prev => prev ? { ...prev, category: e.target.value as any } : null)}
                    className="w-full px-2.5 py-1.5 border border-gray-200 rounded-md text-xs font-['Open_Sans',sans-serif]"
                  >
                    <option value="recruitment">Recrutamento</option>
                    <option value="quality">Qualidade</option>
                    <option value="efficiency">Eficiência</option>
                    <option value="satisfaction">Satisfação</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setEditingTemplate(null)}
                  className="text-xs h-8 font-['Open_Sans',sans-serif]"
                >
                  Cancelar
                </Button>
                <Button 
                  size="sm"
                  onClick={() => {
                    if (editingTemplate) {
                      setTemplateOverrides(prev => ({
                        ...prev,
                        [editingTemplate.id]: {
                          name: editingTemplate.name,
                          description: editingTemplate.description,
                          defaultTarget: editingTemplate.defaultTarget,
                          unit: editingTemplate.unit,
                          period: editingTemplate.period,
                          category: editingTemplate.category
                        }
                      }))
                      setEditingTemplate(null)
                    }
                  }}
                  className="text-xs h-8 font-['Open_Sans',sans-serif] bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
                >
                  <Save className="w-3 h-3 mr-1.5" />
                  Salvar Alterações
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
