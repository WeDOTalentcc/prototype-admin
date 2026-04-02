"use client"

import React from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  GraduationCap,
  Users,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Calendar,
  Plus,
  ArrowRight,
  Play,
  RefreshCw } from "lucide-react"

interface Training {
  id: number
  name: string
  trained: number
  pending: number
  completion: number
  dueDate: string | null
  category: 'compliance' | 'security' | 'privacy' | 'ethics'
  mandatory: boolean
  periodicity: 'Anual' | 'Semestral' | 'Único'
  lastCompletion: string | null
}

interface UserTrainingStatus {
  id: number
  user: string
  userEmail: string
  department: string
  training: string
  status: 'Concluído' | 'Pendente' | 'Em andamento'
  completionDate?: string
  dueDate?: string
}

const trainings: Training[] = [
  { id: 1, name: 'Segurança da Informação', trained: 45, pending: 5, completion: 90, dueDate: '2025-01-31', category: 'security', mandatory: true, periodicity: 'Anual', lastCompletion: '2024-01-15' },
  { id: 2, name: 'LGPD e Privacidade', trained: 42, pending: 8, completion: 84, dueDate: '2025-02-15', category: 'privacy', mandatory: true, periodicity: 'Anual', lastCompletion: '2024-02-20' },
  { id: 3, name: 'Código de Ética', trained: 48, pending: 2, completion: 96, dueDate: null, category: 'ethics', mandatory: true, periodicity: 'Único', lastCompletion: '2024-06-01' },
  { id: 4, name: 'Anti-assédio', trained: 50, pending: 0, completion: 100, dueDate: null, category: 'ethics', mandatory: true, periodicity: 'Anual', lastCompletion: '2024-11-15' },
  { id: 5, name: 'Anti-Fraude', trained: 38, pending: 12, completion: 76, dueDate: '2025-02-28', category: 'compliance', mandatory: true, periodicity: 'Anual', lastCompletion: '2024-03-01' },
  { id: 6, name: 'Gestão de Dados Sensíveis', trained: 35, pending: 15, completion: 70, dueDate: '2025-03-15', category: 'privacy', mandatory: false, periodicity: 'Semestral', lastCompletion: '2024-09-10' },
  { id: 7, name: 'Código de Conduta', trained: 47, pending: 3, completion: 94, dueDate: '2025-04-01', category: 'ethics', mandatory: true, periodicity: 'Anual', lastCompletion: '2024-04-15' },
]

const userTrainingStatus: UserTrainingStatus[] = [
  { id: 1, user: 'Maria Silva', userEmail: 'maria.silva@empresa.com', department: 'RH', training: 'Segurança da Informação', status: 'Concluído', completionDate: '2024-11-15' },
  { id: 2, user: 'Carlos Santos', userEmail: 'carlos.santos@empresa.com', department: 'TI', training: 'LGPD e Privacidade', status: 'Em andamento', dueDate: '2025-02-15' },
  { id: 3, user: 'Ana Costa', userEmail: 'ana.costa@empresa.com', department: 'Financeiro', training: 'Compliance Geral', status: 'Pendente', dueDate: '2025-02-28' },
  { id: 4, user: 'Pedro Lima', userEmail: 'pedro.lima@empresa.com', department: 'Comercial', training: 'Código de Ética', status: 'Concluído', completionDate: '2024-12-01' },
  { id: 5, user: 'Julia Ferreira', userEmail: 'julia.ferreira@empresa.com', department: 'RH', training: 'Anti-assédio', status: 'Concluído', completionDate: '2024-10-20' },
  { id: 6, user: 'Roberto Souza', userEmail: 'roberto.souza@empresa.com', department: 'Jurídico', training: 'LGPD e Privacidade', status: 'Pendente', dueDate: '2025-02-15' },
  { id: 7, user: 'Fernanda Lima', userEmail: 'fernanda.lima@empresa.com', department: 'TI', training: 'Segurança da Informação', status: 'Em andamento', dueDate: '2025-01-31' },
  { id: 8, user: 'Lucas Pereira', userEmail: 'lucas.pereira@empresa.com', department: 'Operações', training: 'Gestão de Dados Sensíveis', status: 'Pendente', dueDate: '2025-03-15' },
]

const upcomingTrainings = [
  { id: 1, name: 'Atualização LGPD 2025', date: '2025-02-01', participants: 50 },
  { id: 2, name: 'Workshop ISO 27001', date: '2025-02-15', participants: 25 },
  { id: 3, name: 'Simulação de Incidentes', date: '2025-03-01', participants: 30 },
]

