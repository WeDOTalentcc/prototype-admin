"use client"

import React, { useState } from "react"
import { cn } from "@/lib/utils"
import {
  User, CheckCircle, XCircle, Target, ThumbsUp, ThumbsDown, Users,
  ChevronDown, ChevronUp, Plus, Award, Filter, Minus, ExternalLink,
  Briefcase, GraduationCap, type LucideIcon,
} from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import type { CalibrationData, CalibrationCandidate } from "../wizard-types"

// Onda 33 — Local UI type for criteria tables. Backend currently emits only
// `{label, type}` (see CriterionItem below); the optional fields here are
// rendered when present and fall back to defaults otherwise.
// TODO: aguardar backend emitir constraints reais com field/value/quality.
interface CriterionItem {
  label: string
  type: "must_have" | "sourcing"
  field?: string
  value?: string
  quality?: "good" | "warning" | "poor"
}

const QUALITY_DOT: Record<NonNullable<CriterionItem["quality"]>, string> = {
  good: "text-status-success",
  warning: "text-status-warning",
  poor: "text-status-error",
}

/** Formata número de meses em representação legível (ex: "1a 4m", "8m"). */
function formatMonths(months: number): string {
  if (months < 12) return `${months}m`
  const years = Math.floor(months / 12)
  const rem = months % 12
  return rem > 0 ? `${years}a ${rem}m` : `${years}a`
}

interface Props {
  data: Record<string, unknown>
  onApprove?: () => void
  onReject?: () => void
}

/**
 * CalibrationPanel — present candidates for calibration.
 * Enforces minimum 3 profile approvals before allowing advancement.
 * Shows pool counter + Must-haves vs Sourcing Constraints sections.
 */
