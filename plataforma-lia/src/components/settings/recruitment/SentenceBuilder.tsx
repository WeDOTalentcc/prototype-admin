"use client"

/**
 * SentenceBuilder — P2-2 Sprint A.1 canonical impeccable.
 *
 * Paradigma: automation = frase PT-BR com slots clicaveis.
 * Substitui form grid tradicional (anti-canonical Workato/Zapier slop).
 *
 * Slot types canonical:
 * - 'trigger': "Quando X acontecer"
 * - 'condition': "e Y for Z"
 * - 'action': "entao faca W"
 *
 * Cyan exclusivo pra slots LIA-driven (memory).
 *
 * Audit ref: AUTOMATIONS_IMPECCABLE_CRITIQUE.md +
 * AUTOMATIONS_SPRINT_PLAN_ADR.md Sprint A.1
 */

import { useMemo, useState } from "react"
import { Plus, Sparkles, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"

// ── Types ─────────────────────────────────────────────────────────────────

export interface ParamOption {
  value: string
  label: string
}

export interface ParamDef {
  name: string
  label: string
  type: "string" | "number" | "select"
  options?: ParamOption[]
}

export interface TriggerOption {
  value: string
  label: string
  description?: string
  params?: ParamDef[]
}

export interface ConditionOperator {
  value: string
  label: string
}

export interface ConditionFieldDef {
  value: string
  label: string
  type?: "string" | "number" | "select"
  options?: ParamOption[]
}

export interface ActionOption {
  value: string
  label: string
  description?: string
  params?: ParamDef[]
}

export interface SentenceBuilderState {
  trigger?: { type: string; params: Record<string, unknown> }
  conditions: Array<{ field: string; operator: string; value: unknown }>
  actions: Array<{ type: string; params: Record<string, unknown> }>
  name?: string
}

interface Props {
  initial?: SentenceBuilderState
  triggers: TriggerOption[]
  actions: ActionOption[]
  operators: ConditionOperator[]
  conditionFields: ConditionFieldDef[]
  onSave: (state: SentenceBuilderState) => Promise<void> | void
  onCancel: () => void
}

// ── Helpers ───────────────────────────────────────────────────────────────

const EMPTY_STATE: SentenceBuilderState = {
  trigger: undefined,
  conditions: [],
  actions: [],
  name: "",
}

export function isValid(state: SentenceBuilderState): boolean {
  if (!state.trigger?.type) return false
  if (state.actions.length === 0) return false
  for (const a of state.actions) {
    if (!a.type) return false
  }
  for (const c of state.conditions) {
    if (!c.field || !c.operator) return false
    if (c.value === undefined || c.value === null || c.value === "") return false
  }
  return true
}

export function suggestName(
  state: SentenceBuilderState,
  triggers: TriggerOption[],
  actions: ActionOption[],
): string {
  const t = triggers.find((x) => x.value === state.trigger?.type)
  const firstAction = state.actions[0]
  const a = actions.find((x) => x.value === firstAction?.type)
  if (!t || !a) return ""
  return `Quando ${t.label} → ${a.label}`
}

// ── Slot primitives ───────────────────────────────────────────────────────

interface SlotShellProps {
  active: boolean
  placeholder: string
  display?: string
  children: React.ReactNode
  testId?: string
}

function SlotShell({ active, placeholder, display, children, testId }: SlotShellProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          data-testid={testId}
          data-active={active ? "true" : "false"}
          className={cn(
            "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-sm font-medium transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-cyan/40",
            active
              ? "bg-lia-cyan/15 text-lia-cyan border border-lia-cyan/40"
              : "border border-dashed border-lia-border-default text-lia-text-secondary hover:border-lia-border-medium hover:text-lia-text-primary",
          )}
        >
          {active ? display : placeholder}
        </button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-72 p-2">
        {children}
      </PopoverContent>
    </Popover>
  )
}

interface OptionListProps<T extends { value: string; label: string; description?: string }> {
  options: T[]
  selected?: string
  onSelect: (value: string) => void
}

function OptionList<T extends { value: string; label: string; description?: string }>({
  options,
  selected,
  onSelect,
}: OptionListProps<T>) {
  return (
    <ul className="flex flex-col gap-0.5" role="listbox">
      {options.map((opt) => (
        <li key={opt.value}>
          <button
            type="button"
            role="option"
            aria-selected={selected === opt.value}
            onClick={() => onSelect(opt.value)}
            className={cn(
              "w-full rounded-sm px-2 py-1.5 text-left text-sm",
              "hover:bg-lia-interactive-hover",
              selected === opt.value && "bg-lia-cyan/10 text-lia-cyan",
            )}
          >
            <div>{opt.label}</div>
            {opt.description && (
              <div className="text-xs text-lia-text-tertiary">{opt.description}</div>
            )}
          </button>
        </li>
      ))}
    </ul>
  )
}

// ── ParamsInline (renders params after a trigger/action) ──────────────────

interface ParamsInlineProps {
  defs: ParamDef[]
  values: Record<string, unknown>
  onChange: (name: string, value: unknown) => void
  testIdPrefix: string
}

