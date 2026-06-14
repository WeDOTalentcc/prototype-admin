"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Eye, ChevronsLeftRight, MapPin,
} from "lucide-react"
import { CandidateChatPopover } from "@/components/shared/CandidateChatPopover"
import { SearchFeedbackButtons } from "@/components/search/SearchFeedbackButtons"
import { textStyles } from "@/lib/design-tokens"
import type { Candidate } from "@/components/pages/candidates/types"
import type { RevealedContacts } from "@/stores/candidates-store"
import { renderSourceCell } from "./cells/SourceCell"
import { renderMatchScoreCell, renderLiaScoreCell } from "./cells/ScoreCells"
import { renderEmailCell, renderPhoneCell, renderLinkedinCell, renderGithubCell, renderPortfolioCell } from "./cells/ContactCells"
import { renderPearchInsightCell } from "./cells/PearchCells"

type TranslateFn = (key: string, values?: Record<string, unknown>) => string

export interface CellRendererDeps {
  searchFeedbacks: Record<string, "like" | "dislike">
  revealedContacts: RevealedContacts
  searchQuery: string
  viewedCandidateIds: Set<string>
  expandedRows: Set<string>
  onSearchFeedbackChange: (
    candidateId: string,
    candidateName: string,
    feedback: "like" | "dislike" | null
  ) => void
  onRevealContact: (candidate: Candidate, type: "email" | "phone") => void
  onToggleExpandedRow: (candidateId: string) => void
  t?: TranslateFn
  contactValidity?: Record<string, { email_valid?: boolean | null; email_reason?: string | null; phone_valid?: boolean | null }>
}

