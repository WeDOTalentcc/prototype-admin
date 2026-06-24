"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Checkbox } from"@/components/ui/checkbox"
import { Textarea } from"@/components/ui/textarea"
import { Label } from"@/components/ui/label"
import { Chip } from "@/components/ui/chip"
import { ScrollArea } from"@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import { cn } from"@/lib/utils"
import {
  Briefcase,
  Users,
  Calendar,
  AlertTriangle,
  Filter,
  Megaphone,
  Mail,
  CalendarOff,
  FileText,
  MessageSquare,
  Activity,
  Bell,
} from"lucide-react"

const PAUSE_REASONS = [
  { value: 'budget_review', label: 'Revisão orçamentária' },
  { value: 'headcount_freeze', label: 'Congelamento de headcount' },
  { value: 'restructuring', label: 'Reestruturação da área' },
  { value: 'position_redefinition', label: 'Redefinição do perfil' },
  { value: 'internal_transfer', label: 'Possível transferência interna' },
  { value: 'vacation_period', label: 'Período de férias do gestor' },
  { value: 'market_conditions', label: 'Condições de mercado' },
  { value: 'priority_change', label: 'Mudança de prioridade' },
  { value: 'other', label: 'Outro motivo' },
]

type RecruiterChannel = 'email' | 'teams' | 'bell'

interface PauseOptionsStepProps {
  jobs: Array<{
    id: string
    code?: string
    title: string
    status: string
    candidates_count?: number
    screening_count?: number
    interviews_scheduled?: number
    tests_scheduled?: number
  }>
  candidatesInProposal: Array<{ id: string; name: string }>
  hasProposalBlock: boolean
  totalScreenings: number
  totalInterviews: number
  totalTests: number
  pauseReason: string
  customReason: string
  cancelScreenings: boolean
  cancelInterviews: boolean
  cancelTests: boolean
  notifyRecruiters: boolean
  recruiterChannel: RecruiterChannel
  notifyApplicants: boolean
  onPauseReasonChange: (value: string) => void
  onCustomReasonChange: (value: string) => void
  onCancelScreeningsChange: (checked: boolean) => void
  onCancelInterviewsChange: (checked: boolean) => void
  onCancelTestsChange: (checked: boolean) => void
  onNotifyRecruitersChange: (checked: boolean) => void
  onRecruiterChannelChange: (channel: RecruiterChannel) => void
  onNotifyApplicantsChange: (checked: boolean) => void
}

