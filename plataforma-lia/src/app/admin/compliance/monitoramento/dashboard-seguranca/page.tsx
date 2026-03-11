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
  { severity: 'Crítico', count: 8, color: '#ef4444', percentage: 0.5 },
  { severity: 'Alto', count: 52, color: '#f97316', percentage: 3.2 },
  { severity: 'Médio', count: 283, color: '#eab308', percentage: 17.7 },
  { severity: 'Baixo', count: 1268, color: '#22c55e', percentage: 78.6 },
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
      return { label: 'Crítico', color: 'bg-red-100 text-red-700', dot: 'bg-red-500' }
    case 'high':
      return { label: 'Alto', color: 'bg-orange-100 text-orange-700', dot: 'bg-orange-500' }
    case 'medium':
      return { label: 'Médio', color: 'bg-amber-100 text-amber-700', dot: 'bg-amber-500' }
    case 'low':
      return { label: 'Baixo', color: 'bg-green-100 text-green-700', dot: 'bg-green-500' }
    default:
      return { label: severity, color: 'bg-gray-100 text-gray-800 dark:text-gray-200', dot: 'bg-gray-500' }
  }
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'investigating':
      return { label: 'Investigando', color: 'bg-amber-100 text-amber-700', icon: Eye }
    case 'acknowledged':
      return { label: 'Reconhecido', color: 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-50', icon: CheckCircle2 }
    case 'resolved':
      return { label: 'Resolvido', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2 }
    case 'open':
      return { label: 'Aberto', color: 'bg-red-100 text-red-700', icon: AlertCircle }
    default:
      return { label: status, color: 'bg-gray-100 text-gray-800 dark:text-gray-200', icon: Clock }
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
            className="w-10 h-10 rounded-md flex items-center justify-center"
            style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
          >
            <MonitorDot className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold"
              style={{ 
                color: 'var(--eleven-text-primary)',
                
              }}
            >
              Dashboard de Segurança
            </h1>
            <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
              Monitoramento em tempo real • Atualizado há 2 minutos
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Total de Eventos
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {securityMetrics.totalEvents.toLocaleString('pt-BR')}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <TrendingUp className="w-3 h-3 text-emerald-500" />
                    <span className="text-xs text-emerald-600">+12% vs semana anterior</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <Activity className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Alertas Críticos Ativos
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {securityMetrics.criticalAlerts}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <TrendingDown className="w-3 h-3 text-emerald-500" />
                    <span className="text-xs text-emerald-600">-2 vs ontem</span>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)' }}>
                  <ShieldAlert className="w-5 h-5 text-red-500" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Tempo Médio de Resposta
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {securityMetrics.avgResponseTime}ms
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="text-[10px] bg-emerald-100 text-emerald-700 hover:bg-emerald-100">
                      Dentro do SLA
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                  <Clock className="w-5 h-5 text-emerald-500" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                    Score de Segurança
                  </p>
                  <p className="text-2xl font-semibold mt-1" style={{ color: 'var(--eleven-text-primary)' }}>
                    {securityMetrics.securityScore}/100
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="text-[10px] bg-emerald-100 text-emerald-700 hover:bg-emerald-100">
                      Excelente
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <Gauge className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
              </div>
              <div className="mt-3">
                <Progress value={securityMetrics.securityScore} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', borderColor: 'rgba(96, 190, 209, 0.3)' }}>
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div 
                  className="w-10 h-10 rounded-md flex items-center justify-center"
                  style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
                >
                  <KeyRound className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div>
                  <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
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
              <div className="flex items-center gap-3 p-3 rounded-md border" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>SSO</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Ativo</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-md border" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>SCIM</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Ativo</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-md border" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>MFA</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Habilitado</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-md border" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                <Users className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>Sessões</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Gerenciadas via WorkOS</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <Card className="lg:col-span-2" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                <BarChart3 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                Eventos por Dia (Últimos 7 dias)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-end justify-between h-40 gap-3">
                {eventsByDay.map((item, idx) => (
                  <div key={idx} className="flex flex-col items-center flex-1">
                    <div className="w-full flex flex-col-reverse rounded-t overflow-hidden" style={{ height: `${(item.count / maxDayCount) * 100}%`, minHeight: '20px' }}>
                      <div style={{ height: `${(item.low / item.count) * 100}%`, backgroundColor: '#22c55e' }} />
                      <div style={{ height: `${(item.medium / item.count) * 100}%`, backgroundColor: '#eab308' }} />
                      <div style={{ height: `${(item.high / item.count) * 100}%`, backgroundColor: '#f97316' }} />
                      <div style={{ height: `${(item.critical / item.count) * 100}%`, backgroundColor: '#ef4444' }} />
                    </div>
                    <span className="text-xs font-medium mt-2" style={{ color: 'var(--eleven-text-primary)' }}>
                      {item.count}
                    </span>
                    <span className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      {item.day}
                    </span>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-center gap-6 mt-4 pt-3 border-t" style={{ borderColor: 'var(--eleven-border-subtle)' }}>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: '#ef4444' }} />
                  <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Crítico</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: '#f97316' }} />
                  <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Alto</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: '#eab308' }} />
                  <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Médio</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: '#22c55e' }} />
                  <span className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Baixo</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                <Shield className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                Distribuição por Severidade
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {severityDistribution.map((item, idx) => (
                  <div key={idx}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded" style={{ backgroundColor: item.color }} />
                        <span className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                          {item.severity}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          {item.count}
                        </span>
                        <span className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                          {item.percentage}%
                        </span>
                      </div>
                    </div>
                    <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                      <div 
                        className="h-full rounded-full transition-all"
                        style={{ width: `${item.percentage}%`, backgroundColor: item.color }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div 
                className="mt-4 p-3 rounded-md"
                style={{ backgroundColor: 'rgba(229, 231, 235, 0.2)' }}
              >
                <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                  Total: {totalSeverityCount.toLocaleString('pt-BR')} eventos nos últimos 7 dias
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                <AlertTriangle className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                Top 5 Tipos de Eventos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {topEventTypes.map((event, idx) => (
                  <div 
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-md border hover:bg-gray-50 transition-colors"
                    style={{ borderColor: 'var(--eleven-border-subtle)' }}
                  >
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium"
                        style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
                      >
                        {idx + 1}
                      </div>
                      <span className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                        {event.type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                        {event.count}
                      </span>
                      <div className={`flex items-center gap-1 ${event.trend > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
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

          <Card className="lg:col-span-2" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-medium flex items-center gap-2" style={{ color: 'var(--eleven-text-primary)' }}>
                  <Activity className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  Eventos Recentes
                </CardTitle>
                <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
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
                          <span className="text-xs font-mono" style={{ color: 'var(--eleven-text-secondary)' }}>
                            {new Date(event.timestamp).toLocaleString('pt-BR', {
                              day: '2-digit',
                              month: '2-digit',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                            {event.type}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge className={severityConfig.color}>
                            {severityConfig.label}
                          </Badge>
                        </TableCell>
                        <TableCell className="hidden md:table-cell max-w-[200px]">
                          <span className="text-xs truncate block" style={{ color: 'var(--eleven-text-tertiary)' }}>
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
