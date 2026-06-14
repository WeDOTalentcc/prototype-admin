"use client"

import React from "react"
import {
  Briefcase,
  ChevronRight,
  Code2,
  GraduationCap,
  Users,
  Zap,
  type LucideIcon,
} from "lucide-react"
import {
  PIPELINE_TEMPLATES,
  type PipelineTemplateCardData,
  type PipelineTemplateOption,
  type PipelineTemplateType,
} from "./wizard-plan-card"
import { cn } from "@/lib/utils"

/**
 * WizardPipelineTemplateCard — non-persisted assistant card injected
 * into the chat feed when the backend surfaces a
 * `suggestions_data.pipeline_template` block (Onda 25). Renders the 5
 * pipeline options as selectable tiles; the option matching
 * `suggestedType` is highlighted so the recruiter can confirm the
 * recommendation in one click or pivot to another preset.
 *
 * Tokens follow DS LIA v4.2.x — no hex colors, no ad-hoc grays —
 * so dark mode inherits from the same CSS variables and contrast
 * stays WCAG AA.
 */

const TEMPLATE_ICONS: Record<PipelineTemplateType, LucideIcon> = {
  technical: Code2,
  executive: Briefcase,
  operational: Zap,
  mass_hiring: Users,
  intern: GraduationCap,
}

interface Props {
  data: PipelineTemplateCardData
  /**
   * Invoked when the recruiter picks a template. The chat surface
   * forwards the selection to LIA via `sendChatMessage` (free-text
   * confirmation pattern shared with other in-chat decisions).
   */
  onSelect: (option: PipelineTemplateOption) => void
  /** Disables every tile while a selection is in-flight (post-click). */
  disabled?: boolean
  /**
   * Id of an already-selected template. When set, the matching tile
   * shows a "Selecionado" badge and other tiles fade — used after the
   * recruiter clicks but before the backend echoes the next stage.
   */
  selectedId?: PipelineTemplateType | null
}

export function WizardPipelineTemplateCard({
  data,
  onSelect,
  disabled = false,
  selectedId = null,
}: Props) {
  const { suggestedType, allowedTypes } = data
  const visible = allowedTypes
    ? PIPELINE_TEMPLATES.filter((t) => allowedTypes.includes(t.id))
    : PIPELINE_TEMPLATES
  if (visible.length === 0) return null

  return (
    <div
      role="group"
      aria-label="Opções de pipeline para esta vaga"
      data-testid="wizard-template-card"
      className="mt-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary p-3"
    >
      <p className="text-[11px] font-medium uppercase tracking-wide text-lia-text-secondary">
        Pipeline sugerido
      </p>
      <p className="mt-0.5 text-sm font-semibold text-lia-text-primary">
        Escolha o pipeline desta vaga
      </p>

      <div className="mt-3 flex flex-col gap-2">
        {visible.map((option) => {
          const Icon = TEMPLATE_ICONS[option.id]
          const isSuggested = option.id === suggestedType
          const isSelected = option.id === selectedId
          const isDimmed = selectedId !== null && !isSelected
          return (
            <button
              key={option.id}
              type="button"
              role="button"
              aria-label={`Usar template ${option.name}: ${option.description}`}
              aria-pressed={isSelected}
              data-testid={`wizard-template-option-${option.id}`}
              data-suggested={isSuggested ? "true" : undefined}
              disabled={disabled || isSelected}
              onClick={() => onSelect(option)}
              className={cn(
                "group flex w-full items-start gap-2.5 rounded-md border p-2.5 text-left transition-colors motion-reduce:transition-none",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-wedo-cyan focus-visible:ring-offset-1",
                isSuggested
                  ? "border-wedo-cyan bg-wedo-cyan/5 hover:bg-wedo-cyan/10"
                  : "border-lia-border-default bg-lia-bg-primary hover:bg-lia-interactive-hover",
                isSelected && "border-status-success bg-status-success/5",
                isDimmed && "opacity-50",
                (disabled || isSelected) && "cursor-not-allowed",
              )}
            >
              <span
                className={cn(
                  "mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md",
                  isSuggested
                    ? "bg-wedo-cyan/15 text-wedo-cyan-text"
                    : "bg-lia-bg-tertiary text-lia-text-secondary",
                )}
                aria-hidden="true"
              >
                <Icon className="h-4 w-4" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex flex-wrap items-center gap-1.5">
                  <span className="text-sm font-medium text-lia-text-primary">
                    {option.name}
                  </span>
                  {isSuggested && !isSelected && (
                    <span className="rounded-full bg-wedo-cyan/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-wedo-cyan-text">
                      Sugerido
                    </span>
                  )}
                  {isSelected && (
                    <span className="rounded-full bg-status-success/15 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-status-success">
                      Selecionado
                    </span>
                  )}
                </span>
                <span className="mt-0.5 block text-[12px] text-lia-text-secondary">
                  {option.description}
                </span>
                <span className="mt-1.5 flex flex-wrap items-center gap-x-1 gap-y-0.5 text-[11px] text-lia-text-disabled">
                  {option.stages.map((stage, idx) => (
                    <React.Fragment key={stage}>
                      <span>{stage}</span>
                      {idx < option.stages.length - 1 && (
                        <ChevronRight
                          className="h-3 w-3"
                          aria-hidden="true"
                        />
                      )}
                    </React.Fragment>
                  ))}
                </span>
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
