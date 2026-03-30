"use client"

import React, { use } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"
import {
  Shield,
  Lock,
  AlertTriangle,
  CheckCircle2,
  Users,
  FileText,
  Calendar,
  AlertCircle,
  RefreshCw,
  Loader2,
  Clock,
  Mail,
  UserCheck,
  UserX,
  Download,
  Trash2
} from "lucide-react"
import { useLGPDCompliance } from '@/hooks/admin/useLGPDCompliance'

interface TabLink {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

const internalTabs: TabLink[] = [
  { name: 'Visão Geral', href: '', icon: Shield },
  { name: 'LGPD', href: '/lgpd', icon: Lock },
  { name: 'Controles', href: '/controles', icon: CheckCircle2 },
  { name: 'Incidentes', href: '/incidentes', icon: AlertTriangle },
]

const dsrTypeIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  access: FileText,
  deletion: Trash2,
  portability: Download,
  rectification: UserCheck,
}

const dsrTypeLabels: Record<string, string> = {
  access: 'Acesso',
  deletion: 'Exclusão',
  portability: 'Portabilidade',
  rectification: 'Retificação',
}

const dsrStatusColors: Record<string, string> = {
  pending: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  in_progress: 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-50',
  completed: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success',
  overdue: 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error',
}

const dsrStatusLabels: Record<string, string> = {
  pending: 'Pendente',
  in_progress: 'Em Andamento',
  completed: 'Concluído',
  overdue: 'Atrasado',
}

function LoadingSpinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'
  return <Loader2 className={`${sizeClass} animate-spin text-gray-600`} />
}

