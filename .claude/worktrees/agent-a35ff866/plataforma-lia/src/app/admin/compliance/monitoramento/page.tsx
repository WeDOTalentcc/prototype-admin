"use client"

import React from "react"
import Link from "next/link"
import { 
  Activity, 
  AlertCircle, 
  Bell, 
  CheckCircle2,
  Clock, 
  MonitorDot, 
  Radio,
  TrendingUp,
  ExternalLink,
  Server,
  Wifi,
  WifiOff,
  ArrowRight,
  Database,
  Globe,
  Shield,
  Zap
} from "lucide-react"
import { getWorkOSLinks } from "@/lib/workos-links"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"

type SystemStatus = 'ok' | 'degraded' | 'critical'

const systemOverview = {
  status: 'ok' as SystemStatus,
  systemsMonitored: 6,
  openIncidents: 1,
  alerts24h: 7,
  avgUptime: 99.95
}

const recentAlerts = [
  { id: 'ALT-005', title: 'Múltiplas tentativas de login falhas', severity: 'high', type: 'security', createdAt: '2024-12-20T09:45:00' },
  { id: 'ALT-004', title: 'Latência elevada na API', severity: 'medium', type: 'performance', createdAt: '2024-12-20T09:30:00' },
  { id: 'ALT-003', title: 'Certificado SSL expira em 30 dias', severity: 'medium', type: 'compliance', createdAt: '2024-12-20T08:00:00' },
  { id: 'ALT-002', title: 'Falha na sincronização com Gupy', severity: 'high', type: 'integration', createdAt: '2024-12-20T07:45:00' },
  { id: 'ALT-001', title: 'Novo dispositivo detectado', severity: 'low', type: 'security', createdAt: '2024-12-20T07:30:00' },
]

const mainServices = [
  { name: 'Plataforma LIA', status: 'ok', uptime: 99.99, latency: '45ms', lastCheck: '2024-12-20T10:00:00' },
  { name: 'Banco de Dados', status: 'ok', uptime: 99.95, latency: '12ms', lastCheck: '2024-12-20T10:00:00' },
  { name: 'API Backend', status: 'ok', uptime: 99.98, latency: '28ms', lastCheck: '2024-12-20T10:00:00' },
  { name: 'Integração Gupy', status: 'ok', uptime: 99.90, latency: '120ms', lastCheck: '2024-12-20T09:55:00' },
  { name: 'Integração LinkedIn', status: 'degraded', uptime: 98.50, latency: '350ms', lastCheck: '2024-12-20T09:50:00' },
  { name: 'Serviço de E-mail', status: 'ok', uptime: 99.95, latency: '85ms', lastCheck: '2024-12-20T10:00:00' },
]

const recentIncidents = [
  { 
    id: 'INC-003', 
    title: 'Pico de requisições detectado', 
    severity: 'low', 
    status: 'resolved', 
    startedAt: '2024-12-19T08:15:00',
    resolvedAt: '2024-12-19T08:45:00'
  },
  { 
    id: 'INC-002', 
    title: 'Latência elevada na API', 
    severity: 'medium', 
    status: 'investigating', 
    startedAt: '2024-12-18T14:00:00',
    resolvedAt: null
  },
  { 
    id: 'INC-001', 
    title: 'Tentativa de acesso não autorizado', 
    severity: 'high', 
    status: 'resolved', 
    startedAt: '2024-12-15T10:30:00',
    resolvedAt: '2024-12-15T11:45:00'
  },
]

const integrationStatus = [
  { name: 'Datadog APM', status: 'connected', lastSync: '2024-12-20T09:45:00' },
  { name: 'PagerDuty', status: 'connected', lastSync: '2024-12-20T09:40:00' },
  { name: 'AWS CloudWatch', status: 'connected', lastSync: '2024-12-20T09:30:00' },
]

const getSystemStatusConfig = (status: SystemStatus) => {
  switch (status) {
    case 'ok':
      return { label: 'Operacional', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2, iconColor: 'text-emerald-500', bgColor: 'rgba(16, 185, 129, 0.1)' }
    case 'degraded':
      return { label: 'Degradado', color: 'bg-amber-100 text-amber-700', icon: AlertCircle, iconColor: 'text-amber-500', bgColor: 'rgba(251, 191, 36, 0.1)' }
    case 'critical':
      return { label: 'Crítico', color: 'bg-red-100 text-red-700', icon: AlertCircle, iconColor: 'text-red-500', bgColor: 'rgba(239, 68, 68, 0.1)' }
  }
}