export function createCellRenderer(deps: CellRendererDeps) {
  const {
    searchFeedbacks,
    revealedContacts,
    searchQuery,
    viewedCandidateIds,
    expandedRows,
    onSearchFeedbackChange,
    onRevealContact,
    onToggleExpandedRow,
    t,
    contactValidity,
  } = deps

  const formatDate = (date: string | undefined) => {
    if (!date) return t ? t('na') : "N/A"
    return new Date(date).toLocaleDateString("pt-BR")
  }

  const formatCurrency = (value: number | undefined, currency?: string) => {
    if (!value) return t ? t('na') : "N/A"
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: currency || "BRL",
    }).format(value)
  }

  const formatBoolean = (value: boolean | undefined) => {
    if (value === undefined) return t ? t('na') : "N/A"
    if (t) return value ? t('yes') : t('no')
    return value ? "Sim" : "Não"
  }

  const formatArray = (arr: string[] | undefined) => {
    if (!arr || arr.length === 0) return t ? t('na') : "N/A"
    return arr.slice(0, 3).join(",") + (arr.length > 3 ? ` (+${arr.length - 3})` : "")
  }

  const formatLanguages = (langs: Record<string, string> | undefined) => {
    if (!langs) return t ? t('na') : "N/A"
    const entries = Object.entries(langs)
    if (entries.length === 0) return t ? t('na') : "N/A"
    return entries
      .slice(0, 2)
      .map(([lang, level]) => `${lang}: ${level}`)
      .join(",")
  }

  return function renderCellValue(
    candidate: Candidate,
    columnId: string
  ): React.ReactNode {
    switch (columnId) {
      case "checkbox":
      case "acoes":
      case "actions":
        return null

      case "feedback": {
        const hasFeedback = !!searchFeedbacks[candidate.id]
        return (
          <div
            className={cn("flex items-center justify-center transition-opacity duration-200",
              hasFeedback ? "opacity-100" : "opacity-0 group-hover:opacity-100"
            )}
          >
            <SearchFeedbackButtons
              candidateId={candidate.id}
              candidateName={candidate.name}
              candidateScore={
                (candidate as unknown as Record<string, unknown>).match_score as number || candidate.lia_score || candidate.score
              }
              initialFeedback={searchFeedbacks[candidate.id] || null}
              onFeedbackChange={(id, fb) => onSearchFeedbackChange(candidate.id, candidate.name, fb)}
              size="sm"
              alwaysVisible={hasFeedback}
            />
          </div>
        )
      }

      case "source":
        return renderSourceCell(candidate, t)

      case "enrichment_source": {
        if (candidate.is_enriching) {
          return (
            <Chip variant="neutral" muted className="text-micro px-1.5 py-0.5 bg-status-warning/15 text-status-warning animate-pulse">
              {t ? t('enriching') : "Enriquecendo..."}
            </Chip>
          )
        }
        if (!candidate.enrichment_source) return <span className="text-xs text-lia-text-tertiary">—</span>
        const esrc = String(candidate.enrichment_source).toLowerCase()
        const eConfig = esrc === 'apify'
          ? { label: 'Apify', cls: 'bg-wedo-orange/15 text-wedo-orange-text' }
          : esrc === 'pearch'
            ? { label: 'Pearch', cls: 'bg-wedo-cyan/15 text-wedo-cyan-text' }
            : esrc === 'local'
              ? { label: 'Local', cls: 'bg-stone-400/15 text-stone-500' }
              : { label: candidate.enrichment_source, cls: 'bg-lia-bg-tertiary text-lia-text-secondary' }
        return (
          <Chip variant="neutral" muted className={`text-micro px-1.5 py-0.5 ${eConfig.cls}`}>
            {eConfig.label}
          </Chip>
        )
      }

      case "match_score":
        return renderMatchScoreCell(candidate, searchQuery)

      case "name": {
        const isCandidateViewed = viewedCandidateIds.has(candidate.id)
        return (
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <Avatar className="w-9 h-9">
                <AvatarImage
                  src={
                    candidate.avatar_url ||
                    candidate.avatar ||
                    (candidate as unknown as Record<string, unknown>).photo_url as string ||
                    (candidate as unknown as Record<string, unknown>).picture_url as string ||
                    (candidate as unknown as Record<string, unknown>).photoUrl as string ||
                    (candidate as unknown as Record<string, unknown>).profile_picture as string
                  }
                  alt={candidate.name}
                />
                <AvatarFallback className="text-sm font-medium bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary">
                  {candidate.name
                    .split("")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()}
                </AvatarFallback>
              </Avatar>
              {isCandidateViewed && (
                <div
                  className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-lia-border-default rounded-full flex items-center justify-center border border-white"
                  title={t ? t('profileViewed') : "Perfil visualizado"}
                >
                  <Eye className="w-2.5 h-2.5 text-white" />
                </div>
              )}
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5 group/name">
                <CandidateChatPopover candidateId={candidate.id} candidateName={candidate.name}>
                  <span
                    className="font-medium text-lia-text-primary truncate text-xs"
                    data-lia-entity-type="candidate"
                    data-lia-entity-id={candidate.id}
                    data-lia-entity-label={candidate.name}
                  >
                    {candidate.name}
                  </span>
                </CandidateChatPopover>
              </div>
            </div>
          </div>
        )
      }

      case "id":
        return (
          <span className="font-mono text-xs text-lia-text-primary">
            {candidate.candidateId || candidate.id}
          </span>
        )

      case "lia_score":
        return renderLiaScoreCell(candidate, t)

      case "lia_insights": {
        const insights = candidate.lia_insights
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {insights?.overall_summary?.slice(0, 50) || ""}
            {insights?.overall_summary && insights.overall_summary.length > 50 ? "..." : ""}
          </span>
        )
      }

      case "skills_match_percentage":
        return (
          <span className="text-xs">
            {candidate.skills_match_percentage ? `${candidate.skills_match_percentage}%` : ""}
          </span>
        )

      case "email":
        return renderEmailCell(candidate, revealedContacts, onRevealContact, t, contactValidity?.[candidate.id])

      case "secondary_email":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.secondary_email || ""}
          </span>
        )

      case "phone":
        return renderPhoneCell(candidate, revealedContacts, onRevealContact, "phone", t, contactValidity?.[candidate.id])

      case "mobile_phone":
        return renderPhoneCell(candidate, revealedContacts, onRevealContact, "mobile_phone", t, contactValidity?.[candidate.id])

      case "secondary_phone":
        return <span className="text-xs text-lia-text-primary">{candidate.secondary_phone || ""}</span>

      case "linkedin_url":
        return renderLinkedinCell(candidate, t)

      case "github_url":
        return renderGithubCell(candidate, t)

      case "portfolio_url":
        return renderPortfolioCell(candidate, t)

      case "date_of_birth":
        return <span className="text-xs text-lia-text-primary">{formatDate(candidate.date_of_birth)}</span>
      case "gender":
        return <span className="text-xs text-lia-text-primary">{candidate.gender || ""}</span>
      case "nationality":
        return <span className="text-xs text-lia-text-primary">{candidate.nationality || ""}</span>
      case "marital_status":
        return <span className="text-xs text-lia-text-primary">{candidate.marital_status || ""}</span>
      case "cpf":
        return <span className="text-xs text-lia-text-primary font-mono">{candidate.cpf || ""}</span>

      case "current_title": {
        const titleText = candidate.current_title || candidate.position || ""
        const isRowExpanded = expandedRows.has(candidate.id)
        const titleNeedsTruncation = titleText.length > 40

        return (
          <div className="flex items-start gap-1 max-w-[250px]">
            <span
              className={`text-xs text-lia-text-primary font-medium ${isRowExpanded ? "whitespace-normal break-words" : "truncate"}`}
              title={titleText}
            >
              {titleText}
            </span>
            {titleNeedsTruncation && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onToggleExpandedRow(candidate.id)
                }}
                className="flex-shrink-0 p-0.5 rounded-xl hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
                title={isRowExpanded
                  ? (t ? t('collapseText') : "Recolher texto")
                  : (t ? t('expandText') : "Expandir texto")}
              >
                <ChevronsLeftRight
                  className={`w-3 h-3 text-lia-text-primary hover:text-lia-text-primary transition-transform motion-reduce:transition-none ${isRowExpanded ? "rotate-90" : ""}`}
                />
              </button>
            )}
          </div>
        )
      }

      case "current_company":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.current_company || candidate.workHistory?.[0]?.company || ""}
          </span>
        )
      case "seniority_level":
        return (
          <Chip density="relaxed" variant="neutral" >
            {candidate.seniority_level || ""}
          </Chip>
        )
      case "years_of_experience":
        return (
          <span className="text-xs text-lia-text-primary">
            {candidate.years_of_experience !== undefined
              ? (t ? t('yearsExperience', { years: candidate.years_of_experience }) : `${candidate.years_of_experience} anos`)
              : ""}
          </span>
        )
      case "self_introduction":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.self_introduction?.slice(0, 50) || ""}
            {candidate.self_introduction && candidate.self_introduction.length > 50 ? "..." : ""}
          </span>
        )

      case "technical_skills":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {formatArray(candidate.technical_skills || candidate.skills)}
          </span>
        )
      case "soft_skills":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {formatArray(candidate.soft_skills)}
          </span>
        )
      case "languages":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {formatLanguages(candidate.languages)}
          </span>
        )
      case "certifications":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {formatArray(candidate.certifications)}
          </span>
        )
      case "interests":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {formatArray(candidate.interests)}
          </span>
        )
      case "education": {
        const educationData = candidate.education || (candidate as unknown as Record<string, unknown>).educations as any[]
        if (Array.isArray(educationData) && educationData.length > 0) {
          const firstEdu = educationData[0]
          return (
            <span className="text-xs text-lia-text-primary truncate">
              {firstEdu.degree || firstEdu.course || ""}
              {firstEdu.institution ? ` - ${firstEdu.institution}` : ""}
            </span>
          )
        }
        return <span className="text-xs text-lia-text-primary">—</span>
      }

      case "location_city":
        return (
          <div className="flex items-center gap-1">
            <MapPin className="w-3 h-3 text-lia-text-primary" />
            <span className="text-xs text-lia-text-primary truncate">
              {candidate.location_city || candidate.location?.split(",")[0] || ""}
            </span>
          </div>
        )
      case "location_state":
        return <span className="text-xs text-lia-text-primary">{candidate.location_state || ""}</span>
      case "location_country":
        return <span className="text-xs text-lia-text-primary">{candidate.location_country || ""}</span>

      case "address_street":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.address_street || ""}
          </span>
        )
      case "address_number":
        return <span className="text-xs text-lia-text-primary">{candidate.address_number || ""}</span>
      case "address_district":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.address_district || ""}
          </span>
        )
      case "address_zip":
        return (
          <span className="text-xs text-lia-text-primary font-mono">{candidate.address_zip || ""}</span>
        )
      case "address_complement":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.address_complement || ""}
          </span>
        )

      case "is_remote":
        return (
          <Chip
            variant="neutral"
            className={`text-xs ${candidate.is_remote ? " border-status-success/30" : ""}`}
          >
            {formatBoolean(candidate.is_remote)}
          </Chip>
        )
      case "willing_to_relocate":
        return (
          <span className="text-xs text-lia-text-primary">
            {formatBoolean(candidate.willing_to_relocate)}
          </span>
        )
      case "mobility":
        return <span className="text-xs text-lia-text-primary">{formatBoolean(candidate.mobility)}</span>
      case "work_model_preference": {
        const workModel = candidate.work_model_preference || candidate.workModel
        return (
          <Chip variant="neutral" muted
            className="text-xs"
           
          >
            {workModel === "remoto"
              ? (t ? t('remoteWork') : "🏠 Remoto")
              : workModel === "híbrido"
                ? (t ? t('hybridWork') : "🔄 Híbrido")
                : workModel === "presencial"
                  ? (t ? t('onsiteWork') : "🏢 Presencial")
                  : workModel || ""}
          </Chip>
        )
      }
      case "contract_type_preference":
        return (
          <span className="text-xs text-lia-text-primary">
            {candidate.contract_type_preference || ""}
          </span>
        )

      case "current_salary":
        return (
          <span className="text-xs text-lia-text-primary font-medium">
            {formatCurrency(
              candidate.current_salary || candidate.monthlySalary,
              candidate.salary_currency
            )}
          </span>
        )
      case "salary_currency":
        return (
          <span className="text-xs text-lia-text-primary">{candidate.salary_currency || "BRL"}</span>
        )
      case "desired_salary_min":
        return (
          <span className="text-xs text-lia-text-primary">
            {formatCurrency(candidate.desired_salary_min, candidate.salary_currency)}
          </span>
        )
      case "desired_salary_max":
        return (
          <span className="text-xs text-lia-text-primary">
            {formatCurrency(candidate.desired_salary_max, candidate.salary_currency)}
          </span>
        )
      case "salary_expectation_clt":
        return (
          <span className="text-xs text-lia-text-primary">
            {formatCurrency(candidate.salary_expectation_clt)}
          </span>
        )
      case "salary_expectation_pj":
        return (
          <span className="text-xs text-lia-text-primary">
            {formatCurrency(candidate.salary_expectation_pj)}
          </span>
        )
      case "salary_expectation_freelance":
        return (
          <span className="text-xs text-lia-text-primary">
            {formatCurrency(candidate.salary_expectation_freelance)}
          </span>
        )

      case "resume_url":
        return candidate.resume_url ? (
          <a
            href={candidate.resume_url}
            target="_blank"
            rel="noopener"
            className="text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse hover:underline text-xs flex items-center gap-1"
          >
            {t ? t('resume') : "Currículo"}
          </a>
        ) : (
          <span className="text-xs text-lia-text-primary">{t ? t('na') : "N/A"}</span>
        )
      case "resume_text":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.resume_text?.slice(0, 40) || ""}
            {candidate.resume_text && candidate.resume_text.length > 40 ? "..." : ""}
          </span>
        )
      case "cover_letter":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.cover_letter?.slice(0, 40) || ""}
            {candidate.cover_letter && candidate.cover_letter.length > 40 ? "..." : ""}
          </span>
        )

      case "ats_source_name":
        return <span className="text-xs text-lia-text-primary">{candidate.ats_source_name || ""}</span>
      case "ats_candidate_id":
        return (
          <span className="text-xs text-lia-text-primary font-mono">
            {candidate.ats_candidate_id || ""}
          </span>
        )
      case "pearch_profile_id":
        return (
          <span className="text-xs text-lia-text-primary font-mono">
            {candidate.pearch_profile_id || ""}
          </span>
        )

      case "status": {
        const statusColors: Record<string, string> = {
          novo: "bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary",
          triagem: "bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning",
          entrevista: "bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple-text dark:text-wedo-purple",
          aprovado: "bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success",
          reprovado: "bg-status-error/15 dark:bg-status-error/30 text-status-error dark:text-status-error",
        }
        return (
          <Chip variant="neutral" muted
            className={`text-xs ${statusColors[candidate.status || ""] || "bg-lia-bg-tertiary text-lia-text-primary"}`}
          >
            {candidate.status || ""}
          </Chip>
        )
      }
      case "is_active":
        return (
          <Chip
            variant="neutral"
            className={`text-xs ${candidate.is_active ? "" : ""}`}
          >
            {formatBoolean(candidate.is_active)}
          </Chip>
        )
      case "is_blacklisted":
        return candidate.is_blacklisted ? (
          <Chip density="relaxed" variant="neutral" muted >{t ? t('yes') : "Sim"}</Chip>
        ) : (
          <span className="text-xs text-lia-text-primary">{t ? t('no') : "Não"}</span>
        )
      case "blacklist_reason":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.blacklist_reason || ""}
          </span>
        )

      case "preferred_contact_method":
        return (
          <span className="text-xs text-lia-text-primary">
            {candidate.preferred_contact_method || ""}
          </span>
        )
      case "best_time_to_contact":
        return (
          <span className="text-xs text-lia-text-primary">{candidate.best_time_to_contact || ""}</span>
        )
      case "communication_consent":
        return (
          <Chip
            variant="neutral"
            className={`text-xs ${candidate.communication_consent ? "" : ""}`}
          >
            {formatBoolean(candidate.communication_consent)}
          </Chip>
        )

      case "completed_register":
        return (
          <span className="text-xs text-lia-text-primary">
            {formatBoolean(candidate.completed_register)}
          </span>
        )
      case "accept_terms":
        return (
          <span className="text-xs text-lia-text-primary">{formatBoolean(candidate.accept_terms)}</span>
        )

      case "tags":
        return (
          <span className="text-xs text-lia-text-primary truncate">{formatArray(candidate.tags)}</span>
        )
      case "notes":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.notes?.slice(0, 40) || ""}
            {candidate.notes && candidate.notes.length > 40 ? "..." : ""}
          </span>
        )
      case "additional_data":
        return <span className="text-xs text-lia-text-primary">JSON</span>

      case "created_at":
        return <span className="text-xs text-lia-text-primary">{formatDate(candidate.created_at)}</span>
      case "updated_at":
        return <span className="text-xs text-lia-text-primary">{formatDate(candidate.updated_at)}</span>
      case "last_contacted_at":
        return (
          <span className="text-xs text-lia-text-primary">
            {formatDate(candidate.last_contacted_at)}
          </span>
        )
      case "last_activity_at":
        return (
          <span className="text-xs text-lia-text-primary">
            {formatDate(candidate.last_activity_at)}
          </span>
        )

      default: {
        const pearchResult = renderPearchInsightCell(columnId, candidate, t)
        if (pearchResult !== null) return pearchResult
        return <span className="text-xs text-lia-text-primary">{t ? t('na') : "N/A"}</span>
      }
    }
  }
}
