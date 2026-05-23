"use client"

import React, { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DraggableDialogContent,
} from "@/components/ui/dialog"
import { Loader2 } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import type {
  EscalationRule,
  EscalationRuleInput,
  EscalationActionValue,
  TriggerTypeValue,
} from "@/hooks/policy/use-policy-engine-crud"

interface EscalationRuleFormModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: EscalationRuleInput) => Promise<unknown>
  initialData?: EscalationRule | null
}

const TRIGGER_TYPES: { value: TriggerTypeValue; label: string }[] = [
  { value: "timeout", label: "timeout" },
  { value: "failure", label: "failure" },
  { value: "failure_count", label: "failure_count" },
  { value: "threshold", label: "threshold" },
  { value: "sla_breach", label: "sla_breach" },
]

const ESCALATION_ACTIONS: { value: EscalationActionValue; label: string }[] = [
  { value: "notify_manager", label: "notify_manager" },
  { value: "notify_admin", label: "notify_admin" },
  { value: "pause_workflow", label: "pause_workflow" },
  { value: "require_review", label: "require_review" },
  { value: "send_alert", label: "send_alert" },
  { value: "create_task", label: "create_task" },
]

function emptyInput(): EscalationRuleInput {
  return {
    name: "",
    description: "",
    trigger_type: "timeout",
    condition: {},
    escalate_to: [],
    escalation_action: "notify_manager",
    notification_template: null,
    cooldown_seconds: 3600,
    priority: 100,
    is_active: true,
  }
}

function toInput(rule: EscalationRule): EscalationRuleInput {
  return {
    name: rule.name,
    description: rule.description ?? "",
    trigger_type: rule.trigger_type,
    condition: rule.condition ?? {},
    escalate_to: rule.escalate_to ?? [],
    escalation_action: rule.escalation_action,
    notification_template: rule.notification_template ?? null,
    cooldown_seconds: rule.cooldown_seconds,
    priority: rule.priority,
    is_active: rule.is_active,
  }
}

