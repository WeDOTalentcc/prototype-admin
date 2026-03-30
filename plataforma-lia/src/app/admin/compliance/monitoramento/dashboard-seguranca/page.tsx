"use client"

import React from "react"
import { 
  MonitorDot, 
  ShieldAlert,
  Shield,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Activity,
  CheckCircle2,
  Clock,
  Gauge,
  BarChart3,
  AlertCircle,
  Eye,
  XCircle,
  ExternalLink,
  KeyRound,
  Users
} from "lucide-react"
import { getWorkOSLinks } from "@/lib/workos-links"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const securityMetrics = {
  totalEvents: 1847,
  criticalAlerts: 3,
  avgResponseTime: 145,
  securityScore: 87,
}

const eventsByDay = [
  { day: 'Seg', count: 245, critical: 2, high: 8, medium: 45, low: 190 },
  { day: 'Ter', count: 312, critical: 1, high: 12, medium: 58, low: 241 },
  { day: 'Qua', count: 198, critical: 0, high: 5, medium: 32, low: 161 },
  { day: 'Qui', count: 287, critical: 3, high: 9, medium: 51, low: 224 },
  { day: 'Sex', count: 356, critical: 2, high: 15, medium: 67, low: 272 },
  { day: 'Sáb', count: 124, critical: 0, high: 2, medium: 18, low: 104 },
  { day: 'Dom', count: 89, critical: 0, high: 1, medium: 12, low: 76 },
]

const severityDistribution = [
  { severity: 'Crítico', count: 8, color: 'var(--status-error)', percentage: 0.5 },
  { severity: 'Alto', count: 52, color: 'var(--status-warning)', percentage: 3.2 },
  { severity: 'Médio', count: 283, color: 'var(--status-warning)', percentage: 17.7 },
  { severity: 'Baixo', count: 1268, color: 'var(--status-success)', percentage: 78.6 },
]

const topEventTypes = [
  { type: 'Tentativa de login falha', count: 456, trend: -12 },
  { type: 'Acesso de novo dispositivo', count: 234, trend: 8 },
  { type: 'Requisição bloqueada (WAF)', count: 189, trend: -5 },
  { type: 'Token API expirado', count: 145, trend: 3 },
  { type: 'Alteração de permissão', count: 98, trend: 15 },
]

const recentEvents = [
  { 
    id: 'EVT-1847', 
    timestamp: '2024-12-20T10:45:23', 
    type: 'Tentativa de login falha', 
    severity: 'medium', 
    description: 'Múltiplas tentativas de login do IP 192.168.1.100', 
    status: 'investigating' 
  },
  { 
    id: 'EVT-1846', 
    timestamp: '2024-12-20T10:42:15', 
    type: 'Acesso de novo dispositivo', 
    severity: 'low', 
    description: 'Novo dispositivo registrado para maria.silva@empresa.com', 
    status: 'resolved' 
  },
  { 
    id: 'EVT-1845', 
    timestamp: '2024-12-20T10:38:07', 
    type: 'Requisição bloqueada (WAF)', 
    severity: 'high', 
    description: 'Tentativa de SQL injection detectada e bloqueada', 
    status: 'resolved' 
  },
  { 
    id: 'EVT-1844', 
    timestamp: '2024-12-20T10:35:52', 
    type: 'Token API expirado', 
    severity: 'low', 
    description: 'Token da integração Gupy expirou automaticamente', 
    status: 'resolved' 
  },
  { 
    id: 'EVT-1843', 
    timestamp: '2024-12-20T10:30:11', 
    type: 'Alteração de permissão', 
    severity: 'medium', 
    description: 'Permissões elevadas para usuario admin@empresa.com', 
    status: 'acknowledged' 
  },
  { 
    id: 'EVT-1842', 
    timestamp: '2024-12-20T10:28:45', 
    type: 'Acesso suspeito', 
    severity: 'critical', 
    description: 'Acesso de localização incomum detectado para conta root', 
    status: 'investigating' 
  },
  { 
    id: 'EVT-1841', 
    timestamp: '2024-12-20T10:22:33', 
    type: 'Rate limit excedido', 
    severity: 'low', 
    description: 'API rate limit atingido pelo cliente ID 4521', 
    status: 'resolved' 
  },
  { 
    id: 'EVT-1840', 
    timestamp: '2024-12-20T10:18:19', 
    type: 'Tentativa de escalação', 
    severity: 'high', 
    description: 'Tentativa de acesso não autorizado a recursos admin', 
    status: 'investigating' 
  },
]

