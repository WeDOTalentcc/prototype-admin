"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Eye, ChevronsLeftRight, MapPin,
} from "lucide-react"
import { SearchFeedbackButtons } from "@/components/search/SearchFeedbackButtons"
import { textStyles } from "@/lib/design-tokens"
import type { Candidate } from "@/components/pages/candidates/types"
import { renderSourceCell } from "./cells/SourceCell"
import { renderMatchScoreCell, renderLiaScoreCell } from "./cells/ScoreCells"
import { renderEmailCell, renderPhoneCell, renderLinkedinCell, renderGithubCell, renderPortfolioCell } from "./cells/ContactCells"
import { renderPearchInsightCell } from "./cells/PearchCells"

// ---------------------------------------------------------------------------
// Deps interface — todas as dependências que vêm do componente pai
// ---------------------------------------------------------------------------

export interface CellRendererDeps {
  /** Feedbacks de busca indexados por candidateId */
  searchFeedbacks: Record<string, "like" | "dislike">
  /** Contatos revelados (Pearch) indexados por candidateId */
  revealedContacts: Record<string, { email?: string; phone?: string }>
  /** Query da busca atual — usado para decidir se exibe match_score */
  searchQuery: string
  /** IDs de candidatos cujo perfil já foi visualizado */
  viewedCandidateIds: Set<string>
  /** IDs de linhas expandidas (current_title longo) */
  expandedRows: Set<string>
  /** Callback ao alterar feedback de busca */
  onSearchFeedbackChange: (
    candidateId: string,
    candidateName: string,
    feedback: "like" | "dislike" | null
  ) => void
  /** Abre modal de revelação de contato (email | phone) */
  onRevealContact: (candidate: Candidate, type: "email" | "phone") => void
  /** Alterna expansão de linha para candidatos com título longo */
  onToggleExpandedRow: (candidateId: string) => void
}

