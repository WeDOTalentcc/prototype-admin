"use client"

import React, { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  RefreshCw,
  CheckCircle2,
  Circle,
  AlertCircle,
  Clock,
  Building2,
  Mail,
  Key,
  UserPlus,
  LogIn,
  Settings,
  Briefcase,
  ChevronDown,
  ExternalLink,
  Send,
  Eye,
  ArrowUpDown,
} from "lucide-react"
import { useClients, Client } from "@/hooks/use-clients"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

interface OnboardingStep {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  completed: boolean
  unavailable?: boolean
}

interface ClientOnboardingData {
  client: Client
  steps: OnboardingStep[]
  progress: number
  lastActivity: string
  status: "pending" | "in_progress" | "complete" | "stalled"
  daysSinceLastActivity: number
}

type FilterType = "all" | "pending" | "in_progress" | "complete" | "stalled"
type SortType = "date" | "progress" | "name"

function getOnboardingSteps(client: Client): OnboardingStep[] {
  const hasClientCreated = !!client.createdAt
  const hasAdminInvited = (client.usersCount || 0) > 0
  const hasSetupComplete = client.status === 'active'
  const hasFirstJob = (client.activeJobsCount || 0) > 0

  return [
    { id: "client_created", label: "Cliente criado", icon: Building2, completed: hasClientCreated },
    { id: "workos_org", label: "WorkOS Organization criada", icon: Key, completed: false, unavailable: true },
    { id: "welcome_email", label: "Email de boas-vindas enviado", icon: Mail, completed: false, unavailable: true },
    { id: "sso_configured", label: "SSO configurado", icon: Key, completed: false, unavailable: true },
    { id: "admin_invited", label: "Admin convidado", icon: UserPlus, completed: hasAdminInvited },
    { id: "admin_login", label: "Admin fez primeiro login", icon: LogIn, completed: hasAdminInvited },
    { id: "setup_complete", label: "Setup inicial completo", icon: Settings, completed: hasSetupComplete },
    { id: "first_job", label: "Primeira vaga criada", icon: Briefcase, completed: hasFirstJob },
  ]
}

function calculateProgress(steps: OnboardingStep[]): number {
  const availableSteps = steps.filter(s => !s.unavailable)
  const completed = availableSteps.filter(s => s.completed).length
  return availableSteps.length > 0 ? Math.round((completed / availableSteps.length) * 100) : 0
}

function getStatus(progress: number, daysSinceLastActivity: number): "pending" | "in_progress" | "complete" | "stalled" {
  if (progress === 100) return "complete"
  if (progress === 0) return "pending"
  if (daysSinceLastActivity > 7) return "stalled"
  return "in_progress"
}

function getDaysSinceLastActivity(updatedAt?: string): number {
  if (!updatedAt) return 0
  const updated = new Date(updatedAt)
  const now = new Date()
  const diffTime = Math.abs(now.getTime() - updated.getTime())
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

function formatLastActivity(days: number): string {
  if (days === 0) return "Hoje"
  if (days === 1) return "Ontem"
  if (days < 7) return `${days} dias atrás`
  if (days < 30) return `${Math.floor(days / 7)} semana(s) atrás`
  return `${Math.floor(days / 30)} mês(es) atrás`
}

function StatusBadge({ status }: { status: "pending" | "in_progress" | "complete" | "stalled" }) {
  const configs = {
    pending: { label: "Pendente", variant: "warning" as const, icon: Circle },
    in_progress: { label: "Em progresso", variant: "info" as const, icon: Clock },
    complete: { label: "Completo", variant: "success" as const, icon: CheckCircle2 },
    stalled: { label: "Parado", variant: "destructive" as const, icon: AlertCircle },
  }
  
  const config = configs[status]
  const Icon = config.icon
  
  return (
    <Badge variant={config.variant} className="flex items-center gap-1">
      <Icon className="w-3 h-3" />
      {config.label}
    </Badge>
  )
}

function OnboardingStepsChecklist({ steps }: { steps: OnboardingStep[] }) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {steps.map(step => {
        const Icon = step.icon
        if (step.unavailable) {
          return (
            <div
              key={step.id}
              className="flex items-center gap-2 text-xs text-gray-300 italic"
            >
              <Circle className="w-3.5 h-3.5" />
              <span className="truncate">{step.label}</span>
              <span className="text-micro">(Dados indisponíveis)</span>
            </div>
          )
        }
        return (
          <div
            key={step.id}
            className={`flex items-center gap-2 text-xs ${
              step.completed ? "text-status-success" : "text-gray-400"
            }`}
          >
            {step.completed ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-status-success" />
            ) : (
              <Circle className="w-3.5 h-3.5" />
            )}
            <span className="truncate">{step.label}</span>
          </div>
        )
      })}
    </div>
  )
}

