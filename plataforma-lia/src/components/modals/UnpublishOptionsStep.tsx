"use client"

import React from "react"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  AlertTriangle,
  Snowflake,
  Bell,
  AlertCircle,
  Archive,
  Briefcase,
} from "lucide-react"
import { FREEZE_REASONS } from "./useJobUnpublishModal"

export interface UnpublishOptionsStepProps {
  jobs: Array<{
    id: string
    code?: string
    title: string
    status: string
    is_published?: boolean
    published_channels?: string[]
  }>
  freezeJob: boolean
  setFreezeJob: (v: boolean) => void
  freezeReason: string
  setFreezeReason: (v: string) => void
  freezeStartDate: string
  setFreezeStartDate: (v: string) => void
  unfreezeDate: string
  setUnfreezeDate: (v: string) => void
  notifyApplicants: boolean
  setNotifyApplicants: (v: boolean) => void
  hasProposalBlock: boolean
  candidatesInProposal: Array<{ id: string; name: string }>
}

export function UnpublishOptionsStep({
  jobs,
  freezeJob,
  setFreezeJob,
  freezeReason,
  setFreezeReason,
  freezeStartDate,
  setFreezeStartDate,
  unfreezeDate,
  setUnfreezeDate,
  notifyApplicants,
  setNotifyApplicants,
  hasProposalBlock,
  candidatesInProposal,
}: UnpublishOptionsStepProps) {
  return (
    <div className="space-y-4" data-testid="unpublish-options-step">
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
            <div className="ml-6 space-y-3 pt-2 pl-3 border-l-2 border-lia-border-default">
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
