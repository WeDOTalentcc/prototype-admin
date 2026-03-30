"use client"

import React, { useState, useEffect, useCallback, use, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Users,
  Calendar,
  TrendingUp,
  TrendingDown,
  Target,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ChevronDown,
  ChevronRight,
  Brain,
  Download,
  RefreshCw,
  Loader2,
  AlertCircle,
  DollarSign,
  Building2
} from "lucide-react"

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

interface DepartmentSummary {
  name: string
  totalPlanned: number
  totalFilled: number
  totalOpen: number
  vacancies: PlannedVacancy[]
  expanded: boolean
}

interface Alert {
  id: string
  type: 'sla_warning' | 'budget_pending' | 'over_budget' | 'under_plan'
  title: string
  description: string
  severity: 'low' | 'medium' | 'high'
}

const months = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']

const priorityConfig = {
  low: { label: 'Baixa', color: 'lia-text-600', bg: 'bg-gray-100' },
  medium: { label: 'Média', color: 'text-status-warning', bg: 'bg-status-warning/15' },
  high: { label: 'Alta', color: 'text-wedo-orange', bg: 'bg-wedo-orange/15' },
  critical: { label: 'Crítica', color: 'text-status-error', bg: 'bg-status-error/15' }
}

const statusConfig = {
  planned: { label: 'Planejada', color: 'lia-text-600 dark:text-lia-text-tertiary', bg: 'bg-gray-100 dark:bg-lia-bg-secondary' },
  open: { label: 'Aberta', color: 'text-status-warning', bg: 'bg-status-warning/15' },
  filled: { label: 'Preenchida', color: 'text-status-success', bg: 'bg-status-success/15' },
  cancelled: { label: 'Cancelada', color: 'lia-text-600', bg: 'bg-gray-100' }
}

const headcountTypeConfig = {
  replacement: { label: 'Reposição', icon: RefreshCw },
  expansion: { label: 'Expansão', icon: TrendingUp },
  new_role: { label: 'Nova Posição', icon: Brain }
}

function MetricCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-16" />
          </div>
          <Skeleton className="w-10 h-10 rounded-md" />
        </div>
      </CardContent>
    </Card>
  )
}