const getSeverityConfig = (severity: string) => {
  switch (severity) {
    case 'critical':
      return { label: 'Crítico', color: 'bg-status-error/15 text-status-error', dot: 'bg-status-error' }
    case 'high':
      return { label: 'Alto', color: 'bg-wedo-orange/15 text-wedo-orange', dot: 'bg-wedo-orange' }
    case 'medium':
      return { label: 'Médio', color: 'bg-status-warning/15 text-status-warning', dot: 'bg-status-warning' }
    case 'low':
      return { label: 'Baixo', color: 'bg-status-success/15 text-status-success', dot: 'bg-status-success' }
    default:
      return { label: severity, color: 'bg-gray-100 lia-text-800 dark:text-lia-text-primary', dot: 'bg-gray-500' }
  }
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'investigating':
      return { label: 'Investigando', color: 'bg-status-warning/15 text-status-warning', icon: Eye }
    case 'acknowledged':
      return { label: 'Reconhecido', color: 'bg-gray-100 dark:bg-lia-bg-secondary lia-text-900 dark:lia-text-50', icon: CheckCircle2 }
    case 'resolved':
      return { label: 'Resolvido', color: 'bg-status-success/15 text-status-success', icon: CheckCircle2 }
    case 'open':
      return { label: 'Aberto', color: 'bg-status-error/15 text-status-error', icon: AlertCircle }
    default:
      return { label: status, color: 'bg-gray-100 lia-text-800 dark:text-lia-text-primary', icon: Clock }
  }
}