export function EscalationRuleFormModal({
  open,
  onClose,
  onSubmit,
  initialData,
}: EscalationRuleFormModalProps) {
  const [form, setForm] = useState<EscalationRuleInput>(emptyInput())
  const [conditionText, setConditionText] = useState<string>("{}")
  const [escalateToText, setEscalateToText] = useState<string>("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    if (initialData) {
      const inp = toInput(initialData)
      setForm(inp)
      setConditionText(JSON.stringify(inp.condition ?? {}, null, 2))
      setEscalateToText((inp.escalate_to ?? []).join(", "))
    } else {
      setForm(emptyInput())
      setConditionText("{}")
      setEscalateToText("")
    }
    setError(null)
  }, [open, initialData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    let parsedCondition: Record<string, unknown>
    try {
      parsedCondition = JSON.parse(conditionText || "{}")
      if (typeof parsedCondition !== "object" || parsedCondition === null || Array.isArray(parsedCondition)) {
        throw new Error("condition deve ser objeto JSON")
      }
    } catch (err) {
      setError(`JSON inválido em condition: ${err instanceof Error ? err.message : String(err)}`)
      return
    }

    const escalateToArray = escalateToText
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0)

    const payload: EscalationRuleInput = {
      ...form,
      condition: parsedCondition,
      escalate_to: escalateToArray,
    }

    setSaving(true)
    try {
      await onSubmit(payload)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar")
    } finally {
      setSaving(false)
    }
  }

  const isEdit = Boolean(initialData?.id)
  const disabled = saving || !form.name.trim()

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DraggableDialogContent className="sm:max-w-[640px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className={textStyles.h3}>
            {isEdit ? "Editar Escalation Rule" : "Nova Escalation Rule"}
          </DialogTitle>
          <DialogDescription className={textStyles.description}>
            Define gatilhos de escalation (timeout/failure/SLA-breach) e destinatários.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3 py-1.5" data-testid="escalation-rule-form">
          <div>
            <Label htmlFor="er-name" className={textStyles.label}>Nome</Label>
            <Input
              id="er-name"
              data-field="name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Ex: escalate_offer_timeout_24h"
              className="mt-1 rounded-full text-xs py-1.5 px-2"
              required
              maxLength={255}
            />
          </div>

          <div>
            <Label htmlFor="er-desc" className={textStyles.label}>Descrição</Label>
            <Textarea
              id="er-desc"
              data-field="description"
              value={form.description ?? ""}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Quando dispara"
              className="mt-1 rounded-xl text-xs py-1.5 px-2"
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className={textStyles.label}>Trigger type</Label>
              <Select
                value={form.trigger_type}
                onValueChange={(value) =>
                  setForm({ ...form, trigger_type: value as TriggerTypeValue })
                }
              >
                <SelectTrigger className="mt-1 rounded-md text-xs" data-field="trigger_type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TRIGGER_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value} className="text-xs">
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label className={textStyles.label}>Escalation action</Label>
              <Select
                value={form.escalation_action}
                onValueChange={(value) =>
                  setForm({ ...form, escalation_action: value as EscalationActionValue })
                }
              >
                <SelectTrigger className="mt-1 rounded-md text-xs" data-field="escalation_action">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ESCALATION_ACTIONS.map((a) => (
                    <SelectItem key={a.value} value={a.value} className="text-xs">
                      {a.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="er-escalate-to" className={textStyles.label}>
              Escalate to (lista de IDs/emails, separados por vírgula)
            </Label>
            <Input
              id="er-escalate-to"
              data-field="escalate_to"
              value={escalateToText}
              onChange={(e) => setEscalateToText(e.target.value)}
              placeholder="manager@empresa.com, admin-user-id"
              className="mt-1 rounded-full text-xs py-1.5 px-2"
            />
          </div>

          <div>
            <Label htmlFor="er-condition" className={textStyles.label}>
              Condition (JSON)
            </Label>
            <Textarea
              id="er-condition"
              data-field="condition"
              value={conditionText}
              onChange={(e) => setConditionText(e.target.value)}
              placeholder='{"hours_without_response": 24}'
              className="mt-1 rounded-xl text-xs py-1.5 px-2 font-mono"
              rows={4}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="er-cooldown" className={textStyles.label}>Cooldown (s)</Label>
              <Input
                id="er-cooldown"
                data-field="cooldown_seconds"
                type="number"
                min={0}
                value={form.cooldown_seconds ?? 3600}
                onChange={(e) =>
                  setForm({
                    ...form,
                    cooldown_seconds: parseInt(e.target.value, 10) || 0,
                  })
                }
                className="mt-1 rounded-full text-xs py-1.5 px-2"
              />
            </div>

            <div>
              <Label htmlFor="er-priority" className={textStyles.label}>Prioridade (1-1000)</Label>
              <Input
                id="er-priority"
                data-field="priority"
                type="number"
                min={1}
                max={1000}
                value={form.priority ?? 100}
                onChange={(e) =>
                  setForm({ ...form, priority: parseInt(e.target.value, 10) || 100 })
                }
                className="mt-1 rounded-full text-xs py-1.5 px-2"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="er-template" className={textStyles.label}>
              Notification template (opcional)
            </Label>
            <Textarea
              id="er-template"
              data-field="notification_template"
              value={form.notification_template ?? ""}
              onChange={(e) =>
                setForm({ ...form, notification_template: e.target.value || null })
              }
              placeholder="Olá {{manager}}, a oferta {{offer_id}} está sem resposta há {{hours}}h."
              className="mt-1 rounded-xl text-xs py-1.5 px-2"
              rows={2}
            />
          </div>

          <div className="flex items-center justify-between p-2.5 rounded-xl bg-lia-bg-secondary">
            <div>
              <Label className={textStyles.label}>Ativa</Label>
              <p className={textStyles.caption}>Backend não expõe DELETE: desative para descartar.</p>
            </div>
            <Switch
              checked={form.is_active ?? true}
              onCheckedChange={(checked: boolean) => setForm({ ...form, is_active: checked })}
              data-toggle="is_active"
            />
          </div>

          {error && (
            <p className="text-xs text-status-error" role="alert">{error}</p>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="rounded-md text-xs"
            >
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={disabled}
              className="rounded-md text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
              data-testid="escalation-rule-save"
            >
              {saving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
                  Salvando...
                </>
              ) : isEdit ? (
                "Salvar alterações"
              ) : (
                "Criar escalation"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DraggableDialogContent>
    </Dialog>
  )
}
