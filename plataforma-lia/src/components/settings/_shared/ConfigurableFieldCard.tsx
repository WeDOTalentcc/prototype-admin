"use client"

/**
 * ConfigurableFieldCard — card unificado de "campo configurável" (P3c, 2026-06-01).
 *
 * Realiza o modelo do plano (Q3): um conceito = valor/toggle + instrução de
 * texto livre, num card coeso. Padrão canônico INLINE (textarea sempre visível),
 * substituindo os dois padrões anteriores (switch+popover de LiaFieldToggle e a
 * seção inline ad-hoc do HiringPoliciesHub).
 *
 * Presentational puro (CLAUDE.md _shared REGRA 6): zero hooks de dados, zero
 * fetch. Estado local só para o texto em edição + auto-save on-blur.
 *
 * Facetas:
 *  - toggle (opcional, showToggle): "a IA usa este campo?" — gates de empresa.
 *  - instruction (sempre): texto livre que orienta a LIA.
 * O valor tipado (gate de política) NÃO vive aqui — é editado nos controles
 * tipados (MinhaEmpresaCard). Invariante de segurança: instrução nunca é gate.
 */

import React from "react"
import { Bot, CheckCircle2, Loader2 } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

export interface ConfigurableFieldCardProps {
  label: string
  /** Subtexto: dica de uso ou localização do campo. */
  hint?: string
  /** Texto livre persistido (fonte da verdade vinda do servidor/estado pai). */
  instruction: string
  /** Chamado on-blur quando o texto mudou. */
  onInstructionSave: (instruction: string) => void
  placeholder?: string
  /** Faceta toggle (opcional). Quando ausente, o card é só-instrução. */
  showToggle?: boolean
  isActive?: boolean
  onToggleChange?: (isActive: boolean) => void
  isSaving?: boolean
  isReadOnly?: boolean
  className?: string
  "data-testid"?: string
}

export function ConfigurableFieldCard({
  label,
  hint,
  instruction,
  onInstructionSave,
  placeholder,
  showToggle = false,
  isActive = true,
  onToggleChange,
  isSaving = false,
  isReadOnly = false,
  className,
  "data-testid": dataTestId,
}: ConfigurableFieldCardProps) {
  const [draft, setDraft] = React.useState(instruction)
  // Sincroniza quando o valor do servidor muda (CLAUDE.md: evitar stale useState).
  React.useEffect(() => {
    setDraft(instruction)
  }, [instruction])

  const dirty = draft !== instruction
  const showSaved = !dirty && !isSaving && instruction.trim().length > 0
  // Instrução desabilitada se read-only OU (tem toggle e está desligado).
  const instructionDisabled = isReadOnly || (showToggle && !isActive)

  const handleBlur = () => {
    if (draft !== instruction) onInstructionSave(draft)
  }

  return (
    <div
      data-testid={dataTestId}
      className={cn(
        "rounded-xl border border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary p-3 space-y-2",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <label className="text-sm font-medium text-lia-text-primary leading-snug block">{label}</label>
          {hint && <p className="text-xs text-lia-text-secondary leading-relaxed mt-0.5">{hint}</p>}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {isSaving && <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-lia-text-secondary" aria-label="Salvando" />}
          {showSaved && (
            <span className="flex items-center gap-1 text-micro text-status-success" aria-label="Salvo">
              <CheckCircle2 className="w-3 h-3" />Salvo
            </span>
          )}
          {showToggle && (
            <Switch
              checked={isActive}
              disabled={isReadOnly}
              onCheckedChange={(c) => onToggleChange?.(c)}
              aria-label={`A LIA usa o campo ${label}`}
              className="data-[state=checked]:bg-lia-btn-primary-bg dark:data-[state=checked]:bg-lia-bg-secondary"
            />
          )}
        </div>
      </div>

      {instructionDisabled && showToggle && !isActive ? (
        <p className="flex items-center gap-1.5 text-xs text-lia-text-tertiary italic">
          <Bot className="w-3 h-3" />
          Campo desativado — a LIA usa estratégias de fallback no lugar deste dado.
        </p>
      ) : (
        <Textarea
          value={draft}
          disabled={instructionDisabled}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={handleBlur}
          placeholder={placeholder}
          rows={2}
          className="resize-none text-sm bg-lia-bg-primary dark:bg-lia-bg-elevated border-lia-border-subtle focus:border-lia-border-medium placeholder:text-lia-text-tertiary"
        />
      )}
    </div>
  )
}
