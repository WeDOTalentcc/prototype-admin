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
      return { label: 'Operacional', color: 'bg-status-success/15 text-status-success', icon: CheckCircle2, iconColor: 'text-status-success', bgColor: 'var(--status-success-bg)' }
    case 'degraded':
      return { label: 'Degradado', color: 'bg-status-warning/15 text-status-warning', icon: AlertCircle, iconColor: 'text-status-warning', bgColor: 'var(--status-warning-bg)' }
    case 'critical':
      return { label: 'Crítico', color: 'bg-status-error/15 text-status-error', icon: AlertCircle, iconColor: 'text-status-error', bgColor: 'var(--status-error-bg)' }
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
      return { color: 'bg-status-error/15 text-status-error border-status-error/30', dot: 'bg-status-error' }
    case 'high':
      return { color: 'bg-wedo-orange/15 text-wedo-orange border-wedo-orange/30', dot: 'bg-wedo-orange' }
    case 'medium':
      return { color: 'bg-status-warning/15 text-status-warning border-status-warning/30', dot: 'bg-status-warning' }
    case 'low':
      return { color: 'bg-status-success/15 text-status-success border-status-success/30', dot: 'bg-status-success' }
    default:
      return { color: 'bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary border-lia-border-subtle', dot: 'bg-lia-bg-secondary0' }
  }
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'resolved':
      return { label: 'Resolvido', color: 'bg-status-success/15 text-status-success', icon: CheckCircle2 }
    case 'investigating':
      return { label: 'Investigando', color: 'bg-status-warning/15 text-status-warning', icon: Clock }
    case 'mitigating':
      return { label: 'Mitigando', color: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary', icon: Activity }
    default:
      return { label: status, color: 'bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary', icon: Clock }
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
            className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
          >
            <Activity className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
              
            >
              Monitoramento & SOC
            </h1>
            <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
              Centro de operações de segurança e monitoramento contínuo
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Sistemas Monitorados
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {systemOverview.systemsMonitored}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className={`text-micro ${statusConfig.color} hover:${statusConfig.color}`}>
                      {statusConfig.label}
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{backgroundColor: statusConfig.bgColor}}>
                  <MonitorDot className={`w-5 h-5 ${statusConfig.iconColor}`} />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Incidentes Abertos
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {systemOverview.openIncidents}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="text-micro bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
                      Em investigação
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-warning-bg">
                  <AlertCircle className="w-5 h-5 text-wedo-orange" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Alertas (últimas 24h)
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {systemOverview.alerts24h}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-status-warning">2 alta prioridade</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30">
                  <Bell className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Uptime Médio
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {systemOverview.avgUptime}%
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <TrendingUp className="w-3 h-3 text-status-success" />
                    <span className="text-xs text-status-success">Últimos 30 dias</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <Server className="w-5 h-5 text-status-success" />
                </div>
              </div>
              <div className="mt-3">
                <Progress value={systemOverview.avgUptime} className="h-1.5" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6" >
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-medium flex items-center gap-2 text-lia-text-primary dark:text-lia-text-primary" >
                <Server className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                Status dos Serviços Principais
              </CardTitle>
              <Badge className="bg-status-success/15 text-status-success">
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
                    className="p-4 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle"
                    
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <ServiceIcon className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                        <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                          {service.name}
                        </span>
                      </div>
                      <Badge className={isOk ? 'bg-status-success/15 text-status-success' : 'bg-status-warning/15 text-status-warning'}>
                        {isOk ? 'Operacional' : 'Degradado'}
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Uptime</span>
                        <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary" >{service.uptime}%</span>
                      </div>
                      <Progress value={service.uptime} className="h-1.5" />
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >Latência</span>
                        <span className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary" >{service.latency}</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <Card >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-medium flex items-center gap-2 text-lia-text-primary dark:text-lia-text-primary" >
                  <Bell className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  Últimos Alertas
                </CardTitle>
                <Link 
                  href="/admin/compliance/monitoramento/alertas"
                  className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary hover:underline flex items-center gap-1"
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
                      className="flex items-center justify-between p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle"
                      
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${severityConfig.dot} ${alert.severity === 'high' || alert.severity === 'critical' ? 'animate-pulse motion-reduce:animate-none' : ''}`} />
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="font-mono text-xs">
                              {alert.id}
                            </Badge>
                            <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                              {alert.title}
                            </span>
                          </div>
                          <p className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary" >
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

          <Card >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                  Status das Integrações
                </CardTitle>
                <a 
                  href={getWorkOSLinks().logStreams}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary hover:underline flex items-center gap-1"
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
                    className="flex items-center justify-between p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle"
                    
                  >
                    <div className="flex items-center gap-3">
                      {integration.status === 'connected' ? (
                        <Wifi className="w-4 h-4 text-status-success" />
                      ) : (
                        <WifiOff className="w-4 h-4 text-status-warning" />
                      )}
                      <div>
                        <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                          {integration.name}
                        </span>
                        {integration.lastSync && (
                          <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                            Última sincronização: {new Date(integration.lastSync).toLocaleString('pt-BR')}
                          </p>
                        )}
                      </div>
                    </div>
                    <Badge 
                      className={
                        integration.status === 'connected' 
                          ? 'bg-status-success/15 text-status-success hover:bg-status-success/15' 
                          : 'bg-status-warning/15 text-status-warning hover:bg-status-warning/15'
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
                  
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div 
                        className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
                      >
                        <Icon className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                      </div>
                      <ArrowRight className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                    </div>
                    <h3 className="font-medium mb-1 text-lia-text-primary dark:text-lia-text-primary" >
                      {page.name}
                    </h3>
                    <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                      {page.description}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            )
          })}
          <Card 
            className="h-full border-dashed border-2 border-lia-border-subtle dark:border-lia-border-subtle bg-wedo-cyan/[0.02]"
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div 
                  className="w-10 h-10 rounded-md flex items-center justify-center bg-wedo-purple/10"
                >
                  <Radio className="w-5 h-5 text-wedo-purple" />
                </div>
                <ExternalLink className="w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary"  />
              </div>
              <h3 className="font-medium mb-1 text-lia-text-primary dark:text-lia-text-primary" >
                Log Streaming (SIEM)
              </h3>
              <p className="text-sm mb-4 text-lia-text-tertiary dark:text-lia-text-secondary" >
                Configure streaming de logs para Datadog, Splunk, S3 e outros diretamente no WorkOS Dashboard.
              </p>
              <a
                href={getWorkOSLinks().logStreams}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium text-white bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
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
