"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  X, Calendar, Clock, Mail, Users, Settings, Plus, Edit, Trash2,
  Play, Pause, BarChart3, FileText, Send, Target, AlertCircle,
  CheckCircle, Timer, Repeat, Bell, Download
} from "lucide-react"

interface ScheduledReport {
  id: string
  name: string
  description: string
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly'
  dayOfWeek?: number // 0 = Sunday, 1 = Monday, etc.
  dayOfMonth?: number
  time: string // HH:MM format
  recipients: string[]
  reportType: 'summary' | 'detailed' | 'executive' | 'custom'
  jobIds: string[] // Empty array means all jobs
  isActive: boolean
  lastSent?: string
  nextSend: string
  createdBy: string
  createdAt: string
  template?: string
}

const mockScheduledReports: ScheduledReport[] = [
  {
    id: '1',
    name: 'Relatório Executivo Semanal',
    description: 'Resumo semanal para diretoria com métricas consolidadas',
    frequency: 'weekly',
    dayOfWeek: 1, // Monday
    time: '09:00',
    recipients: ['diretoria@empresa.com', 'rh@empresa.com'],
    reportType: 'executive',
    jobIds: [],
    isActive: true,
    lastSent: '2024-01-15T09:00:00Z',
    nextSend: '2024-01-22T09:00:00Z',
    createdBy: 'Ana Silva',
    createdAt: '2024-01-01T10:00:00Z',
    template: 'executive-summary'
  },
  {
    id: '2',
    name: 'Status de Vagas Prioritárias',
    description: 'Acompanhamento diário das vagas de alta prioridade',
    frequency: 'daily',
    time: '08:30',
    recipients: ['gestores@empresa.com'],
    reportType: 'summary',
    jobIds: ['WDT-2025-001', 'WDT-2025-002'],
    isActive: true,
    nextSend: '2024-01-17T08:30:00Z',
    createdBy: 'Carlos Santos',
    createdAt: '2024-01-10T15:00:00Z'
  },
  {
    id: '3',
    name: 'Relatório Mensal Completo',
    description: 'Análise detalhada mensal para review de performance',
    frequency: 'monthly',
    dayOfMonth: 1,
    time: '10:00',
    recipients: ['ceo@empresa.com', 'chro@empresa.com'],
    reportType: 'detailed',
    jobIds: [],
    isActive: false,
    nextSend: '2024-02-01T10:00:00Z',
    createdBy: 'Maria Costa',
    createdAt: '2023-12-01T12:00:00Z'
  }
]

interface ReportSchedulerProps {
  isOpen: boolean
  onClose: () => void
}