export default function ClientWorkforcePage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const [plan, setPlan] = useState<WorkforcePlan | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedDepts, setExpandedDepts] = useState<Set<string>>(new Set())
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [aiSuggestions, setAiSuggestions] = useState<any[]>([])

  const fetchPlan = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch(`/api/backend-proxy/workforce/plans?fiscal_year=${selectedYear}&client_id=${clientId}`)
      
      if (!response.ok) {
        if (response.status === 404) {
          setPlan({
            year: selectedYear,
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
      const plans = Array.isArray(data) ? data : [data]
      const vacancies: PlannedVacancy[] = []
      let totalPlanned = 0
      let totalOpen = 0
      let totalFilled = 0
      
      for (const planItem of plans) {
        totalPlanned += planItem.total_headcount || 0
        
        let headcounts = planItem.planned_headcounts
        
        if (!headcounts && planItem.id) {
          try {
            const hcResponse = await fetch(`/api/backend-proxy/workforce/plans/${planItem.id}/headcounts?client_id=${clientId}`)
            if (hcResponse.ok) {
              headcounts = await hcResponse.json()
            }
          } catch (e) {
          }
        }
        
        if (headcounts && Array.isArray(headcounts)) {
          headcounts.forEach((hc: Record<string, unknown>) => {
            vacancies.push({
              id: hc.id || `${planItem.id}-${vacancies.length}`,
              title: hc.title || 'Posição Planejada',
              department: hc.department_name || hc.department || 'Sem Departamento',
              plannedMonth: hc.target_month || 1,
              plannedYear: hc.target_year || planItem.fiscal_year || selectedYear,
              status: hc.status || 'planned',
              priority: hc.priority || 'medium',
              budgetApproved: hc.budget_approved ?? true,
              headcountType: hc.headcount_type || 'expansion'
            })
            
            if (hc.status === 'open') totalOpen++
            if (hc.status === 'filled') totalFilled++
          })
        }
      }
      
      setPlan({
        year: selectedYear,
        totalPlanned: totalPlanned || vacancies.length,
        totalOpen,
        totalFilled,
        plannedVacancies: vacancies
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar plano')
      setPlan(null)
    } finally {
      setIsLoading(false)
    }
  }, [selectedYear, clientId])

  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch(`/api/backend-proxy/workforce/alerts?client_id=${clientId}`)
      if (response.ok) {
        const data = await response.json()
        setAlerts(Array.isArray(data) ? data : [])
      }
    } catch (e) {
    }
  }, [clientId])

  useEffect(() => {
    fetchPlan()
    fetchAlerts()
  }, [fetchPlan, fetchAlerts])

  const departmentSummaries = useMemo(() => {
    if (!plan) return []
    
    const deptMap = new Map<string, DepartmentSummary>()
    
    plan.plannedVacancies.forEach(v => {
      const existing = deptMap.get(v.department)
      if (existing) {
        existing.totalPlanned++
        if (v.status === 'filled') existing.totalFilled++
        if (v.status === 'open') existing.totalOpen++
        existing.vacancies.push(v)
      } else {
        deptMap.set(v.department, {
          name: v.department,
          totalPlanned: 1,
          totalFilled: v.status === 'filled' ? 1 : 0,
          totalOpen: v.status === 'open' ? 1 : 0,
          vacancies: [v],
          expanded: expandedDepts.has(v.department)
        })
      }
    })
    
    return Array.from(deptMap.values()).sort((a, b) => b.totalPlanned - a.totalPlanned)
  }, [plan, expandedDepts])

  const monthlyData = useMemo(() => {
    if (!plan) return []
    
    return months.map((month, idx) => {
      const monthNum = idx + 1
      const monthVacancies = plan.plannedVacancies.filter(v => v.plannedMonth === monthNum)
      const planned = monthVacancies.length
      const filled = monthVacancies.filter(v => v.status === 'filled').length
      const open = monthVacancies.filter(v => v.status === 'open').length
      
      return { month, planned, filled, open }
    })
  }, [plan])

  const pendingBudgetApprovals = useMemo(() => {
    if (!plan) return []
    return plan.plannedVacancies.filter(v => !v.budgetApproved && v.status !== 'cancelled')
  }, [plan])

  const toggleDepartment = (deptName: string) => {
    setExpandedDepts(prev => {
      const next = new Set(prev)
      if (next.has(deptName)) {
        next.delete(deptName)
      } else {
        next.add(deptName)
      }
      return next
    })
  }

  const progressPercent = plan ? (plan.totalFilled / Math.max(plan.totalPlanned, 1)) * 100 : 0

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <MetricCardSkeleton key={i} />
          ))}
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="w-16 h-16 rounded-full bg-status-error/10 dark:bg-status-error/20 flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-status-error" />
        </div>
        <h3 className="text-lg font-medium mb-1 lia-text-800 dark:text-lia-text-primary">
          Erro ao carregar dados
        </h3>
        <p className="text-sm mb-4 lia-text-400 dark:lia-text-500">
          {error}
        </p>
        <Button variant="outline" onClick={fetchPlan}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Calendar className="w-6 h-6 lia-text-600 dark:text-lia-text-tertiary" />
            <h2 
              className="text-lg font-semibold lia-text-800 dark:text-lia-text-primary"
            >
              Planejamento de Contratações
            </h2>
          </div>
          <p className="text-sm lia-text-400 dark:lia-text-500">
            Planejamento anual de contratações e headcount
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="text-sm border rounded-md px-3 py-2 border-lia-border-subtle dark:border-lia-border-subtle bg-white dark:lia-bg-950 lia-text-800 dark:text-lia-text-primary"
          >
            <option value={2024}>2024</option>
            <option value={2025}>2025</option>
            <option value={2026}>2026</option>
          </select>
          <Button variant="outline" size="sm" onClick={fetchPlan}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Atualizar
          </Button>
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Exportar
          </Button>
        </div>
      </div>

      {(alerts.length > 0 || pendingBudgetApprovals.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {pendingBudgetApprovals.length > 0 && (
            <Card className="border-status-warning/30 bg-status-warning/10/50 dark:border-status-warning/30 dark:bg-status-warning/20">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <DollarSign className="w-5 h-5 text-status-warning mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-status-warning dark:text-status-warning" aria-live="polite" aria-atomic="true">
                      {pendingBudgetApprovals.length} vaga(s) aguardando aprovação de budget
                    </p>
                    <p className="text-xs text-status-warning dark:text-status-warning mt-1">
                      {pendingBudgetApprovals.map(v => v.title).slice(0, 3).join(', ')}
                      {pendingBudgetApprovals.length > 3 && ` e mais ${pendingBudgetApprovals.length - 3}`}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {alerts.filter(a => a.severity === 'high').length > 0 && (
            <Card className="border-status-error/30 bg-status-error/10/50 dark:border-status-error/30 dark:bg-status-error/20">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-status-error mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-status-error dark:text-status-error">
                      {alerts.filter(a => a.severity === 'high').length} alerta(s) de SLA
                    </p>
                    <p className="text-xs text-status-error dark:text-status-error mt-1">
                      {alerts.filter(a => a.severity === 'high')[0]?.description}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs lia-text-400 dark:lia-text-500">
                  Total Planejado {selectedYear}
                </p>
                <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary">
                  {plan?.totalPlanned || 0}
                </p>
                <p className="text-xs mt-1 lia-text-400 dark:lia-text-500" aria-live="polite" aria-atomic="true">
                  vagas no plano anual
                </p>
              </div>
              <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center">
                <Target className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs lia-text-400 dark:lia-text-500">
                  Preenchidas
                </p>
                <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary">
                  {plan?.totalFilled || 0}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">
                    {progressPercent.toFixed(0)}% do plano
                  </span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-success/15 dark:bg-status-success/30 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs lia-text-400 dark:lia-text-500">
                  Em Processo
                </p>
                <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary">
                  {plan?.totalOpen || 0}
                </p>
                <p className="text-xs mt-1 lia-text-400 dark:lia-text-500" aria-live="polite" aria-atomic="true">
                  vagas abertas
                </p>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-warning/15 dark:bg-status-warning/30 flex items-center justify-center">
                <Clock className="w-5 h-5 text-status-warning" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs lia-text-400 dark:lia-text-500">
                  Departamentos
                </p>
                <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary">
                  {departmentSummaries.length}
                </p>
                <p className="text-xs mt-1 lia-text-400 dark:lia-text-500" aria-live="polite" aria-atomic="true">
                  com vagas planejadas
                </p>
              </div>
              <div className="w-10 h-10 rounded-md bg-wedo-purple/15 dark:bg-wedo-purple/30 flex items-center justify-center">
                <Building2 className="w-5 h-5 text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2 lia-text-800 dark:text-lia-text-primary">
                <Calendar className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                Plano Anual por Mês
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
                      <th className="text-left py-2 pr-4 font-medium lia-text-400 dark:lia-text-500">Mês</th>
                      <th className="text-center py-2 px-2 font-medium lia-text-400 dark:lia-text-500">Planejado</th>
                      <th className="text-center py-2 px-2 font-medium lia-text-400 dark:lia-text-500">Preenchido</th>
                      <th className="text-center py-2 px-2 font-medium lia-text-400 dark:lia-text-500">Aberto</th>
                      <th className="text-left py-2 pl-4 font-medium lia-text-400 dark:lia-text-500">Progresso</th>
                    </tr>
                  </thead>
                  <tbody>
                    {monthlyData.map((row, idx) => (
                      <tr 
                        key={row.month} 
                        className="border-b last:border-0 border-lia-border-subtle dark:border-lia-border-subtle"
                      >
                        <td className="py-3 pr-4 font-medium lia-text-800 dark:text-lia-text-primary">
                          {row.month}
                        </td>
                        <td className="py-3 px-2 text-center lia-text-500 dark:text-lia-text-tertiary">
                          {row.planned}
                        </td>
                        <td className="py-3 px-2 text-center">
                          <span className="text-status-success">{row.filled}</span>
                        </td>
                        <td className="py-3 px-2 text-center">
                          <span className="text-status-warning">{row.open}</span>
                        </td>
                        <td className="py-3 pl-4">
                          <div className="flex items-center gap-2">
                            <Progress 
                              value={row.planned > 0 ? (row.filled / row.planned) * 100 : 0} 
                              className="h-2 flex-1" 
                            />
                            <span className="text-xs min-w-10 lia-text-400 dark:lia-text-500">
                              {row.planned > 0 ? Math.round((row.filled / row.planned) * 100) : 0}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2 lia-text-800 dark:text-lia-text-primary">
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Sugestões da LIA
              </CardTitle>
            </CardHeader>
            <CardContent>
              {aiSuggestions.length > 0 ? (
                <div className="space-y-3">
                  {aiSuggestions.map((suggestion, idx) => (
                    <div 
                      key={idx}
                      className="p-3 rounded-md bg-wedo-cyan/[0.08]"
                    >
                      <p className="text-sm lia-text-800 dark:text-lia-text-primary">
                        {suggestion.text}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div 
                  className="p-4 rounded-md text-center bg-gray-50 dark:bg-lia-bg-primary"
                >
                  <Brain className="w-8 h-8 mx-auto mb-2 text-wedo-cyan opacity-50" />
                  <p className="text-sm lia-text-400 dark:lia-text-500">
                    A LIA analisará os dados de recrutamento e fornecerá sugestões de otimização do plano.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2 lia-text-800 dark:text-lia-text-primary">
              <Building2 className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
              Breakdown por Departamento
            </CardTitle>
            <Button 
              variant="ghost" 
              size="sm"
              onClick={() => {
                if (expandedDepts.size === departmentSummaries.length) {
                  setExpandedDepts(new Set())
                } else {
                  setExpandedDepts(new Set(departmentSummaries.map(d => d.name)))
                }
              }}
            >
              {expandedDepts.size === departmentSummaries.length ? 'Recolher Todos' : 'Expandir Todos'}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {departmentSummaries.length === 0 ? (
            <div className="text-center py-8">
              <Building2 className="w-12 h-12 mx-auto mb-3 opacity-20" />
              <p className="text-sm lia-text-400 dark:lia-text-500" aria-live="polite" aria-atomic="true">
                Nenhuma vaga planejada para {selectedYear}
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {departmentSummaries.map((dept) => (
                <div 
                  key={dept.name}
                  className="border rounded-md overflow-hidden border-lia-border-subtle dark:border-lia-border-subtle"
                >
                  <div 
                    className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors motion-reduce:transition-none"
                    onClick={() => toggleDepartment(dept.name)}
                  >
                    <div className="flex items-center gap-3">
                      {expandedDepts.has(dept.name) ? (
                        <ChevronDown className="w-4 h-4 lia-text-400 dark:lia-text-500" />
                      ) : (
                        <ChevronRight className="w-4 h-4 lia-text-400 dark:lia-text-500" />
                      )}
                      <div>
                        <p className="font-medium lia-text-800 dark:text-lia-text-primary">
                          {dept.name}
                        </p>
                        <p className="text-xs lia-text-400 dark:lia-text-500">
                          {dept.vacancies.length} posição(ões)
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary">
                          {dept.totalFilled}/{dept.totalPlanned}
                        </p>
                        <p className="text-xs lia-text-400 dark:lia-text-500">
                          preenchidas
                        </p>
                      </div>
                      <div className="w-24">
                        <Progress 
                          value={(dept.totalFilled / Math.max(dept.totalPlanned, 1)) * 100} 
                          className="h-2" 
                        />
                      </div>
                    </div>
                  </div>

                  {expandedDepts.has(dept.name) && (
                    <div 
                      className="border-t border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary"
                    >
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
                              <th className="text-left py-2 px-4 font-medium lia-text-400 dark:lia-text-500">Posição</th>
                              <th className="text-center py-2 px-2 font-medium lia-text-400 dark:lia-text-500">Mês</th>
                              <th className="text-center py-2 px-2 font-medium lia-text-400 dark:lia-text-500">Tipo</th>
                              <th className="text-center py-2 px-2 font-medium lia-text-400 dark:lia-text-500">Prioridade</th>
                              <th className="text-center py-2 px-2 font-medium lia-text-400 dark:lia-text-500">Status</th>
                              <th className="text-center py-2 px-4 font-medium lia-text-400 dark:lia-text-500">Budget</th>
                            </tr>
                          </thead>
                          <tbody>
                            {dept.vacancies.map((vacancy) => {
                              const HeadcountIcon = headcountTypeConfig[vacancy.headcountType]?.icon || TrendingUp
                              return (
                                <tr 
                                  key={vacancy.id}
                                  className="border-b last:border-0 border-lia-border-subtle dark:border-lia-border-subtle"
                                >
                                  <td className="py-3 px-4 lia-text-800 dark:text-lia-text-primary">
                                    {vacancy.title}
                                  </td>
                                  <td className="py-3 px-2 text-center lia-text-500 dark:text-lia-text-tertiary">
                                    {months[vacancy.plannedMonth - 1]}
                                  </td>
                                  <td className="py-3 px-2 text-center">
                                    <div className="flex items-center justify-center gap-1">
                                      <HeadcountIcon className="w-3 h-3 lia-text-400 dark:lia-text-500" />
                                      <span className="text-xs lia-text-400 dark:lia-text-500">
                                        {headcountTypeConfig[vacancy.headcountType]?.label}
                                      </span>
                                    </div>
                                  </td>
                                  <td className="py-3 px-2 text-center">
                                    <Badge 
                                      variant="outline" 
                                      className={`text-xs ${priorityConfig[vacancy.priority].color} ${priorityConfig[vacancy.priority].bg}`}
                                    >
                                      {priorityConfig[vacancy.priority].label}
                                    </Badge>
                                  </td>
                                  <td className="py-3 px-2 text-center">
                                    <Badge 
                                      variant="outline"
                                      className={`text-xs ${statusConfig[vacancy.status].color} ${statusConfig[vacancy.status].bg}`}
                                    >
                                      {statusConfig[vacancy.status].label}
                                    </Badge>
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    {vacancy.budgetApproved ? (
                                      <CheckCircle2 className="w-4 h-4 mx-auto text-status-success" />
                                    ) : (
                                      <Clock className="w-4 h-4 mx-auto text-status-warning" />
                                    )}
                                  </td>
                                </tr>
                              )
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
