"use client"

import React from "react"
import { MapPin } from "lucide-react"
import { CandidateAvatar } from "@/components/candidate-profile/CandidateAvatar"
import { CandidateSkillsList } from "@/components/candidate-profile/CandidateSkillsList"
import { WSIMiniScore } from "@/components/wsi/wsi-scorecard"
import {
  buildCandidateProfileCard,
  type CandidateProfileCardData,
} from "./candidate-card-data"

/**
 * CandidateProfileCard — compact, non-persisted assistant card surfaced in the
 * chat feed when the LIA brings a candidate into focus (search result, etc.).
 *
 * Visual support only: the recruiter keeps deciding via chat. The optional
 * shortcuts render exclusively when the chat surface wires an `onAction`
 * handler — we never show dead buttons.
 */

export type CandidateProfileActionId =
  | "open_profile"
  | "evaluate"
  | "add_to_vacancy"

interface CandidateProfileCardProps {
  /** Raw candidate payload from the chat message metadata. */
  raw: unknown
  /**
   * Optional shortcut handler. When omitted, no action row is rendered so the
   * card stays purely informational (chat remains the primary interface).
   */
  onAction?: (action: CandidateProfileActionId, data: CandidateProfileCardData) => void
}

const ACTIONS: { id: CandidateProfileActionId; label: string }[] = [
  { id: "open_profile", label: "Ver perfil completo" },
  { id: "evaluate", label: "Avaliar" },
  { id: "add_to_vacancy", label: "Adicionar à vaga" },
]

export function CandidateProfileCard({ raw, onAction }: CandidateProfileCardProps) {
  const data = React.useMemo(() => buildCandidateProfileCard(raw), [raw])
  if (!data) return null

  const subtitle = [data.role, data.company].filter(Boolean).join(" • ")

  return (
    <div className="mt-2 rounded-md border border-lia-border-subtle bg-lia-bg-primary p-3 shadow-lia-sm dark:bg-lia-bg-secondary">
      <div className="flex items-start gap-3">
        <CandidateAvatar name={data.name} avatarUrl={data.avatarUrl} size="md" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <p className="truncate text-sm font-medium text-lia-text-primary">
              {data.name}
            </p>
            {data.matchScore !== null && <WSIMiniScore score={data.matchScore} />}
          </div>
          {subtitle && (
            <p className="truncate text-xs text-lia-text-secondary">{subtitle}</p>
          )}
          {data.location && (
            <p className="mt-0.5 flex items-center gap-1 text-xs text-lia-text-tertiary">
              <MapPin className="h-3 w-3 flex-shrink-0" />
              <span className="truncate">{data.location}</span>
            </p>
          )}
        </div>
      </div>

      {data.skills.length > 0 && (
        <div className="mt-3">
          <CandidateSkillsList skills={data.skills} maxVisible={5} />
        </div>
      )}

      {onAction && (
        <div className="mt-3 flex flex-wrap gap-2 border-t border-lia-border-subtle pt-3">
          {ACTIONS.map((action) => (
            <button
              key={action.id}
              type="button"
              onClick={() => onAction(action.id, data)}
              className="rounded-md border border-lia-border-default px-2.5 py-1 text-xs text-lia-text-secondary transition-colors hover:bg-lia-bg-tertiary"
            >
              {action.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
