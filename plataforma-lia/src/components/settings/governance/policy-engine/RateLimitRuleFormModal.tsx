"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
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
  RateLimitRule,
  RateLimitRuleInput,
  TargetTypeValue,
} from "@/hooks/policy/use-policy-engine-crud"

interface RateLimitRuleFormModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (data: RateLimitRuleInput) => Promise<unknown>
  initialData?: RateLimitRule | null
}

const TARGET_TYPES: { value: TargetTypeValue; label: string }[] = [
  { value: "company", label: "company" },
  { value: "user", label: "user" },
  { value: "agent", label: "agent" },
  { value: "action", label: "action" },
]

function emptyInput(): RateLimitRuleInput {
  return {
    name: "",
    description: "",
    target_type: "company",
    target_id: null,
    action_pattern: null,
    limit_value: 100,
    window_seconds: 60,
    burst_limit: null,
    is_active: true,
  }
}

function toInput(rule: RateLimitRule): RateLimitRuleInput {
  return {
    name: rule.name,
    description: rule.description ?? "",
    target_type: rule.target_type,
    target_id: rule.target_id ?? null,
    action_pattern: rule.action_pattern ?? null,
    limit_value: rule.limit_value,
    window_seconds: rule.window_seconds,
    burst_limit: rule.burst_limit ?? null,
    is_active: rule.is_active,
  }
}

export function RateLimitRuleFormModal({
  open,
  onClose,
  onSubmit,
  initialData,
}: RateLimitRuleFormModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('rate-limit-rule-form', open)

  const [form, setForm] = useState<RateLimitRuleInput>(emptyInput())
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    if (initialData) {
      setForm(toInput(initialData))
    } else {
      setForm(emptyInput())
    }
    setError(null)
  }, [open, initialData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (form.limit_value < 1) {
      setError("limit_value deve ser >= 1")
      return
    }
    if (form.window_seconds < 1) {
      setError("window_seconds deve ser >= 1")
      return
    }

    setSaving(true)
    try {
      await onSubmit(form)
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
            {isEdit ? "Editar Rate Limit" : "Novo Rate Limit"}
          </DialogTitle>
          <DialogDescription className={textStyles.description}>
            Define limites de chamadas por janela de tempo (target × window).
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-3 py-1.5" data-testid="rate-limit-rule-form">
          <div>
            <Label htmlFor="rl-name" className={textStyles.label}>Nome</Label>
            <Input
              id="rl-name"
              data-field="name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Ex: limit_offers_per_company"
              className="mt-1 rounded-full text-xs py-1.5 px-2"
              required
              maxLength={255}
            />
          </div>

          <div>
            <Label htmlFor="rl-desc" className={textStyles.label}>Descrição</Label>
            <Textarea
              id="rl-desc"
              data-field="description"
              value={form.description ?? ""}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Quando esse rate limit aplica"
              className="mt-1 rounded-xl text-xs py-1.5 px-2"
              rows={2}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label className={textStyles.label}>Target type</Label>
              <Select
                value={form.target_type}
                onValueChange={(value) =>
                  setForm({ ...form, target_type: value as TargetTypeValue })
                }
              >
                <SelectTrigger className="mt-1 rounded-md text-xs" data-field="target_type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TARGET_TYPES.map((t) => (
                    <SelectItem key={t.value} value={t.value} className="text-xs">
                      {t.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="rl-target-id" className={textStyles.label}>
                Target ID (opcional)
              </Label>
              <Input
                id="rl-target-id"
                data-field="target_id"
                value={form.target_id ?? ""}
                onChange={(e) =>
                  setForm({ ...form, target_id: e.target.value || null })
                }
                placeholder="UUID ou identificador"
                className="mt-1 rounded-full text-xs py-1.5 px-2"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="rl-action-pattern" className={textStyles.label}>
              Action pattern (opcional, regex)
            </Label>
            <Input
              id="rl-action-pattern"
              data-field="action_pattern"
              value={form.action_pattern ?? ""}
              onChange={(e) =>
                setForm({ ...form, action_pattern: e.target.value || null })
              }
              placeholder="Ex: offer:.*"
              className="mt-1 rounded-full text-xs py-1.5 px-2"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <Label htmlFor="rl-limit" className={textStyles.label}>Limit</Label>
              <Input
                id="rl-limit"
                data-field="limit_value"
                type="number"
                min={1}
                value={form.limit_value}
                onChange={(e) =>
                  setForm({ ...form, limit_value: parseInt(e.target.value, 10) || 1 })
                }
                className="mt-1 rounded-full text-xs py-1.5 px-2"
                required
              />
            </div>

            <div>
              <Label htmlFor="rl-window" className={textStyles.label}>Window (s)</Label>
              <Input
                id="rl-window"
                data-field="window_seconds"
                type="number"
                min={1}
                value={form.window_seconds}
                onChange={(e) =>
                  setForm({ ...form, window_seconds: parseInt(e.target.value, 10) || 1 })
                }
                className="mt-1 rounded-full text-xs py-1.5 px-2"
                required
              />
            </div>

            <div>
              <Label htmlFor="rl-burst" className={textStyles.label}>Burst (opcional)</Label>
              <Input
                id="rl-burst"
                data-field="burst_limit"
                type="number"
                min={1}
                value={form.burst_limit ?? ""}
                onChange={(e) =>
                  setForm({
                    ...form,
                    burst_limit: e.target.value ? parseInt(e.target.value, 10) : null,
                  })
                }
                className="mt-1 rounded-full text-xs py-1.5 px-2"
              />
            </div>
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
              data-testid="rate-limit-rule-save"
            >
              {saving ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none mr-1.5" />
                  Salvando...
                </>
              ) : isEdit ? (
                "Salvar alterações"
              ) : (
                "Criar rate limit"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DraggableDialogContent>
    </Dialog>
  )
}
