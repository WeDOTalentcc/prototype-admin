"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
/**
 * Onda 4 Agent E (2026-05-29) — AssignAgentModal generico canonical.
 *
 * Rule of Three: extraido apos 3 consumers estabilizados
 *   (talent_pool / job / pipeline_stage), reduzindo ~70-80% codigo
 *   duplicado entre os modais Sprint 7B + Onda 3.F3 + Onda 3.F5.
 *
 * Responsabilidades:
 *   - Renderiza Dialog com agent select, trigger mode picker, cron picker
 *     condicional (so se on_schedule valido + selecionado), active toggle.
 *   - Le VALID_TRIGGER_MODES_BY_TARGET (TS canonical) e renderiza APENAS os
 *     modos validos pro target_type.
 *   - Resolve labels via getTriggerModeI18nKey (canonical key resolver) +
 *     namespace canonical agents.assignModal.*.
 *   - Delega o submit ao caller via prop `onSubmit` (mutation hook).
 *   - Reset interno + close em sucesso.
 *
 * Mantida fora da abstracao:
 *   - Hook de mutation (caller injeta — useAttachJobAgent, assignAgentToPool,
 *     postCreateDeployment, etc.). Generico nao conhece endpoint.
 *   - Filtros adicionais (e.g., category filter no pool legacy) — wrappers
 *     fazem isso ao redor SE precisarem; abstracao nao carrega complexidade.
 */