const getCategoryBadge = (category: 'compliance' | 'security' | 'privacy' | 'ethics') => {
  switch (category) {
    case 'compliance':
      return <Badge className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary">Compliance</Badge>
    case 'security':
      return <Badge className="bg-status-warning/15 text-status-warning dark:bg-status-warning/20 dark:text-status-warning">Segurança</Badge>
    case 'privacy':
      return <Badge className="bg-wedo-purple/15 text-wedo-purple dark:bg-wedo-purple/20 dark:text-wedo-purple">Privacidade</Badge>
    case 'ethics':
      return <Badge className="bg-status-success/15 text-status-success dark:bg-status-success/20 dark:text-status-success">Ética</Badge>
  }
}

const getStatusBadge = (status: 'Concluído' | 'Pendente' | 'Em andamento') => {
  switch (status) {
    case 'Concluído':
      return <Badge variant="success" className="gap-1"><CheckCircle2 className="w-3 h-3" />Concluído</Badge>
    case 'Pendente':
      return <Badge variant="destructive" className="gap-1"><Clock className="w-3 h-3" />Pendente</Badge>
    case 'Em andamento':
      return <Badge className="bg-status-warning/15 text-status-warning dark:bg-status-warning/20 dark:text-status-warning gap-1"><Play className="w-3 h-3" />Em andamento</Badge>
  }
}

const getCompletionColor = (completion: number) => {
  if (completion >= 90) return 'text-status-success'
  if (completion >= 70) return 'text-status-warning'
  return 'text-status-error'
}

const getProgressColor = (completion: number) => {
  if (completion >= 90) return 'bg-status-success'
  if (completion >= 70) return 'bg-status-warning'
  return 'bg-status-error'
}

