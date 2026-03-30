"use client"

import React from "react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Home, Globe, CheckCircle, DollarSign, Brain, Eye,
  Mail, Phone, Linkedin, Github, FileText, MapPin,
  ChevronsLeftRight, Copy,
} from "lucide-react"
import { SearchFeedbackButtons } from "@/components/search/SearchFeedbackButtons"
import { ScoreBreakdownBadgeLazy } from "@/components/score/ScoreBreakdownBadge"
import { getSourceDetails, isGlobalSource } from "@/lib/utils/source-detection"
import { textStyles, badgeStyles } from "@/lib/design-tokens"
import type { Candidate } from "@/components/pages/candidates/types"

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
                candidate.match_score || candidate.lia_score || candidate.score
              }
              initialFeedback={searchFeedbacks[candidate.id] || null}
              onFeedbackChange={onSearchFeedbackChange}
              size="sm"
              alwaysVisible={hasFeedback}
            />
          </div>
        )
      }

      // Fonte (Local vs Global) — com tooltips dinâmicos
      case "source": {
        const hasPearchId = !!candidate.pearch_profile_id
        const sourceInfo = getSourceDetails(candidate.source, hasPearchId)
        const isLocal = sourceInfo.isLocal

        return (
          <div className="relative group flex items-center justify-center cursor-help">
            {isLocal ? (
              <div
                className="w-6 h-6 rounded-full flex items-center justify-center transition-[width,height] hover:scale-110 bg-stone-400/20"
              >
                <Home className="w-3.5 h-3.5" style={{color: "var(--gray-500)"}} />
              </div>
            ) : (
              <div className="w-6 h-6 rounded-full flex items-center justify-center transition-[width,height] hover:scale-110 bg-gray-100 dark:bg-lia-bg-elevated">
                <Globe className="w-3.5 h-3.5 text-gray-600 dark:text-lia-text-secondary" />
              </div>
            )}
            {/* Tooltip dinâmico com informações de créditos */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 pointer-events-none">
              <div className="px-3 py-2 rounded-md text-xs min-w-[180px] text-white bg-gray-900">
                <div className="font-semibold mb-1 flex items-center gap-1.5">
                  {isLocal ? (
                    <Home className="w-3.5 h-3.5" style={{color: "var(--wedo-orange)"}} />
                  ) : (
                    <Globe className="w-3.5 h-3.5 text-gray-300" />
                  )}
                  {sourceInfo.label}
                </div>
                <div className="text-xs text-gray-500 mb-1">{sourceInfo.subtext}</div>
                {isLocal ? (
                  <div className="text-xs font-medium flex items-center gap-1 mt-1.5 pt-1.5 border-t border-gray-700 text-wedo-green-light">
                    <CheckCircle className="w-3 h-3" />
                    Sem consumo de créditos
                  </div>
                ) : (
                  <div
                    className="text-xs font-medium flex items-center gap-1 mt-1.5 pt-1.5 border-t border-gray-700 text-status-warning"
                  >
                    <DollarSign className="w-3 h-3" />
                    {sourceInfo.credits || "5-7 créditos/candidato"}
                  </div>
                )}
                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
              </div>
            </div>
          </div>
        )
      }

      // Match Score — Ring Progress
      case "match_score": {
        const matchScore = candidate.score || 0
        const hasActiveSearch = searchQuery && searchQuery.length > 0

        if (!hasActiveSearch || matchScore === 0) {
          return (
            <div className="flex items-center justify-center">
              <span className={textStyles.label}>—</span>
            </div>
          )
        }

        const getMatchRingColor = (score: number) => {
          if (score >= 85) return "var(--gray-600)"
          if (score >= 70) return "var(--wedo-green-light)"
          if (score >= 50) return "var(--wedo-orange)"
          return "var(--gray-400)"
        }

        const ringColor = getMatchRingColor(matchScore)
        const ringSize = 32
        const strokeWidth = 3
        const radius = (ringSize - strokeWidth) / 2
        const circumference = radius * 2 * Math.PI
        const strokeDashoffset = circumference - (matchScore / 100) * circumference

        return (
          <div className="flex items-center justify-center">
            <div className="relative" style={{width: ringSize, height: ringSize}}>
              {/* Background ring */}
              <svg className="absolute" width={ringSize} height={ringSize}>
                <circle
                  cx={ringSize / 2}
                  cy={ringSize / 2}
                  r={radius}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={strokeWidth}
                  className="text-gray-500 dark:text-gray-500"
                />
              </svg>
              {/* Progress ring */}
              <svg className="absolute -rotate-90" width={ringSize} height={ringSize}>
                <circle
                  cx={ringSize / 2}
                  cy={ringSize / 2}
                  r={radius}
                  fill="none"
                  stroke={ringColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  className="transition-colors duration-300"
                />
              </svg>
              {/* Percentage text */}
              <div className="absolute inset-0 flex items-center justify-center">
                <span className={`${textStyles.label} font-bold dark:text-lia-text-primary`}>
                  {matchScore}
                </span>
              </div>
            </div>
          </div>
        )
      }

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
                    candidate.photo_url ||
                    candidate.picture_url ||
                    candidate.photoUrl ||
                    candidate.profile_picture
                  }
                  alt={candidate.name}
                />
                <AvatarFallback className="text-sm font-medium bg-gray-100 dark:bg-lia-bg-elevated text-gray-600 dark:text-lia-text-secondary">
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
                <span className="font-medium text-gray-950 dark:text-lia-text-primary truncate text-xs">
                  {candidate.name}
                </span>
              </div>
            </div>
          </div>
        )
      }

      case "id":
        return (
          <span className="font-mono text-xs text-gray-800">
            {candidate.candidateId || candidate.id}
          </span>
        )

      // IA
      case "lia_score": {
        const score = candidate.lia_score || 0
        const hasBeenEvaluated = candidate.lia_score && candidate.lia_score > 0

        if (!hasBeenEvaluated) {
          return (
            <div className="relative group cursor-help">
              <span className="text-xs text-gray-800">—</span>
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50">
                <div className="bg-gray-900 dark:bg-lia-bg-elevated text-white px-3 py-2 rounded-md text-xs min-w-[180px]">
                  <div className="font-semibold mb-1.5 flex items-center gap-1.5">
                    <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                    Sem avaliação
                  </div>
                  <div className="text-xs text-gray-500">
                    Este candidato ainda não participou de nenhum processo seletivo.
                  </div>
                  <div className="text-xs text-gray-800 mt-1.5">
                    O Score LIA é calculado quando o candidato é avaliado para uma vaga específica.
                  </div>
                  <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
                </div>
              </div>
            </div>
          )
        }

        return (
          <ScoreBreakdownBadgeLazy
            score={score}
            candidateId={candidate.id}
            jobId={(candidate.additional_data?.job_id as string) ?? ""}
            size="sm"
          />
        )
      }

      case "lia_insights": {
        const insights = candidate.lia_insights
        return (
          <span className="text-xs text-gray-800 truncate">
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

      // Contato — com sistema de reveal para candidatos Pearch
      case "email": {
        const candidateEmail = revealedContacts[candidate.id]?.email || candidate.email
        const canRevealEmail =
          isGlobalSource(candidate.source, Boolean(candidate.pearch_profile_id)) &&
          candidate.has_email !== false

        if (candidateEmail) {
          return <span className="text-xs text-gray-800 truncate">{candidateEmail}</span>
        }

        if (canRevealEmail) {
          return (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onRevealContact(candidate, "email")
              }}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-lia-bg-secondary dark:text-lia-text-secondary dark:hover:bg-gray-700 transition-colors"
              title="Clique para revelar email (2 créditos)"
            >
              <Mail className="w-3 h-3" />
              <span>Revelar</span>
              <span className="opacity-60">(2 cr)</span>
            </button>
          )
        }

        return <span className="text-xs text-gray-800">-</span>
      }

      case "secondary_email":
        return (
          <span className="text-xs text-gray-800 truncate">
            {candidate.secondary_email || ""}
          </span>
        )

      case "phone": {
        const candidatePhone = revealedContacts[candidate.id]?.phone || candidate.phone
        const canRevealPhone =
          isGlobalSource(candidate.source, Boolean(candidate.pearch_profile_id)) &&
          candidate.has_phone !== false

        if (candidatePhone) {
          return <span className="text-xs text-gray-800">{candidatePhone}</span>
        }

        if (canRevealPhone) {
          return (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onRevealContact(candidate, "phone")
              }}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full bg-status-success/10 text-status-success hover:bg-status-success/15 transition-colors"
              title="Clique para revelar telefone (14 créditos)"
            >
              <Phone className="w-3 h-3" />
              <span>Revelar</span>
              <span className="opacity-60">(14 cr)</span>
            </button>
          )
        }

        return <span className="text-xs text-gray-800">-</span>
      }

      case "mobile_phone": {
        const candidateMobile =
          revealedContacts[candidate.id]?.phone || candidate.mobile_phone || candidate.phone
        const canRevealMobile =
          isGlobalSource(candidate.source, Boolean(candidate.pearch_profile_id)) &&
          candidate.has_phone !== false

        if (candidateMobile) {
          return <span className="text-xs text-gray-800">{candidateMobile}</span>
        }

        if (canRevealMobile) {
          return (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onRevealContact(candidate, "phone")
              }}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full bg-status-success/10 text-status-success hover:bg-status-success/15 transition-colors"
              title="Clique para revelar celular (14 créditos)"
            >
              <Phone className="w-3 h-3" />
              <span>Revelar</span>
              <span className="opacity-60">(14 cr)</span>
            </button>
          )
        }

        return <span className="text-xs text-gray-800">-</span>
      }

      case "secondary_phone":
        return <span className="text-xs text-gray-800">{candidate.secondary_phone || ""}</span>

      case "linkedin_url":
        return candidate.linkedin_url ? (
          <a
            href={candidate.linkedin_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center w-6 h-6 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Ver perfil no LinkedIn"
          >
            <Linkedin className="w-4 h-4 text-gray-600" />
          </a>
        ) : (
          <span
            className="inline-flex items-center justify-center w-6 h-6"
            title="LinkedIn não informado"
          >
            <Linkedin className="w-4 h-4 text-gray-500 dark:text-gray-500" />
          </span>
        )

      case "github_url":
        return candidate.github_url ? (
          <a
            href={candidate.github_url}
            target="_blank"
            rel="noopener"
            className="text-gray-800 hover:underline text-xs flex items-center gap-1"
          >
            <Github className="w-3 h-3" /> GitHub
          </a>
        ) : (
          <span className="text-xs text-gray-800">N/A</span>
        )

      case "portfolio_url":
        return candidate.portfolio_url ? (
          <a
            href={candidate.portfolio_url}
            target="_blank"
            rel="noopener"
            className="text-wedo-purple hover:underline text-xs flex items-center gap-1"
          >
            <Globe className="w-3 h-3" /> Portfólio
          </a>
        ) : (
          <span className="text-xs text-gray-800">N/A</span>
        )

      // Pessoal
      case "date_of_birth":
        return <span className="text-xs text-gray-800">{formatDate(candidate.date_of_birth)}</span>
      case "gender":
        return <span className="text-xs text-gray-800">{candidate.gender || ""}</span>
      case "nationality":
        return <span className="text-xs text-gray-800">{candidate.nationality || ""}</span>
      case "marital_status":
        return <span className="text-xs text-gray-800">{candidate.marital_status || ""}</span>
      case "cpf":
        return <span className="text-xs text-gray-800 font-mono">{candidate.cpf || ""}</span>

      // Profissional
      case "current_title": {
        const titleText = candidate.current_title || candidate.position || ""
        const isRowExpanded = expandedRows.has(candidate.id)
        const titleNeedsTruncation = titleText.length > 40

        return (
          <div className="flex items-start gap-1 max-w-[250px]">
            <span
              className={`text-xs text-gray-800 font-medium ${isRowExpanded ? "whitespace-normal break-words" : "truncate"}`}
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
                className="flex-shrink-0 p-0.5 rounded-md hover:bg-gray-100 transition-colors"
                title={isRowExpanded ? "Recolher texto" : "Expandir texto"}
              >
                <ChevronsLeftRight
                  className={`w-3 h-3 text-gray-800 hover:text-gray-800 transition-transform ${isRowExpanded ? "rotate-90" : ""}`}
                />
              </button>
            )}
          </div>
        )
      }

      case "current_company":
        return (
          <span className="text-xs text-gray-800 truncate">
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
          <span className="text-xs text-gray-800">
            {candidate.years_of_experience !== undefined
              ? `${candidate.years_of_experience} anos`
              : ""}
          </span>
        )
      case "self_introduction":
        return (
          <span className="text-xs text-gray-800 truncate">
            {candidate.self_introduction?.slice(0, 50) || ""}
            {candidate.self_introduction && candidate.self_introduction.length > 50 ? "..." : ""}
          </span>
        )

      // Competências
      case "technical_skills":
        return (
          <span className="text-xs text-gray-800 truncate">
            {formatArray(candidate.technical_skills || candidate.skills)}
          </span>
        )
      case "soft_skills":
        return (
          <span className="text-xs text-gray-800 truncate">
            {formatArray(candidate.soft_skills)}
          </span>
        )
      case "languages":
        return (
          <span className="text-xs text-gray-800 truncate">
            {formatLanguages(candidate.languages)}
          </span>
        )
      case "certifications":
        return (
          <span className="text-xs text-gray-800 truncate">
            {formatArray(candidate.certifications)}
          </span>
        )
      case "interests":
        return (
          <span className="text-xs text-gray-800 truncate">
            {formatArray(candidate.interests)}
          </span>
        )
      case "education": {
        const educationData = candidate.education || candidate.educations
        if (Array.isArray(educationData) && educationData.length > 0) {
          const firstEdu = educationData[0]
          return (
            <span className="text-xs text-gray-800 truncate">
              {firstEdu.degree || firstEdu.course || ""}
              {firstEdu.institution ? ` - ${firstEdu.institution}` : ""}
            </span>
          )
        }
        return <span className="text-xs text-gray-800">—</span>
      }

      // Localização
      case "location_city":
        return (
          <div className="flex items-center gap-1">
            <MapPin className="w-3 h-3 text-gray-800" />
            <span className="text-xs text-gray-800 truncate">
              {candidate.location_city || candidate.location?.split(",")[0] || ""}
            </span>
          </div>
        )
      case "location_state":
        return <span className="text-xs text-gray-800">{candidate.location_state || ""}</span>
      case "location_country":
        return <span className="text-xs text-gray-800">{candidate.location_country || ""}</span>

      // Endereço
      case "address_street":
        return (
          <span className="text-xs text-gray-800 truncate">
            {candidate.address_street || ""}
          </span>
        )
      case "address_number":
        return <span className="text-xs text-gray-800">{candidate.address_number || ""}</span>
      case "address_district":
        return (
          <span className="text-xs text-gray-800 truncate">
            {candidate.address_district || ""}
          </span>
        )
      case "address_zip":
        return (
          <span className="text-xs text-gray-800 font-mono">{candidate.address_zip || ""}</span>
        )
      case "address_complement":
        return (
          <span className="text-xs text-gray-800 truncate">
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
          <span className="text-xs text-gray-800">
            {formatBoolean(candidate.willing_to_relocate)}
          </span>
        )
      case "mobility":
        return <span className="text-xs text-gray-800">{formatBoolean(candidate.mobility)}</span>
      case "work_model_preference": {
        const workModel = candidate.work_model_preference || candidate.workModel
        return (
          <Badge
            className="text-xs"
            style={{backgroundColor:
                workModel === "remoto"
                  ? "var(--gray-200)"
                  : workModel === "híbrido"
                    ? "var(--gray-200)"
                    : "var(--gray-200)",
              color:
                workModel === "remoto"
                  ? "var(--gray-600)"
                  : workModel === "híbrido"
                    ? "var(--gray-600)"
                    : "var(--gray-600)"}}
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
          <span className="text-xs text-gray-800">
            {candidate.contract_type_preference || ""}
          </span>
        )

      // Salário
      case "current_salary":
        return (
          <span className="text-xs text-gray-800 font-medium">
            {formatCurrency(
              candidate.current_salary || candidate.monthlySalary,
              candidate.salary_currency
            )}
          </span>
        )
      case "salary_currency":
        return (
          <span className="text-xs text-gray-800">{candidate.salary_currency || "BRL"}</span>
        )
      case "desired_salary_min":
        return (
          <span className="text-xs text-gray-800">
            {formatCurrency(candidate.desired_salary_min, candidate.salary_currency)}
          </span>
        )
      case "desired_salary_max":
        return (
          <span className="text-xs text-gray-800">
            {formatCurrency(candidate.desired_salary_max, candidate.salary_currency)}
          </span>
        )
      case "salary_expectation_clt":
        return (
          <span className="text-xs text-gray-800">
            {formatCurrency(candidate.salary_expectation_clt)}
          </span>
        )
      case "salary_expectation_pj":
        return (
          <span className="text-xs text-gray-800">
            {formatCurrency(candidate.salary_expectation_pj)}
          </span>
        )
      case "salary_expectation_freelance":
        return (
          <span className="text-xs text-gray-800">
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
            className="text-gray-700 dark:text-lia-text-secondary hover:text-gray-900 dark:hover:text-gray-100 hover:underline text-xs flex items-center gap-1"
          >
            <FileText className="w-3 h-3" /> Currículo
          </a>
        ) : (
          <span className="text-xs text-gray-800">N/A</span>
        )
      case "resume_text":
        return (
          <span className="text-xs text-gray-800 truncate">
            {candidate.resume_text?.slice(0, 40) || ""}
            {candidate.resume_text && candidate.resume_text.length > 40 ? "..." : ""}
          </span>
        )
      case "cover_letter":
        return (
          <span className="text-xs text-gray-800 truncate">
            {candidate.cover_letter?.slice(0, 40) || ""}
            {candidate.cover_letter && candidate.cover_letter.length > 40 ? "..." : ""}
          </span>
        )

      // Origem
      case "ats_source_name":
        return <span className="text-xs text-gray-800">{candidate.ats_source_name || ""}</span>
      case "ats_candidate_id":
        return (
          <span className="text-xs text-gray-800 font-mono">
            {candidate.ats_candidate_id || ""}
          </span>
        )
      case "pearch_profile_id":
        return (
          <span className="text-xs text-gray-800 font-mono">
            {candidate.pearch_profile_id || ""}
          </span>
        )

      // Busca Global / Pearch
      case "is_open_to_work": {
        const isOpenToWork = candidate.is_opentowork || candidate.is_open_to_work
        return isOpenToWork ? (
          <Badge className="text-xs bg-status-success/15 text-status-success">Open to Work</Badge>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      }
      case "is_decision_maker":
        return candidate.is_decision_maker ? (
          <Badge className="text-xs bg-wedo-purple/15 text-wedo-purple">Decision Maker</Badge>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "is_top_universities":
        return candidate.is_top_universities ? (
          <Badge className="text-xs bg-gray-100 dark:bg-lia-bg-secondary text-gray-700 dark:text-lia-text-secondary">
            Top University
          </Badge>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "is_hiring":
        return candidate.is_hiring ? (
          <Badge className="text-xs bg-wedo-orange/15 text-wedo-orange">Contratando</Badge>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "headline":
        return <span className="text-xs text-gray-800 truncate">{candidate.headline || ""}</span>
      case "expertise":
        return (
          <span className="text-xs text-gray-800 truncate">
            {formatArray(candidate.expertise)}
          </span>
        )
      case "linkedin_followers_count":
        return candidate.linkedin_followers_count ? (
          <span className="text-xs text-gray-800">
            {candidate.linkedin_followers_count.toLocaleString("pt-BR")}
          </span>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "linkedin_connections_count":
        return candidate.linkedin_connections_count ? (
          <span className="text-xs text-gray-800">
            {candidate.linkedin_connections_count.toLocaleString("pt-BR")}
          </span>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "outreach_message":
        return candidate.outreach_message ? (
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-800 truncate max-w-sidebar-content">
              {candidate.outreach_message.slice(0, 50)}...
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                navigator.clipboard.writeText(candidate.outreach_message!)
              }}
              className="p-0.5 hover:bg-gray-100 rounded-md"
              title="Copiar mensagem"
            >
              <Copy className="w-3 h-3 text-gray-500" />
            </button>
          </div>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "pearch_insights":
        return candidate.pearch_insights?.overall_summary ? (
          <span className="text-xs text-gray-800 truncate">
            {candidate.pearch_insights.overall_summary.slice(0, 50)}...
          </span>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "best_personal_email":
        return candidate.best_personal_email ? (
          <a
            href={`mailto:${candidate.best_personal_email}`}
            className="text-xs text-gray-700 dark:text-lia-text-secondary hover:text-gray-900 dark:hover:text-gray-100 hover:underline truncate"
          >
            {candidate.best_personal_email}
          </a>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "phone_types": {
        if (!candidate.phone_types || Object.keys(candidate.phone_types).length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        const activeTypes = Object.entries(candidate.phone_types)
          .filter(([_, active]) => active)
          .map(([type]) => type)
        return (
          <span className="text-xs text-gray-800">{activeTypes.join(", ") || "—"}</span>
        )
      }
      case "estimated_age":
        return candidate.estimated_age ? (
          <span className="text-xs text-gray-800">{candidate.estimated_age} anos</span>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "match_reasoning":
        return candidate.pearch_insights?.match_reasoning ? (
          <span
            className="text-xs text-gray-800 truncate"
            title={candidate.pearch_insights.match_reasoning}
          >
            {candidate.pearch_insights.match_reasoning.slice(0, 60)}...
          </span>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "overall_summary":
        return candidate.pearch_insights?.overall_summary ? (
          <span
            className="text-xs text-gray-800 truncate"
            title={candidate.pearch_insights.overall_summary}
          >
            {candidate.pearch_insights.overall_summary.slice(0, 60)}...
          </span>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "query_insights": {
        const queryInsights = candidate.pearch_insights?.query_insights
        if (!queryInsights || queryInsights.length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        return (
          <div className="flex flex-col gap-0.5">
            {queryInsights.slice(0, 2).map((insight, idx) => (
              <div key={idx} className="flex items-center gap-1">
                <Badge
                  className={`text-micro px-1 py-0 ${
                    insight.match_level === "Exceeds"
                      ? "bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success"
                      : insight.match_level === "Meets"
                        ? "bg-gray-100 dark:bg-lia-bg-secondary text-gray-700 dark:text-lia-text-secondary"
                        : insight.match_level === "Partial"
                          ? "bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning"
                          : "bg-gray-100 dark:bg-lia-bg-secondary text-gray-800 dark:text-lia-text-secondary"
                  }`}
                >
                  {insight.match_level}
                </Badge>
                <span
                  className={`${textStyles.caption} truncate max-w-[150px]`}
                  title={insight.subquery}
                >
                  {insight.subquery?.slice(0, 25)}...
                </span>
              </div>
            ))}
            {queryInsights.length > 2 && (
              <span className={textStyles.caption}>+{queryInsights.length - 2} mais</span>
            )}
          </div>
        )
      }
      case "middle_name":
        return candidate.middle_name ? (
          <span className="text-xs text-gray-800 truncate">{candidate.middle_name}</span>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "best_business_email":
        return candidate.best_business_email ? (
          <a
            href={`mailto:${candidate.best_business_email}`}
            className="text-xs text-gray-700 dark:text-lia-text-secondary hover:text-gray-900 dark:hover:text-gray-100 hover:underline truncate"
          >
            {candidate.best_business_email}
          </a>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "personal_emails": {
        const personalEmailsArr = candidate.personal_emails
        if (!personalEmailsArr || personalEmailsArr.length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        return (
          <span
            className="text-xs text-gray-800 truncate"
            title={personalEmailsArr.join(", ")}
          >
            {personalEmailsArr.length === 1
              ? personalEmailsArr[0]
              : `${personalEmailsArr[0]} (+${personalEmailsArr.length - 1})`}
          </span>
        )
      }
      case "business_emails": {
        const businessEmailsArr = candidate.business_emails
        if (!businessEmailsArr || businessEmailsArr.length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        return (
          <span
            className="text-xs text-gray-800 truncate"
            title={businessEmailsArr.join(", ")}
          >
            {businessEmailsArr.length === 1
              ? businessEmailsArr[0]
              : `${businessEmailsArr[0]} (+${businessEmailsArr.length - 1})`}
          </span>
        )
      }
      case "company_followers_count":
        return candidate.company_followers_count != null ? (
          <span className="text-xs text-gray-800">
            {candidate.company_followers_count.toLocaleString("pt-BR")}
          </span>
        ) : (
          <span className="text-xs text-gray-500">—</span>
        )
      case "company_keywords": {
        const companyKeywordsArr = candidate.company_keywords
        if (!companyKeywordsArr || companyKeywordsArr.length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        return (
          <div className="flex flex-wrap gap-1">
            {companyKeywordsArr.slice(0, 3).map((keyword, idx) => (
              <Badge key={idx} variant="outline" className={`${badgeStyles.default} px-1 py-0`}>
                {keyword}
              </Badge>
            ))}
            {companyKeywordsArr.length > 3 && (
              <span className={textStyles.caption}>+{companyKeywordsArr.length - 3}</span>
            )}
          </div>
        )
      }

      // Status
      case "status": {
        const statusColors: Record<string, string> = {
          novo: "bg-gray-100 dark:bg-lia-bg-secondary text-gray-700 dark:text-lia-text-secondary",
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
            className={`text-xs ${statusColors[candidate.status || ""] || "bg-gray-100 text-gray-800"}`}
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
          <span className="text-xs text-gray-800">Não</span>
        )
      case "blacklist_reason":
        return (
          <span className="text-xs text-gray-800 truncate">
            {candidate.blacklist_reason || ""}
          </span>
        )

      // Comunicação
      case "preferred_contact_method":
        return (
          <span className="text-xs text-gray-800">
            {candidate.preferred_contact_method || ""}
          </span>
        )
      case "best_time_to_contact":
        return (
          <span className="text-xs text-gray-800">{candidate.best_time_to_contact || ""}</span>
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
          <span className="text-xs text-gray-800">
            {formatBoolean(candidate.completed_register)}
          </span>
        )
      case "accept_terms":
        return (
          <span className="text-xs text-gray-800">{formatBoolean(candidate.accept_terms)}</span>
        )

      // Adicional
      case "tags":
        return (
          <span className="text-xs text-gray-800 truncate">{formatArray(candidate.tags)}</span>
        )
      case "notes":
        return (
          <span className="text-xs text-gray-800 truncate">
            {candidate.notes?.slice(0, 40) || ""}
            {candidate.notes && candidate.notes.length > 40 ? "..." : ""}
          </span>
        )
      case "additional_data":
        return <span className="text-xs text-gray-800">JSON</span>

      // Datas
      case "created_at":
        return <span className="text-xs text-gray-800">{formatDate(candidate.created_at)}</span>
      case "updated_at":
        return <span className="text-xs text-gray-800">{formatDate(candidate.updated_at)}</span>
      case "last_contacted_at":
        return (
          <span className="text-xs text-gray-800">
            {formatDate(candidate.last_contacted_at)}
          </span>
        )
      case "last_activity_at":
        return (
          <span className="text-xs text-gray-800">
            {formatDate(candidate.last_activity_at)}
          </span>
        )

      default:
        return <span className="text-xs text-gray-800">N/A</span>
    }
  }
}