export default function LGPDPage({ params }: { params: Promise<{ clientId: string }> }) {
  const { clientId } = use(params)
  const pathname = usePathname()
  const basePath = `/admin/clientes/${clientId}/conformidade`
  
  const { stats, dpo, breaches, decisions, totalBreaches, totalDecisions, isLoading, error, refetch } = useLGPDCompliance(clientId)

  const formatDate = (dateStr: string | undefined | null) => {
    if (!dateStr) return '-'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const isTabActive = (tabHref: string) => {
    const fullPath = basePath + tabHref
    if (tabHref === '') {
      return pathname === basePath
    }
    return pathname === fullPath
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-1 border-b pb-px -mb-px border-gray-200 dark:border-gray-700">
          {internalTabs.map((tab) => {
            const Icon = tab.icon
            return (
              <Link
                key={tab.href}
                href={basePath + tab.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                  "border-transparent"
                )}
                className="text-gray-500 dark:text-gray-400"
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </Link>
            )
          })}
        </div>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-sm text-gray-400 dark:text-gray-500">Carregando dados LGPD...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-1 border-b pb-px -mb-px border-gray-200 dark:border-gray-700">
          {internalTabs.map((tab) => {
            const Icon = tab.icon
            return (
              <Link
                key={tab.href}
                href={basePath + tab.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                  "border-transparent"
                )}
                className="text-gray-500 dark:text-gray-400"
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </Link>
            )
          })}
        </div>
        <div className="p-6 text-center">
          <AlertCircle className="w-8 h-8 text-status-error mx-auto mb-2" />
          <p className="text-sm text-status-error">Erro ao carregar dados LGPD</p>
          <Button variant="outline" size="sm" onClick={refetch} className="mt-3">
            <RefreshCw className="w-4 h-4 mr-2" />
            Tentar novamente
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-1 border-b pb-px -mb-px border-gray-200 dark:border-gray-700">
        {internalTabs.map((tab) => {
          const isActive = isTabActive(tab.href)
          const Icon = tab.icon
          return (
            <Link
              key={tab.href}
              href={basePath + tab.href}
              className={cn(
                "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                isActive
                  ? "border-gray-900 dark:border-gray-50 text-gray-900 dark:text-gray-50"
                  : "border-transparent hover:border-gray-300 dark:hover:border-gray-600 text-gray-500 dark:text-gray-400"
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.name}
            </Link>
          )
        })}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-400 dark:text-gray-500">Consentimentos</p>
                <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100">{stats?.totalConsents || 0}</p>
                <div className="flex items-center gap-1 mt-1">
                  <UserCheck className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">{stats?.activeConsents || 0} ativos</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-success/10 dark:bg-status-success/20 flex items-center justify-center">
                <Users className="w-5 h-5 text-status-success dark:text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-400 dark:text-gray-500">DSRs Pendentes</p>
                <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100">{stats?.pendingDSRs || 0}</p>
                <div className="flex items-center gap-1 mt-1">
                  <Clock className="w-3 h-3 text-status-warning" />
                  <span className="text-xs text-status-warning">Aguardando resposta</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-warning/10 dark:bg-status-warning/20 flex items-center justify-center">
                <FileText className="w-5 h-5 text-status-warning dark:text-status-warning" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-400 dark:text-gray-500">Taxa Consentimento</p>
                <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100">{(stats?.consentComplianceRate || 0).toFixed(0)}%</p>
                <Progress value={stats?.consentComplianceRate || 0} className="h-2 mt-2 w-24" />
              </div>
              <div className="w-10 h-10 rounded-md bg-gray-50 dark:bg-gray-800/50 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-gray-400 dark:text-gray-500">Incidentes LGPD</p>
                <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100">{totalBreaches}</p>
                <div className="flex items-center gap-1 mt-1">
                  {breaches.filter(b => b.status !== 'closed').length > 0 ? (
                    <>
                      <AlertTriangle className="w-3 h-3 text-status-error" />
                      <span className="text-xs text-status-error">{breaches.filter(b => b.status !== 'closed').length} abertos</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-status-success" />
                      <span className="text-xs text-status-success">Nenhum aberto</span>
                    </>
                  )}
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-error/10 dark:bg-status-error/20 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-status-error dark:text-status-error" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {dpo && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium text-gray-800 dark:text-gray-100">
              Encarregado de Dados (DPO)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-wedo-purple/10 dark:bg-wedo-purple/20 flex items-center justify-center">
                <UserCheck className="w-6 h-6 text-wedo-purple dark:text-wedo-purple" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-gray-800 dark:text-gray-100">{dpo.name}</p>
                <div className="flex items-center gap-4 mt-1">
                  <div className="flex items-center gap-1">
                    <Mail className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">{dpo.email}</span>
                  </div>
                  {dpo.phone && (
                    <span className="text-sm text-gray-400 dark:text-gray-500">{dpo.phone}</span>
                  )}
                </div>
                {dpo.registrationDate && (
                  <p className="text-xs mt-2 text-gray-400 dark:text-gray-500">
                    Registrado em {formatDate(dpo.registrationDate)}
                  </p>
                )}
              </div>
              <Badge variant={dpo.status === 'active' ? 'success' : 'warning'}>
                {dpo.status === 'active' ? 'Ativo' : 'Inativo'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium text-gray-800 dark:text-gray-100">
              Solicitações de Titulares (DSR)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {decisions.length > 0 ? (
              <div className="space-y-3">
                {decisions.slice(0, 5).map((decision) => {
                  const TypeIcon = dsrTypeIcons[decision.decisionType] || FileText
                  return (
                    <div key={decision.id} className="flex items-center justify-between p-3 rounded-md bg-gray-50 dark:bg-gray-900">
                      <div className="flex items-center gap-3">
                        <TypeIcon className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                        <div>
                          <p className="text-sm font-medium text-gray-800 dark:text-gray-100">
                            {decision.candidateName || 'Titular'}
                          </p>
                          <p className="text-xs text-gray-400 dark:text-gray-500">
                            {dsrTypeLabels[decision.decisionType] || decision.decisionType} - {formatDate(decision.createdAt)}
                          </p>
                        </div>
                      </div>
                      <Badge className={dsrStatusColors[decision.status] || dsrStatusColors.pending}>
                        {dsrStatusLabels[decision.status] || decision.status}
                      </Badge>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="text-center py-6">
                <FileText className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-400 dark:text-gray-500">Nenhuma solicitação registrada</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium text-gray-800 dark:text-gray-100">
              Retenção de Dados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-500 dark:text-gray-400">Conformidade de Retenção</span>
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-100">
                    {(stats?.dataRetentionCompliance || 0).toFixed(0)}%
                  </span>
                </div>
                <Progress value={stats?.dataRetentionCompliance || 0} className="h-2" />
              </div>
              
              <div className="grid grid-cols-2 gap-4 pt-4">
                <div className="p-3 rounded-md bg-status-success/10 dark:bg-status-success/20">
                  <p className="text-lg font-semibold text-status-success dark:text-status-success">{stats?.dataWithinRetention || 0}</p>
                  <p className="text-xs text-status-success dark:text-status-success">Dentro do prazo</p>
                </div>
                <div className="p-3 rounded-md bg-status-error/10 dark:bg-status-error/20">
                  <p className="text-lg font-semibold text-status-error dark:text-status-error">{stats?.dataExceedingRetention || 0}</p>
                  <p className="text-xs text-status-error dark:text-status-error">Prazo excedido</p>
                </div>
              </div>

              {stats?.nextRetentionReview && (
                <div className="flex items-center gap-2 pt-3 border-t border-gray-200 dark:border-gray-700">
                  <Calendar className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                  <span className="text-sm text-gray-400 dark:text-gray-500">
                    Próxima revisão: {formatDate(stats.nextRetentionReview)}
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {breaches.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium text-gray-800 dark:text-gray-100">
              Incidentes de Dados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-2 text-xs font-medium text-gray-400 dark:text-gray-500">Incidente</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-gray-400 dark:text-gray-500">Severidade</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-gray-400 dark:text-gray-500">Data</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-gray-400 dark:text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {breaches.slice(0, 5).map((breach) => (
                    <tr key={breach.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800/50 border-gray-200 dark:border-gray-700">
                      <td className="py-3 px-2 text-sm text-gray-800 dark:text-gray-100">{breach.title}</td>
                      <td className="py-3 px-2">
                        <Badge variant={breach.severity === 'critical' || breach.severity === 'high' ? 'destructive' : breach.severity === 'medium' ? 'warning' : 'default'}>
                          {breach.severity}
                        </Badge>
                      </td>
                      <td className="py-3 px-2 text-sm text-gray-400 dark:text-gray-500">{formatDate(breach.detectedAt)}</td>
                      <td className="py-3 px-2">
                        <Badge variant={breach.status === 'closed' ? 'success' : breach.status === 'investigating' ? 'warning' : 'destructive'}>
                          {breach.status === 'closed' ? 'Fechado' : breach.status === 'investigating' ? 'Investigando' : 'Aberto'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
