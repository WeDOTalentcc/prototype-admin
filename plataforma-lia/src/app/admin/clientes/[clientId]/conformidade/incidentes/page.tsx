"use client"

import React, { use, useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { toast } from "sonner"
import {
  Shield,
  Lock,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Loader2,
  Clock,
  Activity,
  Server,
  Wifi,
  WifiOff } from "lucide-react"
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

interface Integration {
  id: string
  name: string
  type: string
  status: 'up' | 'down' | 'degraded'
  uptime: number
  lastCheck: string
  responseTime?: number
}

interface Incident {
  id: string
  title: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  status: 'open' | 'investigating' | 'resolved'
  startedAt: string
  resolvedAt?: string
  affectedServices: string[]
}

const severityColors: Record<string, string> = {
  critical: 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error',
  high: 'bg-wedo-orange/15 text-wedo-orange dark:bg-wedo-orange/30 dark:text-wedo-orange',
  medium: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  low: 'bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary' }

const statusColors: Record<string, string> = {
  open: 'bg-status-error/15 text-status-error dark:bg-status-error/30 dark:text-status-error',
  investigating: 'bg-status-warning/15 text-status-warning dark:bg-status-warning/30 dark:text-status-warning',
  resolved: 'bg-status-success/15 text-status-success dark:bg-status-success/30 dark:text-status-success' }

const statusLabels: Record<string, string> = {
  open: 'Aberto',
  investigating: 'Investigando',
  resolved: 'Resolvido' }

function LoadingSpinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'
  return <Loader2 className={`${sizeClass} animate-spin motion-reduce:animate-none text-lia-text-secondary`} />
}

