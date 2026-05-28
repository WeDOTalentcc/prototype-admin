"use client"

/**
 * Onda 3 F3 (2026-05-28) — AssignAgentToJobModal canonical.
 *
 * Modal para acoplar um custom_agent a uma vaga (target_type="job").
 * Trigger modes canonical pra job: on_create, on_schedule, manual, on_apply.
 *
 * Reuso:
 *  - useCustomAgents (Studio) → lista de agentes
 *  - useAttachJobAgent (Onda 3.F3) → mutation POST
 *  - Tokens canonical (lia-cyan, lia-text-*, lia-border-*)
 *  - Radix Dialog
 *
 * Pattern base: AssignAgentModal (Sprint 7B, pages-talent-pools/) — não
 * extraímos generic ainda (Rule of Three: pool + job + stage será 3 sites;
 * generic vem em Onda 4 quando o terceiro consumer estabilizar).
 *
 * Trigger mode labels passam por i18n via `getTriggerModeI18nKey` canonical.
 * Cron picker reutiliza `CronScheduleBuilder` (Sprint 7C, pages-talent-pools/).
 */
import React, { useMemo, useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"
import { useTranslations } from "next-intl"
import { useCustomAgents } from "@/hooks/agents/use-custom-agents"
import { useAttachJobAgent } from "@/hooks/agents/use-job-agents"
import { TRIGGER_MODES_BY_TARGET, type TriggerMode } from "@/types/agents/job-agent"
import { CronScheduleBuilder } from "@/components/pages-talent-pools/CronScheduleBuilder"

interface AssignAgentToJobModalProps {
  jobId: string
  jobTitle?: string
  open: boolean
  onClose: () => void
  onAssigned?: () => void
}

export function AssignAgentToJobModal({
  jobId,
  jobTitle,
  open,
  onClose,
  onAssigned,
}: AssignAgentToJobModalProps) {
  const t = useTranslations("jobs.agents.attachModal")
  const tTrigger = useTranslations("jobs.agents.triggerMode")
  const { agents, isLoading: agentsLoading, isError: agentsError } =
    useCustomAgents()
  const attachAgent = useAttachJobAgent(jobId)

  const [selectedAgentId, setSelectedAgentId] = useState<string>("")
  const [triggerMode, setTriggerMode] = useState<TriggerMode>("manual")
  const [scheduleCron, setScheduleCron] = useState<string>("0 9 * * 1-5")
  const [isActive, setIsActive] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const validModes = useMemo(() => TRIGGER_MODES_BY_TARGET.job, [])

  const handleSubmit = async () => {
    if (!selectedAgentId) {
      setError(t("errors.agentRequired"))
      return
    }
    setError(null)
    try {
      await attachAgent.mutateAsync({
        agent_id: selectedAgentId,
        trigger_mode: triggerMode,
        schedule_cron: triggerMode === "on_schedule" ? scheduleCron : null,
        is_active: isActive,
      })
      // Reset
      setSelectedAgentId("")
      setTriggerMode("manual")
      onAssigned?.()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : t("errors.generic"))
    }
  }

  const handleOpenChange = (next: boolean) => {
    if (!next) onClose()
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="max-w-lg"
        data-testid="assign-agent-to-job-modal"
      >
        <DialogHeader>
          <DialogTitle className="text-lia-text-primary">
            {t("title")}
          </DialogTitle>
          {jobTitle ? (
            <p className="mt-1 text-xs text-lia-text-secondary">
              {t("jobLabel")}: <span className="font-medium">{jobTitle}</span>
            </p>
          ) : null}
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Agente */}
          <div className="space-y-2">
            <label
              htmlFor="job-agent-select"
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
                id="job-agent-select"
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                data-testid="job-agent-select"
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
              {validModes.map((mode) => (
                <label
                  key={mode}
                  className="flex cursor-pointer items-center gap-2 text-sm text-lia-text-primary"
                >
                  <input
                    type="radio"
                    name="job-trigger-mode"
                    value={mode}
                    checked={triggerMode === mode}
                    onChange={() => setTriggerMode(mode as TriggerMode)}
                    data-testid={`trigger-radio-${mode}`}
                    className="accent-lia-cyan"
                  />
                  <span>{tTrigger(mode)}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Cron picker — só visível em on_schedule */}
          {triggerMode === "on_schedule" ? (
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
              data-testid="active-checkbox"
              className="accent-lia-cyan"
            />
            <span>{t("fields.activateNow")}</span>
          </label>

          {error ? (
            <p
              className="text-xs text-status-error"
              role="alert"
              data-testid="attach-error"
            >
              {error}
            </p>
          ) : null}
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={attachAgent.isPending}
          >
            {t("cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={attachAgent.isPending || !selectedAgentId}
            data-testid="attach-submit"
            className="bg-lia-cyan text-white hover:bg-lia-cyan/90"
          >
            {attachAgent.isPending ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin motion-reduce:animate-none" />
            ) : null}
            {t("submit")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
