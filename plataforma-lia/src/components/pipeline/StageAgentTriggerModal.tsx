"use client"

/**
 * Onda 3 F5 (2026-05-28) — StageAgentTriggerModal canonical.
 *
 * Modal aberto ao clicar "+ Agente" no header de uma coluna do Funil.
 * Acopla um custom_agent a um pipeline_stage com trigger event-driven.
 *
 * Trigger modes canonical pra pipeline_stage:
 *   - on_enter_stage    → quando candidato entra nesta etapa
 *   - on_exit_stage     → quando candidato sai desta etapa
 *   - on_stuck_in_stage → quando candidato fica travado nesta etapa
 *   - on_stage_change   → qualquer mudança que envolva esta etapa
 *
 * Submit: POST /api/backend-proxy/agent-deployments com target_type='pipeline_stage'.
 */
import React, { useMemo, useState } from "react"
import { useTranslations } from "next-intl"
import { useMutation, useQueryClient } from "@tanstack/react-query"
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
import { TRIGGER_MODES_BY_TARGET, type TriggerMode } from "@/types/agents/job-agent"

interface StageAgentTriggerModalProps {
  stageId: string
  stageName?: string
  open: boolean
  onClose: () => void
  onAssigned?: () => void
}

function authHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {}
  const token = localStorage.getItem("auth_token")
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function postCreateDeployment(payload: {
  agent_id: string
  target_type: "pipeline_stage"
  target_id: string
  trigger_mode: TriggerMode
  is_active: boolean
}): Promise<unknown> {
  // Backend canonical: POST /custom-agents/{agent_id}/deployments
  const res = await fetch(
    `/api/backend-proxy/custom-agents/${encodeURIComponent(payload.agent_id)}/deployments`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({
        target_type: payload.target_type,
        target_id: payload.target_id,
        trigger_mode: payload.trigger_mode,
        is_active: payload.is_active,
      }),
    },
  )
  if (!res.ok) {
    let detail = ""
    try {
      const data = await res.json()
      detail = data?.detail || data?.message || ""
    } catch {
      /* ignore */
    }
    throw new Error(detail || `Failed to create deployment: ${res.status}`)
  }
  return res.json()
}

export function StageAgentTriggerModal({
  stageId,
  stageName,
  open,
  onClose,
  onAssigned,
}: StageAgentTriggerModalProps) {
  const t = useTranslations("pipeline.stage.attachModal")
  const tTrigger = useTranslations("pipeline.stage.triggerMode")
  const { agents, isLoading: agentsLoading, isError: agentsError } =
    useCustomAgents()
  const qc = useQueryClient()

  const [selectedAgentId, setSelectedAgentId] = useState<string>("")
  const [triggerMode, setTriggerMode] = useState<TriggerMode>("on_enter_stage")
  const [isActive, setIsActive] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const validModes = useMemo(() => TRIGGER_MODES_BY_TARGET.pipeline_stage, [])

  const mutation = useMutation({
    mutationFn: () =>
      postCreateDeployment({
        agent_id: selectedAgentId,
        target_type: "pipeline_stage",
        target_id: stageId,
        trigger_mode: triggerMode,
        is_active: isActive,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["agent-deployments"] })
      setSelectedAgentId("")
      setTriggerMode("on_enter_stage")
      onAssigned?.()
      onClose()
    },
    onError: (e: Error) => setError(e.message),
  })

  const handleSubmit = () => {
    if (!selectedAgentId) {
      setError(t("errors.agentRequired"))
      return
    }
    setError(null)
    mutation.mutate()
  }

  const handleOpenChange = (next: boolean) => {
    if (!next) onClose()
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="max-w-lg"
        data-testid="stage-agent-trigger-modal"
      >
        <DialogHeader>
          <DialogTitle className="text-lia-text-primary">
            {t("title")}
          </DialogTitle>
          {stageName ? (
            <p className="mt-1 text-xs text-lia-text-secondary">
              {t("stageLabel")}:{" "}
              <span className="font-medium">{stageName}</span>
            </p>
          ) : null}
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Agente */}
          <div className="space-y-2">
            <label
              htmlFor="stage-agent-select"
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
                id="stage-agent-select"
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(e.target.value)}
                data-testid="stage-agent-select"
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
                    name="stage-trigger-mode"
                    value={mode}
                    checked={triggerMode === mode}
                    onChange={() => setTriggerMode(mode as TriggerMode)}
                    data-testid={`stage-trigger-radio-${mode}`}
                    className="accent-lia-cyan"
                  />
                  <span>{tTrigger(mode)}</span>
                </label>
              ))}
            </div>
          </fieldset>

          {/* Active toggle */}
          <label className="flex cursor-pointer items-center gap-2 text-sm text-lia-text-primary">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              data-testid="stage-active-checkbox"
              className="accent-lia-cyan"
            />
            <span>{t("fields.activateNow")}</span>
          </label>

          {error ? (
            <p
              className="text-xs text-status-error"
              role="alert"
              data-testid="stage-attach-error"
            >
              {error}
            </p>
          ) : null}
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={mutation.isPending}
          >
            {t("cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={mutation.isPending || !selectedAgentId}
            data-testid="stage-attach-submit"
            className="bg-lia-cyan text-white hover:bg-lia-cyan/90"
          >
            {mutation.isPending ? (
              <Loader2 className="mr-1 h-4 w-4 animate-spin motion-reduce:animate-none" />
            ) : null}
            {t("submit")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
