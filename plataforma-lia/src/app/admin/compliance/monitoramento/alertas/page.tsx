"use client"

import React, { useState } from "react"
import { 
  Bell, 
  Shield,
  Activity,
  Settings,
  Globe,
  CheckCircle2,
  Mail,
  MessageSquare,
  Smartphone,
  Filter,
  Eye,
  MoreHorizontal,
  Clock,
  Zap,
  AlertTriangle,
  FileText
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Tabs,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type AlertType = 'security' | 'performance' | 'compliance' | 'integration'
type AlertStatus = 'new' | 'acknowledged' | 'resolved'
type AlertSeverity = 'critical' | 'high' | 'medium' | 'low'

interface Alert {
  id: number
  type: AlertType
  title: string
  message: string
  severity: AlertSeverity
  createdAt: string
  status: AlertStatus
}

const alerts: Alert[] = [
  { 
    id: 1, 
    type: 'security', 
    title: 'Múltiplas tentativas de login falhas', 
    message: 'Detectadas 15 tentativas de login falhas do IP 192.168.1.100 nos últimos 5 minutos.', 
    severity: 'high', 
    createdAt: '2024-12-20T09:45:00', 
    status: 'new' 
  },
  { 
    id: 2, 
    type: 'performance', 
    title: 'Latência elevada na API', 
    message: 'O tempo de resposta da API está acima de 500ms (média atual: 650ms).', 
    severity: 'medium', 
    createdAt: '2024-12-20T09:30:00', 
    status: 'acknowledged' 
  },
  { 
    id: 3, 
    type: 'compliance', 
    title: 'Certificado SSL expira em 30 dias', 
    message: 'O certificado SSL do domínio principal expira em 30 dias. Renovação necessária.', 
    severity: 'medium', 
    createdAt: '2024-12-20T08:00:00', 
    status: 'new' 
  },
  { 
    id: 4, 
    type: 'integration', 
    title: 'Falha na sincronização com Gupy', 
    message: 'A última sincronização com a Gupy falhou. Erro: timeout após 30 segundos.', 
    severity: 'high', 
    createdAt: '2024-12-20T07:45:00', 
    status: 'resolved' 
  },
  { 
    id: 5, 
    type: 'security', 
    title: 'Novo dispositivo detectado', 
    message: 'Login realizado de um novo dispositivo para o usuário admin@empresa.com.', 
    severity: 'low', 
    createdAt: '2024-12-20T07:30:00', 
    status: 'acknowledged' 
  },
  { 
    id: 6, 
    type: 'performance', 
    title: 'Uso de CPU acima de 80%', 
    message: 'O servidor principal está com uso de CPU em 85% nos últimos 10 minutos.', 
    severity: 'high', 
    createdAt: '2024-12-20T07:00:00', 
    status: 'resolved' 
  },
  { 
    id: 7, 
    type: 'compliance', 
    title: 'Política de senha não atualizada', 
    message: '3 usuários não atualizaram a senha nos últimos 90 dias conforme política.', 
    severity: 'medium', 
    createdAt: '2024-12-19T18:00:00', 
    status: 'new' 
  },
  { 
    id: 8, 
    type: 'integration', 
    title: 'LinkedIn API rate limit atingido', 
    message: 'O limite de requisições da API do LinkedIn foi atingido. Aguardando reset.', 
    severity: 'medium', 
    createdAt: '2024-12-19T16:30:00', 
    status: 'resolved' 
  },
  { 
    id: 9, 
    type: 'security', 
    title: 'Token de API expirando', 
    message: 'O token de API do serviço de e-mail expira em 7 dias. Renovação recomendada.', 
    severity: 'low', 
    createdAt: '2024-12-19T14:00:00', 
    status: 'acknowledged' 
  },
  { 
    id: 10, 
    type: 'performance', 
    title: 'Banco de dados com conexões elevadas', 
    message: 'O número de conexões ativas no banco de dados está em 85% da capacidade.', 
    severity: 'medium', 
    createdAt: '2024-12-19T12:00:00', 
    status: 'new' 
  },
]

const notificationChannels = [
  { id: 'email', name: 'E-mail', icon: Mail, enabled: true, description: 'Notificações por e-mail' },
  { id: 'slack', name: 'Slack', icon: MessageSquare, enabled: true, description: 'Mensagens no canal de compliance' },
  { id: 'sms', name: 'SMS', icon: Smartphone, enabled: false, description: 'Alertas urgentes por SMS' },
]

const getTypeConfig = (type: AlertType) => {
  switch (type) {
    case 'security':
      return { label: 'Segurança', icon: Shield, color: 'bg-status-error/15 text-status-error', iconBg: 'var(--status-error-bg)', iconColor: 'text-status-error' }
    case 'performance':
 return { label: 'Performance', icon: Activity, color: 'bg-gray-100 dark:bg-lia-bg-secondary lia-text-600', iconBg: 'var(--gray-bg-30)', iconColor: 'dark:text-lia-text-tertiary' }
    case 'compliance':
      return { label: 'Compliance', icon: FileText, color: 'bg-wedo-purple/15 text-wedo-purple', iconBg: 'var(--wedo-purple-bg-10)', iconColor: 'text-wedo-purple' }
    case 'integration':
      return { label: 'Integração', icon: Globe, color: 'bg-status-warning/15 text-status-warning', iconBg: 'var(--status-warning-bg)', iconColor: 'text-status-warning' }
  }
}

const getSeverityConfig = (severity: AlertSeverity) => {
  switch (severity) {
    case 'critical':
      return { label: 'Crítico', color: 'bg-status-error/15 text-status-error', dot: 'bg-status-error' }
    case 'high':
      return { label: 'Alto', color: 'bg-wedo-orange/15 text-wedo-orange', dot: 'bg-wedo-orange' }
    case 'medium':
      return { label: 'Médio', color: 'bg-status-warning/15 text-status-warning', dot: 'bg-status-warning' }
    case 'low':
      return { label: 'Baixo', color: 'bg-status-success/15 text-status-success', dot: 'bg-status-success' }
  }
}

const getStatusConfig = (status: AlertStatus) => {
  switch (status) {
    case 'new':
      return { label: 'Novo', color: 'bg-gray-100 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary', icon: Bell }
    case 'acknowledged':
      return { label: 'Reconhecido', color: 'bg-status-warning/15 text-status-warning', icon: Eye }
    case 'resolved':
      return { label: 'Resolvido', color: 'bg-status-success/15 text-status-success', icon: CheckCircle2 }
  }
}

export default function AlertasPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')
  const [severityFilter, setSeverityFilter] = useState<string>('all')
  const [channels, setChannels] = useState(notificationChannels)

  const newAlerts = alerts.filter(a => a.status === 'new').length
  const highSeverityAlerts = alerts.filter(a => a.severity === 'high' || a.severity === 'critical').length

  const filteredAlerts = alerts.filter(alert => {
    if (statusFilter !== 'all' && alert.status !== statusFilter) return false
    if (typeFilter !== 'all' && alert.type !== typeFilter) return false
    if (severityFilter !== 'all' && alert.severity !== severityFilter) return false
    return true
  })

  const toggleChannel = (channelId: string) => {
    setChannels(prev => prev.map(ch => 
      ch.id === channelId ? { ...ch, enabled: !ch.enabled } : ch
    ))
  }

  const alertsByType = {
    security: alerts.filter(a => a.type === 'security').length,
    performance: alerts.filter(a => a.type === 'performance').length,
    compliance: alerts.filter(a => a.type === 'compliance').length,
    integration: alerts.filter(a => a.type === 'integration').length,
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
          >
            <Bell className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary"
              
            >
              Alertas Proativos
            </h1>
            <p className="text-sm lia-text-400 dark:lia-text-500" >
              Monitoramento e gestão de alertas do sistema
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm lia-text-400 dark:lia-text-500" >
                    Total de Alertas
                  </p>
                  <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary" >
                    {alerts.length}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30">
                  <Bell className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm lia-text-400 dark:lia-text-500" >
                    Novos
                  </p>
                  <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary" >
                    {newAlerts}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30">
                  <AlertTriangle className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm lia-text-400 dark:lia-text-500" >
                    Alta Severidade
                  </p>
                  <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary" >
                    {highSeverityAlerts}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-red-500/10">
                  <Zap className="w-5 h-5 text-status-error" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm lia-text-400 dark:lia-text-500" >
                    Canais Ativos
                  </p>
                  <p className="text-2xl font-semibold mt-1 lia-text-800 dark:text-lia-text-primary" >
                    {channels.filter(c => c.enabled).length}/{channels.length}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <Settings className="w-5 h-5 text-status-success" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary" >
                    Lista de Alertas
                  </CardTitle>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Select value={typeFilter} onValueChange={setTypeFilter}>
                      <SelectTrigger className="w-[140px]">
                        <SelectValue placeholder="Tipo" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todos os tipos</SelectItem>
                        <SelectItem value="security">Segurança</SelectItem>
                        <SelectItem value="performance">Performance</SelectItem>
                        <SelectItem value="compliance">Compliance</SelectItem>
                        <SelectItem value="integration">Integração</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={severityFilter} onValueChange={setSeverityFilter}>
                      <SelectTrigger className="w-[140px]">
                        <SelectValue placeholder="Severidade" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">Todas</SelectItem>
                        <SelectItem value="critical">Crítico</SelectItem>
                        <SelectItem value="high">Alto</SelectItem>
                        <SelectItem value="medium">Médio</SelectItem>
                        <SelectItem value="low">Baixo</SelectItem>
                      </SelectContent>
                    </Select>
                    <Tabs value={statusFilter} onValueChange={setStatusFilter}>
                      <TabsList>
                        <TabsTrigger value="all">Todos</TabsTrigger>
                        <TabsTrigger value="new">Novos</TabsTrigger>
                        <TabsTrigger value="acknowledged">Reconhecidos</TabsTrigger>
                        <TabsTrigger value="resolved">Resolvidos</TabsTrigger>
                      </TabsList>
                    </Tabs>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Tipo</TableHead>
                      <TableHead>Mensagem</TableHead>
                      <TableHead>Severidade</TableHead>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredAlerts.map((alert) => {
                      const typeConfig = getTypeConfig(alert.type)
                      const severityConfig = getSeverityConfig(alert.severity)
                      const statusConfig = getStatusConfig(alert.status)
                      const TypeIcon = typeConfig.icon
                      const StatusIcon = statusConfig.icon
                      return (
                        <TableRow key={alert.id} className="hover:bg-gray-50">
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-8 h-8 rounded-md flex items-center justify-center"
                                style={{backgroundColor: typeConfig.iconBg}}
                              >
                                <TypeIcon className={`w-4 h-4 ${typeConfig.iconColor}`} />
                              </div>
                              <Badge className={typeConfig.color}>
                                {typeConfig.label}
                              </Badge>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="max-w-[250px]">
                              <span className="font-medium text-sm lia-text-800 dark:text-lia-text-primary" >
                                {alert.title}
                              </span>
                              <p className="text-xs truncate lia-text-400 dark:lia-text-500" >
                                {alert.message}
                              </p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className={`w-2 h-2 rounded-full ${severityConfig.dot}`} />
                              <span className="text-sm">{severityConfig.label}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm lia-text-500 dark:text-lia-text-tertiary" >
                              {new Date(alert.createdAt).toLocaleString('pt-BR')}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge className={`${statusConfig.color} flex items-center gap-1 w-fit`}>
                              <StatusIcon className="w-3 h-3" />
                              {statusConfig.label}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <MoreHorizontal className="w-4 h-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem>
                                  <Eye className="w-4 h-4 mr-2" />
                                  Ver detalhes
                                </DropdownMenuItem>
                                {alert.status === 'new' && (
                                  <DropdownMenuItem>
                                    <CheckCircle2 className="w-4 h-4 mr-2" />
                                    Reconhecer
                                  </DropdownMenuItem>
                                )}
                                {alert.status !== 'resolved' && (
                                  <DropdownMenuItem>
                                    <CheckCircle2 className="w-4 h-4 mr-2" />
                                    Resolver
                                  </DropdownMenuItem>
                                )}
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
                {filteredAlerts.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-sm lia-text-400 dark:lia-text-500" >
                      Nenhum alerta encontrado com os filtros selecionados.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card >
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2 lia-text-800 dark:text-lia-text-primary" >
                  <Settings className="w-4 h-4 lia-text-600 dark:text-lia-text-tertiary" />
                  Canais de Notificação
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {channels.map((channel) => {
                    const Icon = channel.icon
                    return (
                      <div 
                        key={channel.id}
                        className="flex items-center justify-between p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle"
                        
                      >
                        <div className="flex items-center gap-3">
                          <div 
                            className="w-8 h-8 rounded-md flex items-center justify-center"
                            style={{backgroundColor: channel.enabled ? 'var(--status-success-bg)' : 'var(--gray-bg-10)'}}
                          >
                            <Icon className={`w-4 h-4 ${channel.enabled ? 'text-status-success' : 'lia-text-400'}`} />
                          </div>
                          <div>
                            <span className="font-medium text-sm lia-text-800 dark:text-lia-text-primary" >
                              {channel.name}
                            </span>
                            <p className="text-xs lia-text-400 dark:lia-text-500" >
                              {channel.description}
                            </p>
                          </div>
                        </div>
                        <Switch 
                          checked={channel.enabled}
                          onCheckedChange={() => toggleChannel(channel.id)}
                        />
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>

            <Card >
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium lia-text-800 dark:text-lia-text-primary" >
                  Alertas por Tipo
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(['security', 'performance', 'compliance', 'integration'] as AlertType[]).map((type) => {
                    const typeConfig = getTypeConfig(type)
                    const TypeIcon = typeConfig.icon
                    const count = alertsByType[type]
                    return (
                      <div 
                        key={type}
                        className={`flex items-center justify-between p-2 rounded-md hover:bg-gray-50 transition-colors cursor-pointer ${typeFilter === type ? 'bg-gray-50 dark:bg-lia-bg-primary' : ''}`}
                        onClick={() => setTypeFilter(type)}
                      >
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-6 h-6 rounded-md flex items-center justify-center"
                            style={{backgroundColor: typeConfig.iconBg}}
                          >
                            <TypeIcon className={`w-3 h-3 ${typeConfig.iconColor}`} />
                          </div>
                          <span className="text-sm lia-text-500 dark:text-lia-text-tertiary" >
                            {typeConfig.label}
                          </span>
                        </div>
                        <Badge variant="outline">{count}</Badge>
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
