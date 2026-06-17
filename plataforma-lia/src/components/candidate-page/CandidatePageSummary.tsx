"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import {
  Linkedin,
  Github,
  Globe,
  Mail,
  Phone,
  MapPin,
  Briefcase,
} from "lucide-react"
import { CandidateAvatar } from "@/components/candidate-profile/CandidateAvatar"
import { CandidateScoreBadge } from "@/components/candidate-profile/CandidateScoreBadge"

type CandidateRecord = {
  name?: string
  id?: string
  candidateId?: string
  avatar_url?: string
  avatar?: string
  email?: string
  phone?: string
  position?: string
  current_title?: string
  headline?: string
  location?: string
  linkedin_url?: string
  linkedinUrl?: string
  github_url?: string
  portfolio_url?: string
  website?: string
  pipeline_stage?: string
  kanban_stage?: string
  current_stage?: string
  stage?: string
  is_hired?: boolean
  hired_job_title?: string | null
  is_blacklisted?: boolean
  liaAnalysis?: { score?: number; fitScore?: number }
  [key: string]: unknown
}

interface CandidatePageSummaryProps {
  candidate: CandidateRecord
  liaScore: number
}

/**
 * Sticky right-rail summary for <CandidatePage mode="page">.
 * Renders compact identity + canonical WSI badge + key contact links.
 *
 * Read-only by design — the header is the action surface; this panel
 * keeps essential context visible while users scroll long tabs (profile,
 * activities, opinions).
 *
 * Pipeline stage chip rendering precedence:
 *   1. Drawer/kanban context: `pipeline_stage` / `kanban_stage` / `stage`
 *   2. Standalone route (global talent pool view): `is_hired` → "Contratado",
 *      `is_blacklisted` → "Bloqueado". Active candidates show no chip
 *      (raw "active" status is noise — recruiter already knows).
 */
export function CandidatePageSummary({
  candidate,
  liaScore,
}: CandidatePageSummaryProps) {
  const name = (candidate.name as string | undefined) ?? ""
  const positionRaw =
    (candidate.position as string | undefined) ??
    (candidate.current_title as string | undefined) ??
    (candidate.headline as string | undefined) ??
    ""
  const location = candidate.location as string | undefined
  const email = candidate.email as string | undefined
  const phone = candidate.phone as string | undefined
  const linkedin =
    (candidate.linkedin_url as string | undefined) ??
    (candidate.linkedin_url as string | undefined)
  const github = candidate.github_url as string | undefined
  const portfolio =
    (candidate.portfolio_url as string | undefined) ??
    (candidate.website as string | undefined)
  const stage =
    (candidate.pipeline_stage as string | undefined) ??
    (candidate.kanban_stage as string | undefined) ??
    (candidate.current_stage as string | undefined) ??
    (candidate.stage as string | undefined)
  const isHired = candidate.is_hired === true
  const hiredJobTitle = candidate.hired_job_title as string | null | undefined
  const isBlacklisted = candidate.is_blacklisted === true
  // Compose global-state chip when no kanban stage is present.
  // hired and blacklisted are not mutually exclusive in the DB schema but
  // blacklisted wins display (signals attention needed).
  const globalStateChip: { label: string; tone: "success" | "danger" } | null =
    isBlacklisted
      ? { label: "Bloqueado", tone: "danger" }
      : isHired
        ? { label: hiredJobTitle ? `Contratado · ${hiredJobTitle}` : "Contratado", tone: "success" }
        : null
  const candidateRef = (candidate.candidateId as string | undefined) ??
    (candidate.id as string | undefined)

  return (
    <Card
      data-testid="candidate-page-summary"
      className="border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-secondary"
    >
      <CardContent className="p-5 space-y-4">
        <div className="flex items-start gap-3">
          <CandidateAvatar
            name={name}
            avatarUrl={
              (candidate.avatar_url as string | undefined) ||
              (candidate.avatar as string | undefined)
            }
            size="lg"
          />
          <div className="min-w-0 flex-1">
            <h2 className="text-sm font-semibold text-lia-text-primary truncate">
              {name || "—"}
            </h2>
            {candidateRef && (
              <p className="text-micro text-lia-text-secondary mt-0.5 truncate">
                ID {candidateRef}
              </p>
            )}
            {positionRaw && (
              <div className="flex items-center gap-1.5 text-xs text-lia-text-secondary mt-1">
                <Briefcase className="w-3 h-3 shrink-0" aria-hidden="true" />
                <span className="truncate">{positionRaw}</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {liaScore > 0 && (
            <CandidateScoreBadge score={liaScore} format="percent" />
          )}
          {stage && (
            <Chip
              variant="neutral"
              density="relaxed"
              className="px-2 py-0.5 text-micro"
              data-testid="summary-stage-chip"
            >
              {stage}
            </Chip>
          )}
          {!stage && globalStateChip && (
            <Chip
              variant={globalStateChip.tone === "success" ? "success" : "danger"}
              density="relaxed"
              className="px-2 py-0.5 text-micro"
              data-testid="summary-global-state-chip"
            >
              {globalStateChip.label}
            </Chip>
          )}
        </div>

        {(email || phone || location) && (
          <div className="space-y-1.5 pt-1 border-t border-lia-border-subtle">
            {location && (
              <div className="flex items-center gap-2 text-xs text-lia-text-secondary pt-1.5">
                <MapPin className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
                <span className="truncate">{location}</span>
              </div>
            )}
            {email && (
              <a
                href={`mailto:${email}`}
                className="flex items-center gap-2 text-xs text-lia-text-secondary hover:text-wedo-coral transition-colors group"
                data-testid="summary-email-link"
              >
                <Mail className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
                <span className="truncate group-hover:underline">{email}</span>
              </a>
            )}
            {phone && (
              <a
                href={`tel:${phone}`}
                className="flex items-center gap-2 text-xs text-lia-text-secondary hover:text-wedo-coral transition-colors group"
                data-testid="summary-phone-link"
              >
                <Phone className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
                <span className="truncate group-hover:underline">{phone}</span>
              </a>
            )}
          </div>
        )}

        {(linkedin || github || portfolio) && (
          <div className="flex items-center gap-1.5 pt-1 border-t border-lia-border-subtle">
            {linkedin && (
              <Button
                asChild
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                aria-label="LinkedIn"
              >
                <a
                  href={linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  data-testid="summary-linkedin-link"
                >
                  <Linkedin className="w-4 h-4" aria-hidden="true" />
                </a>
              </Button>
            )}
            {github && (
              <Button
                asChild
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                aria-label="GitHub"
              >
                <a
                  href={github}
                  target="_blank"
                  rel="noopener noreferrer"
                  data-testid="summary-github-link"
                >
                  <Github className="w-4 h-4" aria-hidden="true" />
                </a>
              </Button>
            )}
            {portfolio && (
              <Button
                asChild
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                aria-label="Portfolio"
              >
                <a
                  href={portfolio}
                  target="_blank"
                  rel="noopener noreferrer"
                  data-testid="summary-portfolio-link"
                >
                  <Globe className="w-4 h-4" aria-hidden="true" />
                </a>
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