function ClientRow({ data, onResendEmail }: { data: ClientOnboardingData; onResendEmail: (id: string) => void }) {
  const [showSteps, setShowSteps] = useState(false)
  
  return (
    <>
      <tr 
        className={`border-b border-gray-100 hover:bg-gray-50/50 transition-colors cursor-pointer ${
          data.status === "stalled" ? "bg-status-error/10/30" : ""
        }`}
        onClick={() => setShowSteps(!showSteps)}
      >
        <td className="py-4 px-4">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center text-white font-semibold bg-gray-900"
            >
              {data.client.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-medium text-gray-950 dark:text-gray-50">{data.client.name}</p>
              <p className="text-xs text-gray-500">{data.client.email || 'Sem email'}</p>
            </div>
          </div>
        </td>
        <td className="py-4 px-4">
          <div className="flex items-center gap-3">
            <Progress value={data.progress} className="w-24 h-2" />
            <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{data.progress}%</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {data.steps.filter(s => s.completed && !s.unavailable).length}/{data.steps.filter(s => !s.unavailable).length} etapas
          </p>
        </td>
        <td className="py-4 px-4">
          <span className={`text-sm ${data.daysSinceLastActivity > 7 ? 'text-status-error font-medium' : 'text-gray-600'}`}>
            {formatLastActivity(data.daysSinceLastActivity)}
          </span>
          {data.daysSinceLastActivity > 7 && (
            <div className="flex items-center gap-1 mt-1">
              <AlertCircle className="w-3 h-3 text-status-error" />
              <span className="text-xs text-status-error">Atenção necessária</span>
            </div>
          )}
        </td>
        <td className="py-4 px-4">
          <StatusBadge status={data.status} />
        </td>
        <td className="py-4 px-4">
          <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
            <Link href={`/admin/clientes/${data.client.id}`}>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <Eye className="w-4 h-4" />
              </Button>
            </Link>
            {data.status !== "complete" && (
              <Button 
                variant="ghost" 
                size="sm" 
                className="h-8 w-8 p-0"
                onClick={() => onResendEmail(data.client.id)}
                title="Reenviar email"
              >
                <Send className="w-4 h-4" />
              </Button>
            )}
            <Link href={`/admin/clientes/${data.client.id}`}>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <ExternalLink className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </td>
      </tr>
      {showSteps && (
        <tr className="bg-gray-50">
          <td colSpan={5} className="py-4 px-6">
            <div className="pl-12">
              <p className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-3">Etapas de Onboarding:</p>
              <OnboardingStepsChecklist steps={data.steps} />
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

export default function OnboardingClientesPage() {
  const [mounted, setMounted] = useState(false)
  const [filter, setFilter] = useState<FilterType>("all")
  const [sortBy, setSortBy] = useState<SortType>("date")
  const [isRefreshing, setIsRefreshing] = useState(false)

  const { clients, isLoading, error, refetch } = useClients({
    autoFetch: true,
    initialLimit: 100,
  })

  useEffect(() => {
    setMounted(true)
  }, [])

  const onboardingData: ClientOnboardingData[] = useMemo(() => {
    return clients.map(client => {
      const steps = getOnboardingSteps(client)
      const progress = calculateProgress(steps)
      const daysSinceLastActivity = getDaysSinceLastActivity(client.updatedAt)
      const status = getStatus(progress, daysSinceLastActivity)

      return {
        client,
        steps,
        progress,
        lastActivity: formatLastActivity(daysSinceLastActivity),
        status,
        daysSinceLastActivity,
      }
    })
  }, [clients])

  const filteredData = useMemo(() => {
    let data = [...onboardingData]

    if (filter !== "all") {
      data = data.filter(d => d.status === filter)
    }

    data.sort((a, b) => {
      switch (sortBy) {
        case "progress":
          return b.progress - a.progress
        case "name":
          return a.client.name.localeCompare(b.client.name)
        case "date":
        default:
          return b.daysSinceLastActivity - a.daysSinceLastActivity
      }
    })

    return data
  }, [onboardingData, filter, sortBy])

  const stats = useMemo(() => {
    const total = onboardingData.length
    const pending = onboardingData.filter(d => d.status === "pending").length
    const inProgress = onboardingData.filter(d => d.status === "in_progress").length
    const complete = onboardingData.filter(d => d.status === "complete").length
    const stalled = onboardingData.filter(d => d.status === "stalled").length
    
    return { total, pending, inProgress, complete, stalled }
  }, [onboardingData])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await refetch()
    setIsRefreshing(false)
  }

  const handleResendEmail = (clientId: string) => {
  }

  if (!mounted) {
    return (
      <div className="p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded-md w-1/3 mb-4" />
          <div className="h-4 bg-gray-200 rounded-md w-1/2 mb-8" />
          <div className="h-64 bg-gray-100 rounded-md" />
        </div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1
            className="text-2xl font-semibold mb-1 text-gray-800 dark:text-gray-100"
            
          >
            Onboarding de Clientes
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400" >
            Status consolidado de todos os clientes
          </p>
        </div>
        <Button 
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
          Atualizar
        </Button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <Card 
          className={`p-4 cursor-pointer transition-all ${filter === 'all' ? 'ring-2 ring-gray-900/20' : ''}`}
          onClick={() => setFilter('all')}
        >
          <p className="text-xs text-gray-500 uppercase tracking-wider">Total</p>
          <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">{stats.total}</p>
        </Card>
        <Card 
          className={`p-4 cursor-pointer transition-all ${filter === 'pending' ? 'ring-2 ring-gray-900/20' : ''}`}
          onClick={() => setFilter('pending')}
        >
          <p className="text-xs text-gray-500 uppercase tracking-wider">Pendentes</p>
          <p className="text-2xl font-bold text-wedo-orange">{stats.pending}</p>
        </Card>
        <Card 
          className={`p-4 cursor-pointer transition-all ${filter === 'in_progress' ? 'ring-2 ring-gray-900/20' : ''}`}
          onClick={() => setFilter('in_progress')}
        >
          <p className="text-xs text-gray-500 uppercase tracking-wider">Em Progresso</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-gray-50">{stats.inProgress}</p>
        </Card>
        <Card 
          className={`p-4 cursor-pointer transition-all ${filter === 'complete' ? 'ring-2 ring-gray-900/20' : ''}`}
          onClick={() => setFilter('complete')}
        >
          <p className="text-xs text-gray-500 uppercase tracking-wider">Completos</p>
          <p className="text-2xl font-bold text-status-success">{stats.complete}</p>
        </Card>
        <Card 
          className={`p-4 cursor-pointer transition-all ${filter === 'stalled' ? 'ring-2 ring-gray-900/20' : ''}`}
          onClick={() => setFilter('stalled')}
        >
          <p className="text-xs text-gray-500 uppercase tracking-wider">Parados (+7 dias)</p>
          <p className="text-2xl font-bold text-status-error">{stats.stalled}</p>
        </Card>
      </div>

      <Card className="overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">
              Mostrando {filteredData.length} cliente(s)
            </span>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <ArrowUpDown className="w-4 h-4 mr-2" />
                Ordenar por
                <ChevronDown className="w-4 h-4 ml-2" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => setSortBy('date')}>
                Data de criação
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy('progress')}>
                Progresso
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setSortBy('name')}>
                Nome
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {isLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">Carregando clientes...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center">
            <AlertCircle className="w-8 h-8 mx-auto text-status-error mb-4" />
            <p className="text-status-error">{error}</p>
            <Button onClick={handleRefresh} variant="outline" className="mt-4">
              Tentar novamente
            </Button>
          </div>
        ) : filteredData.length === 0 ? (
          <div className="p-8 text-center">
            <Building2 className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Nenhum cliente encontrado com esse filtro</p>
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Cliente
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Progresso
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Última Atividade
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map(data => (
                <ClientRow 
                  key={data.client.id} 
                  data={data} 
                  onResendEmail={handleResendEmail}
                />
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