// ---------------------------------------------------------------------------
// Factory — retorna renderCellValue com closure sobre as deps
// ---------------------------------------------------------------------------

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
  } = deps

  // -------------------------------------------------------------------------
  // Formatadores locais (sem deps externas)
  // -------------------------------------------------------------------------

  const formatDate = (date: string | undefined) => {
    if (!date) return "N/A"
    return new Date(date).toLocaleDateString("pt-BR")
  }

  const formatCurrency = (value: number | undefined, currency?: string) => {
    if (!value) return "N/A"
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: currency || "BRL",
    }).format(value)
  }

  const formatBoolean = (value: boolean | undefined) => {
    if (value === undefined) return "N/A"
    return value ? "Sim" : "Não"
  }

  const formatArray = (arr: string[] | undefined) => {
    if (!arr || arr.length === 0) return "N/A"
    return arr.slice(0, 3).join(", ") + (arr.length > 3 ? ` (+${arr.length - 3})` : "")
  }

  const formatLanguages = (langs: Record<string, string> | undefined) => {
    if (!langs) return "N/A"
    const entries = Object.entries(langs)
    if (entries.length === 0) return "N/A"
    return entries
      .slice(0, 2)
      .map(([lang, level]) => `${lang}: ${level}`)
      .join(", ")
  }

  // -------------------------------------------------------------------------
  // Função de renderização da célula
  // -------------------------------------------------------------------------

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
            className={cn(
              "flex items-center justify-center transition-opacity duration-200",
              hasFeedback ? "opacity-100" : "opacity-0 group-hover:opacity-100"
            )}
          >
            <SearchFeedbackButtons
              candidateId={candidate.id}
              candidateName={candidate.name}
              candidateScore={
                // @ts-ignore TODO: fix type
                candidate.match_score || candidate.lia_score || candidate.score
              }
              initialFeedback={searchFeedbacks[candidate.id] || null}
              // @ts-ignore TODO: fix type
              onFeedbackChange={onSearchFeedbackChange}
              size="sm"
              alwaysVisible={hasFeedback}
            />
          </div>
        )
      }

      // Delegated to SourceCell
      case "source":
        return renderSourceCell(candidate)

      // Delegated to ScoreCells
      case "match_score":
        return renderMatchScoreCell(candidate, searchQuery)

      // Básico
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
                    // @ts-ignore TODO: fix type
                    candidate.photo_url ||
                    // @ts-ignore TODO: fix type
                    candidate.picture_url ||
                    // @ts-ignore TODO: fix type
                    candidate.photoUrl ||
                    // @ts-ignore TODO: fix type
                    candidate.profile_picture
                  }
                  alt={candidate.name}
                />
                <AvatarFallback className="text-sm font-medium bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-secondary">
                  {candidate.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()}
                </AvatarFallback>
              </Avatar>
              {isCandidateViewed && (
                <div
                  className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-gray-300 rounded-full flex items-center justify-center border border-white"
                  title="Perfil visualizado"
                >
                  <Eye className="w-2.5 h-2.5 text-white" />
                </div>
              )}
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-medium text-lia-text-primary dark:text-lia-text-primary truncate text-xs">
                  {candidate.name}
                </span>
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

      // IA — delegated to ScoreCells
      case "lia_score":
        return renderLiaScoreCell(candidate)

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

      // Contato — delegated to ContactCells
      case "email":
        return renderEmailCell(candidate, revealedContacts, onRevealContact)

      case "secondary_email":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.secondary_email || ""}
          </span>
        )

      case "phone":
        return renderPhoneCell(candidate, revealedContacts, onRevealContact, "phone")

      case "mobile_phone":
        return renderPhoneCell(candidate, revealedContacts, onRevealContact, "mobile_phone")

      case "secondary_phone":
        return <span className="text-xs text-lia-text-primary">{candidate.secondary_phone || ""}</span>

      case "linkedin_url":
        return renderLinkedinCell(candidate)

      case "github_url":
        return renderGithubCell(candidate)

      case "portfolio_url":
        return renderPortfolioCell(candidate)

      // Pessoal
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

      // Profissional
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
                className="flex-shrink-0 p-0.5 rounded-md hover:bg-gray-100 transition-colors motion-reduce:transition-none"
                title={isRowExpanded ? "Recolher texto" : "Expandir texto"}
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
          <Badge variant="outline" className="text-xs">
            {candidate.seniority_level || ""}
          </Badge>
        )
      case "years_of_experience":
        return (
          <span className="text-xs text-lia-text-primary">
            {candidate.years_of_experience !== undefined
              ? `${candidate.years_of_experience} anos`
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

      // Competências
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
        // @ts-ignore TODO: fix type
        const educationData = candidate.education || candidate.educations
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

      // Localização
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

      // Endereço
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

      // Preferências
      case "is_remote":
        return (
          <Badge
            variant="outline"
            className={`text-xs ${candidate.is_remote ? "bg-status-success/10 text-status-success border-status-success/30" : ""}`}
          >
            {formatBoolean(candidate.is_remote)}
          </Badge>
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
          <Badge
            className="text-xs"
            style={{backgroundColor: "var(--gray-200)", color: "var(--gray-600)"}}
          >
            {workModel === "remoto"
              ? "🏠 Remoto"
              : workModel === "híbrido"
                ? "🔄 Híbrido"
                : workModel === "presencial"
                  ? "🏢 Presencial"
                  : workModel || ""}
          </Badge>
        )
      }
      case "contract_type_preference":
        return (
          <span className="text-xs text-lia-text-primary">
            {candidate.contract_type_preference || ""}
          </span>
        )

      // Salário
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

      // Documentos
      case "resume_url":
        return candidate.resume_url ? (
          <a
            href={candidate.resume_url}
            target="_blank"
            rel="noopener"
            className="text-lia-text-secondary dark:text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse hover:underline text-xs flex items-center gap-1"
          >
            Currículo
          </a>
        ) : (
          <span className="text-xs text-lia-text-primary">N/A</span>
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

      // Origem
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

      // Status
      case "status": {
        const statusColors: Record<string, string> = {
          novo: "bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary",
          triagem:
            "bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning",
          entrevista:
            "bg-wedo-purple/15 dark:bg-wedo-purple/30 text-wedo-purple dark:text-wedo-purple",
          aprovado:
            "bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success",
          reprovado:
            "bg-status-error/15 dark:bg-status-error/30 text-status-error dark:text-status-error",
        }
        return (
          <Badge
            className={`text-xs ${statusColors[candidate.status || ""] || "bg-gray-100 text-lia-text-primary"}`}
          >
            {candidate.status || ""}
          </Badge>
        )
      }
      case "is_active":
        return (
          <Badge
            variant="outline"
            className={`text-xs ${candidate.is_active ? "bg-status-success/10 text-status-success" : "bg-status-error/10 text-status-error"}`}
          >
            {formatBoolean(candidate.is_active)}
          </Badge>
        )
      case "is_blacklisted":
        return candidate.is_blacklisted ? (
          <Badge className="text-xs bg-status-error/15 text-status-error">Sim</Badge>
        ) : (
          <span className="text-xs text-lia-text-primary">Não</span>
        )
      case "blacklist_reason":
        return (
          <span className="text-xs text-lia-text-primary truncate">
            {candidate.blacklist_reason || ""}
          </span>
        )

      // Comunicação
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
          <Badge
            variant="outline"
            className={`text-xs ${candidate.communication_consent ? "bg-status-success/10 text-status-success" : ""}`}
          >
            {formatBoolean(candidate.communication_consent)}
          </Badge>
        )

      // Cadastro
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

      // Adicional
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

      // Datas
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

      // Busca Global / Pearch — delegated to PearchCells
      default: {
        const pearchResult = renderPearchInsightCell(columnId, candidate)
        if (pearchResult !== null) return pearchResult
        return <span className="text-xs text-lia-text-primary">N/A</span>
      }
    }
  }
}