export function CalibrationPanel({ data, onApprove, onReject }: Props) {
  const d = data as unknown as CalibrationData & {
    pool_count?: number
    criteria?: CriterionItem[]
  }
  const candidates = d.candidates || []
  const threshold = d.threshold || 3
  const approvedCount = d.approved_count || 0
  const canAdvance = approvedCount >= threshold
  const poolCount = d.pool_count ?? null
  const mustHaves = d.criteria?.filter((c) => c.type === "must_have") ?? []
  const sourcingConstraints = d.criteria?.filter((c) => c.type === "sourcing") ?? []
  // Onda 33 — criteria toggle (open by default when there are criteria to show)
  const hasCriteria = mustHaves.length > 0 || sourcingConstraints.length > 0
  const [criteriaOpen, setCriteriaOpen] = useState(hasCriteria)

  const handleApproveCandidate = (candidateId: string, comment?: string) => {
    window.dispatchEvent(new CustomEvent("lia:wizard-edit-question", {
      detail: { type: "calibration_approve", candidateId, reason: comment },
    }))
  }

  const handleRejectCandidate = (candidateId: string, comment?: string) => {
    window.dispatchEvent(new CustomEvent("lia:wizard-edit-question", {
      detail: { type: "calibration_reject", candidateId, reason: comment },
    }))
  }

  const handleSkipCandidate = (candidateId: string) => {
    window.dispatchEvent(new CustomEvent("lia:wizard-edit-question", {
      detail: { type: "calibration_skip", candidateId },
    }))
  }

  return (
    <div className="flex flex-col">
      {/* Progress header */}
      <div className="px-4 py-2.5 border-b border-lia-border-subtle">
        <div className="flex items-center justify-between">
          <span className="text-xs text-lia-text-secondary">
            Calibração: {approvedCount}/{threshold} perfis
          </span>
          <div className="flex items-center gap-2">
            {/* Pool counter — updates as user gives feedback */}
            {poolCount !== null && (
              <span className="flex items-center gap-1 text-[10px] text-wedo-cyan-text font-medium">
                <Users className="w-3 h-3" aria-hidden="true" />
                {poolCount.toLocaleString("pt-BR")} compatíveis
              </span>
            )}
            {d.complete && (
              <span className="px-2 py-0.5 rounded bg-status-success/10 text-status-success text-[10px] font-medium">
                Completa
              </span>
            )}
          </div>
        </div>
        {/* Progress bar */}
        <div className="mt-1.5 h-1.5 rounded-full bg-lia-bg-tertiary overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-[width] duration-300",
              canAdvance ? "bg-status-success" : "bg-wedo-cyan"
            )}
            style={{ width: `${Math.min(100, (approvedCount / threshold) * 100)}%` }}
          />
        </div>
        {!canAdvance && (
          <p className="text-[10px] text-status-warning mt-1">
            Avalie pelo menos {threshold} perfis para continuar
          </p>
        )}
        {/* Onda 33 — criteria toggle (only shown when there ARE criteria) */}
        {hasCriteria && (
          <button
            onClick={() => setCriteriaOpen((v) => !v)}
            aria-expanded={criteriaOpen}
            aria-controls="calibration-criteria-tables"
            data-testid="calibration-criteria-toggle"
            className="mt-2 inline-flex items-center gap-1 text-[11px] font-medium text-wedo-cyan-text hover:underline transition-colors motion-reduce:transition-none"
          >
            {criteriaOpen ? "Ocultar critérios" : "Mostrar critérios"}
            {criteriaOpen ? (
              <ChevronUp className="w-3 h-3" aria-hidden="true" />
            ) : (
              <ChevronDown className="w-3 h-3" aria-hidden="true" />
            )}
          </button>
        )}
      </div>

      {/* Onda 33 — Criteria tables (Must-have + Sourcing). Replaces the
          previous chip-based overview. Only rendered when toggle is open. */}
      {hasCriteria && criteriaOpen && (
        <div
          id="calibration-criteria-tables"
          className="px-4 py-2.5 border-b border-lia-border-subtle space-y-3"
        >
          <CriteriaTable
            title="Must-haves (eliminatórios)"
            criteria={mustHaves}
            defaultIcon={Award}
          />
          <CriteriaTable
            title="Preferências (sourcing)"
            criteria={sourcingConstraints}
            defaultIcon={Filter}
          />
        </div>
      )}

      {/* Candidate cards */}
      <div className="px-4 py-3 space-y-2">
        {candidates.map((c) => (
          <CandidateCard
            key={c.id}
            candidate={c}
            onApproveCandidate={handleApproveCandidate}
            onRejectCandidate={handleRejectCandidate}
            onSkipCandidate={handleSkipCandidate}
          />
        ))}
        {candidates.length === 0 && (
          <div className="text-center py-4">
            <div className="w-5 h-5 mx-auto mb-2 border-2 border-wedo-cyan border-t-transparent rounded-full animate-spin" />
            <p className="text-xs text-lia-text-tertiary">
              Aguardando candidatos para calibracao...
            </p>
          </div>
        )}
      </div>

      {/* Advance footer */}
      {candidates.length > 0 && (
        <div className="flex-shrink-0 px-4 py-3 border-t border-lia-border-subtle bg-lia-bg-primary">
          <button
            onClick={onApprove}
            disabled={!canAdvance}
            className={cn(
              "w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
              canAdvance
                ? "bg-wedo-cyan text-white hover:bg-wedo-cyan/90"
                : "bg-lia-bg-tertiary text-lia-text-disabled cursor-not-allowed"
            )}
          >
            <CheckCircle className="w-4 h-4" />
            {canAdvance ? "Calibracao completa — Avancar" : `Faltam ${Math.max(0, (threshold ?? 0) - (approvedCount ?? 0))} perfis`}
          </button>
        </div>
      )}
    </div>
  )
}