import React, { useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { Loader2 } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { useCustomAgents } from "@/hooks/agents/use-custom-agents"
import type { DeploymentTargetType } from "@/types/agents/agent-deployment"
import type { TriggerMode } from "@/types/agents/job-agent"
import {
  getValidTriggerModes,
  getDefaultTriggerMode,
  isScheduleTrigger,
} from "@/lib/agents/trigger-modes"
import { getTriggerModeI18nKey } from "@/lib/agents/triggerModeLabels"
import { CronScheduleBuilder } from "@/components/pages-talent-pools/CronScheduleBuilder"

export interface AssignAgentPayload {
  agent_id: string
  trigger_mode: TriggerMode
  schedule_cron: string | null
  is_active: boolean
}

export interface AssignAgentModalProps {
  open: boolean
  onClose: () => void
  /** Tipo de target ao qual o agente sera acoplado. */
  targetType: DeploymentTargetType
  /** ID do target (job_id, pool_id, stage_id, etc.). Usado pelo caller na mutation. */
  targetId: string
  /** Display label do target (ex: "Vaga: Dev Senior"). Mostrado no header. */
  targetLabel?: string
  /**
   * Submit handler — async. Recebe payload canonical, deve lancar Error em
   * falha. O modal cuida de reset/close em sucesso e mostra error inline em
   * falha.
   */
  onSubmit: (payload: AssignAgentPayload) => Promise<void>
  /** Callback opcional apos submit bem-sucedido. */
  onAssigned?: () => void
  /** data-testid prefix opcional pra facilitar tests do consumer. */
  testIdPrefix?: string
}

const TARGET_LABEL_I18N_KEY: Record<DeploymentTargetType, string> = {
  job: "jobLabel",
  talent_pool: "poolLabel",
  pipeline_stage: "stageLabel",
  candidate_list: "listLabel",
}

export function AssignAgentModal({
  open,
  onClose,
  targetType,
  targetId: _targetId,
  targetLabel,
  onSubmit,
  onAssigned,
  testIdPrefix = "assign-agent",
}: AssignAgentModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('assign-agent', open)

  const t = useTranslations("agents.assignModal")
  const tRoot = useTranslations()
  const {
    agents,
    isLoading: agentsLoading,
    isError: agentsError,
  } = useCustomAgents()

  const validModes = useMemo(() => getValidTriggerModes(targetType), [targetType])
  const defaultMode = useMemo(() => getDefaultTriggerMode(targetType), [targetType])

  const [selectedAgentId, setSelectedAgentId] = useState<string>("")
  const [triggerMode, setTriggerMode] = useState<TriggerMode>(defaultMode)
  const [scheduleCron, setScheduleCron] = useState<string>("0 9 * * 1-5")
  const [isActive, setIsActive] = useState<boolean>(true)
  const [submitting, setSubmitting] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const reset = () => {
    setSelectedAgentId("")
    setTriggerMode(defaultMode)
    setScheduleCron("0 9 * * 1-5")
    setIsActive(true)
    setError(null)
  }

  const handleSubmit = async () => {
    if (!selectedAgentId) {
      setError(t("errors.agentRequired"))
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await onSubmit({
        agent_id: selectedAgentId,
        trigger_mode: triggerMode,
        schedule_cron: isScheduleTrigger(triggerMode) ? scheduleCron : null,
        is_active: isActive,
      })
      reset()
      onAssigned?.()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.generic"))
    } finally {
      setSubmitting(false)
    }
  }

  const handleOpenChange = (next: boolean) => {
    if (!next && !submitting) onClose()
  }

  const targetLabelKey = TARGET_LABEL_I18N_KEY[targetType]
  const showCronPicker =
    isScheduleTrigger(triggerMode) && validModes.includes("on_schedule")

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="max-w-lg"
        data-testid={`${testIdPrefix}-modal`}
      >
        <DialogHeader>
          <DialogTitle className="text-lia-text-primary">
            {t(`title.${targetType}`)}
          </DialogTitle>
          {targetLabel ? (
            <p className="mt-1 text-xs text-lia-text-secondary">
              {t(targetLabelKey)}:{" "}
              <span className="font-medium">{targetLabel}</span>
            </p>
          ) : null}
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Agente */}
          <div className="space-y-2">
            <label
              htmlFor={`${testIdPrefix}-agent-select`}
              className="text-xs font-medium text-lia-text-primary"
            >
              {t("fields.agent")}
            </label>
            {agentsLoading ? (
              <div className="flex items-center gap-2 text-xs text-lia-text-tertiary">
                <Loader2 className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none" />
                {t("loadingAgents")}
              </div>
            ) : agentsError ? (
              <p className="text-xs text-status-error" role="alert">
                {t("errors.agentsLoadFailed")}
              </p>
            ) : (
              <select
                id={`${testIdPrefix}-agent-select`}
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                data-testid={`${testIdPrefix}-agent-select`}
                className="w-full rounded-md border border-lia-border-default bg-lia-bg-elevated px-3 py-2 text-sm text-lia-text-primary focus:border-lia-cyan focus:outline-none focus:ring-1 focus:ring-lia-cyan"
              >
                <option value="">{t("fields.agentPlaceholder")}</option>
                {agents.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Trigger mode */}
          <fieldset className="rounded-md border border-lia-border-subtle p-3">
            <legend className="px-2 text-xs font-medium text-lia-text-primary">
              {t("fields.trigger")}
            </legend>
            <div className="space-y-2">
              {validModes.map((mode) => {
                const i18nKey = getTriggerModeI18nKey(mode, targetType)
                return (
                  <label
                    key={mode}
                    className="flex cursor-pointer items-center gap-2 text-sm text-lia-text-primary"
                  >
                    <input
                      type="radio"
                      name={`${testIdPrefix}-trigger-mode`}
                      value={mode}
                      checked={triggerMode === mode}
                      onChange={() => setTriggerMode(mode as TriggerMode)}
                      data-testid={`${testIdPrefix}-trigger-radio-${mode}`}
                      className="accent-lia-cyan"
                    />
                    <span>{tRoot(i18nKey)}</span>
                  </label>
                )
              })}
            </div>
          </fieldset>

          {/* Cron picker — so visivel em on_schedule */}
          {showCronPicker ? (
            <div className="space-y-2">
              <label className="text-xs font-medium text-lia-text-primary">
                {t("fields.schedule")}
              </label>
              <CronScheduleBuilder
                value={scheduleCron}
                onChange={(cron) => setScheduleCron(cron)}
              />
            </div>
          ) : null}

          {/* Active toggle */}
          <label className="flex cursor-pointer items-center gap-2 text-sm text-lia-text-primary">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              data-testid={`${testIdPrefix}-active-checkbox`}
              className="accent-lia-cyan"
            />
            <span>{t("fields.activateNow")}</span>
          </label>

          {error ? (
            <p
              className="text-xs text-status-error"
              role="alert"
              data-testid={`${testIdPrefix}-error`}
            >
              {error}
            </p>
          ) : null}
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={submitting}
          >
            {t("cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={submitting || !selectedAgentId}
            data-testid={`${testIdPrefix}-submit`}
            className="bg-lia-cyan text-white hover:bg-lia-cyan/90"
          >
            {submitting ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin motion-reduce:animate-none" />
            ) : null}
            {t(`submit.${targetType}`)}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
