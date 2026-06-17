import React, { useState } from "react"
import {
  ChevronDown,
  ClipboardCheck,
  CheckCircle,
  XCircle,
  Globe,
  MapPin,
  Shuffle,
  Sparkles,
  AlertTriangle,
} from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import type { ReviewData } from "./wizard-types"

const CHECK_LABELS: Record<string, string> = {
  jd_approved: "JD aprovado pelo recrutador",
  questions_approved: "Perguntas aprovadas",
  has_questions: "Perguntas geradas",
  has_seniority: "Senioridade definida",
  quality_score_ok: "Quality score >= 50",
  has_eligibility: "Elegibilidade configurada",
  has_salary: "Faixa salarial definida",
}

const SOURCING_OPTIONS = [
  {
    value: "local" as const,
    icon: MapPin,
    label: "Local",
    description: "Buscar apenas no banco interno da empresa",
  },
  {
    value: "hybrid" as const,
    icon: Shuffle,
    label: "Híbrido",
    description: "Banco interno + pool global WeDOTalent",
  },
  {
    value: "global" as const,
    icon: Globe,
    label: "Global",
    description: "Pool global WeDOTalent (máximo alcance)",
  },
]

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

/**
 * WizardReviewCard — card inline no chat para o stage de review/checklist.
 *
 * Renderiza a checklist de publicacao, banner de prontidao, seletor de
 * modo de sourcing e defaults aplicados. Despacha CustomEvents para que
 * o orchestrator consuma as acoes de forma homogenea.
 */
export function WizardReviewCard({ data, onUpdate }: Props) {
  const [expanded, setExpanded] = useState(true)
  const d = data as unknown as ReviewData

  const readiness = d.readiness || { ready: false, checks: {}, missing: [] }
  const checks = readiness.checks || {}
  const missing = readiness.missing || []
  const isReady = readiness.ready
  const defaultsApplied = d.defaults_applied || []
  const sourcingMode = d.sourcing_mode ?? null

  const totalChecks = Object.keys(checks).length
  const passedChecks = Object.values(checks).filter(Boolean).length

  const handleSourcingSelect = (mode: "local" | "hybrid" | "global") => {
    onUpdate?.({ sourcing_mode: mode })
  }

  const handleApplyDefaults = () => {
    window.dispatchEvent(
      new CustomEvent("lia:prefill-message", {
        detail: { text: "Aplicar defaults da empresa nesta vaga" },
      }),
    )
  }

  return (
    <div
      role="region"
      aria-label="Checklist de publicação"
      className="mt-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary overflow-hidden"
    >
      {/* Header — toggle */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-lia-interactive-hover transition-colors text-left"
      >
        <ClipboardCheck
          className="w-4 h-4 text-wedo-cyan flex-shrink-0"
          aria-hidden="true"
        />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-lia-text-primary">
            Checklist de publicação
          </p>
          <p className="text-xs text-lia-text-secondary">
            {passedChecks}/{totalChecks} verificações
          </p>
        </div>
        {isReady && (
          <span className="px-2 py-0.5 rounded bg-status-success/10 text-status-success text-[10px] font-medium flex-shrink-0">
            Pronto
          </span>
        )}
        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-muted flex-shrink-0 transition-transform",
            expanded && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      {/* Progress bar */}
      <div className="h-1 bg-lia-bg-tertiary">
        <div
          className={cn(
            "h-full transition-[width] duration-300",
            isReady ? "bg-status-success" : "bg-wedo-cyan",
          )}
          style={{
            width: `${totalChecks > 0 ? Math.min(100, (passedChecks / totalChecks) * 100) : 0}%`,
          }}
        />
      </div>

      {/* Expandable body */}
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="review-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="px-3 py-2 space-y-3 border-t border-lia-border-subtle">
              {/* Checklist */}
              {totalChecks > 0 && (
                <div className="space-y-1.5">
                  {Object.entries(checks).map(([key, passed]) => (
                    <div key={key} className="flex items-center gap-2">
                      {passed ? (
                        <CheckCircle
                          className="w-3.5 h-3.5 text-status-success flex-shrink-0"
                          aria-hidden="true"
                        />
                      ) : (
                        <XCircle
                          className="w-3.5 h-3.5 text-status-error flex-shrink-0"
                          aria-hidden="true"
                        />
                      )}
                      <span
                        className={cn(
                          "text-xs",
                          passed
                            ? "text-lia-text-secondary"
                            : "text-lia-text-primary font-medium",
                        )}
                      >
                        {CHECK_LABELS[key] || key}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Ready / Pending banner */}
              {isReady ? (
                <div className="flex items-center gap-2 px-2.5 py-2 rounded-md bg-status-success/10">
                  <CheckCircle
                    className="w-4 h-4 text-status-success flex-shrink-0"
                    aria-hidden="true"
                  />
                  <p className="text-xs font-medium text-status-success">
                    Vaga pronta para publicar!
                  </p>
                </div>
              ) : (
                missing.length > 0 && (
                  <div className="flex items-start gap-2 px-2.5 py-2 rounded-md bg-status-warning/10">
                    <AlertTriangle
                      className="w-4 h-4 text-status-warning flex-shrink-0 mt-0.5"
                      aria-hidden="true"
                    />
                    <p className="text-xs text-status-warning">
                      <span className="font-medium">Pendências:</span>{" "}
                      {missing.join(", ")}
                    </p>
                  </div>
                )
              )}

              {/* Sourcing mode selector */}
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-lia-text-primary">
                  Modo de sourcing
                </p>
                <div className="grid grid-cols-3 gap-1.5">
                  {SOURCING_OPTIONS.map((opt) => {
                    const Icon = opt.icon
                    const selected = sourcingMode === opt.value
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => handleSourcingSelect(opt.value)}
                        className={cn(
                          "flex flex-col items-center gap-1 px-2 py-2 rounded-md border text-center transition-colors",
                          selected
                            ? "border-wedo-cyan bg-wedo-cyan/10"
                            : "border-lia-border-subtle bg-lia-bg-primary hover:bg-lia-interactive-hover",
                        )}
                      >
                        <Icon
                          className={cn(
                            "w-4 h-4",
                            selected
                              ? "text-wedo-cyan"
                              : "text-lia-text-muted",
                          )}
                          aria-hidden="true"
                        />
                        <span
                          className={cn(
                            "text-[11px] font-medium",
                            selected
                              ? "text-wedo-cyan"
                              : "text-lia-text-primary",
                          )}
                        >
                          {opt.label}
                        </span>
                        <span className="text-[9px] text-lia-text-tertiary leading-tight">
                          {opt.description}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Defaults applied */}
              {defaultsApplied.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] text-lia-text-tertiary font-medium uppercase tracking-wider">
                    Defaults aplicados
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {defaultsApplied.map((d, i) => (
                      <span
                        key={i}
                        className="px-1.5 py-0.5 rounded bg-lia-bg-tertiary text-lia-text-secondary text-[10px]"
                      >
                        {d}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Apply defaults button — only when NOT ready */}
            {!isReady && (
              <div className="px-3 pb-3 border-t border-lia-border-subtle pt-2">
                <button
                  type="button"
                  onClick={handleApplyDefaults}
                  className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md text-xs font-medium bg-wedo-cyan text-white hover:bg-wedo-cyan/90 transition-colors"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Aplicar defaults da empresa
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
