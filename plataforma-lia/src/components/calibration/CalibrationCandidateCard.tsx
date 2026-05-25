"use client"

/**
 * CalibrationCandidateCard — shared presentation component for calibration review.
 *
 * Renders a two-panel layout:
 *   Left:  Candidate profile (avatar, title, competências, experience, education)
 *   Right: Match criteria analysis + action buttons (approve/reject)
 *
 * CalibrationCardModal uses this component via the `fromAgentStudio` adapter.
 * (The legacy `fromExpandedChat` adapter was removed with the deprecated
 * `expanded-chat-modal` surface — Task #860 — A-01.)
 *
 * Design system: Open Sans, rounded-md, 90% mono + 10% WeDo accent (#60BED1).
 */

import React from"react"
import {
  ThumbsUp,
  ThumbsDown,
  Building2,
  GraduationCap,
  Edit3,
  CheckCircle2,
  X,
} from"lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Chip } from "@/components/ui/chip"
import { cn } from"@/lib/utils"
import type { NormalizedCandidate, MatchLevel } from"./types"

// ---------- Match badge config ----------

const MATCH_BADGE: Record<MatchLevel, { label: string; className: string }> = {
  good: {
    label:"Good Match",
    className:"bg-green-100 text-green-800 border-green-200",
  },
  partial: {
    label:"Partial Match",
    className:"bg-amber-100 text-amber-800 border-amber-200",
  },
  no: {
    label:"No Match",
    className:"bg-red-100 text-red-800 border-red-200",
  },
}

// ---------- Props ----------

export interface CalibrationCandidateCardProps {
  candidate: NormalizedCandidate
  onApprove: () => void
  onReject: () => void
  /** Optional slot rendered below the action buttons (comment textarea, extra controls, etc.) */
  actionsFooter?: React.ReactNode
  /** Optional slot rendered above match criteria (e.g. edit criteria button) */
  criteriaHeader?: React.ReactNode
  /** Class name applied to the outermost wrapper */
  className?: string
}

// ---------- Component ----------

export function CalibrationCandidateCard({
  candidate,
  onApprove,
  onReject,
  actionsFooter,
  criteriaHeader,
  className,
}: CalibrationCandidateCardProps) {
  return (
    <div className={cn("flex h-full", className)}>
      {/* ---- Left Panel: Candidate Profile ---- */}
      <div className="w-1/2 overflow-y-auto border-r border-lia-border-subtle p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <Avatar className="w-12 h-12">
            <AvatarImage src={candidate.avatarUrl} />
            <AvatarFallback className="bg-lia-bg-inverse text-white text-sm font-semibold">
              {candidate.name
                .split("")
                .map((n) => n[0])
                .join("")
                .slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <div>
            <h3 className="text-base font-semibold text-lia-text-primary">
              {candidate.name}
            </h3>
            <p className="text-xs text-lia-text-tertiary">{candidate.location}</p>
          </div>
        </div>

        {/* Current role */}
        <div className="mb-4">
          <p className="text-sm font-medium text-lia-text-primary">
            {candidate.currentTitle} at {candidate.currentCompany}
          </p>
        </div>

        {/* Skills */}
        {candidate.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-4">
            {candidate.skills.slice(0, 8).map((skill) => (
              <Chip
                key={skill}
                variant="neutral" muted
                className="bg-lia-bg-tertiary text-lia-text-secondary text-xs rounded-xl border-none"
              >
                {skill}
              </Chip>
            ))}
          </div>
        )}

        {/* Experience stat */}
        <div className="flex gap-6 mb-4 py-3 border-y border-lia-border-subtle">
          <div>
            <p className="text-xs text-lia-text-tertiary uppercase tracking-wide">
              Total experiência
            </p>
            <p className="text-sm font-semibold text-lia-text-primary">
              {candidate.totalExperience}
            </p>
          </div>
        </div>

        {/* Experiences */}
        {candidate.experiences.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
              Experiências
            </h4>
            <div className="space-y-3">
              {candidate.experiences.slice(0, 4).map((exp) => (
                <div key={exp.id} className="flex gap-3">
                  <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary flex items-center justify-center flex-shrink-0">
                    <Building2 className="w-4 h-4 text-lia-text-tertiary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-lia-text-primary">
                        {exp.title}
                      </p>
                      {exp.isPromotion && (
                        <span className="px-2 py-0.5 text-micro font-medium text-[#60BED1] bg-[#60BED1]/10 rounded-full">
                          Promotion
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-lia-text-tertiary">
                      {exp.company} · {exp.period}
                      {exp.durationLabel ? ` · ${exp.durationLabel}` :""}
                    </p>
                    {exp.description && (
                      <p className="text-xs text-lia-text-tertiary mt-1">
                        {exp.description}
                      </p>
                    )}
                    {exp.skills && exp.skills.length > 0 && (
                      <p className="text-xs text-lia-text-tertiary mt-1">
                        Skills: {exp.skills.slice(0, 6).join(" ·")}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Education */}
        {candidate.education.length > 0 && (
          <div className="mt-4">
            <h4 className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-2">
              Educação
            </h4>
            <div className="space-y-2">
              {candidate.education.slice(0, 3).map((edu) => (
                <div key={edu.id} className="flex gap-3">
                  <div className="w-8 h-8 rounded-xl bg-lia-bg-tertiary flex items-center justify-center flex-shrink-0">
                    <GraduationCap className="w-4 h-4 text-lia-text-tertiary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-lia-text-primary">
                      {edu.degree} — {edu.field}
                    </p>
                    <p className="text-xs text-lia-text-tertiary">
                      {edu.institution}
                      {edu.period ? ` · ${edu.period}` :""}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ---- Right Panel: Match Criteria + Actions ---- */}
      <div className="w-1/2 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6">
          {/* Optional header (edit criteria, etc.) */}
          {criteriaHeader ?? (
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-lia-text-primary">
                Por que combinamos este perfil
              </h3>
            </div>
          )}

          {/* Match criteria list */}
          <div className="space-y-4">
            {candidate.matchCriteria.map((mc) => {
              const badge = MATCH_BADGE[mc.match]
              return (
                <div key={mc.id} className="space-y-1">
                  <Chip
                    variant="neutral"
                    className={cn("text-xs rounded-md", badge.className)}
                  >
                    {badge.label}
                  </Chip>
                  <p className="text-sm font-medium text-lia-text-primary">
                    {mc.criterion}
                  </p>
                  <p className="text-xs text-lia-text-tertiary leading-relaxed">
                    {mc.explanation}
                  </p>
                </div>
              )
            })}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex-shrink-0 p-6 border-t border-lia-border-subtle space-y-3">
          <div className="flex gap-2">
            <button
              onClick={onApprove}
              className="flex-1 py-2.5 px-3 bg-lia-bg-inverse text-white rounded-xl font-medium text-sm hover:bg-lia-bg-inverse transition-colors flex items-center justify-center gap-1.5"
            >
              <CheckCircle2 className="w-4 h-4" />
              Aprovar
            </button>
            <button
              onClick={onReject}
              className="flex-1 py-2.5 px-3 bg-white text-red-600 border border-red-300 rounded-xl font-medium text-sm hover:bg-red-50 transition-colors flex items-center justify-center gap-1.5"
            >
              <X className="w-4 h-4" />
              Reprovar
            </button>
          </div>

          {/* Optional footer slot (comment, skip, progress dots, etc.) */}
          {actionsFooter}
        </div>
      </div>
    </div>
  )
}
