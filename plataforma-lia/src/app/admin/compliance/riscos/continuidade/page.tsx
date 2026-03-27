"use client"

import React from "react"
import { 
  RefreshCw, 
  Clock, 
  Database, 
  Server, 
  CheckCircle2, 
  AlertTriangle,
  Calendar,
  Play,
  FileText,
  Shield,
  AlertCircle,
  HardDrive,
  Mail,
  Info
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

const systems = [
  { 
    name: 'API Principal', 
    rto: '4 horas', 
    rpo: '1 hora', 
    lastBackup: '2025-01-15 03:00', 
    lastTest: '2024-11-15', 
    status: 'ok',
    icon: Server
  },
  { 
    name: 'Banco de Dados', 
    rto: '2 horas', 
    rpo: '15 minutos', 
    lastBackup: '2025-01-15 04:00', 
    lastTest: '2024-11-15', 
    status: 'ok',
    icon: Database
  },
  { 
    name: 'Serviço de Email', 
    rto: '8 horas', 
    rpo: '4 horas', 
    lastBackup: '2025-01-14', 
    lastTest: 'N/A', 
    status: 'pending',
    icon: Mail
  },
]

const drTests = [
  { id: 1, date: '2024-12-15', type: 'Simulação completa', result: 'Sucesso', rtoAchieved: '3h 45min', rpoAchieved: '45min', notes: 'Todos os sistemas recuperados dentro do prazo estabelecido' },
  { id: 2, date: '2024-09-20', type: 'Teste parcial - Banco de dados', result: 'Sucesso', rtoAchieved: '45min', rpoAchieved: '12min', notes: 'Failover automático para réplica funcionou corretamente' },
  { id: 3, date: '2024-06-15', type: 'Simulação completa', result: 'Parcial', rtoAchieved: '5h', rpoAchieved: '1h 30min', notes: 'Sistema de email excedeu RTO em 1 hora - ação corretiva aplicada' },
]

const continuityPlans = [
  { id: 1, name: 'PCN - Plano de Continuidade de Negócios', version: '2.1', lastUpdate: '2024-11-01', status: 'approved', owner: 'TI' },
  { id: 2, name: 'PRD - Plano de Recuperação de Desastres', version: '1.5', lastUpdate: '2024-10-15', status: 'approved', owner: 'Infra' },
  { id: 3, name: 'Plano de Comunicação de Crise', version: '1.3', lastUpdate: '2024-12-01', status: 'approved', owner: 'Marketing' },
  { id: 4, name: 'Runbook de Incidentes Críticos', version: '3.0', lastUpdate: '2024-11-20', status: 'approved', owner: 'SRE' },
]

const objectives = {
  rtoTarget: '4 horas',
  rpoTarget: '1 hora',
  lastTest: '2024-12-15',
  nextTest: '2025-03-15'
}

const getResultBadge = (result: string) => {
  switch (result) {
    case 'Sucesso':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        Sucesso
      </Badge>
    case 'Parcial':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
        <AlertTriangle className="w-3 h-3 mr-1" />
        Parcial
      </Badge>
    case 'Falha':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">
        <AlertCircle className="w-3 h-3 mr-1" />
        Falha
      </Badge>
    default:
      return <Badge variant="secondary">{result}</Badge>
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'approved':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">Aprovado</Badge>
    case 'review':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">Em Revisão</Badge>
    case 'draft':
      return <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200 hover:bg-gray-100">Rascunho</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

const getSystemStatusBadge = (status: string) => {
  switch (status) {
    case 'ok':
      return <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
        <CheckCircle2 className="w-3 h-3 mr-1" />
        OK
      </Badge>
    case 'pending':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
        <Clock className="w-3 h-3 mr-1" />
        Pendente
      </Badge>
    case 'attention':
      return <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15">
        <AlertTriangle className="w-3 h-3 mr-1" />
        Atenção
      </Badge>
    case 'critical':
      return <Badge className="bg-status-error/15 text-status-error hover:bg-status-error/15">
        <AlertCircle className="w-3 h-3 mr-1" />
        Crítico
      </Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

export default function ContinuidadePage() {
  const nextTestDate = new Date(objectives.nextTest)
  const today = new Date()
  const daysUntilTest = Math.ceil((nextTestDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  
  const totalTests = drTests.length
  const passedTests = drTests.filter(t => t.result === 'Sucesso').length
  const systemsOk = systems.filter(s => s.status === 'ok').length

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center"
              style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}
            >
              <RefreshCw className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold"
                style={{ 
                  color: 'var(--eleven-text-primary)',
                  
                }}
              >
                Continuidade de Negócios
              </h1>
              <p className="text-sm" style={{ color: 'var(--eleven-text-tertiary)' }}>
                PCN/PRD, RTO/RPO e planos de recuperação
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline">
              <FileText className="w-4 h-4 mr-2" />
              Baixar PCN
            </Button>
            <Button>
              <Play className="w-4 h-4 mr-2" />
              Iniciar Teste DR
            </Button>
          </div>
        </div>

        <Card className="mb-6" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', borderLeft: '4px solid #ef4444' }}>
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-status-error mt-0.5" />
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-medium text-sm text-status-error">
                    Gap de Compliance - BCB 498/2025
                  </p>
                  <Badge className="bg-status-warning/15 text-status-warning hover:bg-status-warning/15 text-micro">
                    Em implementação
                  </Badge>
                </div>
                <p className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                  A Resolução BCB 498/2025 exige plano de continuidade de negócios com definição clara de RTO/RPO 
                  e testes periódicos de recuperação de desastres. Mantenha os planos atualizados e realize 
                  testes de DR trimestralmente.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Card className="border-l-4 border-l-gray-300" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                  <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{objectives.rtoTarget}</p>
                    <Badge variant="outline" className="text-xs">RTO</Badge>
                  </div>
                  <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>Recovery Time Objective</p>
                  <p className="text-xs mt-2 p-2 rounded" style={{ backgroundColor: 'var(--eleven-bg-subtle)', color: 'var(--eleven-text-secondary)' }}>
                    <Info className="w-3 h-3 inline mr-1" />
                    Tempo máximo aceitável de indisponibilidade do sistema
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)', borderLeft: '4px solid #10b981' }}>
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                  <Database className="w-5 h-5 text-status-success" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{objectives.rpoTarget}</p>
                    <Badge variant="outline" className="text-xs">RPO</Badge>
                  </div>
                  <p className="text-xs mt-1" style={{ color: 'var(--eleven-text-tertiary)' }}>Recovery Point Objective</p>
                  <p className="text-xs mt-2 p-2 rounded" style={{ backgroundColor: 'var(--eleven-bg-subtle)', color: 'var(--eleven-text-secondary)' }}>
                    <Info className="w-3 h-3 inline mr-1" />
                    Perda máxima de dados aceitável em caso de falha
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)' }}>
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>
                    {new Date(objectives.lastTest).toLocaleDateString('pt-BR')}
                  </p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Último Teste DR</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(234, 179, 8, 0.1)' }}>
                  <Calendar className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <p className="text-lg font-semibold" style={{ color: 'var(--eleven-text-primary)' }}>{daysUntilTest > 0 ? `${daysUntilTest} dias` : 'Hoje'}</p>
                  <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>Próximo Teste Agendado</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mb-6" style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  Sistemas Críticos - RTO/RPO
                </CardTitle>
              </div>
              <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
                {systemsOk}/{systems.length} OK
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sistema</TableHead>
                  <TableHead className="text-center">RTO</TableHead>
                  <TableHead className="text-center">RPO</TableHead>
                  <TableHead>Último Backup</TableHead>
                  <TableHead>Último Teste</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {systems.map((system, index) => {
                  const Icon = system.icon
                  return (
                    <TableRow key={index}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)' }}>
                            <Icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                          </div>
                          <span className="font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                            {system.name}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline" className="font-mono text-xs">
                          {system.rto}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge variant="outline" className="font-mono text-xs">
                          {system.rpo}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                          {system.lastBackup}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm" style={{ color: 'var(--eleven-text-secondary)' }}>
                          {new Date(system.lastTest).toLocaleDateString('pt-BR')}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        {getSystemStatusBadge(system.status)}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                    Histórico de Testes de DR
                  </CardTitle>
                </div>
                <Badge className="bg-status-success/15 text-status-success hover:bg-status-success/15">
                  {passedTests}/{totalTests} aprovados
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {drTests.map((test) => (
                  <div 
                    key={test.id}
                    className="p-4 rounded-md border"
                    style={{ 
                      backgroundColor: 'var(--eleven-bg-card)',
                      borderColor: 'var(--eleven-border-subtle)'
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-medium text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                          {test.type}
                        </p>
                        <p className="text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                          {new Date(test.date).toLocaleDateString('pt-BR')}
                        </p>
                      </div>
                      {getResultBadge(test.result)}
                    </div>
                    <div className="flex items-center gap-4 mb-2">
                      <div className="text-xs">
                        <span style={{ color: 'var(--eleven-text-tertiary)' }}>RTO: </span>
                        <Badge variant="outline" className="font-mono text-micro">{test.rtoAchieved}</Badge>
                      </div>
                      <div className="text-xs">
                        <span style={{ color: 'var(--eleven-text-tertiary)' }}>RPO: </span>
                        <Badge variant="outline" className="font-mono text-micro">{test.rpoAchieved}</Badge>
                      </div>
                    </div>
                    <p className="text-xs p-2 rounded" style={{ backgroundColor: 'var(--eleven-bg-subtle)', color: 'var(--eleven-text-secondary)' }}>
                      {test.notes}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card style={{ boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <CardTitle className="text-base font-medium" style={{ color: 'var(--eleven-text-primary)' }}>
                  Planos de Continuidade
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {continuityPlans.map((plan) => (
                  <div 
                    key={plan.id}
                    className="p-4 rounded-md border"
                    style={{ 
                      backgroundColor: 'var(--eleven-bg-card)',
                      borderColor: 'var(--eleven-border-subtle)'
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        <span className="font-medium text-sm" style={{ color: 'var(--eleven-text-primary)' }}>
                          {plan.name}
                        </span>
                      </div>
                      {getStatusBadge(plan.status)}
                    </div>
                    <div className="flex items-center gap-4 text-xs" style={{ color: 'var(--eleven-text-tertiary)' }}>
                      <span>Versão: {plan.version}</span>
                      <span>Atualizado: {new Date(plan.lastUpdate).toLocaleDateString('pt-BR')}</span>
                      <span>Owner: {plan.owner}</span>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-4 p-3 rounded-md bg-status-success/10 border border-status-success/30">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-status-success" />
                  <span className="text-sm font-medium text-status-success">
                    {continuityPlans.filter(p => p.status === 'approved').length} de {continuityPlans.length} planos aprovados
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
