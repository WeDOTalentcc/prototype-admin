"use client"

import React, { useState } from "react"
import { 
  AlertCircle, 
  Search,
  Filter,
  CheckCircle2,
  Clock,
  XCircle,
  Eye,
  ArrowRight,
  FileText,
  Shield,
  Trash2,
  RefreshCw,
  BookOpen,
  MoreHorizontal,
  Plus,
  X,
  Target,
  Layers
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
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
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface Incident {
  id: string
  title: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  status: 'open' | 'investigating' | 'mitigating' | 'resolved' | 'closed'
  startedAt: string
  resolvedAt: string | null
  assignee: string
  currentPhase: number
  affectedServices: string[]
}

const incidents: Incident[] = [
  { 
    id: 'INC-001', 
    title: 'Tentativa de acesso não autorizado', 
    severity: 'high', 
    status: 'investigating', 
    startedAt: '2024-12-18T10:30:00', 
    resolvedAt: null, 
    assignee: 'Equipe SOC',
    currentPhase: 2,
    affectedServices: ['Autenticação', 'API Backend']
  },
  { 
    id: 'INC-002', 
    title: 'Latência elevada na API', 
    severity: 'medium', 
    status: 'resolved', 
    startedAt: '2024-12-17T14:00:00', 
    resolvedAt: '2024-12-17T15:30:00', 
    assignee: 'Infra',
    currentPhase: 6,
    affectedServices: ['API Backend', 'Banco de Dados']
  },
  { 
    id: 'INC-003', 
    title: 'Pico de requisições detectado', 
    severity: 'low', 
    status: 'resolved', 
    startedAt: '2024-12-16T08:15:00', 
    resolvedAt: '2024-12-16T08:45:00', 
    assignee: 'Infra',
    currentPhase: 6,
    affectedServices: ['API Backend']
  },
  { 
    id: 'INC-004', 
    title: 'Falha temporária no serviço de e-mail', 
    severity: 'medium', 
    status: 'closed', 
    startedAt: '2024-12-15T16:00:00', 
    resolvedAt: '2024-12-15T17:30:00', 
    assignee: 'Equipe SOC',
    currentPhase: 6,
    affectedServices: ['Serviço de E-mail', 'Notificações']
  },
]

const responseWorkflow = [
  { phase: 1, name: 'Detecção', icon: Eye, description: 'Identificar e registrar' },
  { phase: 2, name: 'Classificação', icon: Layers, description: 'Avaliar severidade' },
  { phase: 3, name: 'Contenção', icon: Shield, description: 'Limitar impacto' },
  { phase: 4, name: 'Erradicação', icon: Trash2, description: 'Eliminar causa raiz' },
  { phase: 5, name: 'Recuperação', icon: RefreshCw, description: 'Restaurar operações' },
  { phase: 6, name: 'Lições Aprendidas', icon: BookOpen, description: 'Documentar e melhorar' },
]

const slaNotifications = [
  { severity: 'critical', sla: '1h', description: 'Notificação imediata ao DPO, CISO e equipe de resposta' },
  { severity: 'high', sla: '4h', description: 'Notificação à equipe de segurança e stakeholders' },
  { severity: 'medium', sla: '24h', description: 'Registro e notificação à equipe responsável' },
  { severity: 'low', sla: '48h', description: 'Registro e análise programada' },
]

const lgpdNotifications = [
  { type: '24h', description: 'Notificação interna ao DPO e equipe de segurança', mandatory: true },
  { type: '48h', description: 'Comunicação à ANPD (em caso de vazamento de dados)', mandatory: true },
  { type: '72h', description: 'Notificação aos titulares afetados (se aplicável)', mandatory: true },
]

const availableServices = [
  'Plataforma LIA',
  'API Backend',
  'Banco de Dados',
  'Autenticação',
  'Serviço de E-mail',
  'Notificações',
  'Integração Gupy',
  'Integração LinkedIn',
  'Cache Redis',
]

const getSeverityConfig = (severity: string) => {
  switch (severity) {
    case 'critical':
      return { label: 'Crítico', color: 'bg-status-error/15 text-status-error border-status-error/30', dot: 'bg-status-error' }
    case 'high':
      return { label: 'Alto', color: 'bg-wedo-orange/15 text-wedo-orange border-wedo-orange/30', dot: 'bg-wedo-orange' }
    case 'medium':
      return { label: 'Médio', color: 'bg-status-warning/15 text-status-warning border-status-warning/30', dot: 'bg-status-warning' }
    case 'low':
      return { label: 'Baixo', color: 'bg-status-success/15 text-status-success border-status-success/30', dot: 'bg-status-success' }
    default:
      return { label: severity, color: 'bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary border-lia-border-subtle', dot: 'bg-lia-bg-secondary0' }
  }
}

const getStatusConfig = (status: string) => {
  switch (status) {
    case 'open':
      return { label: 'Aberto', color: 'bg-status-error/15 text-status-error', icon: AlertCircle }
    case 'investigating':
      return { label: 'Investigando', color: 'bg-status-warning/15 text-status-warning', icon: Clock }
    case 'mitigating':
      return { label: 'Mitigando', color: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary', icon: Shield }
    case 'resolved':
      return { label: 'Resolvido', color: 'bg-status-success/15 text-status-success', icon: CheckCircle2 }
    case 'closed':
      return { label: 'Fechado', color: 'bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary', icon: XCircle }
    default:
      return { label: status, color: 'bg-lia-bg-tertiary text-lia-text-primary dark:text-lia-text-primary', icon: Clock }
  }
}

export default function IncidentesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [newIncident, setNewIncident] = useState({
    title: '',
    severity: '',
    assignee: '',
    description: '',
    affectedServices: [] as string[]
  })

  const filteredIncidents = incidents.filter(incident =>
    incident.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    incident.id.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const openIncidents = incidents.filter(i => ['open', 'investigating', 'mitigating'].includes(i.status)).length
  const resolvedIncidents = incidents.filter(i => ['resolved', 'closed'].includes(i.status)).length
  const criticalIncidents = incidents.filter(i => i.severity === 'critical' || i.severity === 'high').length

  const handleSubmitIncident = () => {
    setIsDialogOpen(false)
    setNewIncident({ title: '', severity: '', assignee: '', description: '', affectedServices: [] })
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
            >
              <AlertCircle className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
                
              >
                Gestão de Incidentes (PRI)
              </h1>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                Plano de Resposta a Incidentes e registro de ocorrências
              </p>
            </div>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active">
                <Plus className="w-4 h-4 mr-2" />
                Registrar Incidente
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-panel-xl">
              <DialogHeader>
                <DialogTitle className="text-lia-text-primary dark:text-lia-text-primary" >Registrar Novo Incidente</DialogTitle>
                <DialogDescription>
                  Preencha as informações do incidente para iniciar o processo de resposta.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="title">Título do Incidente</Label>
                  <Input
                    id="title"
                    placeholder="Ex: Falha no serviço de autenticação"
                    value={newIncident.title}
                    onChange={(e) => setNewIncident({ ...newIncident, title: e.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="grid gap-2">
                    <Label htmlFor="severity">Severidade</Label>
                    <Select
                      value={newIncident.severity}
                      onValueChange={(value) => setNewIncident({ ...newIncident, severity: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="critical">Crítico</SelectItem>
                        <SelectItem value="high">Alto</SelectItem>
                        <SelectItem value="medium">Médio</SelectItem>
                        <SelectItem value="low">Baixo</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="assignee">Responsável</Label>
                    <Select
                      value={newIncident.assignee}
                      onValueChange={(value) => setNewIncident({ ...newIncident, assignee: value })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecione" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="Equipe SOC">Equipe SOC</SelectItem>
                        <SelectItem value="Infra">Infra</SelectItem>
                        <SelectItem value="Desenvolvimento">Desenvolvimento</SelectItem>
                        <SelectItem value="Segurança">Segurança</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label>Serviços Afetados</Label>
                  <div className="flex flex-wrap gap-2">
                    {availableServices.map((service) => (
                      <Badge
                        key={service}
                        variant="outline"
                        className={`cursor-pointer transition-colors motion-reduce:transition-none ${
                          newIncident.affectedServices.includes(service)
                            ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary border-lia-btn-primary-bg dark:border-lia-border-subtle'
                            : 'hover:bg-lia-bg-tertiary'
                        }`}
                        onClick={() => {
                          setNewIncident(prev => ({
                            ...prev,
                            affectedServices: prev.affectedServices.includes(service)
                              ? prev.affectedServices.filter(s => s !== service)
                              : [...prev.affectedServices, service]
                          }))
                        }}
                      >
                        {service}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="description">Descrição</Label>
                  <Textarea
                    id="description"
                    placeholder="Descreva o incidente em detalhes..."
                    value={newIncident.description}
                    onChange={(e) => setNewIncident({ ...newIncident, description: e.target.value })}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancelar
                </Button>
                <Button 
                  className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active"
                  onClick={handleSubmitIncident}
                >
                  Registrar Incidente
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        <div 
          className="rounded-md border p-4 mb-6 flex items-center gap-3 bg-status-error-bg border-status-error-border"
        >
          <AlertCircle className="w-5 h-5 text-status-error" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="font-medium text-sm text-status-error">Gap Identificado: Plano de Resposta a Incidentes</p>
              <Badge className="text-micro bg-status-error/15 text-status-error">Crítico</Badge>
            </div>
            <p className="text-xs text-status-error">
              É necessário documentar e formalizar o PRI com procedimentos detalhados para cada tipo de incidente, conforme requisitos do BCB 498 e ISO 27001.
            </p>
          </div>
          <Badge className="bg-status-warning/15 text-status-warning">Em estruturação</Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Incidentes Abertos
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {openIncidents}
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
                    Alta Severidade
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {criticalIncidents}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className={`text-micro ${criticalIncidents === 0 ? 'bg-status-success/15 text-status-success' : 'bg-wedo-orange/15 text-wedo-orange'} hover:bg-status-success/15`}>
                      {criticalIncidents === 0 ? 'Sem críticos' : `${criticalIncidents} ativo(s)`}
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{backgroundColor: criticalIncidents === 0 ? 'var(--status-success-bg)' : 'var(--status-error-bg)'}}>
                  <Shield className={`w-5 h-5 ${criticalIncidents === 0 ? 'text-status-success' : 'text-status-error'}`} />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card >
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Resolvidos (30 dias)
                  </p>
                  <p className="text-2xl font-semibold mt-1 text-lia-text-primary dark:text-lia-text-primary" >
                    {resolvedIncidents}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className="text-micro bg-status-success/15 text-status-success hover:bg-status-success/15">
                      100% dentro do SLA
                    </Badge>
                  </div>
                </div>
                <div className="w-10 h-10 rounded-md flex items-center justify-center bg-green-500/10">
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6" >
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
              Workflow de Resposta a Incidentes (PRI)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between overflow-x-auto">
              {responseWorkflow.map((step, idx) => {
                const Icon = step.icon
                return (
                  <React.Fragment key={step.phase}>
                    <div className="flex flex-col items-center text-center flex-1 min-w-[100px]">
                      <div 
                        className="w-12 h-12 rounded-full flex items-center justify-center mb-2 bg-lia-interactive-active/30"
                      >
                        <Icon className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                      </div>
                      <Badge variant="outline" className="mb-1 text-xs">
                        {step.phase}
                      </Badge>
                      <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                        {step.name}
                      </span>
                      <span className="text-xs mt-1 text-lia-text-tertiary dark:text-lia-text-secondary" >
                        {step.description}
                      </span>
                    </div>
                    {idx < responseWorkflow.length - 1 && (
                      <ArrowRight className="w-5 h-5 flex-shrink-0 mx-2 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                    )}
                  </React.Fragment>
                )
              })}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2">
            <Card >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                    Histórico de Incidentes
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <div className="relative w-64">
                      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                      <Input
                        placeholder="Buscar incidentes..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-9"
                      />
                    </div>
                    <Button variant="outline" size="icon">
                      <Filter className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-20">ID</TableHead>
                      <TableHead>Título</TableHead>
                      <TableHead>Severidade</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Serviços Afetados</TableHead>
                      <TableHead>Responsável</TableHead>
                      <TableHead>Iniciado em</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredIncidents.map((incident) => {
                      const severityConfig = getSeverityConfig(incident.severity)
                      const statusConfig = getStatusConfig(incident.status)
                      const StatusIcon = statusConfig.icon
                      return (
                        <TableRow key={incident.id} className="hover:bg-lia-bg-secondary">
                          <TableCell>
                            <Badge variant="outline" className="font-mono text-xs">
                              {incident.id}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                              {incident.title}
                            </span>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className={`w-2 h-2 rounded-full ${severityConfig.dot}`} />
                              <span className="text-sm">{severityConfig.label}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge className={`${statusConfig.color} flex items-center gap-1 w-fit`}>
                              <StatusIcon className="w-3 h-3" />
                              {statusConfig.label}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1 max-w-[150px]">
                              {incident.affectedServices.slice(0, 2).map((service, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  {service}
                                </Badge>
                              ))}
                              {incident.affectedServices.length > 2 && (
                                <Badge variant="outline" className="text-xs">
                                  +{incident.affectedServices.length - 2}
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                              {incident.assignee}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                              {new Date(incident.startedAt).toLocaleString('pt-BR')}
                            </span>
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
                                <DropdownMenuItem>
                                  <FileText className="w-4 h-4 mr-2" />
                                  Relatório
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>

          <Card >
            <CardHeader className="pb-3">
              <CardTitle className="text-base font-medium text-lia-text-primary dark:text-lia-text-primary" >
                SLAs por Severidade
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {slaNotifications.map((sla, idx) => {
                  const severityConfig = getSeverityConfig(sla.severity)
                  return (
                    <div 
                      key={idx}
                      className="p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle"
                      
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${severityConfig.dot}`} />
                          <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                            {severityConfig.label}
                          </span>
                        </div>
                        <Badge className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary font-mono">
                          {sla.sla}
                        </Badge>
                      </div>
                      <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                        {sla.description}
                      </p>
                    </div>
                  )
                })}
              </div>
              <div 
                className="mt-4 p-3 rounded-md bg-lia-interactive-active/20"
              >
                <p className="text-xs text-lia-text-tertiary dark:text-lia-text-secondary" >
                  Os prazos são contados a partir da data de conhecimento do incidente pela organização, conforme Art. 48 da LGPD.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
