"use client"

import React, { useState, useEffect, useCallback, use } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { toast } from "sonner"
import {
  Users,
  Briefcase,
  UserSearch,
  Brain,
  Edit,
  Pause,
  Play,
  BarChart3,
  Clock,
  CheckCircle2,
  AlertCircle,
  Loader2,
  RefreshCw,
  FileText,
  Settings,
  Mail,
  Phone,
  ExternalLink,
  TrendingUp } from "lucide-react"

interface ClientData {
  id: string
  name: string
  trade_name?: string
  logo_url?: string
  status: string
  plan_id?: string
  cnpj?: string
  primary_email?: string
  primary_phone?: string
  user_limit: number
  contract_start_date?: string
  contract_end_date?: string
  account_manager_id?: string
  ai_credits_limit?: number
  ai_credits_used?: number
  onboarding_completed?: boolean
  onboarding_progress?: number
  created_at?: string
  updated_at?: string
}

interface ClientMetrics {
  active_users: number
  total_users: number
  open_vacancies: number
  total_candidates: number
  ai_credits_used: number
  ai_credits_limit: number
  screenings_completed: number
  interviews_scheduled: number
}

interface RecentActivity {
  id: string
  type: 'user_added' | 'vacancy_created' | 'candidate_imported' | 'screening_completed' | 'integration_connected' | 'setting_changed'
  description: string
  timestamp: string
  user?: string
}

const statusConfig: Record<string, { label: string, variant: 'success' | 'warning' | 'destructive' | 'info' | 'default' }> = {
  active: { label: 'Ativo', variant: 'success' },
  trial: { label: 'Trial', variant: 'info' },
  suspended: { label: 'Suspenso', variant: 'warning' },
  churned: { label: 'Churned', variant: 'destructive' },
  pending_setup: { label: 'Pendente Setup', variant: 'default' } }

const activityIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  user_added: Users,
  vacancy_created: Briefcase,
  candidate_imported: UserSearch,
  screening_completed: CheckCircle2,
  integration_connected: Settings,
  setting_changed: FileText
}

const onboardingSteps = [
  { id: 'company_profile', label: 'Perfil da Empresa', completed: true },
  { id: 'team_setup', label: 'Configurar Equipe', completed: true },
  { id: 'integrations', label: 'Integrações', completed: false },
  { id: 'first_vacancy', label: 'Primeira Vaga', completed: false },
  { id: 'first_screening', label: 'Primeira Triagem', completed: false },
]

function MetricCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
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

