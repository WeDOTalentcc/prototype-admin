"use client"

import React from "react"
import { CheckCircle, XCircle, ClipboardCheck, Settings, Globe, Building2, Layers, CalendarDays } from "lucide-react"
import type { ReviewData } from "../wizard-types"
import { usePersonaName } from "@/hooks/company/usePersonaName"

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

const CHECK_LABELS: Record<string, string> = {
  jd_approved: "JD aprovado pelo recrutador",
  questions_approved: "Perguntas aprovadas",
  has_questions: "Perguntas geradas",
  has_seniority: "Senioridade definida",
  quality_score_ok: "Quality score >= 50",
  has_eligibility: "Elegibilidade configurada",
  has_salary: "Faixa salarial definida",
}

type SourcingMode = "local" | "global" | "hybrid"

const SOURCING_OPTIONS: Array<{
  value: SourcingMode
  label: string
  description: string
  Icon: typeof Building2
}> = [
  {
    value: "local",
    label: "Talent Pool interno",
    description: "Buscar somente na base da empresa",
    Icon: Building2,
  },
  {
    value: "hybrid",
    label: "Interno + Global",
    description: "Interno primeiro; complementar com global se necessario",
    Icon: Layers,
  },
  {
    value: "global",
    label: "Busca global",
    description: "Sourcing publico + base interna",
    Icon: Globe,
  },
]

function classes(...names: Array<string | false | undefined | null>) {
  return names.filter(Boolean).join(" ")
}

export function ReviewPanel({ data, onUpdate }: Props) {
  const personaName = usePersonaName()
  const d = data as unknown as ReviewData
  const readiness = d.readiness || { ready: false, checks: {}, missing: [] }
  const chronogram = (d as unknown as { derived_chronogram?: Array<{name: string; order: number; sla_days: number; offset_start: number; offset_end: number}> }).derived_chronogram || []
  const defaultsApplied = d.defaults_applied || []
  const sourcingMode = d.sourcing_mode ?? null

  const handleApplyDefaults = () => {
    window.dispatchEvent(new CustomEvent("lia:prefill-message", {
      detail: { message: "Aplicar defaults da empresa nesta vaga" },
    }))
  }

  const handleSourcingSelect = (mode: SourcingMode) => {
    onUpdate?.({ sourcing_mode: mode })
  }

  return (
    <div data-testid="review-panel" className="px-4 py-3 space-y-3">
      <div className="flex items-center gap-2">
        <ClipboardCheck className="w-4 h-4 text-wedo-cyan" />
        <span className="text-sm font-semibold text-lia-text-primary">
          Checklist de publicacao
        </span>
      </div>

      <div className="space-y-1.5">
        {Object.entries(readiness.checks || {}).map(([key, passed]) => (
          <div key={key} className="flex items-center gap-2 text-sm">
            {passed ? (
              <CheckCircle className="w-4 h-4 text-status-success flex-shrink-0" />
            ) : (
              <XCircle className="w-4 h-4 text-status-error flex-shrink-0" />
            )}
            <span className={passed ? "text-lia-text-primary" : "text-status-error"}>
              {CHECK_LABELS[key] || key}
            </span>
          </div>
        ))}
      </div>

      {readiness.ready ? (
        <div className="p-2.5 rounded-md bg-status-success/5 border border-status-success/20">
          <p className="text-xs text-status-success font-medium">
            Vaga pronta para publicar!
          </p>
        </div>
      ) : (
        <div className="p-2.5 rounded-md bg-status-warning/5 border border-status-warning/20">
          <p className="text-xs text-status-warning font-medium">
            Pendencias: {readiness.missing?.join(", ")}
          </p>
        </div>
      )}

      {/* PR-8 ONDA 3 / F-3.5: sourcing_mode explicit selector */}
      <div data-testid="sourcing-mode-selector" className="space-y-1.5">
        <div className="text-xs font-semibold text-lia-text-secondary">
          Onde a {personaName} deve buscar candidatos?
        </div>
        {sourcingMode === null && (
          <div className="text-[10px] text-status-warning">
            Defina o modo antes de publicar (default = Talent Pool interno).
          </div>
        )}
        <div className="grid grid-cols-1 gap-1.5">
          {SOURCING_OPTIONS.map(({ value, label, description, Icon }) => {
            const selected = sourcingMode === value
            return (
              <button
                key={value}
                type="button"
                data-sourcing-mode={value}
                aria-pressed={selected}
                onClick={() => handleSourcingSelect(value)}
                className={classes(
                  "flex items-start gap-2 px-3 py-2 rounded-md border text-left transition-colors motion-reduce:transition-none",
                  selected
                    ? "border-wedo-cyan bg-wedo-cyan/5"
                    : "border-lia-border-subtle hover:border-lia-text-tertiary hover:bg-lia-bg-secondary",
                )}
              >
                <Icon className={classes(
                  "w-4 h-4 flex-shrink-0 mt-0.5",
                  selected ? "text-wedo-cyan" : "text-lia-text-tertiary",
                )} />
                <div className="flex-1 min-w-0">
                  <div className={classes(
                    "text-xs font-medium",
                    selected ? "text-wedo-cyan" : "text-lia-text-primary",
                  )}>
                    {label}
                  </div>
                  <div className="text-[10px] text-lia-text-tertiary leading-tight">
                    {description}
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </div>


      {/* W1-I: Cronograma previsto do pipeline */}
      {chronogram.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5">
            <CalendarDays className="w-4 h-4 text-wedo-cyan" />
            <span className="text-xs font-semibold text-lia-text-secondary">
              Cronograma previsto
            </span>
          </div>
          <div className="space-y-0.5">
            {chronogram.map((stage) => (
              <div key={stage.order} className="flex items-center justify-between text-[10px]">
                <span className="text-lia-text-primary truncate max-w-[120px]">{stage.name}</span>
                <div className="flex items-center gap-1 text-lia-text-tertiary shrink-0">
                  <span>{stage.sla_days}d</span>
                  <span>·</span>
                  <span className="text-lia-text-secondary">até +{stage.offset_end} dias</span>
                </div>
              </div>
            ))}
            <div className="pt-0.5 border-t border-lia-border-subtle mt-1 flex justify-between text-[10px] font-medium">
              <span className="text-lia-text-secondary">Total estimado</span>
              <span className="text-wedo-cyan">{chronogram[chronogram.length - 1].offset_end} dias</span>
            </div>
          </div>
        </div>
      )}

      {/* Applied defaults */}
      {defaultsApplied.length > 0 && (
        <div className="text-[10px] text-lia-text-tertiary">
          Defaults aplicados: {defaultsApplied.join(", ")}
        </div>
      )}

      {/* Apply defaults button */}
      {!readiness.ready && (
        <button
          onClick={handleApplyDefaults}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors"
        >
          <Settings className="w-3.5 h-3.5" />
          Aplicar defaults da empresa
        </button>
      )}
    </div>
  )
}
