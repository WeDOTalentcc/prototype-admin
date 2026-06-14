"use client"

import React, { useEffect, useState } from "react"
import { Sparkles } from "lucide-react"

interface SuggestionData {
  value: unknown
  source: string
  confidence: number
  explanation: string
}

interface Props {
  data: Record<string, unknown>
  onUpdate?: (updates: Record<string, unknown>) => void
}

const FIELD_LABELS: Record<string, string> = {
  seniority: "Senioridade",
  work_model: "Modelo de trabalho",
  salary_range: "Faixa salarial",
  department: "Departamento",
}

const SOURCE_LABELS: Record<string, string> = {
  lia_history: "Histórico",
  company_settings: "Empresa",
  imported_ats: "ATS",
  workforce_planning: "Planejamento",
  curated_templates: "Template",
}

function formatSuggestionValue(field: string, value: unknown): string {
  if (value == null) return ""
  if (typeof value === "string") return value
  if (typeof value === "number") return String(value)
  if (typeof value === "object") {
    const o = value as Record<string, unknown>
    if (field === "salary_range") {
      const fmt = (v?: unknown) =>
        v ? `R$ ${Number(v).toLocaleString("pt-BR")}` : ""
      return [fmt(o.min), fmt(o.max)].filter(Boolean).join(" – ")
    }
    return Object.values(o).filter(Boolean).join(", ")
  }
  return String(value)
}

function isFieldEmpty(data: Record<string, unknown>, field: string): boolean {
  const v = data[field]
  if (v == null || v === "") return true
  if (Array.isArray(v)) return v.length === 0
  if (typeof v === "object" && v !== null) {
    const o = v as Record<string, unknown>
    return Object.values(o).every((x) => x == null || x === "")
  }
  return false
}

/** Chips de sugestão baseados no histórico da empresa (WizardDataPriority — W3-D).
 *
 * Busca sugestões para campos ainda vazios via /api/v1/wizard/suggestions/all.
 * Só renderiza quando title ou department está presente. Confiança mínima = 0.6.
 * Clicar aplica o valor via onUpdate e descarta o chip. Falha silenciosa: sem
 * sugestões = sem chips (fail-open, nunca bloqueia o wizard).
 */
export function WizardSuggestionChips({ data, onUpdate }: Props) {
  const [suggestions, setSuggestions] = useState<Record<string, SuggestionData>>({})
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

  const title = data.parsed_title as string | undefined
  const department = data.department as string | undefined
  const seniority = data.seniority as string | undefined

  useEffect(() => {
    if (!title && !department) return

    const ctrl = new AbortController()

    fetch("/api/v1/wizard/suggestions/all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_title: title,
        department,
        seniority,
        fields: ["seniority", "work_model", "salary_range"],
      }),
      signal: ctrl.signal,
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => {
        if (body?.suggestions) {
          setSuggestions(body.suggestions as Record<string, SuggestionData>)
        }
      })
      .catch(() => {
        // fail-open: network/API error → sem chips, wizard segue normalmente
      })

    return () => ctrl.abort()
  }, [title, department, seniority])

  const visibleChips = Object.entries(suggestions).filter(([field, s]) => {
    if (dismissed.has(field)) return false
    if (s.confidence < 0.6) return false
    if (!isFieldEmpty(data, field)) return false
    return Boolean(formatSuggestionValue(field, s.value))
  })

  if (visibleChips.length === 0) return null

  return (
    <div
      data-testid="wizard-suggestion-chips"
      className="space-y-2 pt-2 border-t border-lia-border-subtle"
    >
      <p className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wider flex items-center gap-1">
        <Sparkles className="w-3 h-3 text-wedo-cyan" />
        Sugestões do histórico
      </p>
      <div className="flex flex-wrap gap-2">
        {visibleChips.map(([field, s]) => {
          const label = FIELD_LABELS[field] ?? field
          const valueText = formatSuggestionValue(field, s.value)
          const sourceLabel = SOURCE_LABELS[s.source] ?? s.source

          return (
            <button
              key={field}
              data-testid={`suggestion-chip-${field}`}
              onClick={() => {
                onUpdate?.({ [field]: s.value })
                setDismissed((prev) => new Set([...prev, field]))
              }}
              title={s.explanation}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border border-wedo-cyan/30 bg-wedo-cyan/[0.08] text-wedo-cyan-text hover:bg-wedo-cyan/15 transition-colors cursor-pointer"
            >
              <span className="font-medium">{label}:</span>
              <span>{valueText}</span>
              <span className="text-lia-text-disabled text-micro opacity-70">
                ({sourceLabel})
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
