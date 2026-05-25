"use client"

/**
 * AssignAgentModal — Sprint 7B-2.
 *
 * Modal canonical para attach um custom_agent ao talent_pool.
 * Consome `useCustomAgents()` (Studio) + `useAssignAgent` (foundation 7B-1).
 *
 * Schedule type: apenas on_demand habilitado nesta sprint.
 * Cron/event_driven viram em Sprint 7C.
 */
import React, { useState, useMemo } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { textStyles, buttonStyles } from "@/lib/design-tokens"
import { Loader2 } from "lucide-react"
import { useCustomAgents } from "@/hooks/agents/use-custom-agents"
import { useAssignAgent } from "@/hooks/talent-pools/use-pool-agents"
import type { ScheduleType } from "@/types/pool-agent-assignment"

type CategoryFilter = "all" | "sourcing" | "screening" | "communication" | "analytics" | "automation"

const CATEGORY_OPTIONS: { value: CategoryFilter; label: string }[] = [
  { value: "all", label: "Todos" },
  { value: "sourcing", label: "Sourcing" },
  { value: "screening", label: "Screening" },
  { value: "communication", label: "Comunicação" },
  { value: "analytics", label: "Analytics" },
  { value: "automation", label: "Automação" },
]

interface AssignAgentModalProps {
  poolId: string
  open: boolean
  initialCategory?: string
  onClose: () => void
  onAssigned: () => void
}

export function AssignAgentModal({
  poolId,
  open,
  initialCategory,
  onClose,
  onAssigned,
}: AssignAgentModalProps) {
  const { agents, isLoading, isError } = useCustomAgents()
  const assignAgent = useAssignAgent({ poolId })

  const [category, setCategory] = useState<CategoryFilter>(
    (initialCategory as CategoryFilter) || "all",
  )
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null)
  const [scheduleType] = useState<ScheduleType>("on_demand")
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const filtered = useMemo(() => {
    if (category === "all") return agents
    return agents.filter((a) => a.category === category || a.domain === category)
  }, [agents, category])

  const handleSubmit = async () => {
    if (!selectedAgentId) {
      setError("Selecione um agente.")
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      await assignAgent({
        custom_agent_id: selectedAgentId,
        schedule_type: scheduleType,
      })
      onAssigned()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao atribuir agente")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Adicionar agente ao pool</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Category filter */}
          <div className="flex items-center gap-2 flex-wrap">
            {CATEGORY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setCategory(opt.value)}
                data-testid={`modal-filter-${opt.value}`}
                className={
                  category === opt.value
                    ? "px-3 py-1 text-sm rounded-full border border-lia-border bg-lia-surface-strong"
                    : "px-3 py-1 text-sm rounded-full border border-lia-border-subtle bg-lia-surface text-lia-text-secondary"
                }
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Agents list */}
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {isLoading && (
              <div className="flex items-center justify-center py-6 gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className={textStyles.bodySmall}>Carregando agentes…</span>
              </div>
            )}
            {isError && (
              <p className={textStyles.bodySmall + " text-red-500"}>
                Erro ao carregar agentes. Tente novamente.
              </p>
            )}
            {!isLoading && filtered.length === 0 && (
              <p className={textStyles.bodySmall + " text-lia-text-tertiary py-4 text-center"}>
                Nenhum agente nesta categoria. Crie em Agent Studio.
              </p>
            )}
            {filtered.map((a) => {
              const isSelected = selectedAgentId === a.id
              return (
                <button
                  key={a.id}
                  type="button"
                  data-testid={`agent-row-${a.id}`}
                  onClick={() => setSelectedAgentId(a.id)}
                  className={
                    isSelected
                      ? "w-full text-left p-3 rounded-md border border-lia-border bg-lia-surface-strong"
                      : "w-full text-left p-3 rounded-md border border-lia-border-subtle bg-lia-surface hover:border-lia-border"
                  }
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={textStyles.h4}>{a.name}</span>
                      {a.category && (
                        <Chip variant="neutral" muted>
                          {String(a.category)}
                        </Chip>
                      )}
                    </div>
                  </div>
                  {a.description && (
                    <p className={textStyles.bodySmall + " text-lia-text-secondary mt-1"}>
                      {a.description}
                    </p>
                  )}
                </button>
              )
            })}
          </div>

          {/* Schedule type */}
          <fieldset className="border border-lia-border-subtle rounded-md p-3">
            <legend className={textStyles.bodySmall + " px-2"}>Tipo de execução</legend>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="schedule_type"
                  value="on_demand"
                  defaultChecked
                  data-testid="schedule-radio-on_demand"
                />
                <span className={textStyles.body}>On-demand (manual)</span>
              </label>
              <label className="flex items-center gap-2 cursor-not-allowed opacity-50">
                <input
                  type="radio"
                  name="schedule_type"
                  value="cron"
                  disabled
                  data-testid="schedule-radio-cron"
                />
                <span className={textStyles.body}>Cron (em breve)</span>
              </label>
              <label className="flex items-center gap-2 cursor-not-allowed opacity-50">
                <input
                  type="radio"
                  name="schedule_type"
                  value="event_driven"
                  disabled
                  data-testid="schedule-radio-event_driven"
                />
                <span className={textStyles.body}>Event-driven (em breve)</span>
              </label>
            </div>
          </fieldset>

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
            disabled={submitting || !selectedAgentId}
            data-testid="assign-submit"
            className={buttonStyles.primary}
          >
            {submitting && <Loader2 className="w-4 h-4 mr-1 animate-spin" />}
            Atribuir
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
