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
  rectification: UserCheck }

const dsrTypeLabels: Record<string, string> = {
  access: 'Acesso',
  deletion: 'Exclusão',
  portability: 'Portabilidade',
  rectification: 'Retificação' }

const dsrStatusColors: Record<string, string> = {
  pending: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  in_progress: 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary',
  completed: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success',
  overdue: 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error' }

const dsrStatusLabels: Record<string, string> = {
  pending: 'Pendente',
  in_progress: 'Em Andamento',
  completed: 'Concluído',
  overdue: 'Atrasado' }

function LoadingSpinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'
  return <Loader2 className={`${sizeClass} animate-spin motion-reduce:animate-none text-lia-text-secondary`} />
}

export default function LGPDPage({ params }: { params: Promise<{ clientId: string }> }) {
  const { clientId } = use(params)
  const pathname = usePathname()
  const basePath = `/admin/clientes/${clientId}/conformidade`
  
  const { stats, dpo, breaches, decisions, totalBreaches, isLoading, error, refetch } = useLGPDCompliance(clientId)

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
        <div className="flex items-center gap-1 border-b pb-px -mb-px border-lia-border-subtle dark:border-lia-border-subtle">
          {internalTabs.map((tab) => {
            const Icon = tab.icon
            return (
              <Link
                key={tab.href}
                href={basePath + tab.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                  "border-transparent",
                  "text-lia-text-secondary dark:text-lia-text-tertiary"
                )}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </Link>
            )
          })}
        </div>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Carregando dados LGPD...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-1 border-b pb-px -mb-px border-lia-border-subtle dark:border-lia-border-subtle">
          {internalTabs.map((tab) => {
            const Icon = tab.icon
            return (
              <Link
                key={tab.href}
                href={basePath + tab.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                  "border-transparent",
                  "text-lia-text-secondary dark:text-lia-text-tertiary"
                )}
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
      <div className="flex items-center gap-1 border-b pb-px -mb-px border-lia-border-subtle dark:border-lia-border-subtle">
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
                  ? "border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary"
                  : "border-transparent hover:border-lia-border-default dark:hover:border-lia-border-medium text-lia-text-secondary dark:text-lia-text-tertiary"
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
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Consentimentos</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{(stats as any)?.totalConsents || 0}</p>
                <div className="flex items-center gap-1 mt-1">
                  <UserCheck className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">{(stats as any)?.activeConsents || 0} ativos</span>
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
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">DSRs Pendentes</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{(stats as any)?.pendingDSRs || 0}</p>
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
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Taxa Consentimento</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{((stats as any)?.consentComplianceRate || 0).toFixed(0)}%</p>
                <Progress value={(stats as any)?.consentComplianceRate || 0} className="h-2 mt-2 w-24" />
              </div>
              <div className="w-10 h-10 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Incidentes LGPD</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{totalBreaches}</p>
                <div className="flex items-center gap-1 mt-1">
                  {breaches.filter(b => (b as any).status !== 'closed').length > 0 ? (
                    <>
                      <AlertTriangle className="w-3 h-3 text-status-error" />
                      <span className="text-xs text-status-error">{breaches.filter(b => (b as any).status !== 'closed').length} abertos</span>
                    </>
                  ) : (
                    // @ts-ignore TODO: fix type
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
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Encarregado de Dados (DPO)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-wedo-purple/10 dark:bg-wedo-purple/20 flex items-center justify-center">
                <UserCheck className="w-6 h-6 text-wedo-purple dark:text-wedo-purple" />
              </div>
              <div className="flex-1">
                <p className="font-medium text-lia-text-primary dark:text-lia-text-primary">{(dpo as any).name}</p>
                <div className="flex items-center gap-4 mt-1">
                  <div className="flex items-center gap-1">
                    <Mail className="w-3 h-3 text-lia-text-tertiary dark:text-lia-text-secondary" />
                    <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">{(dpo as any).email}</span>
                  </div>
                  {(dpo as any).phone && (
                    // @ts-ignore TODO: fix type — Property 'phone' does not exist on type 'DPORegistry'.
                    <span className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">{dpo.phone}</span>
                  )}
                </div>
                {(dpo as any).registrationDate && (
                  <p className="text-xs mt-2 text-lia-text-tertiary dark:text-lia-text-secondary">
                    {/* @ts-ignore TODO: fix type */}
                    Registrado em {formatDate((dpo as any).registrationDate)}
                  </p>
                )}
              </div>
              <Badge variant={(dpo as any).status === 'active' ? 'success' : 'warning'}>
                {(dpo as any).status === 'active' ? 'Ativo' : 'Inativo'}
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

{/* @ts-ignore TODO: fix type */}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Solicitações de Titulares (DSR)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {decisions.length > 0 ? (
              <div className="space-y-3">
                {decisions.slice(0, 5).map((decision) => {
                  const TypeIcon = dsrTypeIcons[decision.decisionType] || FileText
                  return (
                    <div key={decision.id} className="flex items-center justify-between p-3 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary">
                      <div className="flex items-center gap-3">
                        <TypeIcon className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
                        <div>
                          <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                            {decision.candidateName || 'Titular'}
                          </p>
                          <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                            {dsrTypeLabels[decision.decisionType] || decision.decisionType} - {formatDate(decision.createdAt)}
                          </p>
                        </div>
                      </div>
                      <Badge className={dsrStatusColors[(decision as any).status] || dsrStatusColors.pending}>
                        {/* @ts-ignore TODO: fix type */}
                        {dsrStatusLabels[(decision as any).status] || (decision as any).status}
                      </Badge>
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="text-center py-6">
                <FileText className="w-8 h-8 text-lia-text-tertiary mx-auto mb-2" />
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Nenhuma solicitação registrada</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* @ts-ignore TODO: fix type */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Retenção de Dados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Conformidade de Retenção</span>
                  <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                    {((stats as any)?.dataRetentionCompliance || 0).toFixed(0)}%
                  </span>
                </div>
                <Progress value={(stats as any)?.dataRetentionCompliance || 0} className="h-2" />
              </div>
              
              <div className="grid grid-cols-2 gap-4 pt-4">
                <div className="p-3 rounded-md bg-status-success/10 dark:bg-status-success/20">
                  <p className="text-lg font-semibold text-status-success dark:text-status-success">{(stats as any)?.dataWithinRetention || 0}</p>
                  <p className="text-xs text-status-success dark:text-status-success">Dentro do prazo</p>
                </div>
                <div className="p-3 rounded-md bg-status-error/10 dark:bg-status-error/20">
                  <p className="text-lg font-semibold text-status-error dark:text-status-error">{(stats as any)?.dataExceedingRetention || 0}</p>
                  <p className="text-xs text-status-error dark:text-status-error">Prazo excedido</p>
                </div>
              </div>              {(stats as any)?.nextRetentionReview && (
                <div className="flex items-center gap-2 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                  <Calendar className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary" />
                  <span className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">                    Próxima revisão: {formatDate((stats as any).nextRetentionReview)}
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
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Incidentes de Dados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle">
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Incidente</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Severidade</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Data</th>
                    <th className="text-left py-3 px-2 text-xs font-medium text-lia-text-tertiary dark:text-lia-text-secondary">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {breaches.slice(0, 5).map((breach) => (
                    <tr key={breach.id} className="border-b hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 border-lia-border-subtle dark:border-lia-border-subtle">
                      <td className="py-3 px-2 text-sm text-lia-text-primary dark:text-lia-text-primary">{(breach as any).title}</td>
                      <td className="py-3 px-2">
                        <Badge variant={breach.severity === 'critical' || breach.severity === 'high' ? 'destructive' : breach.severity === 'medium' ? 'warning' : 'default'}>
                          {breach.severity}
                        </Badge>
                      </td>
                      <td className="py-3 px-2 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">{formatDate((breach as any).detectedAt)}</td>
                      <td className="py-3 px-2">
                        <Badge variant={(breach as any).status === 'closed' ? 'success' : breach.status === 'investigating' ? 'warning' : 'destructive'}>
                          {(breach as any).status === 'closed' ? 'Fechado' : breach.status === 'investigating' ? 'Investigando' : 'Aberto'}
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