function ParamsInline({ defs, values, onChange, testIdPrefix }: ParamsInlineProps) {
  return (
    <>
      {defs.map((def) => {
        const current = values[def.name]
        const display = current !== undefined && current !== "" ? String(current) : undefined
        if (def.type === "select" && def.options) {
          return (
            <span key={def.name}>
              {" : "}
              <SlotShell
                active={display !== undefined}
                placeholder={`selecione ${def.label}`}
                display={
                  def.options.find((o) => o.value === current)?.label ?? display
                }
                testId={`${testIdPrefix}-param-${def.name}`}
              >
                <OptionList
                  options={def.options}
                  selected={display}
                  onSelect={(v) => onChange(def.name, v)}
                />
              </SlotShell>
            </span>
          )
        }
        return (
          <span key={def.name} className="inline-flex items-center gap-1">
            {" : "}
            <input
              data-testid={`${testIdPrefix}-param-${def.name}`}
              type={def.type === "number" ? "number" : "text"}
              value={current === undefined ? "" : String(current)}
              onChange={(e) =>
                onChange(
                  def.name,
                  def.type === "number" ? Number(e.target.value) : e.target.value,
                )
              }
              placeholder={def.label}
              className="rounded-md border border-lia-border-default bg-transparent px-2 py-0.5 text-sm text-lia-text-primary focus:border-lia-cyan focus:outline-none"
            />
          </span>
        )
      })}
    </>
  )
}

// ── Main component ────────────────────────────────────────────────────────

