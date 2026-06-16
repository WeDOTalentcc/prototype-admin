"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import {
  Briefcase,
  Users,
  Calendar,
  Filter,
  Megaphone,
  Mail,
  XCircle,
  MessageSquare,
  Bell,
} from "lucide-react"
import { CANCEL_REASONS } from "./types"

type RecruiterChannel = 'email' | 'teams' | 'bell'

interface CancelOptionsStepProps {
  jobs: Array<{
    id: string
    code?: string
    title: string
    status: string
    candidates_count?: number
    screening_count?: number
    interviews_scheduled?: number
  }>
  cancelReason: string
  customReason: string
  notifyRecruiters: boolean
  recruiterChannel: RecruiterChannel
  notifyApplicants: boolean
  onCancelReasonChange: (value: string) => void
  onCustomReasonChange: (value: string) => void
  onNotifyRecruitersChange: (checked: boolean) => void
  onRecruiterChannelChange: (channel: RecruiterChannel) => void
  onNotifyApplicantsChange: (checked: boolean) => void
}

export function CancelOptionsStep({
  jobs,
  cancelReason,
  customReason,
  notifyRecruiters,
  recruiterChannel,
  notifyApplicants,
  onCancelReasonChange,
  onCustomReasonChange,
  onNotifyRecruitersChange,
  onRecruiterChannelChange,
  onNotifyApplicantsChange,
}: CancelOptionsStepProps) {
  return (
    <div data-testid="cancel-options-step" className="space-y-4">
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

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">Motivo do Cancelamento</h4>
          <Select value={cancelReason} onValueChange={onCancelReasonChange}>
            <SelectTrigger className="h-9 text-xs border-lia-border-subtle">
              <SelectValue placeholder="Selecione um motivo..." />
            </SelectTrigger>
            <SelectContent>
              {CANCEL_REASONS.map((reason) => (
                <SelectItem key={reason.value} value={reason.value} className="text-xs">{reason.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          {cancelReason === 'other' && (
            <Textarea
              value={customReason}
              onChange={(e) => onCustomReasonChange(e.target.value)}
              placeholder="Digite o motivo do cancelamento..."
              className="mt-2 h-16 text-xs border-lia-border-subtle resize-none"
            />
          )}
        </div>
        <div>
          <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">Impacto</h4>
          <div className="space-y-1.5 p-3 rounded-xl bg-status-error/10 border border-status-error/30">
            <div className="flex items-start gap-2 text-xs text-lia-text-primary"><XCircle className="w-3.5 h-3.5 text-status-error flex-shrink-0 mt-0.5" /><span>Vaga será cancelada permanentemente</span></div>
            <div className="flex items-start gap-2 text-xs text-lia-text-primary"><span className="flex-shrink-0">📅</span><span>Entrevistas e triagens serão canceladas</span></div>
            <div className="flex items-start gap-2 text-xs text-lia-text-primary"><span className="flex-shrink-0">📢</span><span>Publicações serão removidas</span></div>
            <div className="flex items-start gap-2 text-xs text-lia-text-primary"><span className="flex-shrink-0">👥</span><span aria-live="polite" aria-atomic="true">Candidatos ativos serão marcados como cancelados</span></div>
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
            <Checkbox id="cancelNotifyRecruiters" checked={notifyRecruiters} onCheckedChange={(c) => onNotifyRecruitersChange(c === true)} className="mt-0.5 border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
            <div className="flex-1">
              <Label htmlFor="cancelNotifyRecruiters" className="text-xs font-medium text-lia-text-primary cursor-pointer">Notificar recrutadores</Label>
              <p className="text-micro text-lia-text-secondary">Enviar resumo das ações por email ou Teams</p>
              {notifyRecruiters && (
                <div className="mt-2 flex items-center gap-2">
                  <Label className="text-micro text-lia-text-secondary">Canal:</Label>
                  <div className="flex gap-1">
                    {(['email', 'teams', 'bell'] as RecruiterChannel[]).map((channel) => (
                      <Button key={channel} type="button" variant={recruiterChannel === channel ? 'primary' : 'outline'} size="sm"
                        onClick={() => onRecruiterChannelChange(channel)}
                        className={cn("h-6 px-2 text-micro gap-1", recruiterChannel === channel ? "bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text" : "border border-lia-border-default text-lia-text-secondary")}>
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
              <Checkbox id="cancelNotifyApplicants" checked={notifyApplicants} onCheckedChange={(c) => onNotifyApplicantsChange(c === true)} className="mt-0.5 border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
              <div className="flex-1">
                <Label htmlFor="cancelNotifyApplicants" className="text-xs font-medium text-lia-text-primary cursor-pointer">Enviar comunicação aos candidatos</Label>
                <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">Informar candidatos sobre o cancelamento da vaga</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