export function ReportScheduler({ isOpen, onClose }: ReportSchedulerProps) {
  const [scheduledReports, setScheduledReports] = useState<ScheduledReport[]>(mockScheduledReports)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingReport, setEditingReport] = useState<ScheduledReport | null>(null)

  if (!isOpen) return null

  const toggleReportStatus = (reportId: string) => {
    setScheduledReports(prev =>
      prev.map(report =>
        report.id === reportId
          ? { ...report, isActive: !report.isActive }
          : report
      )
    )
  }

  const deleteReport = (reportId: string) => {
    setScheduledReports(prev => prev.filter(report => report.id !== reportId))
  }

  const getFrequencyLabel = (frequency: string) => {
    const labels = {
      daily: 'Diário',
      weekly: 'Semanal',
      monthly: 'Mensal',
      quarterly: 'Trimestral'
    }
    return labels[frequency as keyof typeof labels] || frequency
  }

  const getNextSendLabel = (nextSend: string) => {
    const date = new Date(nextSend)
    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Hoje'
    if (diffDays === 1) return 'Amanhã'
    if (diffDays < 7) return `Em ${diffDays} dias`

    return date.toLocaleDateString('pt-BR')
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-md w-full max-w-6xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-xl font-semibold text-gray-950 flex items-center gap-2">
              <Timer className="w-5 h-5" />
              Agendamento de Relatórios
            </h2>
            <p className="text-sm lia-text-base">Configure envios automáticos de relatórios</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={() => setShowCreateForm(true)}
              className="gap-2"
            >
              <Plus className="w-4 h-4" />
              Novo Agendamento
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        {!showCreateForm && !editingReport && (
          <div className="flex-1 overflow-y-auto p-6">
            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-gray-900">{scheduledReports.length}</div>
                  <div className="text-sm lia-text-base">Total de Agendamentos</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-status-success">
                    {scheduledReports.filter(r => r.isActive).length}
                  </div>
                  <div className="text-sm lia-text-base">Ativos</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-wedo-orange">
                    {scheduledReports.filter(r => r.frequency === 'daily').length}
                  </div>
                  <div className="text-sm lia-text-base">Diários</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4 text-center">
                  <div className="text-2xl font-bold text-wedo-purple">
                    {scheduledReports.filter(r => {
                      const nextSend = new Date(r.nextSend)
                      const today = new Date()
                      return nextSend.toDateString() === today.toDateString()
                    }).length}
                  </div>
                  <div className="text-sm lia-text-base">Hoje</div>
                </CardContent>
              </Card>
            </div>

            {/* Scheduled Reports List */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-gray-950">Relatórios Agendados</h3>

              {scheduledReports.map((report) => (
                <Card key={report.id} className="hover:transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h4 className="text-lg font-medium text-gray-950">{report.name}</h4>
                          <Badge
                            variant={report.isActive ? "default" : "secondary"}
                            className={report.isActive ? "bg-status-success/15 text-status-success" : ""}
                          >
                            {report.isActive ? 'Ativo' : 'Pausado'}
                          </Badge>
                          <Badge variant="outline">
                            {getFrequencyLabel(report.frequency)}
                          </Badge>
                        </div>

                        <p className="lia-text-base mb-3">{report.description}</p>

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="font-medium text-gray-800 dark:text-lia-text-primary">Próximo Envio:</span>
                            <div className="flex items-center gap-1 mt-1">
                              <Calendar className="w-4 h-4 text-gray-800 dark:text-lia-text-primary" />
                              <span>{getNextSendLabel(report.nextSend)}</span>
                            </div>
                          </div>

                          <div>
                            <span className="font-medium text-gray-800 dark:text-lia-text-primary">Horário:</span>
                            <div className="flex items-center gap-1 mt-1">
                              <Clock className="w-4 h-4 text-gray-800 dark:text-lia-text-primary" />
                              <span>{report.time}</span>
                            </div>
                          </div>

                          <div>
                            <span className="font-medium text-gray-800 dark:text-lia-text-primary">Destinatários:</span>
                            <div className="flex items-center gap-1 mt-1">
                              <Users className="w-4 h-4 text-gray-800 dark:text-lia-text-primary" />
                              <span>{report.recipients.length} pessoa(s)</span>
                            </div>
                          </div>

                          <div>
                            <span className="font-medium text-gray-800 dark:text-lia-text-primary">Tipo:</span>
                            <div className="flex items-center gap-1 mt-1">
                              <FileText className="w-4 h-4 text-gray-800 dark:text-lia-text-primary" />
                              <span className="capitalize">{report.reportType}</span>
                            </div>
                          </div>
                        </div>

                        {report.jobIds.length > 0 && (
                          <div className="mt-3">
                            <span className="font-medium text-gray-800 dark:text-lia-text-primary text-sm">Vagas Específicas:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {report.jobIds.map(jobId => (
                                <Badge key={jobId} variant="outline" className="text-xs">
                                  {jobId}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {report.lastSent && (
                          <div className="mt-3 text-sm text-gray-800 dark:text-lia-text-primary">
                            Último envio: {new Date(report.lastSent).toLocaleDateString('pt-BR')} às {new Date(report.lastSent).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleReportStatus(report.id)}
                          className="gap-2"
                        >
                          {report.isActive ? (
                            <>
                              <Pause className="w-4 h-4" />
                              Pausar
                            </>
                          ) : (
                            <>
                              <Play className="w-4 h-4" />
                              Ativar
                            </>
                          )}
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setEditingReport(report)}
                          className="gap-2"
                        >
                          <Edit className="w-4 h-4" />
                          Editar
                        </Button>

                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deleteReport(report.id)}
                          className="gap-2 text-status-error hover:text-status-error hover:bg-status-error/10"
                        >
                          <Trash2 className="w-4 h-4" />
                          Excluir
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}

              {scheduledReports.length === 0 && (
                <Card className="p-8 text-center">
                  <div className="text-gray-800 dark:text-lia-text-primary">
                    <Timer className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <h3 className="text-lg font-medium mb-2">Nenhum relatório agendado</h3>
                    <p className="text-sm">Crie seu primeiro agendamento automático</p>
                    <Button
                      onClick={() => setShowCreateForm(true)}
                      className="mt-4 gap-2"
                    >
                      <Plus className="w-4 h-4" />
                      Criar Agendamento
                    </Button>
                  </div>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* Create/Edit Form */}
        {(showCreateForm || editingReport) && (
          <CreateScheduleForm
            report={editingReport}
            onSave={(reportData) => {
              if (editingReport) {
                setScheduledReports(prev =>
                  prev.map(r => r.id === editingReport.id ? {
                    ...reportData,
                    id: editingReport.id,
                    isActive: editingReport.isActive,
                    createdBy: editingReport.createdBy,
                    createdAt: editingReport.createdAt
                  } : r)
                )
                setEditingReport(null)
              } else {
                const newReport = {
                  ...reportData,
                  id: Date.now().toString(),
                  createdBy: 'Ana Silva',
                  createdAt: new Date().toISOString(),
                  isActive: true
                }
                setScheduledReports(prev => [...prev, newReport])
                setShowCreateForm(false)
              }
            }}
            onCancel={() => {
              setShowCreateForm(false)
              setEditingReport(null)
            }}
          />
        )}
      </div>
    </div>
  )
}

interface CreateScheduleFormProps {
  report?: ScheduledReport | null
  onSave: (report: Omit<ScheduledReport, 'id' | 'createdBy' | 'createdAt' | 'isActive'>) => void
  onCancel: () => void
}

function CreateScheduleForm({ report, onSave, onCancel }: CreateScheduleFormProps) {
  const [formData, setFormData] = useState({
    name: report?.name || '',
    description: report?.description || '',
    frequency: report?.frequency || 'weekly' as const,
    dayOfWeek: report?.dayOfWeek || 1,
    dayOfMonth: report?.dayOfMonth || 1,
    time: report?.time || '09:00',
    recipients: report?.recipients?.join(', ') || '',
    reportType: report?.reportType || 'summary' as const,
    jobIds: report?.jobIds?.join(', ') || '',
    template: report?.template || ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const nextSend = calculateNextSend(formData.frequency, formData.dayOfWeek, formData.dayOfMonth, formData.time)

    onSave({
      name: formData.name,
      description: formData.description,
      frequency: formData.frequency,
      dayOfWeek: formData.frequency === 'weekly' ? formData.dayOfWeek : undefined,
      dayOfMonth: formData.frequency === 'monthly' ? formData.dayOfMonth : undefined,
      time: formData.time,
      recipients: formData.recipients.split(',').map(email => email.trim()).filter(Boolean),
      reportType: formData.reportType,
      jobIds: formData.jobIds.split(',').map(id => id.trim()).filter(Boolean),
      nextSend: nextSend,
      template: formData.template || undefined
    })
  }

  const calculateNextSend = (frequency: string, dayOfWeek: number, dayOfMonth: number, time: string) => {
    const now = new Date()
    const [hours, minutes] = time.split(':').map(Number)

    const nextDate = new Date()
    nextDate.setHours(hours, minutes, 0, 0)

    switch (frequency) {
      case 'daily':
        if (nextDate <= now) {
          nextDate.setDate(nextDate.getDate() + 1)
        }
        break
      case 'weekly':
        const currentDay = nextDate.getDay()
        const daysUntilTarget = (dayOfWeek - currentDay + 7) % 7
        if (daysUntilTarget === 0 && nextDate <= now) {
          nextDate.setDate(nextDate.getDate() + 7)
        } else {
          nextDate.setDate(nextDate.getDate() + daysUntilTarget)
        }
        break
      case 'monthly':
        nextDate.setDate(dayOfMonth)
        if (nextDate <= now) {
          nextDate.setMonth(nextDate.getMonth() + 1)
        }
        break
    }

    return nextDate.toISOString()
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-950">
            {report ? 'Editar Agendamento' : 'Novo Agendamento'}
          </h3>
          <p className="text-sm lia-text-base">Configure os detalhes do envio automático</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                  Nome do Agendamento
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                  placeholder="Ex: Relatório Semanal da Diretoria"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                  Descrição
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                  placeholder="Descreva o propósito deste relatório..."
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                  Frequência
                </label>
                <select
                  value={formData.frequency}
                  onChange={(e) => setFormData(prev => ({ ...prev, frequency: e.target.value as any }))}
                  className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                >
                  <option value="daily">Diário</option>
                  <option value="weekly">Semanal</option>
                  <option value="monthly">Mensal</option>
                  <option value="quarterly">Trimestral</option>
                </select>
              </div>

              {formData.frequency === 'weekly' && (
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                    Dia da Semana
                  </label>
                  <select
                    value={formData.dayOfWeek}
                    onChange={(e) => setFormData(prev => ({ ...prev, dayOfWeek: Number(e.target.value) }))}
                    className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                  >
                    <option value={1}>Segunda-feira</option>
                    <option value={2}>Terça-feira</option>
                    <option value={3}>Quarta-feira</option>
                    <option value={4}>Quinta-feira</option>
                    <option value={5}>Sexta-feira</option>
                    <option value={6}>Sábado</option>
                    <option value={0}>Domingo</option>
                  </select>
                </div>
              )}

              {formData.frequency === 'monthly' && (
                <div>
                  <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                    Dia do Mês
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="31"
                    value={formData.dayOfMonth}
                    onChange={(e) => setFormData(prev => ({ ...prev, dayOfMonth: Number(e.target.value) }))}
                    className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                  Horário
                </label>
                <input
                  type="time"
                  value={formData.time}
                  onChange={(e) => setFormData(prev => ({ ...prev, time: e.target.value }))}
                  className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                />
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                  Destinatários (separados por vírgula)
                </label>
                <textarea
                  value={formData.recipients}
                  onChange={(e) => setFormData(prev => ({ ...prev, recipients: e.target.value }))}
                  className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                  placeholder="ana.silva@empresa.com, carlos.santos@empresa.com"
                  rows={3}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                  Tipo de Relatório
                </label>
                <select
                  value={formData.reportType}
                  onChange={(e) => setFormData(prev => ({ ...prev, reportType: e.target.value as any }))}
                  className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                >
                  <option value="summary">Resumo</option>
                  <option value="detailed">Detalhado</option>
                  <option value="executive">Executivo</option>
                  <option value="custom">Personalizado</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                  IDs das Vagas (opcional - deixe vazio para todas)
                </label>
                <input
                  type="text"
                  value={formData.jobIds}
                  onChange={(e) => setFormData(prev => ({ ...prev, jobIds: e.target.value }))}
                  className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                  placeholder="WDT-2025-001, WDT-2025-002"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-800 dark:text-lia-text-primary mb-2">
                  Template de Email
                </label>
                <select
                  value={formData.template}
                  onChange={(e) => setFormData(prev => ({ ...prev, template: e.target.value }))}
                  className="w-full p-3 border border-lia-border-default rounded-md focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
                >
                  <option value="">Template padrão</option>
                  <option value="executive-summary">Resumo Executivo</option>
                  <option value="weekly-digest">Resumo Semanal</option>
                  <option value="detailed-analysis">Análise Detalhada</option>
                </select>
              </div>

              <div className="bg-gray-100 dark:bg-lia-bg-secondary p-4 rounded-md">
                <h4 className="font-medium text-wedo-cyan-dark mb-2">📋 Prévia do Próximo Envio</h4>
                <div className="text-sm text-wedo-cyan-dark">
                  <div>Data: {calculateNextSend(formData.frequency, formData.dayOfWeek, formData.dayOfMonth, formData.time) && new Date(calculateNextSend(formData.frequency, formData.dayOfWeek, formData.dayOfMonth, formData.time)).toLocaleDateString('pt-BR')}</div>
                  <div>Horário: {formData.time}</div>
                  <div>Destinatários: {formData.recipients.split(',').filter(Boolean).length} pessoa(s)</div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-6 border-t">
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancelar
            </Button>
            <Button type="submit" className="gap-2">
              <CheckCircle className="w-4 h-4" />
              {report ? 'Salvar Alterações' : 'Criar Agendamento'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