export default function DashboardSegurancaPage() {
  const maxDayCount = Math.max(...eventsByDay.map(d => d.count))
  const totalSeverityCount = severityDistribution.reduce((acc, s) => acc + s.count, 0)

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
          >
            <MonitorDot className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary"
              
            >
              Dashboard de Segurança
            </h1>
            <p className="text-sm lia-text-400 dark:lia-text-500" >
              Monitoramento em tempo real • Atualizado há 2 minutos
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm lia-text-400 dark:lia-text-500" >
                    Total de Eventos
                  </p>
                  <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary" >
                    {securityMetrics.totalEvents.toLocaleString('pt-BR')}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <TrendingUp className="w-3 h-3 text-status-success" />
                    <span className="text-xs text-status-success">+12% vs semana anterior</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30">
                  <Activity className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm lia-text-400 dark:lia-text-500" >
                    Alertas Críticos Ativos
                  </p>
                  <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary" >
                    {securityMetrics.criticalAlerts}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <TrendingDown className="w-3 h-3 text-status-success" />
                    <span className="text-xs text-status-success">-2 vs ontem</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-red-500/10">
                  <ShieldAlert className="w-5 h-5 text-status-error" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm lia-text-400 dark:lia-text-500" >
                    Tempo Médio de Resposta
                  </p>
                  <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary" >
                    {securityMetrics.avgResponseTime}ms
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="text-micro bg-status-success/15 text-status-success hover:bg-status-success/15">
                      Dentro do SLA
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <Clock className="w-5 h-5 text-status-success" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm lia-text-400 dark:lia-text-500" >
                    Score de Segurança
                  </p>
                  <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary" >
                    {securityMetrics.securityScore}/100
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="text-micro bg-status-success/15 text-status-success hover:bg-status-success/15">
                      Excelente
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30">
                  <Gauge className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                </div>
              </div>
              <div className="mt-3">
                <Progress value={securityMetrics.securityScore} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6" style={{borderColor: 'var(--wedo-cyan-border)'}}>
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
                >
                  <KeyRound className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary" >
                    Autenticação Empresarial (WorkOS)
                  </CardTitle>
                  <CardDescription className="mt-1">
                    Métricas de SSO, MFA e sessões disponíveis no WorkOS Dashboard.
                  </CardDescription>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => window.open(getWorkOSLinks().dashboard, '_blank')}
              >
                Ver no WorkOS
                <ExternalLink className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="flex items-center gap-3 p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle" >
                <div className="w-2 h-2 rounded-full bg-status-success" />
                <div>
                  <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >SSO</p>
                  <p className="text-xs lia-text-400 dark:lia-text-500" >Ativo</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle" >
                <div className="w-2 h-2 rounded-full bg-status-success" />
                <div>
                  <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >SCIM</p>
                  <p className="text-xs lia-text-400 dark:lia-text-500" >Ativo</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle" >
                <div className="w-2 h-2 rounded-full bg-status-success" />
                <div>
                  <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >MFA</p>
                  <p className="text-xs lia-text-400 dark:lia-text-500" >Habilitado</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle" >
                <Users className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                <div>
                  <p className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >Sessões</p>
                  <p className="text-xs lia-text-400 dark:lia-text-500" >Gerenciadas via WorkOS</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <Card className="lg:col-span-2" >
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2 lia-text-800 dark:text-lia-text-primary" >
                <BarChart3 className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                Eventos por Dia (Últimos 7 dias)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between h-40 gap-3">
                {eventsByDay.map((item, idx) => (
                  <div key={idx} className="flex flex-col items-center flex-1">
                    <div className="w-full flex flex-col-reverse rounded-t overflow-hidden" style={{height: `${(item.count / maxDayCount) * 100}%`, minHeight: '20px'}}>
                      <div style={{ height: `${(item.low / item.count) * 100}%` }} className="bg-status-success" />
                      <div style={{ height: `${(item.medium / item.count) * 100}%` }} className="bg-status-warning" />
                      <div style={{ height: `${(item.high / item.count) * 100}%` }} className="bg-status-warning" />
                      <div style={{ height: `${(item.critical / item.count) * 100}%` }} className="bg-status-error" />
                    </div>
                    <span className="text-xs font-medium mt-2 lia-text-800 dark:text-lia-text-primary" >
                      {item.count}
                    </span>
                    <span className="text-xs mt-1 lia-text-400 dark:lia-text-500" >
                      {item.day}
                    </span>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-center gap-6 mt-4 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle" >
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-md bg-status-error" />
                  <span className="text-xs lia-text-400 dark:lia-text-500" >Crítico</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-md bg-status-warning" />
                  <span className="text-xs lia-text-400 dark:lia-text-500" >Alto</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-md bg-status-warning" />
                  <span className="text-xs lia-text-400 dark:lia-text-500" >Médio</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-md bg-status-success" />
                  <span className="text-xs lia-text-400 dark:lia-text-500" >Baixo</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2 lia-text-800 dark:text-lia-text-primary" >
                <Shield className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                Distribuição por Severidade
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {severityDistribution.map((item, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-md" style={{backgroundColor: item.color}} />
                        <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >
                          {item.severity}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm lia-text-400 dark:lia-text-500" >
                          {item.count}
                        </span>
                        <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >
                          {item.percentage}%
                        </span>
                      </div>
                    </div>
                    <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                      <div 
                        className="h-full rounded-full transition-[width,height]"
                        style={{width: `${item.percentage}%`, backgroundColor: item.color}}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div 
                className="mt-4 p-3 rounded-md bg-gray-200/20"
              >
                <p className="text-xs lia-text-400 dark:lia-text-500" >
                  Total: {totalSeverityCount.toLocaleString('pt-BR')} eventos nos últimos 7 dias
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <Card >
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2 lia-text-800 dark:text-lia-text-primary" >
                <AlertTriangle className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                Top 5 Tipos de Eventos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {topEventTypes.map((event, idx) => (
                  <div 
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-md border hover:bg-gray-50 transition-colors border-lia-border-subtle dark:border-lia-border-subtle"
                    
                  >
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium bg-gray-200/30"
                      >
                        {idx + 1}
                      </div>
                      <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >
                        {event.type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold lia-text-800 dark:text-lia-text-primary" >
                        {event.count}
                      </span>
                      <div className={`flex items-center gap-1 ${event.trend > 0 ? 'text-status-error' : 'text-status-success'}`}>
                        {event.trend > 0 ? (
                          <TrendingUp className="w-3 h-3" />
                        ) : (
                          <TrendingDown className="w-3 h-3" />
                        )}
                        <span className="text-xs">{Math.abs(event.trend)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2" >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-medium flex items-center gap-2 lia-text-800 dark:text-lia-text-primary" >
                  <Activity className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                  Eventos Recentes
                </CardTitle>
                <Badge className="bg-gray-100 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary">
                  {recentEvents.length} eventos
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[140px]">Timestamp</TableHead>
                    <TableHead>Tipo</TableHead>
                    <TableHead>Severidade</TableHead>
                    <TableHead className="hidden md:table-cell">Descrição</TableHead>
                    <TableHead className="text-right">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentEvents.map((event) => {
                    const severityConfig = getSeverityConfig(event.severity)
                    const statusConfig = getStatusConfig(event.status)
                    const StatusIcon = statusConfig.icon
                    return (
                      <TableRow key={event.id} className="hover:bg-gray-50">
                        <TableCell>
                          <span className="text-xs font-mono lia-text-500 dark:text-lia-text-tertiary" >
                            {new Date(event.timestamp).toLocaleString('pt-BR', {
                              day: '2-digit',
                              month: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm font-medium lia-text-800 dark:text-lia-text-primary" >
                            {event.type}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge className={severityConfig.color}>
                            {severityConfig.label}
                          </Badge>
                        </TableCell>
                        <TableCell className="hidden md:table-cell max-w-sidebar-content">
                          <span className="text-xs truncate block lia-text-400 dark:lia-text-500" >
                            {event.description}
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge className={`${statusConfig.color} gap-1`}>
                            <StatusIcon className="w-3 h-3" />
                            {statusConfig.label}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
