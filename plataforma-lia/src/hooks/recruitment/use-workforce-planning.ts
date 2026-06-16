"use client"

import { useState, useEffect, useCallback } from 'react'

interface PlannedVacancy {
  id: string
  title: string
  department: string
  plannedMonth: number
  plannedYear: number
  status: 'planned' | 'open' | 'filled' | 'cancelled'
  priority: 'low' | 'medium' | 'high' | 'critical'
  budgetApproved: boolean
  headcountType: 'replacement' | 'expansion' | 'new_role'
}

interface WorkforcePlan {
  year: number
  totalPlanned: number
  totalOpen: number
  totalFilled: number
  plannedVacancies: PlannedVacancy[]
}

interface UseWorkforcePlanningResult {
  plan: WorkforcePlan | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  checkIfVacancyIsPlanned: (title: string, department?: string) => {
    isPlanned: boolean
    plannedVacancy: PlannedVacancy | null
    warning: string | null
  }
  getPlannedVacanciesForDepartment: (department: string) => PlannedVacancy[]
  getUnfilledPlannedVacancies: () => PlannedVacancy[]
}

export function useWorkforcePlanning(): UseWorkforcePlanningResult {
  const [plan, setPlan] = useState<WorkforcePlan | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPlan = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const currentYear = new Date().getFullYear()
      const response = await fetch(`/api/backend-proxy/workforce/plans?fiscal_year=${currentYear}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          // No workforce planning configured
          setPlan({
            year: currentYear,
            totalPlanned: 0,
            totalOpen: 0,
            totalFilled: 0,
            plannedVacancies: []
          })
          return
        }
        throw new Error(`Failed to fetch workforce plan: ${response.status}`)
      }

      const data = await response.json()
      
      // Transform API data to our format
      // API returns array of HiringPlan objects - headcounts need separate fetch
      const plans = Array.isArray(data) ? data : [data]
      const vacancies: PlannedVacancy[] = []
      let totalPlanned = 0
      let totalOpen = 0
      let totalFilled = 0
      
      // Fetch headcounts for each plan
      for (const planItem of plans) {
        totalPlanned += planItem.total_headcount || 0
        
        // Try to get headcounts from plan directly first
        let headcounts = planItem.planned_headcounts
        
        // If not embedded, fetch separately
        if (!headcounts && planItem.id) {
          try {
            const hcResponse = await fetch(`/api/backend-proxy/workforce/plans/${planItem.id}/headcounts`)
            if (hcResponse.ok) {
              headcounts = await hcResponse.json()
            }
          } catch (e) {
            console.error("[use-workforce-planning] Error:", e)
          }
        }
        
        if (headcounts && Array.isArray(headcounts)) {
          headcounts.forEach((hc: Record<string, unknown>) => {
            vacancies.push({
              id: (hc.id as string) || `${planItem.id}-${vacancies.length}`,
              title: (hc.title as string) || 'Posição Planejada',
              department: (hc.department_name as string) || (hc.department as string) || '',
              plannedMonth: (hc.target_month as number) || 1,
              plannedYear: (hc.target_year as number) || (planItem.fiscal_year as number) || currentYear,
              status: ((hc.status as string) || 'planned') as 'open' | 'cancelled' | 'filled' | 'planned',
              priority: ((hc.priority as string) || 'medium') as 'critical' | 'high' | 'medium' | 'low',
              budgetApproved: (hc.budget_approved as boolean) ?? true,
              headcountType: ((hc.headcount_type as string) || 'expansion') as 'replacement' | 'expansion' | 'new_role'
            })
            
            if (hc.status === 'open') totalOpen++
            if (hc.status === 'filled') totalFilled++
          })
        }
      }
      
      setPlan({
        year: currentYear,
        totalPlanned: totalPlanned || vacancies.length,
        totalOpen,
        totalFilled,
        plannedVacancies: vacancies
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
      setPlan(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPlan()
  }, [fetchPlan])

  const checkIfVacancyIsPlanned = useCallback((title: string, department?: string): {
    isPlanned: boolean
    plannedVacancy: PlannedVacancy | null
    warning: string | null
  } => {
    if (!plan || plan.plannedVacancies.length === 0) {
      return {
        isPlanned: false,
        plannedVacancy: null,
        warning: 'Não há planejamento de workforce configurado. Esta vaga não está no plano anual.'
      }
    }

    const titleLower = title.toLowerCase()
    const matching = plan.plannedVacancies.find(v => {
      const titleMatch = v.title.toLowerCase().includes(titleLower) || titleLower.includes(v.title.toLowerCase())
      if (department) {
        const deptLower = department.toLowerCase()
        const deptMatch = v.department.toLowerCase().includes(deptLower) || deptLower.includes(v.department.toLowerCase())
        return titleMatch && deptMatch
      }
      return titleMatch
    })

    if (matching) {
      return {
        isPlanned: true,
        plannedVacancy: matching,
        warning: null
      }
    }

    // Check if there are any planned vacancies for the department
    if (department) {
      const deptVacancies = plan.plannedVacancies.filter(v => 
        v.department.toLowerCase().includes(department.toLowerCase())
      )
      if (deptVacancies.length > 0) {
        return {
          isPlanned: false,
          plannedVacancy: null,
          warning: `Esta vaga não está no plano, mas existem ${deptVacancies.length} vagas planejadas para ${department}.`
        }
      }
    }

    return {
      isPlanned: false,
      plannedVacancy: null,
      warning: 'Esta vaga não está no planejamento anual de workforce. Verifique com o RH/Gestão.'
    }
  }, [plan])

  const getPlannedVacanciesForDepartment = useCallback((department: string): PlannedVacancy[] => {
    if (!plan) return []
    return plan.plannedVacancies.filter(v => 
      v.department.toLowerCase().includes(department.toLowerCase())
    )
  }, [plan])

  const getUnfilledPlannedVacancies = useCallback((): PlannedVacancy[] => {
    if (!plan) return []
    return plan.plannedVacancies.filter(v => v.status === 'planned' || v.status === 'open')
  }, [plan])

  return {
    plan,
    isLoading,
    error,
    refetch: fetchPlan,
    checkIfVacancyIsPlanned,
    getPlannedVacanciesForDepartment,
    getUnfilledPlannedVacancies
  }
}

export default useWorkforcePlanning
