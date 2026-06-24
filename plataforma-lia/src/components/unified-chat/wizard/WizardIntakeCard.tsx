"use client"

import React, { useState } from "react"
import { ChevronDown, ClipboardList, ExternalLink } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"
import { useToolSurface } from "@/contexts/ToolSurfaceContext"
import { STAGE_LABELS } from "./wizard-types"

interface IntakeField {
  label: string
  value: string | undefined | null
}

interface WizardIntakeCardProps {
  data: Record<string, unknown>
}

export function WizardIntakeCard({ data }: WizardIntakeCardProps) {
  const surface = useToolSurface()
  const [expanded, setExpanded] = useState(surface === "panel")

  const title = (data.parsed_title as string) ?? (data.title as string) ?? null
  const seniority = (data.parsed_seniority as string) ?? (data.seniority as string) ?? null
  const model = (data.parsed_model as string) ?? (data.work_model as string) ?? null
  const department = (data.parsed_department as string) ?? (data.department as string) ?? null
  const manager = (data.parsed_manager as string) ?? (data.hiring_manager as string) ?? null
  const message = data.message as string | undefined

  const fields: IntakeField[] = [
    { label: "Cargo", value: title },
    { label: "Senioridade", value: seniority },
    { label: "Modelo", value: model },
    { label: "Departamento", value: department },
    { label: "Gestor", value: manager },
  ]

  const filledFields = fields.filter((f) => f.value)
  const filledCount = filledFields.length

  if (filledCount === 0 && !message) return null

  return (
    <div
      role="region"
      aria-label="Ficha da vaga"
      className={cn(
        "mt-2 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary",
        surface !== "panel" && "overflow-hidden",
      )}
    >
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-lia-interactive-hover transition-colors text-left"
      >
        <ClipboardList className="w-4 h-4 text-wedo-cyan flex-shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-lia-text-primary truncate">
            {title ?? "Ficha da vaga"}
          </p>
          <p className="text-xs text-lia-text-secondary">
            {filledCount}/{fields.length} campos preenchidos
          </p>
        </div>
        <ChevronDown
          className={cn(
            "w-4 h-4 text-lia-text-muted flex-shrink-0 transition-transform",
            expanded && "rotate-180",
          )}
          aria-hidden="true"
        />
      </button>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="intake-body"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18, ease: "easeInOut" }}
            className="overflow-hidden border-t border-lia-border-subtle px-3 py-3 space-y-2"
          >
            {filledFields.map((f) => (
              <div key={f.label} className="flex items-baseline gap-2">
                <span className="text-[11px] text-lia-text-tertiary w-24 flex-shrink-0">
                  {f.label}
                </span>
                <span className="text-xs text-lia-text-primary">{f.value}</span>
              </div>
            ))}

            {(data.is_affirmative as boolean) && (
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-wedo-purple/10 text-wedo-purple-text font-medium">
                  Vaga afirmativa
                </span>
                {(data.affirmative_criteria_primary as string) && (
                  <span className="text-[10px] text-lia-text-secondary">
                    {data.affirmative_criteria_primary as string}
                  </span>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