export function SentenceBuilder({
  initial,
  triggers,
  actions,
  operators,
  conditionFields,
  onSave,
  onCancel,
}: Props) {
  const [state, setState] = useState<SentenceBuilderState>(initial ?? EMPTY_STATE)
  const [isSaving, setIsSaving] = useState(false)

  const valid = useMemo(() => isValid(state), [state])
  const nameSuggestion = useMemo(
    () => suggestName(state, triggers, actions),
    [state, triggers, actions],
  )

  // ── Mutations ──────────────────────────────────────────────────────────

  const setTrigger = (type: string) => {
    setState((s) => ({ ...s, trigger: { type, params: {} } }))
  }

  const setTriggerParam = (name: string, value: unknown) => {
    setState((s) => ({
      ...s,
      trigger: s.trigger ? { ...s.trigger, params: { ...s.trigger.params, [name]: value } } : s.trigger,
    }))
  }

  const addCondition = () => {
    setState((s) => ({ ...s, conditions: [...s.conditions, { field: "", operator: "", value: "" }] }))
  }

  const updateCondition = (index: number, patch: Partial<{ field: string; operator: string; value: unknown }>) => {
    setState((s) => ({
      ...s,
      conditions: s.conditions.map((c, i) => (i === index ? { ...c, ...patch } : c)),
    }))
  }

  const removeCondition = (index: number) => {
    setState((s) => ({ ...s, conditions: s.conditions.filter((_, i) => i !== index) }))
  }

  const addAction = () => {
    setState((s) => ({ ...s, actions: [...s.actions, { type: "", params: {} }] }))
  }

  const updateActionType = (index: number, type: string) => {
    setState((s) => ({
      ...s,
      actions: s.actions.map((a, i) => (i === index ? { type, params: {} } : a)),
    }))
  }

  const updateActionParam = (index: number, name: string, value: unknown) => {
    setState((s) => ({
      ...s,
      actions: s.actions.map((a, i) =>
        i === index ? { ...a, params: { ...a.params, [name]: value } } : a,
      ),
    }))
  }

  const removeAction = (index: number) => {
    setState((s) => ({ ...s, actions: s.actions.filter((_, i) => i !== index) }))
  }

  const handleSave = async () => {
    if (!valid || isSaving) return
    setIsSaving(true)
    try {
      const finalName = state.name && state.name.trim() !== "" ? state.name : nameSuggestion
      await onSave({ ...state, name: finalName })
    } finally {
      setIsSaving(false)
    }
  }

  // ── Lookups ────────────────────────────────────────────────────────────

  const currentTrigger = triggers.find((t) => t.value === state.trigger?.type)

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6" data-testid="sentence-builder">
      <div className="text-base leading-relaxed text-lia-text-primary space-y-3">
        {/* Trigger line */}
        <p className="flex flex-wrap items-center gap-1.5">
          <span>Quando</span>
          <SlotShell
            active={!!state.trigger?.type}
            placeholder="selecione um gatilho"
            display={currentTrigger?.label}
            testId="slot-trigger"
          >
            <OptionList options={triggers} selected={state.trigger?.type} onSelect={setTrigger} />
          </SlotShell>
          {currentTrigger?.params && state.trigger && (
            <ParamsInline
              defs={currentTrigger.params}
              values={state.trigger.params}
              onChange={setTriggerParam}
              testIdPrefix="trigger"
            />
          )}
        </p>

        {/* Conditions */}
        {state.conditions.map((cond, i) => {
          const field = conditionFields.find((f) => f.value === cond.field)
          return (
            <p key={i} className="flex flex-wrap items-center gap-1.5">
              <span>e</span>
              <SlotShell
                active={!!cond.field}
                placeholder="selecione um campo"
                display={field?.label}
                testId={`slot-condition-field-${i}`}
              >
                <OptionList
                  options={conditionFields}
                  selected={cond.field}
                  onSelect={(v) => updateCondition(i, { field: v, value: "" })}
                />
              </SlotShell>
              <SlotShell
                active={!!cond.operator}
                placeholder="selecione o operador"
                display={operators.find((o) => o.value === cond.operator)?.label}
                testId={`slot-condition-operator-${i}`}
              >
                <OptionList
                  options={operators}
                  selected={cond.operator}
                  onSelect={(v) => updateCondition(i, { operator: v })}
                />
              </SlotShell>
              <span>:</span>
              {field?.type === "select" && field.options ? (
                <SlotShell
                  active={cond.value !== "" && cond.value !== undefined}
                  placeholder="selecione um valor"
                  display={field.options.find((o) => o.value === cond.value)?.label}
                  testId={`slot-condition-value-${i}`}
                >
                  <OptionList
                    options={field.options}
                    selected={cond.value as string | undefined}
                    onSelect={(v) => updateCondition(i, { value: v })}
                  />
                </SlotShell>
              ) : (
                <input
                  data-testid={`slot-condition-value-${i}`}
                  type={field?.type === "number" ? "number" : "text"}
                  value={cond.value === undefined ? "" : String(cond.value)}
                  onChange={(e) =>
                    updateCondition(i, {
                      value:
                        field?.type === "number"
                          ? Number(e.target.value)
                          : e.target.value,
                    })
                  }
                  placeholder="valor"
                  className="rounded-md border border-lia-border-default bg-transparent px-2 py-0.5 text-sm text-lia-text-primary focus:border-lia-cyan focus:outline-none"
                />
              )}
              <button
                type="button"
                onClick={() => removeCondition(i)}
                aria-label="remover condição"
                data-testid={`remove-condition-${i}`}
                className="rounded-sm p-0.5 text-lia-text-tertiary hover:bg-lia-interactive-hover hover:text-lia-text-primary"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </p>
          )
        })}

        <button
          type="button"
          onClick={addCondition}
          data-testid="add-condition"
          className="inline-flex items-center gap-1 text-xs text-lia-text-secondary hover:text-lia-text-primary"
        >
          <Plus className="h-3 w-3" /> adicionar condição
        </button>

        {/* Actions */}
        {state.actions.map((action, i) => {
          const actionDef = actions.find((a) => a.value === action.type)
          return (
            <p key={i} className="flex flex-wrap items-center gap-1.5">
              <span>{i === 0 ? "então" : "e também"}</span>
              <SlotShell
                active={!!action.type}
                placeholder="selecione uma ação"
                display={actionDef?.label}
                testId={`slot-action-${i}`}
              >
                <OptionList
                  options={actions}
                  selected={action.type}
                  onSelect={(v) => updateActionType(i, v)}
                />
              </SlotShell>
              {actionDef?.params && (
                <ParamsInline
                  defs={actionDef.params}
                  values={action.params}
                  onChange={(name, value) => updateActionParam(i, name, value)}
                  testIdPrefix={`action-${i}`}
                />
              )}
              {state.actions.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeAction(i)}
                  aria-label="remover ação"
                  data-testid={`remove-action-${i}`}
                  className="rounded-sm p-0.5 text-lia-text-tertiary hover:bg-lia-interactive-hover hover:text-lia-text-primary"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </p>
          )
        })}

        <button
          type="button"
          onClick={addAction}
          data-testid="add-action"
          className="inline-flex items-center gap-1 text-xs text-lia-text-secondary hover:text-lia-text-primary"
        >
          <Plus className="h-3 w-3" /> adicionar ação
        </button>
      </div>

      {/* Name field */}
      <div className="space-y-1">
        <input
          data-testid="automation-name"
          type="text"
          placeholder={nameSuggestion ? `Apelido (sugestão: "${nameSuggestion}")` : "Apelido para esta automação (opcional)"}
          value={state.name ?? ""}
          onChange={(e) => setState((s) => ({ ...s, name: e.target.value }))}
          className="w-full rounded-md border border-lia-border-default bg-transparent px-3 py-2 text-sm text-lia-text-primary placeholder:text-lia-text-tertiary focus:border-lia-cyan focus:outline-none"
        />
      </div>

      {/* LIA hint */}
      <div className="flex items-center gap-1.5 text-xs text-lia-text-tertiary">
        <Sparkles className="h-3 w-3 text-lia-cyan" />
        <span>
          Prefere descrever em linguagem natural? Fale com a LIA no chat lateral.
        </span>
      </div>

      {/* CTAs */}
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onCancel} data-testid="cancel">
          Cancelar
        </Button>
        <Button
          variant="primary"
          disabled={!valid || isSaving}
          onClick={handleSave}
          data-testid="save"
        >
          {isSaving ? "Salvando..." : "Salvar automação"}
        </Button>
      </div>
    </div>
  )
}
