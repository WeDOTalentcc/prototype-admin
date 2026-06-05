"use client"

import { useState, useMemo, useEffect, useCallback } from "react"
import { useCompanyLiaInstructions } from "@/hooks/company/use-company-lia-instructions"
import { useCompanyId } from "@/hooks/company/useCompanyId"
import { DEFAULT_ALERTS, INITIAL_DEPARTMENTS, AlertConfig, MonthlyPlanning, Position, DepartmentData } from "./goalsPlanningConstants"
import { apiFetch } from "@/lib/api/api-fetch"

const defaultAlerts = DEFAULT_ALERTS

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
  const [briefingFrequency, setBriefingFrequency] = useState<'twice_daily' | 'daily' | 'weekly' | 'monthly'>('daily')
  const [selectedYear, setSelectedYear] = useState(2024)

  const { companyId, tenantInfo } = useCompanyId()
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
  const [currentPlanId, setCurrentPlanId] = useState<string | null>(null)

  const fetchDepartmentsFromBackend = useCallback(async () => {
    try {
      const response = await apiFetch('/api/backend-proxy/company/departments')
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

  // Bug fix 2026-05-25 (write/read consistency for Planejamento de Headcount):
  // saveDepartmentPositions persists to Sistema B canonical
  // (POST /workforce/plans/{id}/headcounts/bulk → planned_headcounts), but
  // fetchDepartmentsFromBackend above only loads department names from
  // /company/departments — there was NO read path for planned_headcounts at
  // all. Result: user edits Backend Developer = 1 vaga em Jan, clicks Salvar,
  // sees toast verde, reloads → all monthly counts vanish because they were
  // never re-read from the table that received them.
  //
  // This effect fills the gap. It:
  //   1) Resolves the hiring_plan.id for selectedYear (read-only — never
  //      auto-creates; create happens lazily in saveDepartmentPositions).
  //   2) Pages through GET /plans/{id}/headcounts (limit 200 per page is the
  //      backend cap, so we paginate for plans that exceed 200 rows).
  //   3) Buckets rows by (department_id, title) into Position[] with
  //      monthlyPlanned[monthKey] = headcount. Salary fields are taken from
  //      the first row of each bucket (writes already group salary by
  //      position, so all 12 monthly rows share the same min/max).
  //   4) Merges into departments by department_id, preserving any unsaved
  //      in-memory edits for buckets that the backend doesn't know about.
  const fetchHeadcountsForYear = useCallback(async (year: number) => {
    try {
      const plansRes = await apiFetch(`/api/backend-proxy/workforce/plans?fiscal_year=${year}`)
      if (!plansRes.ok) return
      const plans = await plansRes.json()
      if (!Array.isArray(plans) || plans.length === 0) {
        // No plan yet for this year; clear stale positions so the UI doesn't
        // show data leaked from another year.
        setCurrentPlanId(null)
        setDepartments(prev => prev.map(d => ({ ...d, positions: [] })))
        return
      }
      const planId = plans[0].id as string
      setCurrentPlanId(planId)

      const allRows: Record<string, unknown>[] = []
      const PAGE = 200
      for (let skip = 0; ; skip += PAGE) {
        const hcRes = await apiFetch(
          `/api/backend-proxy/workforce/plans/${planId}/headcounts?target_year=${year}&skip=${skip}&limit=${PAGE}`
        )
        if (!hcRes.ok) break
        const page = await hcRes.json()
        if (!Array.isArray(page) || page.length === 0) break
        allRows.push(...page)
        if (page.length < PAGE) break
      }

      // Bucket by department_id + title → Position with monthlyPlanned.
      const buckets = new Map<string, Map<string, Position>>()
      for (const row of allRows) {
        const deptId = (row.department_id ?? '__no_dept__') as string
        const title = (row.title ?? 'Posição') as string
        const month = Number(row.target_month) // 1..12
        const count = Number(row.headcount ?? 0)
        if (!Number.isFinite(month) || month < 1 || month > 12) continue

        let deptBucket = buckets.get(deptId)
        if (!deptBucket) { deptBucket = new Map(); buckets.set(deptId, deptBucket) }

        let pos = deptBucket.get(title)
        if (!pos) {
          pos = {
            id: `${deptId}-${title}`,
            name: title,
            salary_min: (row.salary_min ?? undefined) as number | undefined,
            salary_max: (row.salary_max ?? undefined) as number | undefined,
            monthlyPlanned: { jan: 0, feb: 0, mar: 0, apr: 0, may: 0, jun: 0, jul: 0, aug: 0, sep: 0, oct: 0, nov: 0, dec: 0 },
          }
          deptBucket.set(title, pos)
        }
        const monthKey = monthKeys[month - 1]
        pos.monthlyPlanned[monthKey] = count
      }

      setDepartments(prev => prev.map(d => {
        const fromBackend = buckets.get(d.id)
        if (!fromBackend) return { ...d, positions: [] }
        return { ...d, positions: Array.from(fromBackend.values()) }
      }))
    } catch {
      // Silently skip — UI keeps whatever it had; user will see empty state,
      // not stale wrong data, on real backend failures.
    }
  }, [])

  const createDepartmentInBackend = useCallback(async (name: string): Promise<string | null> => {
    try {
      const response = await apiFetch(`/api/backend-proxy/company/departments?company_id=${encodeURIComponent(companyId || '')}`, {
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const fetchCompanyUsers = useCallback(async () => {
    try {
      const response = await apiFetch('/api/backend-proxy/company/users')
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

  // Hydrate planned_headcounts whenever the department list finishes loading
  // or the user switches year. Without this, save → reload → empty UI.
  useEffect(() => {
    if (!departmentsLoaded) return
    fetchHeadcountsForYear(selectedYear)
  }, [departmentsLoaded, selectedYear, fetchHeadcountsForYear])

  const effectiveUsers = users.length > 0 ? users : fetchedUsers

  const fetchGoals = useCallback(() => {
    setGoalsRefreshKey(prev => prev + 1)
  }, [])

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true)
        setError(null)
        const alertsRes = await apiFetch('/api/backend-proxy/alerts/config')
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
      const response = await apiFetch('/api/backend-proxy/alerts/config', {
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

  const saveDepartmentPositions = async () => {
    try {
      setSaving(true)
      const apiCid = tenantInfo?.clientAccountId || companyId || ''

      // 1. Garantir que há um plano de contratações para o ano (criar se não existir)
      let planId = currentPlanId
      if (!planId) {
        const plansRes = await apiFetch(`/api/backend-proxy/workforce/plans?fiscal_year=${selectedYear}`)
        if (plansRes.ok) {
          const plans = await plansRes.json()
          if (Array.isArray(plans) && plans.length > 0) {
            planId = plans[0].id as string
            setCurrentPlanId(planId)
          }
        }
        if (!planId) {
          const createRes = await apiFetch('/api/backend-proxy/workforce/plans', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              company_id: apiCid,
              name: `Plano de Contratações ${selectedYear}`,
              fiscal_year: selectedYear,
              status: 'active',
            })
          })
          if (!createRes.ok) throw new Error('Falha ao criar plano de contratações')
          const plan = await createRes.json()
          planId = plan.id as string
          setCurrentPlanId(planId)
          // Bug 6.C edge case: dispatch após criar plano novo
          if (typeof window !== 'undefined') {
            window.dispatchEvent(new CustomEvent('lia:settings-updated', {
              detail: {
                actionId: 'create_workforce_plan',
                section: 'workforce',
                field: `plan_${selectedYear}`,
                value: plan.name,
                source: 'ui',
                ts: Date.now(),
              },
            }))
          }
        }
      }

      // 2. Serializar departments → PlannedHeadcountCreate[]
      const MONTH_KEYS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
      const headcounts: object[] = []
      for (const dept of departments) {
        for (const pos of dept.positions) {
          for (const [monthKey, count] of Object.entries(pos.monthlyPlanned)) {
            if ((count as number) > 0) {
              const monthIndex = MONTH_KEYS.indexOf(monthKey) + 1
              headcounts.push({
                hiring_plan_id: planId,
                department_id: dept.id.startsWith('temp-') ? undefined : dept.id,
                title: pos.name || 'Posição',
                target_month: monthIndex,
                target_year: selectedYear,
                headcount: count,
                salary_min: pos.salary_min ?? null,
                salary_max: pos.salary_max ?? null,
                salary_currency: 'BRL',
                status: 'planned',
              })
            }
          }
        }
      }

      if (headcounts.length === 0) {
        setSuccessMessage('Nenhuma posição planejada para salvar.')
        setTimeout(() => setSuccessMessage(null), 3000)
        return
      }

      // 3. Enviar via bulk endpoint
      const bulkRes = await apiFetch(`/api/backend-proxy/workforce/plans/${planId}/headcounts/bulk`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(headcounts)
      })
      if (!bulkRes.ok) throw new Error('Falha ao salvar posições planejadas')
      // Bug 6.C dispatch: notify LIA chat after bulk headcounts save
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('lia:settings-updated', {
          detail: {
            actionId: 'configure_workforce_headcounts',
            section: 'workforce',
            field: `headcounts_${selectedYear}`,
            value: headcounts.length,
            source: 'ui',
            ts: Date.now(),
          },
        }))
      }
      // Re-hydrate from canonical Sistema B so the UI reflects exactly what
      // was persisted (and surfaces any rows the bulk endpoint normalized).
      await fetchHeadcountsForYear(selectedYear)
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('lia:settings-success', {
          detail: { actionId: 'configure_workforce', section: 'workforce', source: 'ui' },
        }))
      }
      setSuccessMessage(`${headcounts.length} posição(ões) salvas com sucesso!`)
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao salvar posições')
      setTimeout(() => setError(null), 5000)
    } finally {
      setSaving(false)
    }
  }

  const getCompanyId = async (): Promise<string> => {
    if (companyId) return companyId
    try {
      const res = await apiFetch('/api/backend-proxy/company/profile')
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
      const response = await apiFetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`, {
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
      const response = await apiFetch(`/api/backend-proxy/company/culture-profile/${encodeURIComponent(companyId)}`, {
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
      await apiFetch(`/api/backend-proxy/company/departments/${deptId}`, {
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
    selectedYear, setSelectedYear,
    liaInstructions, liaToggles,
    departments, departmentsLoaded,
    loading, saving, error, successMessage,
    goalsRefreshKey, effectiveUsers,
    isEditingWorkforce, setIsEditingWorkforce,
    isEditingAlerts, setIsEditingAlerts,
    fetchGoals, fetchHeadcountsForYear,
    saveAlertsConfig, saveDepartmentPositions,
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