export default function ClientOverviewPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const router = useRouter()
  const [client, setClient] = useState<ClientData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [togglingStatus, setTogglingStatus] = useState(false)

  const [metrics] = useState<ClientMetrics>({
    active_users: 12,
    total_users: 15,
    open_vacancies: 8,
    total_candidates: 342,
    ai_credits_used: 2450,
    ai_credits_limit: 5000,
    screenings_completed: 156,
    interviews_scheduled: 23
  })

  const [recentActivities] = useState<RecentActivity[]>([
    { id: '1', type: 'user_added', description: 'Maria Silva foi adicionada como recrutadora', timestamp: '2025-01-15T10:30:00', user: 'Admin' },
    { id: '2', type: 'vacancy_created', description: 'Nova vaga: Desenvolvedor Full Stack Senior', timestamp: '2025-01-15T09:15:00', user: 'João Mendes' },
    { id: '3', type: 'candidate_imported', description: '45 candidatos importados via LinkedIn', timestamp: '2025-01-14T16:45:00', user: 'Sistema' },
    { id: '4', type: 'screening_completed', description: 'Triagem automática finalizada para 12 candidatos', timestamp: '2025-01-14T14:20:00', user: 'LIA' },
    { id: '5', type: 'integration_connected', description: 'Integração com Gupy configurada', timestamp: '2025-01-13T11:00:00', user: 'Admin' },
  ])

  const fetchClient = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(`/api/backend-proxy/clients/${clientId}`)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || 'Erro ao carregar cliente')
      }
      
      const data = await response.json()
      setClient(data.data || data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar cliente')
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchClient()
  }, [fetchClient])

  const handleToggleStatus = async () => {
    if (!client) return
    
    setTogglingStatus(true)
    try {
      const newStatus = client.status === 'suspended' ? 'active' : 'suspended'
      const response = await fetch(`/api/backend-proxy/clients/${clientId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      })
      
      if (!response.ok) {
        throw new Error('Erro ao atualizar status')
      }
      
      toast.success(newStatus === 'suspended' ? 'Cliente suspenso com sucesso' : 'Cliente reativado com sucesso')
      fetchClient()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Erro ao atualizar status')
    } finally {
      setTogglingStatus(false)
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const formatDateTime = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  const aiCreditsPercent = (metrics.ai_credits_used / metrics.ai_credits_limit) * 100
  const completedSteps = onboardingSteps.filter(s => s.completed).length
  const onboardingPercent = (completedSteps / onboardingSteps.length) * 100

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <MetricCardSkeleton key={i} />
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="w-16 h-16 rounded-full bg-status-error/10 dark:bg-status-error/20 flex items-center justify-center mb-4">
          <AlertCircle className="w-8 h-8 text-status-error" />
        </div>
        <h3 className="text-lg font-medium mb-1 text-lia-text-primary dark:text-lia-text-primary">
          Erro ao carregar dados
        </h3>
        <p className="text-sm mb-4 text-lia-text-tertiary dark:text-lia-text-secondary">
          {error}
        </p>
        <Button variant="outline" onClick={fetchClient}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Tentar novamente
        </Button>
      </div>
    )
  }

  const status = client?.status ? (statusConfig[client.status] || statusConfig.pending_setup) : statusConfig.pending_setup

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 
            className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary"
          >
            Visão Geral
          </h2>
          <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
            Dashboard de métricas e atividades do cliente
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(`/admin/clientes/${clientId}/setup`)}
          >
            <Edit className="w-4 h-4 mr-2" />
            Editar
          </Button>
          <Button
            // @ts-ignore TODO: fix type
            variant={client?.status === 'suspended' ? 'default' : 'outline'}
            onClick={handleToggleStatus}
            disabled={togglingStatus}
            className={client?.status === 'suspended' ? 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active' : ''}
          >
            {togglingStatus ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin motion-reduce:animate-none" />
            ) : client?.status === 'suspended' ? (
              <Play className="w-4 h-4 mr-2" />
            ) : (
              <Pause className="w-4 h-4 mr-2" />
            )}
            {client?.status === 'suspended' ? 'Reativar' : 'Suspender'}
          </Button>
          <Button
            variant="outline"
            onClick={() => router.push(`/admin/clientes/${clientId}/metricas`)}
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            Ver Métricas
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
                  Usuários Ativos
                </p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {metrics.active_users}
                  <span className="text-sm font-normal text-lia-text-tertiary dark:text-lia-text-secondary">
                    /{client?.user_limit || metrics.total_users}
                  </span>
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">+2 este mês</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center">
                <Users className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                  Vagas Abertas
                </p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {metrics.open_vacancies}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">+3 esta semana</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-wedo-purple/10 dark:bg-wedo-purple/20 flex items-center justify-center">
                <Briefcase className="w-5 h-5 text-wedo-purple dark:text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                  Candidatos
                </p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {metrics.total_candidates}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <TrendingUp className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">+45 hoje</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-warning/10 dark:bg-status-warning/20 flex items-center justify-center">
                <UserSearch className="w-5 h-5 text-status-warning dark:text-status-warning" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
                  Créditos IA
                </p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {metrics.ai_credits_used.toLocaleString()}
                  <span className="text-sm font-normal text-lia-text-tertiary dark:text-lia-text-secondary">
                    /{metrics.ai_credits_limit.toLocaleString()}
                  </span>
                </p>
                <Progress value={aiCreditsPercent} className="h-1.5 mt-2" />
              </div>
 <div className="w-10 h-10 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-secondary flex items-center justify-center">
                <Brain className="w-5 h-5 text-wedo-cyan" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Informações do Contrato
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-lia-text-tertiary dark:text-lia-text-secondary">
                  Status
                </p>
                <div className="mt-1">
                  <Badge variant={status.variant}>{status.label}</Badge>
                </div>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-lia-text-tertiary dark:text-lia-text-secondary">
                  Plano
                </p>
                <p className="text-sm font-medium mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {client?.plan_id || 'Starter'}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-lia-text-tertiary dark:text-lia-text-secondary">
                  Início do Contrato
                </p>
                <p className="text-sm font-medium mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {client?.contract_start_date ? formatDate(client.contract_start_date) : '-'}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wide text-lia-text-tertiary dark:text-lia-text-secondary">
                  Fim do Contrato
                </p>
                <p className="text-sm font-medium mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {client?.contract_end_date ? formatDate(client.contract_end_date) : '-'}
                </p>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs uppercase tracking-wide text-lia-text-tertiary dark:text-lia-text-secondary">
                    CNPJ
                  </p>
                  <p className="text-sm font-medium mt-1 text-lia-text-primary dark:text-lia-text-primary">
                    {client?.cnpj || '-'}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-lia-text-tertiary dark:text-lia-text-secondary">
                    Email
                  </p>
                  <div className="flex items-center gap-1 mt-1">
                    <Mail className="w-3 h-3 text-lia-text-tertiary dark:text-lia-text-secondary" />
                    <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                      {client?.primary_email || '-'}
                    </p>
                  </div>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-lia-text-tertiary dark:text-lia-text-secondary">
                    Telefone
                  </p>
                  <div className="flex items-center gap-1 mt-1">
                    <Phone className="w-3 h-3 text-lia-text-tertiary dark:text-lia-text-secondary" />
                    <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                      {client?.primary_phone || '-'}
                    </p>
                  </div>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-lia-text-tertiary dark:text-lia-text-secondary">
                    Limite Usuários
                  </p>
                  <p className="text-sm font-medium mt-1 text-lia-text-primary dark:text-lia-text-primary">
                    {client?.user_limit || '-'}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
                Progresso Onboarding
              </CardTitle>
              <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">{Math.round(onboardingPercent)}%</span>
            </div>
          </CardHeader>
          <CardContent>
            <Progress value={onboardingPercent} className="h-2 mb-4" />
            <div className="space-y-3">
              {onboardingSteps.map((step) => (
                <div key={step.id} className="flex items-center gap-3">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center ${
                    step.completed 
                      ? 'bg-status-success/15 dark:bg-status-success/30' 
                      : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary'
                  }`}>
                    {step.completed ? (
                      <CheckCircle2 className="w-3 h-3 text-status-success dark:text-status-success" />
                    ) : (
                      <Clock className="w-3 h-3 text-lia-text-tertiary" />
                    )}
                  </div>
                  <span
                    className={`text-sm ${step.completed ? 'line-through text-lia-text-tertiary dark:text-lia-text-secondary' : 'lia-text-800 dark:text-lia-text-primary'}`}
                  >
                    {step.label}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Atividades Recentes
            </CardTitle>
            <Button variant="ghost" size="sm">
              Ver todas
              <ExternalLink className="w-3 h-3 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentActivities.map((activity) => {
              const Icon = activityIcons[activity.type] || FileText
              return (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center shrink-0">
                    <Icon className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-lia-text-primary dark:text-lia-text-primary">
                      {activity.description}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                        {formatDateTime(activity.timestamp)}
                      </span>
                      {activity.user && (
                        <>
                          <span className="text-lia-text-tertiary dark:text-lia-text-secondary">•</span>
                          <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                            {activity.user}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
