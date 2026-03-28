"use client"

import React, { useState, useMemo, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Target, Bell, Calendar, Plus, Edit, Trash2, Save, X,
  TrendingUp, BarChart3, Users, AlertCircle, CheckCircle, Clock,
  Brain, Settings, Mail, MessageSquare, Zap, Download,
  ChevronDown, ChevronUp, Eye, RefreshCw, Loader2
} from "lucide-react"
import { GoalsManagement } from "./goals-management"
import { SmartImportZone } from "./SmartImportZone"
import { LiaFieldToggle, defaultLiaFieldExamples } from "./LiaFieldToggle"
import { useCompanyLiaInstructions } from "@/hooks/use-company-lia-instructions"
import { textStyles, cardStyles, badgeStyles, buttonStyles, tabStyles, actionButtonStyles } from '@/lib/design-tokens'

interface AlertConfig {
  id: string
  name: string
  description: string
  enabled: boolean
  channel: 'email' | 'teams' | 'both'
}

interface MonthlyPlanning {
  jan: number
  feb: number
  mar: number
  apr: number
  may: number
  jun: number
  jul: number
  aug: number
  sep: number
  oct: number
  nov: number
  dec: number
}

interface Position {
  id: string
  name: string
  salary_min?: number
  salary_max?: number
  monthlyPlanned: MonthlyPlanning
}

interface DepartmentData {
  id: string
  name: string
  positions: Position[]
  expanded: boolean
}

interface WorkforceEntry {
  month: string
  department: string
  planned: number
  actual: number
  aiSuggestion?: number
}

interface GoalsPlanningHubProps {
  users?: any[]
  onGoalUpdate?: (userId: string, goals: any) => void
  activeSubsection?: string
}

const defaultAlerts: AlertConfig[] = [
  { id: '1', name: 'SLA Próximo do Vencimento', description: 'Alerta quando um candidato está há 80% do SLA na mesma etapa', enabled: true, channel: 'both' },
  { id: '2', name: 'Meta Mensal em Risco', description: 'Notifica quando a meta de contratações do mês pode não ser atingida', enabled: true, channel: 'email' },
  { id: '3', name: 'Candidato Sem Interação', description: 'Alerta para candidatos sem contato há mais de 5 dias', enabled: true, channel: 'teams' },
  { id: '4', name: 'Entrevista Não Confirmada', description: 'Lembrete 24h antes de entrevistas sem confirmação', enabled: true, channel: 'both' },
  { id: '5', name: 'Feedback Pendente', description: 'Solicita feedback após 48h de entrevista realizada', enabled: false, channel: 'email' }
]

const mockWorkforce: WorkforceEntry[] = [
  { month: 'Jan', department: 'Tecnologia', planned: 5, actual: 4, aiSuggestion: 6 },
  { month: 'Fev', department: 'Tecnologia', planned: 4, actual: 5 },
  { month: 'Mar', department: 'Tecnologia', planned: 6, actual: 0, aiSuggestion: 5 },
  { month: 'Jan', department: 'Comercial', planned: 3, actual: 3 },
  { month: 'Fev', department: 'Comercial', planned: 2, actual: 2 },
  { month: 'Mar', department: 'Comercial', planned: 4, actual: 0, aiSuggestion: 3 },
  { month: 'Jan', department: 'RH', planned: 1, actual: 1 },
  { month: 'Fev', department: 'RH', planned: 1, actual: 0 },
  { month: 'Mar', department: 'RH', planned: 2, actual: 0, aiSuggestion: 1 }
]

const departments = ['Tecnologia', 'Comercial', 'RH', 'Financeiro', 'Marketing']
const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

