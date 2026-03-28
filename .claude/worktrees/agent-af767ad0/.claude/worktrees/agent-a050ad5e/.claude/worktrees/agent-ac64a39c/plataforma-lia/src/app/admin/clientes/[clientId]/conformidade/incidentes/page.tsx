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
  XCircle,
  AlertCircle,
  RefreshCw,
  Loader2,
  Clock,
  Activity,
  Server,
  Wifi,
  WifiOff,
  Filter
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
  critical: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  high: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  low: 'bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-50',
}

const statusColors: Record<string, string> = {
  open: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  investigating: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  resolved: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
}

const statusLabels: Record<string, string> = {
  open: 'Aberto',
  investigating: 'Investigando',
  resolved: 'Resolvido',
}

function LoadingSpinner({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'
  return <Loader2 className={`${sizeClass} animate-spin text-gray-600`} />
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
      const mappedIntegrations: Integration[] = (data || []).map((item: any) => ({
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
      console.error('Error fetching integrations:', err)
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
    title: b.title,
    severity: b.severity as 'critical' | 'high' | 'medium' | 'low',
    status: b.status === 'closed' ? 'resolved' as const : b.status === 'investigating' ? 'investigating' as const : 'open' as const,
    startedAt: b.detectedAt,
    resolvedAt: b.resolvedAt,
    affectedServices: b.affectedSystems || [],
  }))

  const filteredIncidents = filterStatus === 'all' 
    ? allIncidents 
    : allIncidents.filter(i => i.status === filterStatus)

  const openIncidents = allIncidents.filter(i => i.status !== 'resolved').length
  const resolvedIncidents = allIncidents.filter(i => i.status === 'resolved').length
  const healthyIntegrations = integrations.filter(i => i.status === 'up').length

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-1 border-b pb-px -mb-px" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
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
                style={{ color: 'var(--eleven-text-secondary)' }}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </Link>
            )
          })}
        </div>
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
          <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Carregando incidentes...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-1 border-b pb-px -mb-px" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
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
                style={{ color: 'var(--eleven-text-secondary)' }}
              >
                <Icon className="w-4 h-4" />
                {tab.name}
              </Link>
            )
          })}
        </div>
        <div className="p-6 text-center">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-sm text-red-600">Erro ao carregar incidentes</p>
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
      <div className="flex items-center gap-1 border-b pb-px -mb-px" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
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
                  : "border-transparent hover:border-gray-300 dark:hover:border-gray-600"
              )}
              style={!isActive ? { color: 'var(--eleven-text-secondary)' } : {}}
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
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Incidentes Abertos</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>{openIncidents}</p>
                <div className="flex items-center gap-1 mt-1">
                  {openIncidents > 0 ? (
                    <>
                      <AlertTriangle className="w-3 h-3 text-amber-500" />
                      <span className="text-xs text-amber-600">Requer atenção</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                      <span className="text-xs text-emerald-600">Tudo OK</span>
                    </>
                  )}
                </div>
              </div>
              <div className={cn(
                "w-10 h-10 rounded-md flex items-center justify-center",
                openIncidents > 0 ? "bg-amber-50 dark:bg-amber-900/20" : "bg-emerald-50 dark:bg-emerald-900/20"
              )}>
                <AlertTriangle className={cn(
                  "w-5 h-5",
                  openIncidents > 0 ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400"
                )} />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Resolvidos</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>{resolvedIncidents}</p>
                <div className="flex items-center gap-1 mt-1">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                  <span className="text-xs text-emerald-600">Últimos 30 dias</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Integrações Saudáveis</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                  {integrationsLoading ? '-' : `${healthyIntegrations}/${integrations.length}`}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <Wifi className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                  <span className="text-xs text-gray-600 dark:text-gray-400">Online</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-gray-50 dark:bg-gray-800/50 flex items-center justify-center">
                <Server className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Uptime Médio</p>
                <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                  {integrationsLoading || integrations.length === 0 ? '-' : `${(integrations.reduce((acc, i) => acc + i.uptime, 0) / integrations.length).toFixed(1)}%`}
                </p>
                <div className="flex items-center gap-1 mt-1">
                  <Activity className="w-3 h-3 text-purple-500" />
                  <span className="text-xs text-purple-600">Últimos 30 dias</span>
                </div>
              </div>
              <div className="w-10 h-10 rounded-md bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center">
                <Activity className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
              Incidentes Recentes
            </CardTitle>
            <div className="flex items-center gap-2">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="text-sm px-3 py-1.5 rounded-md border"
                style={{ 
                  backgroundColor: 'var(--eleven-bg-card)',
                  borderColor: 'var(--eleven-border-subtle)',
                  color: 'var(--eleven-text-primary)'
                }}
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
                <div key={incident.id} className="p-4 rounded-md border" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{incident.title}</h4>
                        <Badge className={severityColors[incident.severity]}>
                          {incident.severity}
                        </Badge>
                        <Badge className={statusColors[incident.status]}>
                          {statusLabels[incident.status]}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-2">
                        <div className="flex items-center gap-1">
                          <Clock className="w-3 h-3" style={{ color: 'var(--eleven-text-tertiary)' }} />
                          <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            Início: {formatDateTime(incident.startedAt)}
                          </span>
                        </div>
                        {incident.resolvedAt && (
                          <div className="flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                            <span className="text-xs text-emerald-600">
                              Resolvido: {formatDateTime(incident.resolvedAt)}
                            </span>
                          </div>
                        )}
                      </div>
                      {incident.affectedServices.length > 0 && (
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Serviços afetados:</span>
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
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>Nenhum incidente encontrado</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
            Status das Integrações
          </CardTitle>
        </CardHeader>
        <CardContent>
          {integrationsLoading ? (
            <div className="flex items-center justify-center py-6">
              <LoadingSpinner size="md" />
              <span className="ml-3 text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Carregando integrações...
              </span>
            </div>
          ) : integrations.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {integrations.map((integration) => (
                <div 
                  key={integration.id} 
                  className="p-4 rounded-md border flex items-center justify-between"
                  style={{ borderColor: 'var(--eleven-border-subtle)' }}
                >
                  <div className="flex items-center gap-3">
                    {integration.status === 'up' ? (
                      <Wifi className="w-5 h-5 text-emerald-500" />
                    ) : integration.status === 'down' ? (
                      <WifiOff className="w-5 h-5 text-red-500" />
                    ) : (
                      <Wifi className="w-5 h-5 text-amber-500" />
                    )}
                    <div>
                      <p className="font-medium text-sm" style={{ color: 'var(--eleven-text-primary)' }}>{integration.name}</p>
                      <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>{integration.type}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge variant={integration.status === 'up' ? 'success' : integration.status === 'down' ? 'destructive' : 'warning'}>
                      {integration.status === 'up' ? 'Online' : integration.status === 'down' ? 'Offline' : 'Degradado'}
                    </Badge>
                    <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      {integration.uptime}% uptime
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <Server className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Nenhuma integração configurada
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
