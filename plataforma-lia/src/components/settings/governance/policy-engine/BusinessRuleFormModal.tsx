"use client"

import React, { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { FormField } from "@/components/ui/form-field"
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
  BusinessRule,
  BusinessRuleInput,
  RuleTypeValue,
} from "@/hooks/policy/use-policy-engine-crud"

interface BusinessRuleFormModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: BusinessRuleInput) => Promise<unknown>
  initialData?: BusinessRule | null
}

const RULE_TYPES: { value: RuleTypeValue; label: string }[] = [
  { value: "allow", label: "ALLOW" },
  { value: "deny", label: "DENY" },
  { value: "require_approval", label: "REQUIRE_APPROVAL" },
]

function emptyInput(): BusinessRuleInput {
  return {
    name: "",
    description: "",
    rule_type: "allow",
    conditions: {},
    actions: [],
    priority: 100,
    is_active: true,
  }
}

function toInput(rule: BusinessRule): BusinessRuleInput {
  return {
    name: rule.name,
    description: rule.description ?? "",
    rule_type: rule.rule_type,
    conditions: rule.conditions ?? {},
    actions: rule.actions ?? [],
    priority: rule.priority,
    approval_config: rule.approval_config ?? null,
    is_active: rule.is_active,
    rule_metadata: rule.rule_metadata ?? null,
  }
}

export function BusinessRuleFormModal({
  open,
  onClose,
  onSubmit,
  initialData,
}: BusinessRuleFormModalProps) {
  // Hooks SEMPRE no topo (Rules-of-Hooks discipline)
  const [form, setForm] = useState<BusinessRuleInput>(emptyInput())
  const [conditionsText, setConditionsText] = useState<string>("{}")
  const [actionsText, setActionsText] = useState<string>("")
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset state quando initialData muda (Onda 2 canonical-truth: useEffect pra sync prop async)
  useEffect(() => {
    if (!open) return
    if (initialData) {
      const inp = toInput(initialData)
      setForm(inp)
      setConditionsText(JSON.stringify(inp.conditions ?? {}, null, 2))
      setActionsText((inp.actions ?? []).join(", "))
    } else {
      setForm(emptyInput())
      setConditionsText("{}")
      setActionsText("")
    }
    setError(null)
  }, [open, initialData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    let parsedConditions: Record<string, unknown>
    try {
      parsedConditions = JSON.parse(conditionsText || "{}")
      if (typeof parsedConditions !== "object" || parsedConditions === null || Array.isArray(parsedConditions)) {
        throw new Error("conditions deve ser objeto JSON")
      }
    } catch (err) {
      setError(`JSON inválido em conditions: ${err instanceof Error ? err.message : String(err)}`)
      return
    }

    const actionsArray = actionsText
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0)

    const payload: BusinessRuleInput = {
      ...form,
      conditions: parsedConditions,
      actions: actionsArray,
    }

    setSaving(true)
    try {
      await onSubmit(payload)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar regra")
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
            {isEdit ? "Editar Business Rule" : "Nova Business Rule"}
          </DialogTitle>
          <DialogDescription className={textStyles.description}>
            Define regras de negócio (ALLOW/DENY/REQUIRE_APPROVAL) avaliadas pelo Policy Engine.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3 py-1.5" data-testid="business-rule-form">
          <FormField label="Nome" required labelClassName={textStyles.label}>
            <Input
              data-field="rule_name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Ex: deny_high_risk_offers"
              className="rounded-full text-xs py-1.5 px-2"
              required
              maxLength={255}
            />
          </FormField>

          <FormField label="Descrição" labelClassName={textStyles.label}>
            <Textarea
              data-field="description"
              value={form.description ?? ""}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Explique quando essa regra dispara"
              className="rounded-xl text-xs py-1.5 px-2"
              rows={2}
            />
          </FormField>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className={textStyles.label}>Tipo</Label>
              <Select
                value={form.rule_type}
                onValueChange={(value) => setForm({ ...form, rule_type: value as RuleTypeValue })}
              >
                <SelectTrigger className="mt-1 rounded-md text-xs" data-field="rule_type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {RULE_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value} className="text-xs">
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <FormField label="Prioridade (1-1000)" labelClassName={textStyles.label}>
              <Input
                data-field="priority"
                type="number"
                min={1}
                max={1000}
                value={form.priority ?? 100}
                onChange={(e) =>
                  setForm({ ...form, priority: parseInt(e.target.value, 10) || 100 })
                }
                className="rounded-full text-xs py-1.5 px-2"
              />
            </FormField>
          </div>

          <FormField label="Actions (lista separada por vírgula)" labelClassName={textStyles.label}>
            <Input
              data-field="actions"
              value={actionsText}
              onChange={(e) => setActionsText(e.target.value)}
              placeholder="Ex: send_offer, escalate_to_manager"
              className="rounded-full text-xs py-1.5 px-2"
            />
          </FormField>

          <FormField label="Conditions (JSON)" labelClassName={textStyles.label}>
            <Textarea
              data-field="conditions"
              value={conditionsText}
              onChange={(e) => setConditionsText(e.target.value)}
              placeholder='{"salary_above": 10000}'
              className="rounded-xl text-xs py-1.5 px-2 font-mono"
              rows={4}
            />
          </FormField>

          <div className="flex items-center justify-between p-2.5 rounded-xl bg-lia-bg-secondary">
            <div>
              <Label className={textStyles.label}>Ativa</Label>
              <p className={textStyles.caption}>Regra avaliada quando ativa.</p>
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
              data-testid="business-rule-save"
            >
              {saving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
                  Salvando...
                </>
              ) : isEdit ? (
                "Salvar alterações"
              ) : (
                "Criar regra"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DraggableDialogContent>
    </Dialog>
  )
}
