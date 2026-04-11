"use client"

import React from "react"
import { CheckCircle, Check } from "lucide-react"
import type { NotificationChannel, RecruiterChannel } from "./types"
import { PAUSE_REASONS } from "./types"

interface ConfirmationStepProps {
  jobsCount: number
  cancelScreenings: boolean
  totalScreenings: number
  cancelInterviews: boolean
  totalInterviews: number
  cancelTests: boolean
  totalTests: number
  notifyApplicants: boolean
  selectedCandidateIdsSize: number
  notificationChannel: NotificationChannel
  notifyRecruiters: boolean
  recruiterChannel: RecruiterChannel
  pauseReason: string
  customReason: string
}

export function ConfirmationStep({
  jobsCount,
  cancelScreenings,
  totalScreenings,
  cancelInterviews,
  totalInterviews,
  cancelTests,
  totalTests,
  notifyApplicants,
  selectedCandidateIdsSize,
  notificationChannel,
  notifyRecruiters,
  recruiterChannel,
  pauseReason,
  customReason,
}: ConfirmationStepProps) {
  return (
    <div data-testid="confirmation-step" className="space-y-4">
      <div className="flex items-center gap-2 p-2.5 rounded-xl bg-status-success/10 border border-status-success/30">
        <CheckCircle className="w-4 h-4 text-status-success" />
        <span className="text-xs text-status-success font-medium">
          Confirme as ações abaixo
        </span>
      </div>

      <div className="space-y-2 p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
        <h4 className="text-xs font-semibold text-lia-text-primary mb-2">Resumo das Ações</h4>

        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs">
            <Check className="w-3.5 h-3.5 text-status-success" />
            <span className="text-lia-text-primary" aria-live="polite" aria-atomic="true">Pausar {jobsCount} vaga(s)</span>
          </div>

          {cancelScreenings && totalScreenings > 0 && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary">Desmarcar {totalScreenings} triagem(ns)</span>
            </div>
          )}

          {cancelInterviews && totalInterviews > 0 && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary">Desmarcar {totalInterviews} entrevista(s)</span>
            </div>
          )}

          {cancelTests && totalTests > 0 && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary">Cancelar {totalTests} teste(s)</span>
            </div>
          )}

          {notifyApplicants && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary" aria-live="polite" aria-atomic="true">
                Notificar {selectedCandidateIdsSize} candidato(s) via {notificationChannel === 'both' ? 'Email e WhatsApp' : notificationChannel}
              </span>
            </div>
          )}

          {notifyRecruiters && (
            <div className="flex items-center gap-2 text-xs">
              <Check className="w-3.5 h-3.5 text-status-success" />
              <span className="text-lia-text-primary">
                Enviar resumo para recrutadores via {recruiterChannel === 'teams' ? 'Teams' : recruiterChannel === 'bell' ? 'Notificação interna' : 'Email'}
              </span>
            </div>
          )}
        </div>
      </div>

      {pauseReason && (
        <div className="p-3 rounded-xl bg-lia-bg-secondary border border-lia-border-subtle">
          <h4 className="text-xs font-semibold text-lia-text-secondary mb-1">Motivo</h4>
          <p className="text-xs text-lia-text-primary">
            {pauseReason === 'other' ? customReason : PAUSE_REASONS.find(r => r.value === pauseReason)?.label}
          </p>
        </div>
      )}
    </div>
  )
}