export function PauseOptionsStep({
  jobs,
  candidatesInProposal,
  hasProposalBlock,
  totalScreenings,
  totalInterviews,
  totalTests,
  pauseReason,
  customReason,
  cancelScreenings,
  cancelInterviews,
  cancelTests,
  notifyRecruiters,
  recruiterChannel,
  notifyApplicants,
  onPauseReasonChange,
  onCustomReasonChange,
  onCancelScreeningsChange,
  onCancelInterviewsChange,
  onCancelTestsChange,
  onNotifyRecruitersChange,
  onRecruiterChannelChange,
  onNotifyApplicantsChange,
}: PauseOptionsStepProps) {
  return (
    <div data-testid="pause-options-step" className="space-y-4">
      <div>
        <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">Vagas Selecionadas</h4>
        <ScrollArea className="max-h-[100px]">
          <div className="space-y-1 bg-lia-bg-secondary rounded-xl p-2 border border-lia-border-subtle">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between py-1.5 px-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                  <div className="flex items-center gap-1.5 min-w-0 flex-1">
                    {job.code && <span className="text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full flex-shrink-0">{job.code}</span>}
                    <span className="text-xs font-medium text-lia-text-primary truncate">{job.title}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-micro text-lia-text-tertiary">
                  <span className="flex items-center gap-1"><Users className="w-3 h-3" />{job.candidates_count || 0}</span>
                  <span className="flex items-center gap-1"><Filter className="w-3 h-3" />{job.screening_count || 0}</span>
                  <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{job.interviews_scheduled || 0}</span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {hasProposalBlock && (
        <div className="p-3 rounded-xl bg-status-error/10 border border-status-error/30">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-status-error mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-semibold text-status-error" aria-live="polite" aria-atomic="true">
                {candidatesInProposal.length} candidato(s) em etapa de Proposta
              </p>
              <p className="text-micro text-status-error mt-0.5" aria-live="polite" aria-atomic="true">
                Finalize ou mova esses candidatos antes de pausar a vaga.
              </p>
              <div className="mt-2 space-y-1">
                {candidatesInProposal.slice(0, 3).map(c => (
                  <Chip key={c.id} variant="danger" className="text-micro bg-lia-bg-primary">{c.name}</Chip>
                ))}
                {candidatesInProposal.length > 3 && (
                  <span className="text-micro text-status-error">+{candidatesInProposal.length - 3} mais</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">Motivo (Opcional)</h4>
          <Select value={pauseReason} onValueChange={onPauseReasonChange}>
            <SelectTrigger className="h-9 text-xs border-lia-border-subtle">
              <SelectValue placeholder="Selecione um motivo..." />
            </SelectTrigger>
            <SelectContent>
              {PAUSE_REASONS.map((reason) => (
                <SelectItem key={reason.value} value={reason.value} className="text-xs">{reason.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          {pauseReason === 'other' && (
            <Textarea
              value={customReason}
              onChange={(e) => onCustomReasonChange(e.target.value)}
              placeholder="Digite o motivo para pausar..."
              className="mt-2 h-16 text-xs border-lia-border-subtle resize-none"
            />
          )}
        </div>
        <div>
          <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">Impacto</h4>
          <div className="space-y-1.5 p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
            <div className="flex items-start gap-2 text-xs text-lia-text-primary"><span className="flex-shrink-0">⏸️</span><span>Triagens em andamento serão pausadas</span></div>
            <div className="flex items-start gap-2 text-xs text-lia-text-primary"><span className="flex-shrink-0">📅</span><span>{totalInterviews} entrevista(s) agendada(s)</span></div>
            <div className="flex items-start gap-2 text-xs text-lia-text-primary"><span className="flex-shrink-0">📢</span><span>Publicações serão desativadas</span></div>
            <div className="flex items-start gap-2 text-xs text-lia-text-primary"><span className="flex-shrink-0">📧</span><span aria-live="polite" aria-atomic="true">Novos candidatos → pool de talentos</span></div>
          </div>
        </div>
      </div>

      <div className="space-y-3 bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-2">
          <CalendarOff className="w-3.5 h-3.5 text-lia-text-secondary" />
          Ações ao Pausar
        </h4>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox id="cancelScreenings" checked={cancelScreenings} onCheckedChange={(c) => onCancelScreeningsChange(c === true)} disabled={hasProposalBlock} className="border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
            <Label htmlFor="cancelScreenings" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Filter className="w-3 h-3 text-lia-text-muted" />Desmarcar triagens pendentes ({totalScreenings})
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="cancelInterviews" checked={cancelInterviews} onCheckedChange={(c) => onCancelInterviewsChange(c === true)} disabled={hasProposalBlock} className="border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
            <Label htmlFor="cancelInterviews" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Calendar className="w-3 h-3 text-lia-text-muted" />Desmarcar entrevistas agendadas ({totalInterviews})
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="cancelTests" checked={cancelTests} onCheckedChange={(c) => onCancelTestsChange(c === true)} disabled={hasProposalBlock} className="border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
            <Label htmlFor="cancelTests" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <FileText className="w-3 h-3 text-lia-text-muted" />Cancelar testes agendados ({totalTests})
            </Label>
          </div>
        </div>
      </div>

      <div className="space-y-3 bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary flex items-center gap-2">
          <Megaphone className="w-3.5 h-3.5 text-lia-text-secondary" />
          Notificações
        </h4>
        <div className="space-y-3">
          <div className="flex items-start gap-2">
            <Checkbox id="notifyRecruiters" checked={notifyRecruiters} onCheckedChange={(c) => onNotifyRecruitersChange(c === true)} className="mt-0.5 border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
            <div className="flex-1">
              <Label htmlFor="notifyRecruiters" className="text-xs font-medium text-lia-text-primary cursor-pointer">Notificar recrutadores</Label>
              <p className="text-micro text-lia-text-secondary">Enviar resumo das ações por email ou Teams</p>
              {notifyRecruiters && (
                <div className="mt-2 flex items-center gap-2">
                  <Label className="text-micro text-lia-text-secondary">Canal:</Label>
                  <div className="flex gap-1">
                    {(['email', 'teams', 'bell'] as RecruiterChannel[]).map((channel) => (
                      <Button key={channel} type="button" variant={recruiterChannel === channel ? 'primary' : 'outline'} size="sm"
                        onClick={() => onRecruiterChannelChange(channel)}
                        className={cn("h-6 px-2 text-micro gap-1", recruiterChannel === channel ?"bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text" :"border border-lia-border-default text-lia-text-secondary")}>
                        {channel === 'email' && <Mail className="w-3 h-3" />}
                        {channel === 'teams' && <MessageSquare className="w-3 h-3" />}
                        {channel === 'bell' && <Bell className="w-3 h-3" />}
                        {channel === 'email' ? 'Email' : channel === 'teams' ? 'Teams' : 'Bell'}
                      </Button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
          <div className="pt-3">
            <div className="flex items-start gap-2">
              <Checkbox id="notifyApplicants" checked={notifyApplicants} onCheckedChange={(c) => onNotifyApplicantsChange(c === true)} disabled={hasProposalBlock} className="mt-0.5 border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
              <div className="flex-1">
                <Label htmlFor="notifyApplicants" className="text-xs font-medium text-lia-text-primary cursor-pointer">Enviar email aos candidatos</Label>
                <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">Comunicar candidatos sobre o congelamento da vaga</p>
                {notifyApplicants && (
                  <p className="text-micro text-lia-text-tertiary mt-1 flex items-center gap-1">
                    <Activity className="w-3 h-3" />Após pausar, você selecionará o template e canal
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