function CandidateCard({
  candidate,
  onApproveCandidate,
  onRejectCandidate,
  onSkipCandidate,
}: {
  candidate: CalibrationCandidate
  onApproveCandidate: (id: string, comment?: string) => void
  onRejectCandidate: (id: string, comment?: string) => void
  onSkipCandidate: (id: string) => void
}) {
  const decided = !!candidate.decision
  const [comment, setComment] = useState("")
  const [profileOpen, setProfileOpen] = useState(false)

  return (
    <div className={cn(
      "rounded-md border overflow-hidden",
      decided ? "border-lia-border-subtle/50 opacity-70" : "border-lia-border-subtle",
    )}>
      <div className="flex items-start gap-2.5 px-3 py-2.5">
        {/* Avatar — usa avatar_url se disponível */}
        <div className="w-8 h-8 rounded-full bg-lia-bg-secondary flex items-center justify-center flex-shrink-0 overflow-hidden">
          {candidate.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={candidate.avatar_url} alt={candidate.name} className="w-full h-full object-cover" />
          ) : (
            <User className="w-4 h-4 text-lia-text-disabled" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <p className="text-sm font-medium text-lia-text-primary truncate">
              {candidate.name}
            </p>
            {candidate.linkedin_url && (
              <a
                href={candidate.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[10px] text-wedo-cyan-text hover:underline flex-shrink-0"
                aria-label="Abrir LinkedIn"
              >
                in
              </a>
            )}
          </div>
          <p className="text-xs text-lia-text-secondary truncate">
            {candidate.current_title} @ {candidate.current_company}
          </p>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="flex items-center gap-1 text-[10px] text-wedo-cyan-text font-medium">
              <Target className="w-3 h-3" />
              Match: {Math.round(candidate.match_score * 100)}%
            </span>
            {/* Tenure stats */}
            {candidate.tenure_stats && (
              <span className="flex items-center gap-1 text-[10px] text-lia-text-tertiary">
                {candidate.tenure_stats.current_months !== undefined && (
                  <span title="Tempo no cargo atual">
                    Cargo: {formatMonths(candidate.tenure_stats.current_months)}
                  </span>
                )}
                {candidate.tenure_stats.avg_months !== undefined && (
                  <span title="Média de tempo por empresa" className="ml-1">
                    Média: {formatMonths(candidate.tenure_stats.avg_months)}
                  </span>
                )}
              </span>
            )}
          </div>
          {/* Auto-tags */}
          {candidate.auto_tags && candidate.auto_tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {candidate.auto_tags.map((tag, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 rounded bg-lia-bg-tertiary text-lia-text-secondary text-[10px]"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {decided && (
          candidate.decision === "approved" ? (
            <CheckCircle className="w-5 h-5 text-status-success flex-shrink-0" />
          ) : candidate.decision === "skipped" ? (
            <Minus className="w-5 h-5 text-lia-text-disabled flex-shrink-0" />
          ) : (
            <XCircle className="w-5 h-5 text-status-error flex-shrink-0" />
          )
        )}
      </div>

      {/* Match criteria com reasoning inline */}
      {candidate.match_criteria?.length > 0 && (
        <div className="px-3 pb-2 space-y-1">
          <div className="flex flex-wrap gap-1">
            {candidate.match_criteria.map((mc, i) => (
              <div key={i} className="flex flex-col gap-0.5">
                <span
                  className={cn(
                    "px-1.5 py-0.5 rounded text-[10px]",
                    mc.met ? "bg-status-success/10 text-status-success" : "bg-status-error/10 text-status-error",
                  )}
                >
                  {mc.criterion}
                </span>
                {mc.explanation && (
                  <span className="text-[9px] text-lia-text-tertiary leading-tight max-w-[160px]">
                    {mc.explanation}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Campo de comentário — disponível para approve e reject */}
      {!decided && (
        <div className="px-3 pb-2">
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Por que gostou ou não deste perfil? (opcional)"
            rows={2}
            className="w-full text-[11px] text-lia-text-primary placeholder:text-lia-text-disabled bg-lia-bg-secondary border border-lia-border-subtle rounded px-2 py-1.5 resize-none focus:outline-none focus:ring-1 focus:ring-wedo-cyan/40"
          />
        </div>
      )}

      {/* Action buttons — only if not decided */}
      {!decided && (
        <div className="flex border-t border-lia-border-subtle">
          <button
            onClick={() => onRejectCandidate(candidate.id, comment || undefined)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-status-error hover:bg-status-error/5 transition-colors"
          >
            <ThumbsDown className="w-3.5 h-3.5" />
            Rejeitar
          </button>
          <div className="w-px bg-lia-border-subtle" />
          <button
            onClick={() => onSkipCandidate(candidate.id)}
            className="flex items-center justify-center gap-1.5 px-2.5 py-2 text-xs text-lia-text-tertiary hover:bg-lia-interactive-hover transition-colors"
            title="Pular este candidato"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
          <div className="w-px bg-lia-border-subtle" />
          <button
            onClick={() => onApproveCandidate(candidate.id, comment || undefined)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-status-success hover:bg-status-success/5 transition-colors"
          >
            <ThumbsUp className="w-3.5 h-3.5" />
            Aprovar
          </button>
        </div>
      )}

      {/* "Ver perfil completo" — link que abre modal com experiências + educação */}
      {(candidate.experiences?.length || candidate.education?.length) && (
        <button
          type="button"
          onClick={() => setProfileOpen(true)}
          className="w-full flex items-center justify-center gap-1 px-3 py-1.5 text-[11px] text-lia-text-tertiary hover:text-wedo-cyan transition-colors border-t border-lia-border-subtle/50"
        >
          <ExternalLink className="w-3 h-3" aria-hidden="true" />
          Ver perfil completo
        </button>
      )}

      {/* Full profile dialog */}
      <Dialog open={profileOpen} onOpenChange={setProfileOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {candidate.name}
              <span className="text-sm font-normal text-lia-text-secondary">
                · {candidate.current_title} @ {candidate.current_company}
              </span>
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-5 pt-2">
            {/* Experiências */}
            {candidate.experiences && candidate.experiences.length > 0 && (
              <div>
                <h4 className="flex items-center gap-1.5 text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3">
                  <Briefcase className="w-3.5 h-3.5" />
                  Experiências
                </h4>
                <div className="space-y-3">
                  {candidate.experiences.map((exp, i) => (
                    <div key={i} className="border-l-2 border-lia-border-subtle pl-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm font-medium text-lia-text-primary">{exp.title}</p>
                          <p className="text-xs text-lia-text-secondary">{exp.company}</p>
                        </div>
                        <div className="text-right flex-shrink-0 ml-2">
                          <p className="text-[11px] text-lia-text-tertiary">
                            {exp.start_date} – {exp.end_date ?? "Atual"}
                          </p>
                          {exp.duration_label && (
                            <p className="text-[11px] text-lia-text-disabled">{exp.duration_label}</p>
                          )}
                        </div>
                      </div>
                      {exp.description && (
                        <p className="text-xs text-lia-text-secondary mt-1 leading-relaxed line-clamp-3">
                          {exp.description}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Educação */}
            {candidate.education && candidate.education.length > 0 && (
              <div>
                <h4 className="flex items-center gap-1.5 text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3">
                  <GraduationCap className="w-3.5 h-3.5" />
                  Formação
                </h4>
                <div className="space-y-2">
                  {candidate.education.map((edu, i) => (
                    <div key={i} className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium text-lia-text-primary">
                          {edu.degree} — {edu.field}
                        </p>
                        <p className="text-xs text-lia-text-secondary">{edu.institution}</p>
                      </div>
                      {edu.period && (
                        <p className="text-[11px] text-lia-text-tertiary flex-shrink-0 ml-2">{edu.period}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

/**
 * Onda 33 — CriteriaTable
 *
 * Renders one criteria group (Must-have or Sourcing) as a 5-column table:
 * icon · field · value · quality dot · "+ Add". Falls back gracefully when
 * the backend payload only has `{label, type}` (current state): field uses
 * the label, value renders an em-dash, quality defaults to good.
 */
function CriteriaTable({
  title,
  criteria,
  defaultIcon: DefaultIcon,
}: {
  title: string
  criteria: CriterionItem[]
  defaultIcon: LucideIcon
}) {
  if (criteria.length === 0) return null
  return (
    <div>
      <p className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-1">
        {title}
      </p>
      <table className="w-full text-xs">
        <tbody className="divide-y divide-lia-border-subtle">
          {criteria.map((c, i) => {
            const quality = c.quality ?? "good"
            return (
              <tr key={i} className="hover:bg-lia-bg-secondary/50 transition-colors">
                <td className="py-1.5 pr-2 w-6">
                  <DefaultIcon className="w-3.5 h-3.5 text-lia-text-secondary" aria-hidden="true" />
                </td>
                <td className="py-1.5 pr-2 font-medium text-lia-text-primary">
                  {c.field ?? c.label}
                </td>
                <td className="py-1.5 pr-2 text-lia-text-secondary">
                  {c.value ?? "—"}
                </td>
                <td className="py-1.5 pr-2 w-4 text-center">
                  <span
                    className={cn("text-base leading-none", QUALITY_DOT[quality])}
                    aria-label={`Qualidade ${quality}`}
                  >
                    ●
                  </span>
                </td>
                <td className="py-1.5 text-right">
                  <button
                    type="button"
                    className="inline-flex items-center gap-0.5 text-[10px] text-wedo-cyan-text hover:underline"
                    aria-label={`Adicionar critério a ${title}`}
                  >
                    <Plus className="w-3 h-3" aria-hidden="true" />
                    Add
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
