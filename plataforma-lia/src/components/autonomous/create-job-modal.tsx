"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import React, { useState } from "react"
import {
  Users, FileSearch, BarChart3, Mail, TrendingUp, Brain,
  Loader2, Calendar, Clock
} from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { createBackgroundJob } from "@/services/lia-api"

const JOB_TYPES = [
  { 
    value: 'screening', 
    label: 'Triagem de Candidatos', 
    icon: Users,
    description: 'Análise automática de CVs e perfis de candidatos'
  },
  { 
    value: 'sourcing', 
    label: 'Busca de Talentos', 
    icon: FileSearch,
    description: 'Busca proativa de candidatos em bases externas'
  },
  { 
    value: 'report_generation', 
    label: 'Geração de Relatórios', 
    icon: BarChart3,
    description: 'Criação automática de relatórios analíticos'
  },
  { 
    value: 'candidate_outreach', 
    label: 'Contato com Candidatos', 
    icon: Mail,
    description: 'Envio automatizado de mensagens personalizadas'
  },
  { 
    value: 'market_analysis', 
    label: 'Análise de Mercado', 
    icon: TrendingUp,
    description: 'Análise de tendências e benchmarks do mercado'
  },
  { 
    value: 'pattern_learning', 
    label: 'Aprendizado de Padrões', 
    icon: Brain,
    description: 'Aprendizado com base em decisões anteriores'
  }
]

const SCHEDULE_OPTIONS = [
  { value: 'now', label: 'Executar Agora', icon: Clock },
  { value: 'scheduled', label: 'Agendar', icon: Calendar }
]

interface CreateJobModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onJobCreated?: () => void
}

export function CreateJobModal({ open, onOpenChange, onJobCreated }: CreateJobModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('create-job', open)

  const [jobType, setJobType] = useState<string>('')
  const [jobName, setJobName] = useState('')
  const [scheduleType, setScheduleType] = useState('now')
  const [scheduledDate, setScheduledDate] = useState('')
  const [scheduledTime, setScheduledTime] = useState('')
  const [loading, setLoading] = useState(false)
  const [config, setConfig] = useState<Record<string, string>>({})

  const selectedJobType = JOB_TYPES.find(t => t.value === jobType)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!jobType || !jobName) return

    setLoading(true)
    try {
      let scheduledAt: string | undefined
      if (scheduleType === 'scheduled' && scheduledDate && scheduledTime) {
        scheduledAt = new Date(`${scheduledDate}T${scheduledTime}`).toISOString()
      }

      await createBackgroundJob(
        jobType,
        jobName,
        Object.keys(config).length > 0 ? config : {},
        scheduledAt
      )

      resetForm()
      onJobCreated?.()
    } catch (error) {
    }
    setLoading(false)
  }

  const resetForm = () => {
    setJobType('')
    setJobName('')
    setScheduleType('now')
    setScheduledDate('')
    setScheduledTime('')
    setConfig({})
  }

  const handleClose = (open: boolean) => {
    if (!open) resetForm()
    onOpenChange(open)
  }

  const renderConfigFields = () => {
    if (!jobType) return null

    switch (jobType) {
      case 'screening':
        return (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs">ID da Vaga (opcional)</Label>
              <Input
                placeholder="Ex: vaga-123"
                value={config.job_vacancy_id || ''}
                onChange={(e) => setConfig({ ...config, job_vacancy_id: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Limite de Candidatos</Label>
              <Input
                type="number"
                placeholder="50"
                value={config.limit || ''}
                onChange={(e) => setConfig({ ...config, limit: e.target.value || '' })}
              />
            </div>
          </div>
        )
      case 'sourcing':
        return (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Query de Busca</Label>
              <Input
                placeholder="Ex: desenvolvedor senior python"
                value={config.query || ''}
                onChange={(e) => setConfig({ ...config, query: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Localização</Label>
              <Input
                placeholder="Ex: São Paulo, SP"
                value={config.location || ''}
                onChange={(e) => setConfig({ ...config, location: e.target.value })}
              />
            </div>
          </div>
        )
      case 'report_generation':
        return (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Tipo de Relatório</Label>
              <Select
                value={config.report_type || ''}
                onValueChange={(value) => setConfig({ ...config, report_type: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o tipo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="pipeline">Pipeline de Vagas</SelectItem>
                  <SelectItem value="performance">Performance de Recrutamento</SelectItem>
                  <SelectItem value="diversity">Diversidade</SelectItem>
                  <SelectItem value="market">Análise de Mercado</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )
      case 'candidate_outreach':
        return (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label className="text-xs">Modelo de Email</Label>
              <Select
                value={config.template_id || ''}
                onValueChange={(value) => setConfig({ ...config, template_id: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione o template" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="initial_contact">Contato Inicial</SelectItem>
                  <SelectItem value="followup">Follow-up</SelectItem>
                  <SelectItem value="interview_invite">Convite para Entrevista</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-wedo-cyan" />
            <span className="text-lia-text-primary">Novo Job Autônomo</span>
          </DialogTitle>
          <DialogDescription className="dark:text-lia-text-tertiary">
            Configure uma tarefa para a IA executar em background
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label className="text-xs">Tipo de Job</Label>
            <Select value={jobType} onValueChange={setJobType}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione o tipo de job" />
              </SelectTrigger>
              <SelectContent>
                {JOB_TYPES.map((type) => {
                  const Icon = type.icon
                  return (
                    <SelectItem key={type.value} value={type.value}>
                      <div className="flex items-center gap-2">
                        <Icon className="h-4 w-4 text-lia-text-secondary" />
                        <span>{type.label}</span>
                      </div>
                    </SelectItem>
                  )
                })}
              </SelectContent>
            </Select>
            {selectedJobType && (
              <p className="text-micro text-lia-text-secondary mt-1">
                {selectedJobType.description}
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label className="text-xs">Nome do Job</Label>
            <Input
              placeholder="Ex: Triagem Semanal - Desenvolvedores"
              value={jobName}
              onChange={(e) => setJobName(e.target.value)}
              required
            />
          </div>

          {renderConfigFields()}

          <div className="space-y-1.5">
            <Label className="text-xs">Agendamento</Label>
            <div className="grid grid-cols-2 gap-2">
              {SCHEDULE_OPTIONS.map((option) => {
                const Icon = option.icon
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setScheduleType(option.value)}
                    className={cn(
 "flex items-center justify-center gap-2 p-3 rounded-md border transition-colors text-xs",
                      scheduleType === option.value
                        ? "border-lia-btn-primary-bg bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 text-lia-text-secondary"
                        : "border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default dark:hover:border-lia-border-medium"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    {option.label}
                  </button>
                )
              })}
            </div>
          </div>

          {scheduleType === 'scheduled' && (
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">Data</Label>
                <Input
                  type="date"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  required={scheduleType === 'scheduled'}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Hora</Label>
                <Input
                  type="time"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                  required={scheduleType === 'scheduled'}
                />
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleClose(false)}
              disabled={loading}
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={loading || !jobType || !jobName}
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-1 animate-spin motion-reduce:animate-none" />
                  Criando...
                </>
              ) : (
                'Criar Job'
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