export default function IncidentesPage({ params }: { params: Promise<{ clientId: string }> }) {
  const { clientId } = use(params)
  const pathname = usePathname()
  const basePath = `/admin/clientes/${clientId}/conformidade`
  
  const { breaches, isLoading, error, refetch } = useLGPDCompliance(clientId)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [integrations, setIntegrations] = useState<Integration[]>([])
  const [integrationsLoading, setIntegrationsLoading] = useState(true)

  const fetchIntegrations = useCallback(async () => {
    try {
      setIntegrationsLoading(true)
      const response = await fetch(`/api/backend-proxy/clients/${clientId}/integrations`)
      if (!response.ok) {
        throw new Error('Failed to fetch integrations')
      }
      const data = await response.json()
      const mappedIntegrations: Integration[] = (data || []).map((item: Record<string, unknown>) => ({
        id: item.id || String(Math.random()),
        name: item.name || item.provider || 'Integração',
        type: item.type || item.category || 'Sistema',
        status: item.status === 'active' || item.status === 'connected' ? 'up' : item.status === 'disconnected' ? 'down' : 'degraded',
        uptime: item.uptime || 99.9,
        lastCheck: item.last_check || item.updated_at || new Date().toISOString(),
        responseTime: item.response_time || 100
      }))
      setIntegrations(mappedIntegrations)
    } catch (err) {
      toast.error('Erro ao carregar integrações')
    } finally {
      setIntegrationsLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchIntegrations()
  }, [fetchIntegrations])

  const formatDateTime = (dateStr: string | undefined | null) => {
    if (!dateStr) return '-'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
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

  const allIncidents: Incident[] = breaches.map(b => ({
    id: b.id,
    title: (b as Record<string, unknown>).title as string,
    severity: b.severity as 'critical' | 'high' | 'medium' | 'low',
    status: b.status === 'closed' ? 'resolved' as const : b.status === 'investigating' ? 'investigating' as const : 'open' as const,
    startedAt: (b as Record<string, unknown>).detectedAt as string,
    resolvedAt: (b as Record<string, unknown>).resolvedAt as string | undefined,
    affectedServices: ((b as Record<string, unknown>).affectedSystems as string[]) || [] }))

  const filteredIncidents = filterStatus === 'all' 
    ? allIncidents 
    : allIncidents.filter(i => i.status === filterStatus)

  const openIncidents = allIncidents.filter(i => i.status !== 'resolved').length
  const resolvedIncidents = allIncidents.filter(i => i.status === 'resolved').length
  const healthyIntegrations = integrations.filter(i => i.status === 'up').length

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
          <span className="ml-3 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Carregando incidentes...</span>
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
          <p className="text-sm text-status-error">Erro ao carregar incidentes</p>
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
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Incidentes Abertos</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{openIncidents}</p>
                <div className="flex items-center gap-1 mt-1">
                  {openIncidents > 0 ? (
                    <>
                      <AlertTriangle className="w-3 h-3 text-status-warning" />
                      <span className="text-xs text-status-warning">Requer atenção</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-status-success" />
                      <span className="text-xs text-status-success">Tudo OK</span>
                    </>
                  )}
                </div>
              </div>
              <div className={cn(
                "w-10 h-10 rounded-md flex items-center justify-center",
                openIncidents > 0 ? "bg-status-warning/10 dark:bg-status-warning/20" : "bg-status-success/10 dark:bg-status-success/20"
              )}>
                <AlertTriangle className={cn(
                  "w-5 h-5",
                  openIncidents > 0 ? "text-status-warning dark:text-status-warning" : "text-status-success dark:text-status-success"
                )} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Resolvidos</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">{resolvedIncidents}</p>
                <div className="flex items-center gap-1 mt-1">
                  <CheckCircle2 className="w-3 h-3 text-status-success" />
                  <span className="text-xs text-status-success">Últimos 30 dias</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-success/10 dark:bg-status-success/20 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-status-success dark:text-status-success" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Integrações Saudáveis</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {integrationsLoading ? '-' : `${healthyIntegrations}/${integrations.length}`}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <Wifi className="w-3 h-3 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  <span className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">Online</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 flex items-center justify-center">
                <Server className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">Uptime Médio</p>
                <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary">
                  {integrationsLoading || integrations.length === 0 ? '-' : `${(integrations.reduce((acc, i) => acc + i.uptime, 0) / integrations.length).toFixed(1)}%`}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <Activity className="w-3 h-3 text-wedo-purple" />
                  <span className="text-xs text-wedo-purple">Últimos 30 dias</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-wedo-purple/10 dark:bg-wedo-purple/20 flex items-center justify-center">
                <Activity className="w-5 h-5 text-wedo-purple dark:text-wedo-purple" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
              Incidentes Recentes
            </CardTitle>
            <div className="flex items-center gap-2">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="text-sm px-3 py-1.5 rounded-md border bg-lia-bg-primary dark:bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary"
              >
                <option value="all">Todos</option>
                <option value="open">Abertos</option>
                <option value="investigating">Investigando</option>
                <option value="resolved">Resolvidos</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredIncidents.length > 0 ? (
            <div className="space-y-3">
              {filteredIncidents.map((incident) => (
                <div key={incident.id} className="p-4 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">{incident.title}</h4>
                        <Badge className={severityColors[incident.severity]}>
                          {incident.severity}
                        </Badge>
                        <Badge className={statusColors[incident.status]}>
                          {statusLabels[incident.status]}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-2">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-lia-text-tertiary dark:text-lia-text-secondary" />
                          <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">
                            Início: {formatDateTime(incident.startedAt)}
                          </span>
                        </div>
                        {incident.resolvedAt && (
                          <div className="flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3 text-status-success" />
                            <span className="text-xs text-status-success">
                              Resolvido: {formatDateTime(incident.resolvedAt)}
                            </span>
                          </div>
                        )}
                      </div>
                      {incident.affectedServices.length > 0 && (
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">Serviços afetados:</span>
                          {incident.affectedServices.map((service, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">{service}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <CheckCircle2 className="w-8 h-8 text-status-success mx-auto mb-2" />
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" aria-live="polite" aria-atomic="true">Nenhum incidente encontrado</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary">
            Status das Integrações
          </CardTitle>
        </CardHeader>
        <CardContent>
          {integrationsLoading ? (
            <div className="flex items-center justify-center py-6">
              <LoadingSpinner size="md" />
              <span className="ml-3 text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
                Carregando integrações...
              </span>
            </div>
          ) : integrations.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {integrations.map((integration) => (
                <div 
                  key={integration.id} 
                  className="p-4 rounded-md border flex items-center justify-between border-lia-border-subtle dark:border-lia-border-subtle"
                >
                  <div className="flex items-center gap-3">
                    {integration.status === 'up' ? (
                      <Wifi className="w-5 h-5 text-status-success" />
                    ) : integration.status === 'down' ? (
                      <WifiOff className="w-5 h-5 text-status-error" />
                    ) : (
                      <Wifi className="w-5 h-5 text-status-warning" />
                    )}
                    <div>
                      <p className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary">{integration.name}</p>
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary">{integration.type}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge variant={integration.status === 'up' ? 'success' : integration.status === 'down' ? 'destructive' : 'warning'}>
                      {integration.status === 'up' ? 'Online' : integration.status === 'down' ? 'Offline' : 'Degradado'}
                    </Badge>
                    <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary">
                      {integration.uptime}% uptime
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <Server className="w-8 h-8 text-lia-text-tertiary mx-auto mb-2" />
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
                Nenhuma integração configurada
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
