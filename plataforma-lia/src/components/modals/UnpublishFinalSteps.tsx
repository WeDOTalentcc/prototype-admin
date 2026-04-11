"use client"

import React from "react"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import {
  Check,
  Mail,
  AlertCircle,
  CheckCircle2,
  CalendarOff,
} from "lucide-react"
import type { UseJobUnpublishReturn } from "./useJobUnpublish"

interface StepProps {
  hook: UseJobUnpublishReturn
}

export function ConfirmationStep({ hook }: StepProps) {
  const {
    selectedCandidateIds, notificationChannel,
    acknowledgedWarning, setAcknowledgedWarning,
  } = hook

  return (
    <div className="space-y-4">
      <div className="p-4 bg-status-warning/10 border border-status-warning/30 rounded-xl">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-status-warning flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-xs font-semibold text-status-warning">Confirmação de ações</h4>
            <p className="text-xs text-status-warning mt-1">
              Ao confirmar, as seguintes ações serão executadas:
            </p>
            <ul className="mt-2 space-y-1.5">
              <li className="text-xs text-status-warning flex items-center gap-2">
                <Check className="w-3.5 h-3.5 text-status-warning" />
                A vaga será despublicada dos job boards
              </li>
              <li className="text-xs text-status-warning flex items-center gap-2">
                <Check className="w-3.5 h-3.5 text-status-warning" />
                Status alterado para "Paralisada"
              </li>
              <li className="text-xs text-status-warning flex items-center gap-2">
                <Check className="w-3.5 h-3.5 text-status-warning" />
                {selectedCandidateIds.size} candidato(s) serão notificados via {notificationChannel === 'both' ? 'email e WhatsApp' : notificationChannel}
              </li>
              <li className="text-xs text-status-warning flex items-center gap-2">
                <CalendarOff className="w-3.5 h-3.5 text-status-warning" />
                Entrevistas e triagens agendadas serão canceladas
              </li>
              <li className="text-xs text-status-warning flex items-center gap-2">
                <Mail className="w-3.5 h-3.5 text-status-warning" />
                Você receberá um email com o resumo de todas as ações
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div className="flex items-start gap-2 p-3 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
        <Checkbox
          id="acknowledgeWarning"
          checked={acknowledgedWarning}
          onCheckedChange={(checked) => setAcknowledgedWarning(!!checked)}
          className="mt-0.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
        />
        <Label htmlFor="acknowledgeWarning" className="text-xs text-lia-text-secondary cursor-pointer">
          Li e estou ciente de que todas as ações acima serão executadas e não podem ser desfeitas.
        </Label>
      </div>
    </div>
  )
}

export function CompleteStep({ hook }: StepProps) {
  const { selectedCandidateIds } = hook

  return (
    <div className="py-6 text-center">
      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-status-success/15 flex items-center justify-center">
        <CheckCircle2 className="w-8 h-8 text-status-success" />
      </div>
      <h3 className="text-sm font-semibold text-lia-text-primary mb-2">Processo finalizado!</h3>
      <p className="text-xs text-lia-text-secondary mb-4" aria-live="polite" aria-atomic="true">
        A vaga foi despublicada e congelada com sucesso.
      </p>
      <div className="bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle text-left space-y-2">
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Check className="w-3.5 h-3.5 text-status-success" />
          <span aria-live="polite" aria-atomic="true">Vaga despublicada dos job boards</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Check className="w-3.5 h-3.5 text-status-success" />
          <span>Status alterado para "Paralisada"</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Check className="w-3.5 h-3.5 text-status-success" />
          <span aria-live="polite" aria-atomic="true">{selectedCandidateIds.size} candidatos notificados</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Check className="w-3.5 h-3.5 text-status-success" />
          <span>Agendamentos cancelados</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          <Mail className="w-3.5 h-3.5 text-lia-text-secondary" />
          <span>Resumo enviado para seu email</span>
        </div>
      </div>
    </div>
  )
}