export function GoalsPlanningHub({ users = [], onGoalUpdate, activeSubsection }: GoalsPlanningHubProps) {
  const [activeTab, setActiveTab] = useState(activeSubsection || 'workforce')
  const [alerts, setAlerts] = useState<AlertConfig[]>(defaultAlerts)
  const [workforce, setWorkforce] = useState<WorkforceEntry[]>(mockWorkforce)
  const [briefingFrequency, setBriefingFrequency] = useState<'twice_daily' | 'daily' | 'weekly' | 'monthly'>('daily')
  const [selectedYear, setSelectedYear] = useState(2024)
  const emptyMonthlyPlanning: MonthlyPlanning = { jan: 0, feb: 0, mar: 0, apr: 0, may: 0, jun: 0, jul: 0, aug: 0, sep: 0, oct: 0, nov: 0, dec: 0 }
  
  const { config, instructions: liaInstructions, toggles: liaToggles, refetch: refetchLiaConfig } = useCompanyLiaInstructions()
  
  const [departments, setDepartments] = useState<DepartmentData[]>([
    { id: '1', name: 'Tecnologia', positions: [
      { id: '1a', name: 'Backend Developer', salary_min: 8000, salary_max: 15000, monthlyPlanned: { jan: 1, feb: 1, mar: 0, apr: 1, may: 0, jun: 1, jul: 0, aug: 0, sep: 1, oct: 0, nov: 0, dec: 0 } },
      { id: '1b', name: 'Frontend Developer', salary_min: 7000, salary_max: 14000, monthlyPlanned: { jan: 0, feb: 1, mar: 0, apr: 0, may: 1, jun: 0, jul: 0, aug: 1, sep: 0, oct: 0, nov: 0, dec: 0 } }
    ], expanded: true },
    { id: '2', name: 'Comercial', positions: [
      { id: '2a', name: 'Account Executive', salary_min: 6000, salary_max: 12000, monthlyPlanned: { jan: 1, feb: 0, mar: 1, apr: 0, may: 0, jun: 1, jul: 0, aug: 0, sep: 0, oct: 0, nov: 0, dec: 0 } }
    ], expanded: true },
    { id: '3', name: 'RH', positions: [
      { id: '3a', name: 'Recrutador', salary_min: 4000, salary_max: 8000, monthlyPlanned: { jan: 0, feb: 0, mar: 1, apr: 0, may: 0, jun: 0, jul: 0, aug: 0, sep: 1, oct: 0, nov: 0, dec: 0 } }
    ], expanded: false },
    { id: '4', name: 'Financeiro', positions: [
      { id: '4a', name: 'Controller', salary_min: 12000, salary_max: 20000, monthlyPlanned: { jan: 0, feb: 0, mar: 0, apr: 0, may: 1, jun: 0, jul: 0, aug: 0, sep: 0, oct: 0, nov: 0, dec: 0 } }
    ], expanded: false }
  ])
  
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [goalsRefreshKey, setGoalsRefreshKey] = useState(0)
  const [fetchedUsers, setFetchedUsers] = useState<any[]>([])
  const [departmentsLoaded, setDepartmentsLoaded] = useState(false)
  
  const [isEditingWorkforce, setIsEditingWorkforce] = useState(false)
  const [isEditingAlerts, setIsEditingAlerts] = useState(false)

  const fetchDepartmentsFromBackend = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/company/departments')
      if (response.ok) {
        const backendDepts = await response.json()
        if (Array.isArray(backendDepts) && backendDepts.length > 0) {
          setDepartments(prevDepts => {
            const existingPositionsMap = new Map(prevDepts.map(d => [d.id, d.positions]))
            const existingByName = new Map(prevDepts.map(d => [d.name.toLowerCase(), d.positions]))
            
            return backendDepts.map((d: any) => ({
              id: d.id,
              name: d.name,
              positions: existingPositionsMap.get(d.id) || existingByName.get(d.name.toLowerCase()) || [],
              expanded: false
            }))
          })
          setDepartmentsLoaded(true)
        } else {
          setDepartmentsLoaded(true)
        }
      }
    } catch (err) {
      console.error('Error fetching departments:', err)
      setDepartmentsLoaded(true)
    }
  }, [])

  const createDepartmentInBackend = useCallback(async (name: string): Promise<string | null> => {
    try {
      const response = await fetch('/api/backend-proxy/company/departments?company_id=default', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description: `Departamento criado via Planejamento de Contratações`,
          headcount: 0
        })
      })
      
      if (response.ok) {
        const newDept = await response.json()
        return newDept.id
      }
      return null
    } catch (err) {
      console.error('Error creating department in backend:', err)
      return null
    }
  }, [])

  const fetchCompanyUsers = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/company/users')
      if (response.ok) {
        const data = await response.json()
        const mappedUsers = data.map((u: any) => ({
          id: u.id,
          name: u.name,
          email: u.email,
          role: u.role || 'Recrutador',
          department: u.department || 'Talent Acquisition',
          isActive: u.is_active,
          avatar: u.avatar_url
        }))
        setFetchedUsers(mappedUsers)
      }
    } catch (err) {
      console.error('Error fetching company users:', err)
    }
  }, [])

  useEffect(() => {
    if (users.length === 0) {
      fetchCompanyUsers()
    }
  }, [users.length, fetchCompanyUsers])

  useEffect(() => {
    fetchDepartmentsFromBackend()
  }, [fetchDepartmentsFromBackend])

  const effectiveUsers = users.length > 0 ? users : fetchedUsers

  const fetchWorkforceData = useCallback(async () => {
    try {
      const workforceRes = await fetch('/api/backend-proxy/workforce')
      if (workforceRes.ok) {
        const workforceResult = await workforceRes.json()
        if (Array.isArray(workforceResult) && workforceResult.length > 0) {
          setWorkforce(workforceResult.map((w: any) => ({
            month: w.month,
            department: w.department,
            planned: w.planned || 0,
            actual: w.actual || 0,
            aiSuggestion: w.ai_suggestion
          })))
        }
      }
    } catch (err) {
      console.error('Error fetching workforce data:', err)
    }
  }, [])

  const fetchGoals = useCallback(() => {
    setGoalsRefreshKey(prev => prev + 1)
  }, [])

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)
        
        const [alertsRes, workforceRes] = await Promise.all([
          fetch('/api/backend-proxy/alerts/config'),
          fetch('/api/backend-proxy/workforce')
        ])
        
        if (alertsRes.ok) {
          const alertsResult = await alertsRes.json()
          if (alertsResult && Array.isArray(alertsResult.alerts)) {
            setAlerts(alertsResult.alerts.map((a: any) => ({
              id: a.id,
              name: a.name,
              description: a.description,
              enabled: a.enabled ?? true,
              channel: a.channel || 'email'
            })))
          }
          if (alertsResult?.briefing_frequency) {
            setBriefingFrequency(alertsResult.briefing_frequency)
          }
        }
        
        if (workforceRes.ok) {
          const workforceResult = await workforceRes.json()
          if (Array.isArray(workforceResult) && workforceResult.length > 0) {
            setWorkforce(workforceResult.map((w: any) => ({
              month: w.month,
              department: w.department,
              planned: w.planned || 0,
              actual: w.actual || 0,
              aiSuggestion: w.ai_suggestion
            })))
          }
        }
      } catch (err) {
        console.error('Error fetching goals data:', err)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [])

  const saveAlertsConfig = async () => {
    try {
      setSaving(true)
      const response = await fetch('/api/backend-proxy/alerts/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          alerts: alerts.map(a => ({
            id: a.id,
            name: a.name,
            description: a.description,
            enabled: a.enabled,
            channel: a.channel
          })),
          briefing_frequency: briefingFrequency
        })
      })
      
      if (!response.ok) {
        throw new Error('Falha ao salvar configuração de alertas')
      }
      
      setSuccessMessage('Configuração salva com sucesso!')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  const saveWorkforceData = async () => {
    try {
      setSaving(true)
      const response = await fetch('/api/backend-proxy/workforce', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          year: selectedYear,
          entries: workforce.map(w => ({
            month: w.month,
            department: w.department,
            planned: w.planned,
            actual: w.actual
          }))
        })
      })
      
      if (!response.ok) {
        throw new Error('Falha ao salvar planejamento')
      }
      
      setSuccessMessage('Planejamento salvo com sucesso!')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  const getCompanyId = async (): Promise<string> => {
    try {
      const res = await fetch('/api/backend-proxy/company/profile')
      if (res.ok) {
        const company = await res.json()
        return company.id || 'default'
      }
    } catch (e) {
      console.error('Error fetching company:', e)
    }
    return 'default'
  }

  const handleLiaToggleChange = async (fieldKey: string, isActive: boolean) => {
    try {
      const updatedToggles = {
        ...liaToggles,
        [fieldKey]: isActive
      }
      
      const companyId = await getCompanyId()
      const response = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${companyId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lia_field_toggles: updatedToggles
        })
      })
      
      if (!response.ok) {
        throw new Error('Falha ao salvar toggle do campo')
      }
      
      await refetchLiaConfig()
    } catch (err) {
      console.error('Error saving LIA field toggle:', err)
      setError(err instanceof Error ? err.message : 'Erro ao salvar toggle')
      setTimeout(() => setError(null), 3000)
    }
  }

  const handleLiaInstructionSave = async (fieldKey: string, instruction: string) => {
    try {
      const updatedInstructions = {
        ...liaInstructions,
        [fieldKey]: instruction
      }
      
      const companyId = await getCompanyId()
      const response = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${companyId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lia_instructions: updatedInstructions
        })
      })
      
      if (!response.ok) {
        throw new Error('Falha ao salvar instrução')
      }
      
      await refetchLiaConfig()
      setSuccessMessage('Instrução salva com sucesso!')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      console.error('Error saving LIA instruction:', err)
      setError(err instanceof Error ? err.message : 'Erro ao salvar instrução')
      setTimeout(() => setError(null), 3000)
    }
  }

  const tabs = [
    { id: 'workforce', label: 'Planejamento de Contratações', icon: Calendar }
  ]

  const handleToggleAlert = (id: string) => {
    setAlerts(prev => prev.map(a => 
      a.id === id ? { ...a, enabled: !a.enabled } : a
    ))
  }

  const handleChangeChannel = (id: string, channel: 'email' | 'teams' | 'both') => {
    setAlerts(prev => prev.map(a => 
      a.id === id ? { ...a, channel } : a
    ))
  }

  const handleUpdateWorkforce = (month: string, department: string, value: number) => {
    setWorkforce(prev => {
      const existing = prev.find(w => w.month === month && w.department === department)
      if (existing) {
        return prev.map(w => 
          w.month === month && w.department === department 
            ? { ...w, planned: value }
            : w
        )
      }
      return [...prev, { month, department, planned: value, actual: 0 }]
    })
  }

  const getWorkforceValue = (month: string, department: string) => {
    return workforce.find(w => w.month === month && w.department === department)
  }

  const monthKeys: (keyof MonthlyPlanning)[] = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
  const monthLabels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

  const getPositionTotal = (pos: Position) => {
    return monthKeys.reduce((sum, key) => sum + pos.monthlyPlanned[key], 0)
  }

  const workforceStats = useMemo(() => {
    const totalPlanned = departments.reduce((acc, d) => acc + d.positions.reduce((pAcc, p) => pAcc + getPositionTotal(p), 0), 0)
    return { totalPlanned }
  }, [departments])

  const toggleDepartmentExpand = (deptId: string) => {
    setDepartments(prev => prev.map(d => d.id === deptId ? { ...d, expanded: !d.expanded } : d))
  }

  const addDepartment = async () => {
    const tempId = `temp-${Date.now()}`
    const newName = 'Novo Departamento'
    
    const newDept: DepartmentData = {
      id: tempId,
      name: newName,
      positions: [{ id: `${tempId}-0`, name: 'Nova Posição', salary_min: undefined, salary_max: undefined, monthlyPlanned: { ...emptyMonthlyPlanning } }],
      expanded: true
    }
    setDepartments(prev => [...prev, newDept])
    
    const backendId = await createDepartmentInBackend(newName)
    if (backendId) {
      setDepartments(prev => prev.map(d => d.id === tempId ? { ...d, id: backendId } : d))
      setSuccessMessage('Departamento criado e sincronizado com o sistema!')
      setTimeout(() => setSuccessMessage(null), 3000)
    } else {
      setDepartments(prev => prev.filter(d => d.id !== tempId))
      setError('Falha ao criar departamento no sistema. Tente novamente.')
      setTimeout(() => setError(null), 5000)
    }
  }

  const addPositionToDepartment = (deptId: string) => {
    setDepartments(prev => prev.map(d => 
      d.id === deptId 
        ? { ...d, positions: [...d.positions, { id: Date.now().toString(), name: 'Nova Posição', salary_min: undefined, salary_max: undefined, monthlyPlanned: { ...emptyMonthlyPlanning } }] }
        : d
    ))
  }

  const updatePositionSalary = (deptId: string, posId: string, field: 'salary_min' | 'salary_max', value: number | undefined) => {
    setDepartments(prev => prev.map(d => 
      d.id === deptId 
        ? { ...d, positions: d.positions.map(p => p.id === posId ? { ...p, [field]: value } : p) }
        : d
    ))
  }

  const updatePositionName = (deptId: string, posId: string, name: string) => {
    setDepartments(prev => prev.map(d => 
      d.id === deptId 
        ? { ...d, positions: d.positions.map(p => p.id === posId ? { ...p, name } : p) }
        : d
    ))
  }

  const updatePositionMonth = (deptId: string, posId: string, month: keyof MonthlyPlanning, value: number) => {
    setDepartments(prev => prev.map(d => 
      d.id === deptId 
        ? { ...d, positions: d.positions.map(p => p.id === posId ? { ...p, monthlyPlanned: { ...p.monthlyPlanned, [month]: value } } : p) }
        : d
    ))
  }

  const deletePosition = (deptId: string, posId: string) => {
    setDepartments(prev => prev.map(d => 
      d.id === deptId 
        ? { ...d, positions: d.positions.filter(p => p.id !== posId) }
        : d
    ))
  }

  const updateDepartmentName = async (deptId: string, name: string) => {
    setDepartments(prev => prev.map(d => d.id === deptId ? { ...d, name } : d))
    
    if (deptId.startsWith('temp-')) return
    
    try {
      await fetch(`/api/backend-proxy/company/departments/${deptId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      })
    } catch (err) {
      console.error('Error updating department name in backend:', err)
    }
  }

  const renderGoals = () => (
    <div className="space-y-4">
      <SmartImportZone
        title="Importar Metas"
        description="Importe metas mensais ou trimestrais por recrutador via planilha. A LIA identifica período, responsável e valores automaticamente."
        importEndpoint="/api/backend-proxy/goals/import"
        templateDownloadEndpoint="/api/backend-proxy/goals/import/template"
        expectedFields={["user_id", "name", "target", "period", "category"]}
        onImportSuccess={fetchGoals}
      />

      <GoalsManagement 
        key={goalsRefreshKey}
        users={effectiveUsers} 
        onGoalUpdate={onGoalUpdate || (() => {})} 
      />
    </div>
  )

  const renderAlerts = () => (
    <div className="space-y-3">
      {successMessage && (
        <div className={`${badgeStyles.success} px-3 py-2 flex items-center gap-2 w-full`}>
          <CheckCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span className={textStyles.body}>{successMessage}</span>
        </div>
      )}
      {error && (
        <div className={`${badgeStyles.error} px-3 py-2 flex items-center gap-2 w-full`}>
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span className={textStyles.body}>{error}</span>
        </div>
      )}
      <Card className={cardStyles.default}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h3} flex items-center gap-2`}>
                <Bell className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Configuração de Alertas
              </CardTitle>
              <p className={`${textStyles.description} mt-1`}>
                A LIA aprende com seus padrões e ajusta os alertas automaticamente
              </p>
            </div>
            {!isEditingAlerts ? (
              <button
                onClick={() => setIsEditingAlerts(true)}
                className={buttonStyles.outline}
              >
                <Edit className="w-3 h-3" />
                Editar
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsEditingAlerts(false)}
                  className={buttonStyles.secondary}
                >
                  Cancelar
                </button>
                <button
                  onClick={async () => {
                    await saveAlertsConfig()
                    setIsEditingAlerts(false)
                  }}
                  disabled={saving}
                  className={buttonStyles.primary}
                >
                  {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                  Salvar Alterações
                </button>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {alerts.map((alert) => (
            <div 
              key={alert.id}
              className={`p-2.5 rounded-md border transition-colors ${
                alert.enabled 
                  ? 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700' 
                  : 'bg-gray-50 dark:bg-gray-800/50 border-gray-100 dark:border-gray-800'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2">
                  <div 
                    className={`w-7 h-7 rounded-md flex items-center justify-center transition-colors ${
                      alert.enabled 
                        ? 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400' 
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                    }`}
                  >
                    <Bell className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <p className={`${textStyles.subtitle} ${alert.enabled ? '' : 'text-gray-600 dark:text-gray-400'}`}>
                      {alert.name}
                    </p>
                    <p className={textStyles.description}>{alert.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={alert.channel}
                    onChange={(e) => handleChangeChannel(alert.id, e.target.value as any)}
                    disabled={!isEditingAlerts || !alert.enabled}
                    className={`${textStyles.caption} border border-gray-200 rounded-md px-2 py-1 bg-white dark:bg-gray-700 disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-600 dark:disabled:text-gray-400 dark:border-gray-600 dark:text-gray-200`}
                  >
                    <option value="email">Email</option>
                    <option value="teams">Teams</option>
                    <option value="both">Ambos</option>
                  </select>
                  <button
                    onClick={() => isEditingAlerts && handleToggleAlert(alert.id)}
                    disabled={!isEditingAlerts}
                    className="relative w-10 h-5 rounded-full transition-colors disabled:opacity-60"
                    style={{ backgroundColor: alert.enabled ? '#111827' : '#d1d5db' }}
                  >
                    <span className={`absolute top-0.5 w-4 h-4 bg-white dark:bg-gray-200 rounded-full transition-transform ${
                      alert.enabled ? 'left-5' : 'left-0.5'
                    }`} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className={cardStyles.default}>
        <CardHeader className="pb-2">
          <CardTitle className={`${textStyles.h3} flex items-center gap-2`}>
            <MessageSquare className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            Frequência do Briefing da LIA
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => setBriefingFrequency('twice_daily')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''} ${
                briefingFrequency === 'twice_daily'
                  ? 'border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-900'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <RefreshCw className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                <span className={textStyles.subtitle}>2x ao Dia</span>
              </div>
              <p className={textStyles.description}>
                Resumo às 8h e às 14h
              </p>
            </button>
            <button
              onClick={() => setBriefingFrequency('daily')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''} ${
                briefingFrequency === 'daily'
                  ? 'border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-900'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Clock className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                <span className={textStyles.subtitle}>Diário</span>
              </div>
              <p className={textStyles.description}>
                Resumo todas as manhãs às 8h
              </p>
            </button>
            <button
              onClick={() => setBriefingFrequency('weekly')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''} ${
                briefingFrequency === 'weekly'
                  ? 'border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-900'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Calendar className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                <span className={textStyles.subtitle}>Semanal</span>
              </div>
              <p className={textStyles.description}>
                Resumo toda segunda-feira
              </p>
            </button>
            <button
              onClick={() => setBriefingFrequency('monthly')}
              disabled={!isEditingAlerts}
              className={`p-2.5 rounded-md border-2 transition-colors text-left ${!isEditingAlerts ? 'opacity-60 cursor-not-allowed' : ''} ${
                briefingFrequency === 'monthly'
                  ? 'border-gray-900 dark:border-gray-50 bg-gray-50 dark:bg-gray-900'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
              }`}
            >
              <div className="flex items-center gap-1.5 mb-0.5">
                <Calendar className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                <span className={textStyles.subtitle}>Mensal</span>
              </div>
              <p className={textStyles.description}>
                Resumo no 1º dia útil do mês
              </p>
            </button>
          </div>

          <div className="rounded-md p-2.5 bg-gray-100 dark:bg-gray-800 dark:bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600">
            <div className="flex items-start gap-2">
              <Brain className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-wedo-cyan" />
              <div>
                <p className={`${textStyles.subtitle} text-gray-900 dark:text-gray-50`}>A LIA aprende com você</p>
                <p className={`${textStyles.description} mt-0.5`}>
                  Quanto mais você interage, melhor ela entende quais alertas são relevantes. 
                  Alertas ignorados consistentemente serão automaticamente desativados.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderWorkforce = () => (
    <div className="space-y-4">
      <SmartImportZone
        title="Importar Plano de Headcount"
        description="Importe o plano anual de contratações por departamento e mês. A LIA analisa e sugere ajustes baseados em dados históricos."
        importEndpoint="/api/backend-proxy/workforce/entries/import"
        templateDownloadEndpoint="/api/backend-proxy/workforce/entries/import/template"
        expectedFields={["department", "month", "year", "planned", "actual"]}
        onImportSuccess={fetchWorkforceData}
        disabled={!isEditingWorkforce}
      />

      <Card className={cardStyles.default}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={`${textStyles.h3} flex items-center gap-2 flex-wrap`}>
                <Calendar className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                Planejamento de Headcount {selectedYear}
                {departmentsLoaded && (
                  <Badge variant="outline" className={`${badgeStyles.success} text-[9px] font-normal`}>
                    <RefreshCw className="w-2.5 h-2.5 mr-1" />
                    Sincronizado
                  </Badge>
                )}
                <div className="flex items-center gap-2 ml-2">
                  <LiaFieldToggle
                    fieldKey="headcount_planning"
                    isActive={liaToggles.headcount_planning ?? false}
                    currentInstruction={liaInstructions.headcount_planning || ''}
                    examples={defaultLiaFieldExamples.headcount_planning}
                    onToggleChange={handleLiaToggleChange}
                    onInstructionSave={handleLiaInstructionSave}
                    compact
                  />
                  <span className={textStyles.caption}>Consumido pela LIA</span>
                </div>
              </CardTitle>
              <p className={`${textStyles.description} mt-1`}>
                Departamentos integrados com Empresa e Equipe. Novos departamentos são criados automaticamente.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                disabled={!isEditingWorkforce}
                className={`${textStyles.caption} border border-gray-200 rounded-md px-2 py-1.5 bg-white dark:bg-gray-700 disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500 dark:border-gray-600 dark:text-gray-200`}
              >
                <option value={2024}>2024</option>
                <option value={2025}>2025</option>
              </select>
              <button className={actionButtonStyles.smOutline}>
                <Download className={actionButtonStyles.icon} />
                Exportar
              </button>
              {!isEditingWorkforce ? (
                <button
                  onClick={() => setIsEditingWorkforce(true)}
                  className={actionButtonStyles.smOutline}
                >
                  <Edit className={actionButtonStyles.icon} />
                  Editar
                </button>
              ) : (
                <>
                  <button
                    onClick={() => setIsEditingWorkforce(false)}
                    className={actionButtonStyles.smSecondary}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={async () => {
                      await saveWorkforceData()
                      setIsEditingWorkforce(false)
                    }}
                    disabled={saving}
                    className={actionButtonStyles.smPrimary}
                  >
                    {saving ? <Loader2 className={actionButtonStyles.icon + " animate-spin"} /> : <Save className={actionButtonStyles.icon} />}
                    Salvar Alterações
                  </button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 mb-4">
            <Card className={`${cardStyles.flat} rounded-md flex-1`}>
              <CardContent className="p-2.5">
                <p className={textStyles.caption}>Total Planejado {selectedYear}</p>
                <p className={textStyles.metricLarge}>{workforceStats.totalPlanned} vagas</p>
              </CardContent>
            </Card>
            <p className={`${textStyles.description} max-w-xs`}>
              O acompanhamento do realizado será exibido nos dashboards de performance.
            </p>
          </div>

          <div className="space-y-3">
            {departments.map((dept) => (
              <div key={dept.id} className="border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
                <div 
                  className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 bg-gray-50/50 dark:bg-gray-800/50"
                  onClick={() => toggleDepartmentExpand(dept.id)}
                >
                  <div className="flex items-center gap-2 flex-1">
                    {dept.expanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
                    <input
                      type="text"
                      value={dept.name}
                      onChange={(e) => updateDepartmentName(dept.id, e.target.value)}
                      onClick={(e) => e.stopPropagation()}
                      disabled={!isEditingWorkforce}
                      className={`${textStyles.subtitle} font-semibold border-0 bg-transparent outline-0 disabled:opacity-70 text-gray-900 dark:text-gray-50`}
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={textStyles.description}>
                      {dept.positions.length} posição{dept.positions.length !== 1 ? 's' : ''}
                    </span>
                    <span className={`${textStyles.subtitle} font-semibold text-gray-900 dark:text-gray-50`}>
                      {dept.positions.reduce((acc, p) => acc + getPositionTotal(p), 0)} vagas
                    </span>
                  </div>
                </div>

                {dept.expanded && (
                  <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
                    <div className="overflow-x-auto">
                      <table className={`w-full ${textStyles.caption}`}>
                        <thead>
                          <tr className="border-b border-gray-200 dark:border-gray-700">
                            <th className={`text-left p-2 min-w-[140px] sticky left-0 bg-gray-50 dark:bg-gray-800 ${textStyles.captionBold}`}>Posição</th>
                            <th className={`text-center p-2 min-w-[90px] ${textStyles.captionBold} text-gray-700 dark:text-gray-300`}>Salário Mín.</th>
                            <th className={`text-center p-2 min-w-[90px] ${textStyles.captionBold} text-gray-700 dark:text-gray-300`}>Salário Máx.</th>
                            {monthLabels.map((month, idx) => (
                              <th key={idx} className={`text-center p-2 min-w-[40px] ${textStyles.captionBold} text-gray-700 dark:text-gray-300`}>{month}</th>
                            ))}
                            <th className={`text-center p-2 min-w-[50px] font-semibold text-gray-900 dark:text-gray-50`}>Total</th>
                            <th className="w-8 p-2"></th>
                          </tr>
                        </thead>
                        <tbody>
                          {dept.positions.map((pos) => (
                            <tr key={pos.id} className="border-b border-gray-100 dark:border-gray-700 hover:bg-white dark:hover:bg-gray-700/50">
                              <td className="p-2 sticky left-0 bg-gray-50 dark:bg-gray-800">
                                <input
                                  type="text"
                                  value={pos.name}
                                  onChange={(e) => updatePositionName(dept.id, pos.id, e.target.value)}
                                  placeholder="Nome da posição"
                                  disabled={!isEditingWorkforce}
                                  className={`w-full px-2 py-1 ${textStyles.caption} border border-gray-200 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500 dark:disabled:text-gray-500 dark:text-gray-200`}
                                />
                              </td>
                              <td className="p-1 text-center">
                                <input
                                  type="number"
                                  min={0}
                                  value={pos.salary_min ?? ''}
                                  onChange={(e) => updatePositionSalary(dept.id, pos.id, 'salary_min', e.target.value ? parseInt(e.target.value) : undefined)}
                                  placeholder="R$ 0"
                                  disabled={!isEditingWorkforce}
                                  className={`w-20 px-1 py-1 ${textStyles.caption} border border-gray-200 dark:border-gray-600 rounded text-center bg-white dark:bg-gray-700 disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500 dark:text-gray-200`}
                                />
                              </td>
                              <td className="p-1 text-center">
                                <input
                                  type="number"
                                  min={0}
                                  value={pos.salary_max ?? ''}
                                  onChange={(e) => updatePositionSalary(dept.id, pos.id, 'salary_max', e.target.value ? parseInt(e.target.value) : undefined)}
                                  placeholder="R$ 0"
                                  disabled={!isEditingWorkforce}
                                  className={`w-20 px-1 py-1 ${textStyles.caption} border border-gray-200 dark:border-gray-600 rounded text-center bg-white dark:bg-gray-700 disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500 dark:text-gray-200`}
                                />
                              </td>
                              {monthKeys.map((monthKey, idx) => (
                                <td key={idx} className="p-1 text-center">
                                  <input
                                    type="number"
                                    min={0}
                                    value={pos.monthlyPlanned[monthKey] || 0}
                                    onChange={(e) => updatePositionMonth(dept.id, pos.id, monthKey, parseInt(e.target.value) || 0)}
                                    disabled={!isEditingWorkforce}
                                    className={`w-10 px-1 py-1 ${textStyles.caption} border border-gray-200 dark:border-gray-600 rounded text-center bg-white dark:bg-gray-700 disabled:bg-gray-50 dark:disabled:bg-gray-800 disabled:text-gray-500 dark:text-gray-200`}
                                  />
                                </td>
                              ))}
                              <td className="p-2 text-center font-semibold text-gray-900 dark:text-gray-50">
                                {getPositionTotal(pos)}
                              </td>
                              <td className="p-1">
                                {isEditingWorkforce && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => deletePosition(dept.id, pos.id)}
                                    className="p-1 h-6 w-6"
                                  >
                                    <Trash2 className="w-3 h-3 text-red-500" />
                                  </Button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {isEditingWorkforce && (
                      <div className="p-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => addPositionToDepartment(dept.id)}
                          className={`w-full gap-1.5 py-1.5 text-[10px] rounded-md ${buttonStyles.outline}`}
                        >
                          <Plus className="w-3 h-3" />
                          Adicionar Posição
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {isEditingWorkforce && (
            <Button
              onClick={addDepartment}
              className={`w-full mt-4 gap-1.5 py-1.5 text-[11px] rounded-md ${buttonStyles.primary}`}
            >
              <Plus className="w-3.5 h-3.5" />
              Adicionar Departamento
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )

  const renderContent = () => {
    switch (activeTab) {
      case 'workforce':
        return renderWorkforce()
      default:
        return renderWorkforce()
    }
  }

  return (
    <div className="space-y-3">
      <div className={tabStyles.pillContainer}>
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={activeTab === tab.id ? tabStyles.pillActive : tabStyles.pill}
          >
            <tab.icon className={tabStyles.pillIcon} />
            {tab.label}
          </button>
        ))}
      </div>

      {renderContent()}
    </div>
  )
}