export default function TreinamentosPage() {
  const _totalTrained = trainings.reduce((acc, t) => acc + t.trained, 0)
  const totalPending = trainings.reduce((acc, t) => acc + t.pending, 0)
  const averageCompletion = Math.round(trainings.reduce((acc, t) => acc + t.completion, 0) / trainings.length)
  const completedTrainings = trainings.filter(t => t.completion === 100).length

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric' })
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div 
              className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
            >
              <GraduationCap className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <div>
              <h1 
                className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
              >
                Tracking de Treinamentos
              </h1>
              <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary">
                Acompanhamento de treinamentos de segurança e compliance
              </p>
            </div>
          </div>
          <Button className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:bg-lia-bg-secondary dark:text-lia-text-primary dark:hover:bg-lia-interactive-active">
            <Plus className="w-4 h-4" />
            Novo Treinamento
          </Button>
        </div>

        <Card className="mb-6 border-status-warning/30 bg-status-warning/10 dark:bg-status-warning/10 dark:border-status-warning/30">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-status-warning/15 dark:bg-status-warning/30 rounded-md">
                <AlertTriangle className="w-5 h-5 text-status-warning" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-status-warning dark:text-status-warning">
                  Gap Crítico Identificado - ISO 27001 / LGPD
                </p>
                <p className="text-xs text-status-warning dark:text-status-warning mt-1">
                  O tracking de treinamentos é um requisito obrigatório da <strong>ISO 27001 (A.7.2.2)</strong> e da <strong>LGPD (Art. 50)</strong>. 
                  Todos os funcionários devem completar treinamentos de segurança e privacidade periodicamente. 
                  Funcionários com treinamentos vencidos devem ser notificados imediatamente.
                </p>
              </div>
              <Badge className="bg-status-warning/20 text-status-warning dark:bg-status-warning dark:text-status-warning">Atenção</Badge>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-md">
                  <GraduationCap className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
                <div>
                  <p className="text-sm text-lia-text-secondary">Total de Treinamentos</p>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{trainings.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                  <CheckCircle2 className="w-5 h-5 text-status-success" />
                </div>
                <div>
                  <p className="text-sm text-lia-text-secondary">Concluídos (100%)</p>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{completedTrainings}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-status-warning/10 dark:bg-status-warning/20 rounded-md">
                  <Clock className="w-5 h-5 text-status-warning" />
                </div>
                <div>
                  <p className="text-sm text-lia-text-secondary">Pendentes</p>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{totalPending}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md">
                  <Users className="w-5 h-5 text-wedo-purple" />
                </div>
                <div>
                  <p className="text-sm text-lia-text-secondary">Taxa de Conclusão</p>
                  <p className="text-2xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{averageCompletion}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Card className="mb-6">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium">Treinamentos Obrigatórios</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary/50">
                        <th className="text-left text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-6 py-3">
                          Treinamento
                        </th>
                        <th className="text-left text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-4 py-3">
                          Categoria
                        </th>
                        <th className="text-center text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-4 py-3">
                          Periodicidade
                        </th>
                        <th className="text-left text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-4 py-3">
                          Última Conclusão
                        </th>
                        <th className="text-left text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-4 py-3">
                          Próxima Obrigatória
                        </th>
                        <th className="text-left text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-4 py-3">
                          Completude
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                      {trainings.map((training) => (
                        <tr key={training.id} className="hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 transition-colors motion-reduce:transition-none">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                                {training.name}
                              </span>
                              {training.mandatory && (
                                <Badge variant="outline" className="text-xs">Obrigatório</Badge>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            {getCategoryBadge(training.category)}
                          </td>
                          <td className="px-4 py-4 text-center">
                            <div className="flex items-center justify-center gap-1 text-sm text-lia-text-secondary">
                              <RefreshCw className="w-3 h-3" />
                              {training.periodicity}
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            {training.lastCompletion ? (
                              <span className="text-sm text-lia-text-secondary">{formatDate(training.lastCompletion)}</span>
                            ) : (
                              <span className="text-sm text-lia-text-tertiary">-</span>
                            )}
                          </td>
                          <td className="px-4 py-4">
                            {training.dueDate ? (
                              <div className="flex items-center gap-1 text-sm text-lia-text-secondary">
                                <Calendar className="w-3 h-3" />
                                {formatDate(training.dueDate)}
                              </div>
                            ) : (
                              <Badge variant="success">Concluído</Badge>
                            )}
                          </td>
                          <td className="px-4 py-4">
                            <div className="flex items-center gap-2 min-w-[120px]">
                              <div className="flex-1 h-2 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full overflow-hidden">
                                <div 
                                  className={`h-full rounded-full ${getProgressColor(training.completion)}`}
                                  style={{width: `${training.completion}%`}}
                                />
                              </div>
                              <span className={`text-sm font-medium ${getCompletionColor(training.completion)}`}>
                                {training.completion}%
                              </span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-medium">Status por Usuário</CardTitle>
                  <Badge variant="outline">{userTrainingStatus.length} registros</Badge>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary/50">
                        <th className="text-left text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-6 py-3">Usuário</th>
                        <th className="text-left text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-4 py-3">Departamento</th>
                        <th className="text-left text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-4 py-3">Treinamento</th>
                        <th className="text-center text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-4 py-3">Status</th>
                        <th className="text-left text-xs font-medium text-lia-text-secondary uppercase tracking-wider px-4 py-3">Data</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                      {userTrainingStatus.map((record) => (
                        <tr key={record.id} className="hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 transition-colors motion-reduce:transition-none">
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">{record.user}</p>
                              <p className="text-xs text-lia-text-secondary">{record.userEmail}</p>
                            </div>
                          </td>
                          <td className="px-4 py-4">
                            <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">{record.department}</span>
                          </td>
                          <td className="px-4 py-4">
                            <span className="text-sm text-lia-text-primary dark:text-lia-text-primary">{record.training}</span>
                          </td>
                          <td className="px-4 py-4 text-center">
                            {getStatusBadge(record.status)}
                          </td>
                          <td className="px-4 py-4">
                            {record.completionDate ? (
                              <div className="flex items-center gap-1 text-sm text-status-success">
                                <CheckCircle2 className="w-3 h-3" />
                                {formatDate(record.completionDate)}
                              </div>
                            ) : record.dueDate ? (
                              <div className="flex items-center gap-1 text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                                <Calendar className="w-3 h-3" />
                                {formatDate(record.dueDate)}
                              </div>
                            ) : (
                              <span className="text-sm text-lia-text-tertiary">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>

          <div>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-medium flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                  Próximos Treinamentos
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {upcomingTrainings.map((training) => (
                    <div 
                      key={training.id} 
                      className="p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-btn-primary-bg dark:hover:border-lia-border-subtle transition-colors motion-reduce:transition-none cursor-pointer"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                            {training.name}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
                              <Calendar className="w-3 h-3" />
                              {formatDate(training.date)}
                            </div>
                            <span className="text-lia-text-disabled">•</span>
                            <div className="flex items-center gap-1 text-xs text-lia-text-secondary">
                              <Users className="w-3 h-3" />
                              {training.participants} participantes
                            </div>
                          </div>
                        </div>
                        <ArrowRight className="w-4 h-4 text-lia-text-tertiary" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="mt-4">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-status-warning/10 dark:bg-status-warning/20 rounded-md">
                    <AlertTriangle className="w-5 h-5 text-status-warning" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                      Atenção
                    </p>
                    <p className="text-xs text-lia-text-secondary mt-1">
                      {totalPending} funcionários com treinamentos pendentes. 
                      Verifique os prazos para garantir conformidade.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="mt-4">
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                    <CheckCircle2 className="w-5 h-5 text-status-success" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">
                      Meta de Compliance
                    </p>
                    <p className="text-xs text-lia-text-secondary mt-1">
                      Taxa de conclusão atual: <strong className={getCompletionColor(averageCompletion)}>{averageCompletion}%</strong>. 
                      Meta: 85%. {averageCompletion >= 85 ? 'Meta atingida!' : 'Continue incentivando os treinamentos.'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
