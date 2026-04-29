"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import { ChevronDown, ChevronUp, User } from "lucide-react"

// --- Types ---

interface Criterion {
  icon: string
  label: string
  value: string
  quality: "good" | "warning" | "poor"
}

interface CandidateExperience {
  role: string
  company: string
  dates: string
}

interface CandidateProfile {
  id: string
  name: string
  avatar?: string
  yearsExp: number
  location: string
  experiences: CandidateExperience[]
  criteriaMatched: number
}

export interface WizardCalibrationPanelProps {
  vacancyTitle: string
  onFeedback: (candidateId: string, approved: boolean) => void
  onFinish: () => void
  candidates?: CandidateProfile[]
  poolCount?: number
  mustHaveCriteria?: Criterion[]
  sourcingCriteria?: Criterion[]
}

// --- Helpers ---

function qualityColor(quality: Criterion["quality"]): string {
  if (quality === "good") return "text-green-600"
  if (quality === "warning") return "text-amber-500"
  return "text-red-500"
}

function CriteriaTable({
  title,
  criteria,
}: {
  title: string
  criteria: Criterion[]
}) {
  if (criteria.length === 0) return null
  return (
    <div className="mb-4">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th
              colSpan={5}
              className="text-left text-xs font-semibold text-muted-foreground uppercase tracking-wide pb-2"
            >
              {title}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {criteria.map((c) => (
            <tr key={c.label} className="hover:bg-muted/30 transition-colors">
              <td className="py-2 pr-2 text-base w-6">{c.icon}</td>
              <td className="py-2 pr-2 font-medium text-foreground">{c.label}</td>
              <td className="py-2 pr-2 text-muted-foreground">{c.value}</td>
              <td className="py-2 pr-2 w-4">
                <span className={cn("text-lg leading-none", qualityColor(c.quality))}>●</span>
              </td>
              <td className="py-2 text-right">
                <button className="text-primary text-xs hover:underline">+ Add</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function CandidateCard({
  candidate,
  mustHaveCount,
  onFeedback,
}: {
  candidate: CandidateProfile
  mustHaveCount: number
  onFeedback: (id: string, approved: boolean) => void
}) {
  return (
    <div className="rounded-lg border border-border p-4 space-y-2 bg-card">
      {/* Profile row */}
      <div className="flex items-center gap-3">
        {candidate.avatar ? (
          <img
            src={candidate.avatar}
            alt={candidate.name}
            className="w-10 h-10 rounded-full object-cover flex-shrink-0"
          />
        ) : (
          <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
            <User className="w-5 h-5 text-muted-foreground" />
          </div>
        )}
        <div className="min-w-0">
          <p className="font-medium text-foreground truncate">{candidate.name}</p>
          <p className="text-sm text-muted-foreground">
            {candidate.yearsExp}+ anos · {candidate.location}
          </p>
        </div>
      </div>

      {/* Experiences */}
      {candidate.experiences.length > 0 && (
        <div className="space-y-1">
          {candidate.experiences.slice(0, 3).map((e) => (
            <div key={`${e.company}-${e.dates}`} className="text-xs text-muted-foreground">
              {e.role} @ {e.company} ({e.dates})
            </div>
          ))}
        </div>
      )}

      {/* Footer row */}
      <div className="flex items-center justify-between pt-2 border-t border-border">
        <span className="text-xs text-muted-foreground">
          {candidate.criteriaMatched} de {mustHaveCount} critérios
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => onFeedback(candidate.id, false)}
            className="px-3 py-1 rounded border border-border text-sm hover:bg-destructive/10 transition-colors"
            aria-label={`Rejeitar ${candidate.name}`}
          >
            👎
          </button>
          <button
            onClick={() => onFeedback(candidate.id, true)}
            className="px-3 py-1 rounded border border-border text-sm hover:bg-primary/10 transition-colors"
            aria-label={`Aprovar ${candidate.name}`}
          >
            👍
          </button>
        </div>
      </div>
    </div>
  )
}

// --- Main Component ---

/**
 * WizardCalibrationPanel (Tezi-style) — Onda 26-27 E.2
 *
 * Criteria view: shows must-have and sourcing criteria tables.
 * Candidates view: shows candidate cards with approve/reject buttons.
 * Toggle between views via the header button.
 */
export function WizardCalibrationPanel({
  vacancyTitle,
  onFeedback,
  onFinish,
  candidates = [],
  poolCount = 0,
  mustHaveCriteria = [],
  sourcingCriteria = [],
}: WizardCalibrationPanelProps) {
  const [criteriaOpen, setCriteriaOpen] = useState(true)

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-3 border-b border-border space-y-1">
        <h2 className="text-base font-semibold text-foreground truncate">{vacancyTitle}</h2>
        <p className="text-sm text-muted-foreground">
          Revisar {candidates.length} candidatos · {poolCount.toLocaleString("pt-BR")}+ compatíveis
        </p>
        <button
          onClick={() => setCriteriaOpen((v) => !v)}
          className="flex items-center gap-1 text-xs text-primary hover:underline transition-colors"
        >
          {criteriaOpen ? "Ocultar critérios" : "Ver critérios"}
          {criteriaOpen ? (
            <ChevronUp className="w-3 h-3" />
          ) : (
            <ChevronDown className="w-3 h-3" />
          )}
        </button>
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {criteriaOpen ? (
          /* Criteria tables */
          <>
            <CriteriaTable title="Must-Have Criteria" criteria={mustHaveCriteria} />
            <CriteriaTable title="Sourcing Criteria" criteria={sourcingCriteria} />
            {mustHaveCriteria.length === 0 && sourcingCriteria.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">
                Nenhum critério definido ainda.
              </p>
            )}
          </>
        ) : (
          /* Candidate cards */
          <>
            {candidates.length > 0 ? (
              candidates.map((c) => (
                <CandidateCard
                  key={c.id}
                  candidate={c}
                  mustHaveCount={mustHaveCriteria.length}
                  onFeedback={onFeedback}
                />
              ))
            ) : (
              <div className="text-center py-8 space-y-2">
                <div className="w-5 h-5 mx-auto border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-sm text-muted-foreground">Aguardando candidatos...</p>
              </div>
            )}
          </>
        )}
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 flex items-center justify-between px-4 py-3 border-t border-border bg-background">
        <span className="font-semibold text-sm text-foreground">
          Pool: {poolCount.toLocaleString("pt-BR")}+
        </span>
        <div className="flex gap-2">
          <button
            onClick={onFinish}
            className="px-4 py-2 rounded bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Finalizar Calibração
          </button>
        </div>
      </div>
    </div>
  )
}
