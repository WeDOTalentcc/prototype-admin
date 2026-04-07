"use client"

import { useState, useMemo, useEffect, useCallback } from "react"
import { useCompanyLiaInstructions } from "@/hooks/use-company-lia-instructions"
import { useCompanyId } from "@/hooks/useCompanyId"
import { DEFAULT_ALERTS, MOCK_WORKFORCE, INITIAL_DEPARTMENTS, AlertConfig, WorkforceEntry, MonthlyPlanning, Position, DepartmentData } from "./goalsPlanningConstants"

const defaultAlerts = DEFAULT_ALERTS
const mockWorkforce = MOCK_WORKFORCE

export interface GoalsPlanningHubProps {
  users?: { id: string; name?: string; email?: string; role?: string; [key: string]: unknown }[]
  onGoalUpdate?: (userId: string, goals: Record<string, unknown>) => void
  activeSubsection?: string
}

export const monthKeys: (keyof MonthlyPlanning)[] = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
export const monthLabels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

export const getPositionTotal = (pos: Position) => {
  return monthKeys.reduce((sum, key) => sum + pos.monthlyPlanned[key], 0)
}

export function useGoalsPlanningHub({ users = [], onGoalUpdate, activeSubsection }: GoalsPlanningHubProps) {
  const [activeTab, setActiveTab] = useState(activeSubsection || 'workforce')
  const [alerts, setAlerts] = useState<AlertConfig[]>(defaultAlerts)
  const [workforce, setWorkforce] = useState<WorkforceEntry[]>(mockWorkforce)
  const [briefingFrequency, setBriefingFrequency] = useState<'twice_daily' | 'daily' | 'weekly' | 'monthly'>('daily')
  const [selectedYear, setSelectedYear] = useState(2024)

  const { companyId } = useCompanyId()
  const { instructions: liaInstructions, toggles: liaToggles, refetch: refetchLiaConfig } = useCompanyLiaInstructions()

  const [departments, setDepartments] = useState<DepartmentData[]>([...INITIAL_DEPARTMENTS])

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [goalsRefreshKey, setGoalsRefreshKey] = useState(0)
  const [fetchedUsers, setFetchedUsers] = useState<Array<{ id: string; name?: string; email?: string; role?: string; department?: string; isActive?: boolean; avatar?: string }>>([])
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
            return backendDepts.map((d: Record<string, unknown>) => ({
              id: d.id as string,
              name: d.name as string,
              positions: existingPositionsMap.get(d.id as string) || existingByName.get(String(d.name).toLowerCase()) || [],
              expanded: false
            }))
          })
          setDepartmentsLoaded(true)
        } else {
          setDepartmentsLoaded(true)
        }
      }
    } catch (err) {
      setDepartmentsLoaded(true)
    }
  }, [])

  const createDepartmentInBackend = useCallback(async (name: string): Promise<string | null> => {
    try {
      const response = await fetch(`/api/backend-proxy/company/departments?company_id=${encodeURIComponent(companyId || '')}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description: `Departamento criado via Planejamento de Contratações`, headcount: 0 })
      })
      if (response.ok) {
        const newDept = await response.json()
        return newDept.id
      }
      return null
    } catch (err) {
      return null
    }
  }, [])

  const fetchCompanyUsers = useCallback(async () => {
    try {
      const response = await fetch('/api/backend-proxy/company/users')
      if (response.ok) {
        const data = await response.json()
        const mappedUsers = data.map((u: Record<string, unknown>) => ({
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
          (setWorkforce as (v: unknown[]) => void)(workforceResult.map((w: Record<string, unknown>) => ({
            month: w.month,
            department: w.department,
            planned: w.planned || 0,
            actual: w.actual || 0,
            aiSuggestion: w.ai_suggestion
          })))
        }
      }
    } catch (err) {
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
            setAlerts(alertsResult.alerts.map((a: Record<string, unknown>) => ({
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
            (setWorkforce as (v: unknown[]) => void)(workforceResult.map((w: Record<string, unknown>) => ({
              month: w.month,
              department: w.department,
              planned: w.planned || 0,
              actual: w.actual || 0,
              aiSuggestion: w.ai_suggestion
            })))
          }
        }
      } catch (err) {
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
          alerts: alerts.map(a => ({ id: a.id, name: a.name, description: a.description, enabled: a.enabled, channel: a.channel })),
          briefing_frequency: briefingFrequency
        })
      })
      if (!response.ok) throw new Error('Falha ao salvar configuração de alertas')
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
          entries: workforce.map(w => ({ month: w.month, department: w.department, planned: w.planned, actual: w.actual }))
        })
      })
      if (!response.ok) throw new Error('Falha ao salvar planejamento')
      setSuccessMessage('Planejamento salvo com sucesso!')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar')
    } finally {
      setSaving(false)
    }
  }

  const getCompanyId = async (): Promise<string> => {
    if (companyId) return companyId
    try {
      const res = await fetch('/api/backend-proxy/company/profile')
      if (res.ok) {
        const company = await res.json()
        return company.id || ''
      }
    } catch (e) {
    }
    return ''
  }

  const handleLiaToggleChange = async (fieldKey: string, isActive: boolean) => {
    try {
      const updatedToggles = { ...liaToggles, [fieldKey]: isActive }
      const companyId = await getCompanyId()
      const response = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${companyId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lia_field_toggles: updatedToggles })
      })
      if (!response.ok) throw new Error('Falha ao salvar toggle do campo')
      await refetchLiaConfig()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar toggle')
      setTimeout(() => setError(null), 3000)
    }
  }

  const handleLiaInstructionSave = async (fieldKey: string, instruction: string) => {
    try {
      const updatedInstructions = { ...liaInstructions, [fieldKey]: instruction }
      const companyId = await getCompanyId()
      const response = await fetch(`/api/backend-proxy/company/culture-profile?company_id=${companyId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lia_instructions: updatedInstructions })
      })
      if (!response.ok) throw new Error('Falha ao salvar instrução')
      await refetchLiaConfig()
      setSuccessMessage('Instrução salva com sucesso!')
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar instrução')
      setTimeout(() => setError(null), 3000)
    }
  }

  const handleToggleAlert = (id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, enabled: !a.enabled } : a))
  }

  const handleChangeChannel = (id: string, channel: 'email' | 'teams' | 'both') => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, channel } : a))
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
    const emptyPlanning = { jan: 0, feb: 0, mar: 0, apr: 0, may: 0, jun: 0, jul: 0, aug: 0, sep: 0, oct: 0, nov: 0, dec: 0 }
    const newDept: DepartmentData = {
      id: tempId, name: newName,
      positions: [{ id: `${tempId}-0`, name: 'Nova Posição', salary_min: undefined, salary_max: undefined, monthlyPlanned: { ...emptyPlanning } }],
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
        ? { ...d, positions: [...d.positions, { id: Date.now().toString(), name: 'Nova Posição', salary_min: undefined, salary_max: undefined, monthlyPlanned: { jan: 0, feb: 0, mar: 0, apr: 0, may: 0, jun: 0, jul: 0, aug: 0, sep: 0, oct: 0, nov: 0, dec: 0 } }] }
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
    }
  }

  return {
    activeTab, setActiveTab,
    alerts, briefingFrequency, setBriefingFrequency,
    workforce, selectedYear, setSelectedYear,
    liaInstructions, liaToggles,
    departments, departmentsLoaded,
    loading, saving, error, successMessage,
    goalsRefreshKey, effectiveUsers,
    isEditingWorkforce, setIsEditingWorkforce,
    isEditingAlerts, setIsEditingAlerts,
    fetchGoals, fetchWorkforceData,
    saveAlertsConfig, saveWorkforceData,
    handleLiaToggleChange, handleLiaInstructionSave,
    handleToggleAlert, handleChangeChannel,
    workforceStats, toggleDepartmentExpand,
    addDepartment, addPositionToDepartment,
    updatePositionSalary, updatePositionName,
    updatePositionMonth, deletePosition, updateDepartmentName,
    onGoalUpdate
  }
}

export type UseGoalsPlanningHubReturn = ReturnType<typeof useGoalsPlanningHub>
