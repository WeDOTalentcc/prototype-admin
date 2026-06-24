"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
/**
 * ConfigureAssignmentModal — Sprint 7B-2 + Sprint 7C Part 3.
 *
 * Permite editar `config_overrides` (JSON livre) + toggle status (active↔paused).
 * Sprint 7C Part 3: schedule_type radio + builders contextuais (cron, event_driven).
 *
 * Backend canonical: PATCH /api/backend-proxy/talent-pools/{pool_id}/agents/{assignment_id}
 * com `schedule_type` + `schedule_config` JSONB (Sprint 7A schema).
 */
import React, { useState } from "react"
import { useTranslations } from "next-intl"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"
import { textStyles, buttonStyles } from "@/lib/design-tokens"
import { useUpdateAssignment } from "@/hooks/talent-pools/use-pool-agents"
import { CronScheduleBuilder } from "./CronScheduleBuilder"
import { EventTriggerPicker } from "./EventTriggerPicker"
import type {
  PoolAgentAssignment,
  ScheduleType,
} from "@/types/pool-agent-assignment"

interface ConfigureAssignmentModalProps {
  assignment: PoolAgentAssignment
  poolId: string
  open: boolean
  onClose: () => void
  onSaved: () => void
}

export function ConfigureAssignmentModal({
  assignment,
  poolId,
  open,
  onClose,
  onSaved,
}: ConfigureAssignmentModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('configure-assignment', open)

  const t = useTranslations("talentPool.schedule")
  const updateAssignment = useUpdateAssignment({ poolId })

  const [configText, setConfigText] = useState(
    JSON.stringify(assignment.config_overrides ?? {}, null, 2),
  )
  const [status, setStatus] = useState<"active" | "paused">(
    assignment.status === "paused" ? "paused" : "active",
  )

  // Sprint 7C Part 3 schedule state
  const [scheduleType, setScheduleType] = useState<ScheduleType>(
    assignment.schedule_type ?? "on_demand",
  )
  const initialCron =
    (assignment.schedule_config?.cron_expression as string | undefined) ?? "0 9 * * *"
  const initialEvents =
    (assignment.schedule_config?.event_triggers as string[] | undefined) ?? []
  const [cronExpression, setCronExpression] = useState<string>(initialCron)
  const [cronLabel, setCronLabel] = useState<string>("")
  const [eventTriggers, setEventTriggers] = useState<string[]>(initialEvents)

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleToggleStatus = async () => {
    const next = status === "active" ? "paused" : "active"
    setStatus(next)
    setSubmitting(true)
    setError(null)
    try {
      await updateAssignment(assignment.id, { status: next })
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao atualizar status")
      setStatus(status)
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmit = async () => {
    setError(null)
    let parsed: Record<string, unknown>
    try {
      parsed = JSON.parse(configText)
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        throw new Error("config_overrides deve ser um objeto JSON.")
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "JSON inválido")
      return
    }

    // Compose schedule_config canonical per schedule_type
    let scheduleConfig: Record<string, unknown> = {}
    if (scheduleType === "cron") {
      scheduleConfig = { cron_expression: cronExpression, label: cronLabel }
    } else if (scheduleType === "event_driven") {
      scheduleConfig = { event_triggers: eventTriggers }
    }

    setSubmitting(true)
    try {
      await updateAssignment(assignment.id, {
        config_overrides: parsed,
        schedule_type: scheduleType,
        schedule_config: scheduleConfig,
      })
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao salvar")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            Configurar agente — {assignment.custom_agent_name || "(sem nome)"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Status toggle */}
          <div className="flex items-center justify-between p-3 rounded-md border border-lia-border-subtle bg-lia-bg-elevated">
            <div>
              <p className={textStyles.h4}>Status</p>
              <p className={textStyles.bodySmall + " text-lia-text-secondary"}>
                {status === "active"
                  ? "Agente ativo e disponível para execução."
                  : "Agente pausado — não executa."}
              </p>
            </div>
            <button
              type="button"
              onClick={handleToggleStatus}
              disabled={submitting}
              data-testid="config-status-toggle"
              className={buttonStyles.outline}
            >
              {status === "active" ? "Pausar" : "Ativar"}
            </button>
          </div>

          {/* Schedule type — Sprint 7C Part 3 */}
          <div className="space-y-2 p-3 rounded-md border border-lia-border-subtle">
            <p className={textStyles.h4}>{t("typeLabel")}</p>
            <RadioGroup
              value={scheduleType}
              onValueChange={(v) => setScheduleType(v as ScheduleType)}
              data-testid="schedule-type-radio"
            >
              <div className="flex items-center gap-2">
                <RadioGroupItem value="on_demand" id="st-on_demand" data-testid="schedule-type-on_demand" />
                <Label htmlFor="st-on_demand">{t("types.on_demand")}</Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="cron" id="st-cron" data-testid="schedule-type-cron" />
                <Label htmlFor="st-cron">{t("types.cron")}</Label>
              </div>
              <div className="flex items-center gap-2">
                <RadioGroupItem value="event_driven" id="st-event_driven" data-testid="schedule-type-event_driven" />
                <Label htmlFor="st-event_driven">{t("types.event_driven")}</Label>
              </div>
            </RadioGroup>

            {scheduleType === "cron" && (
              <div className="mt-3 pt-3 border-t border-lia-border-subtle">
                <CronScheduleBuilder
                  value={cronExpression}
                  onChange={(expr, label) => {
                    setCronExpression(expr)
                    setCronLabel(label)
                  }}
                />
              </div>
            )}

            {scheduleType === "event_driven" && (
              <div className="mt-3 pt-3 border-t border-lia-border-subtle">
                <EventTriggerPicker
                  value={eventTriggers}
                  onChange={setEventTriggers}
                />
              </div>
            )}
          </div>

          {/* Config overrides JSON editor */}
          <div>
            <label htmlFor="config-overrides-editor" className={textStyles.h4}>
              Configurações avançadas
            </label>
            <p className={textStyles.bodySmall + " text-lia-text-secondary mb-2"}>
              JSON livre. UI dedicada por categoria virá em breve.
            </p>
            <textarea
              id="config-overrides-editor"
              data-testid="config-overrides-editor"
              value={configText}
              onChange={(e) => setConfigText(e.target.value)}
              rows={10}
              spellCheck={false}
              className="w-full font-mono text-sm p-3 rounded-md border border-lia-border-subtle bg-lia-bg-elevated focus:border-lia-border-default focus:outline-none"
            />
          </div>

          {error && (
            <p className={textStyles.bodySmall + " text-red-500"} role="alert">
              {error}
            </p>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={submitting}
            data-testid="config-submit"
            className={buttonStyles.primary}
          >
            {submitting && <Loader2 className="w-4 h-4 mr-1 animate-spin" />}
            Salvar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
