"use client"

/**
 * ConfigureAssignmentModal — Sprint 7B-2.
 *
 * Permite editar `config_overrides` (JSON livre) + toggle status (active↔paused).
 *
 * Approach pragmático MVP: JSON textarea genérico. UI per-categoria (sourcing
 * tem search_strategy/preferences/outreach_config) fica em Sprint 7C.
 */
import React, { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Loader2 } from "lucide-react"
import { textStyles, buttonStyles } from "@/lib/design-tokens"
import { useUpdateAssignment } from "@/hooks/talent-pools/use-pool-agents"
import type { PoolAgentAssignment } from "@/types/pool-agent-assignment"

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
  const updateAssignment = useUpdateAssignment({ poolId })

  const [configText, setConfigText] = useState(
    JSON.stringify(assignment.config_overrides ?? {}, null, 2),
  )
  const [status, setStatus] = useState<"active" | "paused">(
    assignment.status === "paused" ? "paused" : "active",
  )
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
      // Revert UI
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
    setSubmitting(true)
    try {
      await updateAssignment(assignment.id, { config_overrides: parsed })
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao salvar")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            Configurar agente — {assignment.custom_agent_name || "(sem nome)"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Status toggle */}
          <div className="flex items-center justify-between p-3 rounded-md border border-lia-border-subtle bg-lia-surface">
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
              className="w-full font-mono text-sm p-3 rounded-md border border-lia-border-subtle bg-lia-surface focus:border-lia-border focus:outline-none"
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
