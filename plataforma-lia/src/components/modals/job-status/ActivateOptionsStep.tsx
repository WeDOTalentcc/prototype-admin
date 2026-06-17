"use client"

import React from "react"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Briefcase,
  Clock,
  CheckCircle,
  Filter,
  Megaphone,
  Mail,
  Calendar,
} from "lucide-react"
import { formatPausedDuration } from "./job-status-utils"

interface ActivateOptionsStepProps {
  jobs: Array<{
    id: string
    title: string
    status: string
    paused_since?: string
  }>
  resumeScreening: boolean
  republish: boolean
  updateDeadlines: boolean
  notifyRecruiters: boolean
  notifyApplicants: boolean
  onResumeScreeningChange: (checked: boolean) => void
  onRepublishChange: (checked: boolean) => void
  onUpdateDeadlinesChange: (checked: boolean) => void
  onNotifyRecruitersChange: (checked: boolean) => void
  onNotifyApplicantsChange: (checked: boolean) => void
}

export function ActivateOptionsStep({
  jobs,
  resumeScreening,
  republish,
  updateDeadlines,
  notifyRecruiters,
  notifyApplicants,
  onResumeScreeningChange,
  onRepublishChange,
  onUpdateDeadlinesChange,
  onNotifyRecruitersChange,
  onNotifyApplicantsChange,
}: ActivateOptionsStepProps) {
  return (
    <div data-testid="activate-options-step" className="space-y-4">
      <div className="p-2.5 rounded-xl border bg-lia-bg-secondary border-lia-border-subtle">
        <div className="flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-status-success flex-shrink-0" />
          <span className="text-xs text-lia-text-primary leading-relaxed" aria-live="polite" aria-atomic="true">
            Você está prestes a ativar {jobs.length} vaga{jobs.length > 1 ? 's' : ''} pausada{jobs.length > 1 ? 's' : ''}
          </span>
        </div>
      </div>

      <div>
        <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">Vagas Selecionadas</h4>
        <ScrollArea className="max-h-[120px]">
          <div className="space-y-1 bg-lia-bg-secondary rounded-xl p-2 border border-lia-border-subtle">
            {jobs.map((job) => (
              <div key={job.id} className="flex items-center justify-between py-1.5 px-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                  <span className="text-xs font-medium text-lia-text-primary truncate">{job.title}</span>
                </div>
                <div className="flex items-center gap-2 text-micro text-lia-text-tertiary">
                  <Clock className="w-3 h-3" />
                  <span>Pausada há {formatPausedDuration(job.paused_since)}</span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      <div className="space-y-3 bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary">Ações ao Ativar</h4>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox id="resumeScreening" checked={resumeScreening} onCheckedChange={(c) => onResumeScreeningChange(c === true)} className="border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
            <Label htmlFor="resumeScreening" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Filter className="w-3 h-3 text-lia-text-muted" />Retomar triagens pausadas
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="republish" checked={republish} onCheckedChange={(c) => onRepublishChange(c === true)} className="border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
            <Label htmlFor="republish" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Megaphone className="w-3 h-3 text-lia-text-muted" />Republicar em job boards
            </Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="updateDeadlines" checked={updateDeadlines} onCheckedChange={(c) => onUpdateDeadlinesChange(c === true)} className="border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
            <Label htmlFor="updateDeadlines" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
              <Calendar className="w-3 h-3 text-lia-text-muted" />Atualizar deadlines (+15 dias)
            </Label>
          </div>
        </div>
      </div>

      <div className="space-y-2 bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary">Notificações</h4>
        <div className="flex items-center space-x-2">
          <Checkbox id="notifyRecruitersActivate" checked={notifyRecruiters} onCheckedChange={(c) => onNotifyRecruitersChange(c === true)} className="border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
          <Label htmlFor="notifyRecruitersActivate" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
            <Megaphone className="w-3 h-3 text-lia-text-muted" />Notificar recrutadores
          </Label>
        </div>
        <div className="flex items-center space-x-2">
          <Checkbox id="notifyApplicantsActivate" checked={notifyApplicants} onCheckedChange={(c) => onNotifyApplicantsChange(c === true)} className="border-lia-border-default data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg" />
          <Label htmlFor="notifyApplicantsActivate" className="text-xs text-lia-text-primary cursor-pointer flex items-center gap-1">
            <Mail className="w-3 h-3 text-lia-text-muted" />Notificar candidatos sobre retomada
          </Label>
        </div>
      </div>
    </div>
  )
}