const getServiceIcon = (name: string) => {
  if (name.includes('Plataforma')) return Activity
  if (name.includes('Banco')) return Database
  if (name.includes('API')) return Server
  if (name.includes('Gupy') || name.includes('LinkedIn')) return Globe
  return Zap
}

const subPages = [
  {
    href: '/admin/compliance/monitoramento/dashboard-seguranca',
    icon: MonitorDot,
    name: 'Dashboard de Segurança',
    description: 'KPIs em tempo real'
  },
  {
    href: '/admin/compliance/monitoramento/incidentes',
    icon: AlertCircle,
    name: 'Gestão de Incidentes',
    description: 'Plano de Resposta a Incidentes'
  },
  {
    href: '/admin/compliance/monitoramento/alertas',
    icon: Bell,
    name: 'Alertas Proativos',
    description: 'Configuração de alertas'
  },
]

const getSeverityConfig = (severity: string) => {
  switch (severity) {
    case 'critical':
      return { color: 'bg-red-100 text-red-700 border-red-200', dot: 'bg-red-500' }
    case 'high':
      return { color: 'bg-orange-100 text-orange-700 border-orange-200', dot: 'bg-orange-500' }
    case 'medium':
      return { color: 'bg-amber-100 text-amber-700 border-amber-200', dot: 'bg-amber-500' }
    case 'low':
      return { color: 'bg-green-100 text-green-700 border-green-200', dot: 'bg-green-500' }
    default:
      return { color: 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200', dot: 'bg-gray-500' }
  }
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'resolved':
      return { label: 'Resolvido', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2 }
    case 'investigating':
      return { label: 'Investigando', color: 'bg-amber-100 text-amber-700', icon: Clock }
    case 'mitigating':
      return { label: 'Mitigando', color: 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-50', icon: Activity }
    default:
      return { label: status, color: 'bg-gray-100 text-gray-800 dark:text-gray-200', icon: Clock }
  }
}

export default function MonitoramentoPage() {
  const statusConfig = getSystemStatusConfig(systemOverview.status)
  const StatusIcon = statusConfig.icon

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center"
            style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
          >
            <Activity className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold"
              style={{ 
                color: 'var(--eleven-text-primary)',
                
              }}
            >
              Monitoramento & SOC
            </h1>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Centro de operações de segurança e monitoramento contínuo
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Sistemas Monitorados
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {systemOverview.systemsMonitored}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className={`text-[10px] ${statusConfig.color} hover:${statusConfig.color}`}>
                      {statusConfig.label}
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: statusConfig.bgColor }}>
                  <MonitorDot className={`w-5 h-5 ${statusConfig.iconColor}`} />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Incidentes Abertos
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {systemOverview.openIncidents}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="text-[10px] bg-amber-100 text-amber-700 hover:bg-amber-100">
                      Em investigação
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(251, 146, 60, 0.1)' }}>
                  <AlertCircle className="w-5 h-5 text-orange-500" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Alertas (últimas 24h)
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {systemOverview.alerts24h}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-amber-600">2 alta prioridade</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <Bell className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Uptime Médio
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {systemOverview.avgUptime}%
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <TrendingUp className="w-3 h-3 text-emerald-500" />
                    <span className="text-xs text-emerald-600">Últimos 30 dias</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                  <Server className="w-5 h-5 text-emerald-500" />
                </div>
              </div>
              <div className="mt-3">
                <Progress value={systemOverview.avgUptime} className="h-1.5" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                <Server className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                Status dos Serviços Principais
              </CardTitle>
              <Badge className="bg-emerald-100 text-emerald-700">
                {mainServices.filter(s => s.status === 'ok').length}/{mainServices.length} operacionais
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {mainServices.map((service) => {
                const ServiceIcon = getServiceIcon(service.name)
                const isOk = service.status === 'ok'
                return (
                  <div 
                    key={service.name}
                    className="p-4 rounded-md border"
                    style={{ borderColor: 'var(--eleven-border-subtle)' }}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <ServiceIcon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        <span className="font-medium text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                          {service.name}
                        </span>
                      </div>
                      <Badge className={isOk ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}>
                        {isOk ? 'Operacional' : 'Degradado'}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Uptime</span>
                        <span className="text-xs font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{service.uptime}%</span>
                      </div>
                      <Progress value={service.uptime} className="h-1.5" />
                      <div className="flex items-center justify-between">
                        <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Latência</span>
                        <span className="text-xs font-medium" style={{ color: 'var(--eleven-text-primary)' }}>{service.latency}</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                  <Bell className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  Últimos Alertas
                </CardTitle>
                <Link 
                  href="/admin/compliance/monitoramento/alertas"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:underline flex items-center gap-1"
                >
                  Ver todos <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {recentAlerts.map((alert) => {
                  const severityConfig = getSeverityConfig(alert.severity)
                  return (
                    <div 
                      key={alert.id}
                      className="flex items-center justify-between p-3 rounded-md border"
                      style={{ borderColor: 'var(--eleven-border-subtle)' }}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${severityConfig.dot} ${alert.severity === 'high' || alert.severity === 'critical' ? 'animate-pulse' : ''}`} />
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="font-mono text-xs">
                              {alert.id}
                            </Badge>
                            <span className="font-medium text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                              {alert.title}
                            </span>
                          </div>
                          <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            {new Date(alert.createdAt).toLocaleString('pt-BR')}
                          </p>
                        </div>
                      </div>
                      <Badge className={severityConfig.color}>
                        {alert.severity === 'high' ? 'Alto' : alert.severity === 'medium' ? 'Médio' : alert.severity === 'low' ? 'Baixo' : 'Crítico'}
                      </Badge>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  Status das Integrações
                </CardTitle>
                <a 
                  href={getWorkOSLinks().logStreams}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-gray-600 dark:text-gray-400 hover:underline flex items-center gap-1"
                >
                  Configurar no WorkOS <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {integrationStatus.map((integration) => (
                  <div 
                    key={integration.name}
                    className="flex items-center justify-between p-3 rounded-md border"
                    style={{ borderColor: 'var(--eleven-border-subtle)' }}
                  >
                    <div className="flex items-center gap-3">
                      {integration.status === 'connected' ? (
                        <Wifi className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <WifiOff className="w-4 h-4 text-amber-500" />
                      )}
                      <div>
                        <span className="font-medium text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                          {integration.name}
                        </span>
                        {integration.lastSync && (
                          <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                            Última sincronização: {new Date(integration.lastSync).toLocaleString('pt-BR')}
                          </p>
                        )}
                      </div>
                    </div>
                    <Badge 
                      className={
                        integration.status === 'connected' 
                          ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-100' 
                          : 'bg-amber-100 text-amber-700 hover:bg-amber-100'
                      }
                    >
                      {integration.status === 'connected' ? 'Conectado' : 'Pendente'}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {subPages.map((page) => {
            const Icon = page.icon
            return (
              <Link key={page.href} href={page.href}>
                <Card 
                  className="cursor-pointer hover:transition-shadow h-full"
                  style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div 
                        className="w-10 h-10 rounded-md flex items-center justify-center"
                        style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
                      >
                        <Icon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      </div>
                      <ArrowRight className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
                    </div>
                    <h3 className="font-medium mb-1" style={{ color: 'var(--eleven-text-primary)' }}>
                      {page.name}
                    </h3>
                    <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      {page.description}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            )
          })}
          <Card 
            className="h-full border-dashed border-2"
            style={{ 
              boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
              borderColor: 'var(--eleven-border-subtle)',
              backgroundColor: 'rgba(96, 190, 209, 0.02)'
            }}
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div 
                  className="w-10 h-10 rounded-md flex items-center justify-center"
                  style={{ backgroundColor: 'rgba(139, 92, 246, 0.1)' }}
                >
                  <Radio className="w-5 h-5 text-purple-500" />
                </div>
                <ExternalLink className="w-4 h-4" style={{ color: 'var(--eleven-text-tertiary)' }} />
              </div>
              <h3 className="font-medium mb-1" style={{ color: 'var(--eleven-text-primary)' }}>
                Log Streaming (SIEM)
              </h3>
              <p className="text-sm mb-4" style={{ color: 'var(--eleven-text-tertiary)' }}>
                Configure streaming de logs para Datadog, Splunk, S3 e outros diretamente no WorkOS Dashboard.
              </p>
              <a
                href={getWorkOSLinks().logStreams}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium text-white bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 transition-colors"
              >
                Configurar no WorkOS
                <ExternalLink className="w-3 h-3" />
              </a>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
