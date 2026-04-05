"use client"

import React, { useState } from "react"
import { Settings2, Users, MapPin, Briefcase, GraduationCap, Clock, Code, ChevronDown, ChevronUp } from "lucide-react"
import { cn } from "@/lib/utils"

interface Constraint {
  label: string
  value: string
  editable?: boolean
}

interface SourcingConstraint {
  label: string
  value: string
}

interface CalibrationPanelProps {
  data: Record<string, unknown>
  onUpdateData?: (data: Record<string, unknown>) => void
}

export function CalibrationPanel({ data, onUpdateData }: CalibrationPanelProps) {
  const [expandedSection, setExpandedSection] = useState<"constraints" | "sourcing" | null>("constraints")

  const title = (data.title as string) || "Nova Vaga"
  const poolSize = (data.pool_size as number) || 0
  const poolTarget = (data.pool_target as number) || 100
  const poolPercent = Math.min(Math.round((poolSize / poolTarget) * 100), 100)

  const constraints: Constraint[] = (data.constraints as Constraint[]) || [
    { label: "Título", value: title, editable: true },
    { label: "Localização", value: (data.location as string) || "Não definida", editable: true },
    { label: "Experiência", value: (data.experience as string) || "Não definida", editable: true },
    { label: "Educação", value: (data.education as string) || "Não definida", editable: true },
    { label: "Tenure mínimo", value: (data.tenure as string) || "Não definido", editable: true },
  ]

  const sourcingConstraints: SourcingConstraint[] = (data.sourcing_constraints as SourcingConstraint[]) || [
    { label: "Skills requeridas", value: (data.skills as string) || "Não definidas" },
    { label: "Tenure médio", value: (data.avg_tenure as string) || "Não definido" },
  ]

  const constraintIcons: Record<string, React.ReactNode> = {
    "Título": <Briefcase className="w-3.5 h-3.5" />,
    "Localização": <MapPin className="w-3.5 h-3.5" />,
    "Experiência": <Clock className="w-3.5 h-3.5" />,
    "Educação": <GraduationCap className="w-3.5 h-3.5" />,
    "Tenure mínimo": <Clock className="w-3.5 h-3.5" />,
    "Skills requeridas": <Code className="w-3.5 h-3.5" />,
    "Tenure médio": <Clock className="w-3.5 h-3.5" />,
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-lia-border-subtle flex items-center gap-2">
        <Settings2 className="w-4 h-4 text-wedo-cyan" />
        <span className="text-sm font-semibold text-lia-text-primary">Calibração de Vaga</span>
      </div>

      <div className="px-4 py-3 border-b border-lia-border-subtle">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Users className="w-3.5 h-3.5 text-lia-text-secondary" />
            <span className="text-xs text-lia-text-secondary">Pool de candidatos</span>
          </div>
          <span className="text-xs font-medium text-lia-text-primary">{poolSize}/{poolTarget}</span>
        </div>
        <div className="w-full h-2 rounded-full bg-lia-bg-tertiary overflow-hidden">
          <div
            className="h-full rounded-full bg-wedo-cyan transition-all duration-500"
            style={{ width: `${poolPercent}%` }}
          />
        </div>
        <p className="text-micro text-lia-text-disabled mt-1">
          {poolPercent}% do alvo atingido
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <button
          onClick={() => setExpandedSection(expandedSection === "constraints" ? null : "constraints")}
          className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-lia-bg-secondary transition-colors"
        >
          <span className="text-xs font-semibold text-lia-text-primary uppercase tracking-wider">Constraints</span>
          {expandedSection === "constraints" ? (
            <ChevronUp className="w-3.5 h-3.5 text-lia-text-secondary" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-lia-text-secondary" />
          )}
        </button>
        {expandedSection === "constraints" && (
          <div className="px-4 pb-3 space-y-2">
            {constraints.map((c, i) => (
              <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-lia-bg-secondary">
                <div className="mt-0.5 text-lia-text-secondary">{constraintIcons[c.label] || <Settings2 className="w-3.5 h-3.5" />}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-micro text-lia-text-disabled">{c.label}</p>
                  <p className="text-sm text-lia-text-primary truncate">{c.value}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        <button
          onClick={() => setExpandedSection(expandedSection === "sourcing" ? null : "sourcing")}
          className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-lia-bg-secondary transition-colors border-t border-lia-border-subtle"
        >
          <span className="text-xs font-semibold text-lia-text-primary uppercase tracking-wider">Sourcing Criteria</span>
          {expandedSection === "sourcing" ? (
            <ChevronUp className="w-3.5 h-3.5 text-lia-text-secondary" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-lia-text-secondary" />
          )}
        </button>
        {expandedSection === "sourcing" && (
          <div className="px-4 pb-3 space-y-2">
            {sourcingConstraints.map((c, i) => (
              <div key={i} className="flex items-start gap-2 p-2 rounded-lg bg-lia-bg-secondary">
                <div className="mt-0.5 text-lia-text-secondary">{constraintIcons[c.label] || <Code className="w-3.5 h-3.5" />}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-micro text-lia-text-disabled">{c.label}</p>
                  <p className="text-sm text-lia-text-primary">{c.value}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
