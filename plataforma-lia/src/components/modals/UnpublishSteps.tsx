"use client"

import React from "react"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { cn } from "@/lib/utils"
import {
  AlertTriangle,
  Check,
  Snowflake,
  Bell,
  Mail,
  Briefcase,
  AlertCircle,
  CheckCircle2,
  CalendarOff,
  Archive,
} from "lucide-react"
import { FREEZE_REASONS, type UseJobUnpublishReturn } from "./useJobUnpublish"

export { CommunicationStep } from "./UnpublishCommunicationStep"

interface StepProps {
  hook: UseJobUnpublishReturn
}

export function OptionsStep({ hook }: StepProps) {
  const {
    jobs, freezeJob, setFreezeJob,
    freezeReason, setFreezeReason,
    freezeStartDate, setFreezeStartDate,
    unfreezeDate, setUnfreezeDate,
    notifyApplicants, setNotifyApplicants,
    hasProposalBlock, candidatesInProposal,
  } = hook

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
          Vagas Selecionadas
        </h4>
        <div className="max-h-[100px] overflow-y-auto space-y-1 bg-lia-bg-secondary rounded-xl p-2 border border-lia-border-subtle">
          {jobs.map((job) => (
            <div key={job.id} className="flex items-center justify-between py-1.5 px-2 bg-lia-bg-primary rounded-xl border border-lia-border-subtle">
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <Briefcase className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                <div className="flex items-center gap-1.5 min-w-0 flex-1">
                  {job.code && <span className="text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary px-1.5 py-0.5 rounded-full flex-shrink-0">{job.code}</span>}
                  <span className="text-xs font-medium text-lia-text-primary truncate">{job.title}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-3 bg-lia-bg-secondary rounded-xl p-3 border border-lia-border-subtle">
        <div className="flex items-center gap-2 text-lia-text-primary mb-2">
          <AlertTriangle className="w-3.5 h-3.5 text-lia-text-secondary" />
          <span className="text-xs font-semibold text-lia-text-primary">Opções ao despublicar</span>
        </div>

        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <Checkbox
              id="freezeJob"
              checked={freezeJob}
              onCheckedChange={(checked) => setFreezeJob(!!checked)}
              className="mt-0.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
            />
            <div className="flex-1">
              <Label htmlFor="freezeJob" className="text-xs font-medium text-lia-text-primary cursor-pointer flex items-center gap-1">
                <Snowflake className="w-3 h-3 text-lia-text-secondary" />
                Congelar vaga
              </Label>
              <p className="text-micro text-lia-text-secondary">Pausar temporariamente o processo seletivo (status → Paralisada)</p>
            </div>
          </div>

          {freezeJob && (
            <div className="ml-6 space-y-3 pt-2 pl-3 border-l-4 border-lia-border-default">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-micro text-lia-text-secondary mb-1 block">Data início congelamento</Label>
                  <Input
                    type="date"
                    value={freezeStartDate}
                    onChange={(e) => setFreezeStartDate(e.target.value)}
                    className="h-8 text-xs border-lia-border-subtle"
                  />
                </div>
                <div>
                  <Label className="text-micro text-lia-text-secondary mb-1 block">
                    Previsão descongelamento
                    <span className="text-lia-text-disabled ml-1">(opcional)</span>
                  </Label>
                  <Input
                    type="date"
                    value={unfreezeDate}
                    onChange={(e) => setUnfreezeDate(e.target.value)}
                    min={freezeStartDate || new Date().toISOString().split('T')[0]}
                    className="h-8 text-xs border-lia-border-subtle"
                  />
                </div>
              </div>

              <div>
                <Label className="text-micro text-lia-text-secondary mb-1 block">Motivo do congelamento</Label>
                <Select value={freezeReason} onValueChange={setFreezeReason}>
                  <SelectTrigger className="h-8 text-xs border-lia-border-subtle">
                    <SelectValue placeholder="Selecione um motivo..." />
                  </SelectTrigger>
                  <SelectContent>
                    {FREEZE_REASONS.map((reason) => (
                      <SelectItem key={reason.value} value={reason.value} className="text-xs">
                        {reason.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-lia-border-subtle pt-3">
          <div className="flex items-start gap-2">
            <Checkbox
              id="notifyApplicants"
              checked={notifyApplicants}
              onCheckedChange={(checked) => setNotifyApplicants(!!checked)}
              className="mt-0.5 data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg"
            />
            <div className="flex-1">
              <Label htmlFor="notifyApplicants" className="text-xs font-medium text-lia-text-primary cursor-pointer flex items-center gap-1">
                <Bell className="w-3 h-3 text-lia-text-secondary" />
                Notificar candidatos
              </Label>
              <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                Todos os candidatos do processo receberão uma mensagem
              </p>
              {notifyApplicants && (
                <p className="text-micro text-lia-text-tertiary mt-1 flex items-center gap-1">
                  <Archive className="w-3 h-3" />
                  IA abrirá o modal de envio por email/WhatsApp com template sugerido
                </p>
              )}
            </div>
          </div>
        </div>

        {hasProposalBlock && (
          <div className="mt-3 p-2.5 bg-status-warning/10 border border-status-warning/30 rounded-xl">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-status-warning flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-medium text-status-warning" aria-live="polite" aria-atomic="true">
                  {candidatesInProposal.length} candidato(s) em etapa de Proposta
                </p>
                <p className="text-micro text-status-warning mt-0.5" aria-live="polite" aria-atomic="true">
                  Finalize o status destes candidatos antes de despublicar a vaga:
                </p>
                <ul className="mt-1 space-y-0.5">
                  {candidatesInProposal.slice(0, 3).map(c => (
                    <li key={c.id} className="text-micro text-status-warning flex items-center gap-1">
                      <span className="w-1 h-1 rounded-full bg-status-warning" />
                      {c.name}
                    </li>
                  ))}
                  {candidatesInProposal.length > 3 && (
                    <li className="text-micro text-status-warning italic">
                      e mais {candidatesInProposal.length - 3}...
                    </li>
                  )}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
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
