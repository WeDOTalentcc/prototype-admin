"use client"

import React, { useState } from"react"
import { useLiaEntitySelection } from "@/hooks/shared/use-lia-entity-selection"
import { getPercentageScoreColorClass } from"@/lib/score-utils"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Checkbox } from"@/components/ui/checkbox"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from"@/components/ui/tooltip"
import { 
  MapPin, 
  Briefcase, 
  Mail, 
  Phone, 
  Linkedin, 
  ChevronRight, 
  ChevronLeft,
  Search,
  Database,
  Globe,
  CheckCircle,
  Star,
  UserPlus,
  Users,
  ExternalLink,
  Target,
  Brain,
  Save,
  Eye,
  Loader2,
  Zap
  MessageSquareText,
} from"lucide-react"

export interface CandidateResult {
  id: string
  name: string
  first_name?: string
  last_name?: string
  picture_url?: string
  avatar_url?: string
  headline?: string
  current_title?: string
  current_company?: string
  location?: string
  total_experience_years?: number
  years_experience?: number
  years_of_experience?: number
  seniority_level?: string
  skills: string[]
  score?: number
  match_score?: number
  match_summary?: string
  match_reasoning?: string
  linkedin_url?: string
  has_email: boolean
  has_phone: boolean
  email?: string
  phone?: string
  mobile_phone?: string
  secondary_email?: string
  source:"local" |"pearch"
  contact_source?: "local" | "pearch" | "apify" | null
  enrichment_source?: "pearch" | "apify" | "local" | null
  is_enriching?: boolean
  is_open_to_work?: boolean
  is_opentowork?: boolean
  is_decision_maker?: boolean
  is_top_universities?: boolean
  is_startup?: boolean
  company_info?: Record<string, unknown>
  expertise?: string[]
  outreach_message?: string
  pearch_profile_id?: string
  is_discovered?: boolean
}

interface SearchResultsCardProps {
  query: string
  candidates: CandidateResult[]
  localCount: number
  pearchCount: number
  totalCount: number
  creditsRemaining?: number
  searchTimeSeconds?: number
  warningMessage?: string
  canLoadMore: boolean
  isEnrichingContacts?: boolean
  onLoadMore?: () => void
  onSelectCandidate?: (candidate: CandidateResult) => void
  onAddToJob?: (candidateIds: string[]) => void
  onCompare?: (candidateIds: string[]) => void
  onSaveAsArchetype?: (query: string) => void
  onSaveToBase?: (candidateId: string) => void
  threadId?: string
}

export function SearchResultsCard({
  query,
  candidates,
  localCount,
  pearchCount,
  totalCount,
  creditsRemaining,
  searchTimeSeconds,
  warningMessage,
  canLoadMore,
  isEnrichingContacts,
  onLoadMore,
  onSelectCandidate,
  onAddToJob,
  onCompare,
  onSaveAsArchetype,
  onSaveToBase,
  threadId
}: SearchResultsCardProps) {
  const { openEntityChat } = useLiaEntitySelection()
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [currentPage, setCurrentPage] = useState(0)
  const pageSize = 5
  const totalPages = Math.ceil(candidates.length / pageSize)

  const toggleSelection = (id: string) => {
    const newSet = new Set(selectedIds)
    if (newSet.has(id)) {
      newSet.delete(id)
    } else {
      newSet.add(id)
    }
    setSelectedIds(newSet)
  }

  const selectAll = () => {
    const pageIds = paginatedCandidates.map(c => c.id)
    const allSelected = pageIds.every(id => selectedIds.has(id))
    const newSet = new Set(selectedIds)
    if (allSelected) {
      pageIds.forEach(id => newSet.delete(id))
    } else {
      pageIds.forEach(id => newSet.add(id))
    }
    setSelectedIds(newSet)
  }

  const paginatedCandidates = candidates.slice(
    currentPage * pageSize,
    (currentPage + 1) * pageSize
  )

  const getInitials = (name: string) => {
    const parts = name.split("")
    return parts.length > 1 
      ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
      : name.slice(0, 2).toUpperCase()
  }

  const getScoreColor = (score?: number) => {
    if (!score) return"text-lia-text-secondary"
    return getPercentageScoreColorClass(score)
  }

  return (
    <Card className="w-full border border-lia-border-subtle">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Search className="h-5 w-5 text-lia-text-secondary" />
            <CardTitle className="text-lg font-semibold text-lia-text-primary">
              Resultados da busca
            </CardTitle>
          </div>
          <div className="flex items-center gap-2 text-sm text-lia-text-primary">
            {localCount > 0 && (
              <Chip variant="neutral" className="border-lia-border-default bg-lia-bg-secondary">
                <Database className="h-3 w-3 mr-1" />
                {localCount} local
              </Chip>
            )}
            {pearchCount > 0 && (
              <Chip variant="neutral" className="border-lia-border-default bg-lia-bg-secondary text-lia-text-primary">
                <Globe className="h-3 w-3 mr-1" />
                {pearchCount} Pearch
              </Chip>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between mt-1">
          <p className="text-sm text-lia-text-primary">"{query}" - {totalCount} candidatos encontrados
            {searchTimeSeconds && ` em ${searchTimeSeconds.toFixed(2)}s`}
          </p>
          {onSaveAsArchetype && totalCount > 0 && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs gap-1.5 text-lia-text-primary hover:text-lia-text-primary hover:bg-lia-bg-tertiary"
                    onClick={() => onSaveAsArchetype(query)}
                  >
                    <Target className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">Salvar Arquétipo</span>
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Salvar esta busca como arquétipo para reutilizar</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        {warningMessage && (
          <p className="text-xs text-status-warning mt-1">{warningMessage}</p>
        )}
      </CardHeader>

      {isEnrichingContacts && (
        <div className="mx-6 mb-3 flex items-center gap-2 p-3 rounded-xl border border-status-info/30 bg-status-info/10">
          <Loader2 className="h-4 w-4 animate-spin text-status-info" />
          <span className="text-sm text-status-info font-medium">Enriquecendo contatos via Apify...</span>
          <span className="text-xs text-lia-text-secondary">Isso pode levar 2-5 segundos extras</span>
        </div>
      )}

      <CardContent className="pt-0">
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2 mb-3 p-2 bg-lia-bg-secondary rounded-xl border border-lia-border-subtle">
            <span className="text-sm text-lia-text-secondary">
              {selectedIds.size} selecionado(s)
            </span>
            <div className="flex-1" />
            {onAddToJob && (
              <Button 
                size="sm" 
                variant="outline"
                className="border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-tertiary"
                onClick={() => onAddToJob(Array.from(selectedIds))}
              >
                <UserPlus className="h-4 w-4 mr-1" />
                Adicionar à vaga
              </Button>
            )}
            {onCompare && selectedIds.size >= 2 && (
              <Button 
                size="sm" 
                variant="outline"
                className="border-lia-border-default"
                onClick={() => onCompare(Array.from(selectedIds))}
              >
                <Users className="h-4 w-4 mr-1" />
                Comparar
              </Button>
            )}
          </div>
        )}

        <div className="space-y-2">
          {paginatedCandidates.map((candidate) => (
            <TooltipProvider key={candidate.id}>
              <div 
                className={`flex items-center gap-3 p-3 rounded-md border transition-colors motion-reduce:transition-none cursor-pointer
                  ${selectedIds.has(candidate.id) 
                    ?"bg-lia-bg-secondary border-lia-border-default" 
                    :"bg-lia-bg-primary border-lia-border-subtle hover:bg-lia-bg-secondary"
                  }`}
                onClick={() => onSelectCandidate?.(candidate)}
              >
                <Checkbox
                  checked={selectedIds.has(candidate.id)}
                  onCheckedChange={() => toggleSelection(candidate.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="data-[state=checked]:bg-lia-btn-primary-bg data-[state=checked]:border-lia-btn-primary-bg dark:data-[state=checked]:bg-lia-bg-secondary dark:data-[state=checked]:border-lia-border-subtle"
                />

                <Avatar className="h-10 w-10 flex-shrink-0">
                  {candidate.picture_url ? (
                    <AvatarImage src={candidate.picture_url} alt={candidate.name} />
                  ) : null}
                  <AvatarFallback className="bg-lia-bg-tertiary text-lia-text-secondary text-sm">
                    {getInitials(candidate.name)}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-lia-text-primary truncate">
                      {candidate.name}
                    </span>
                    <button
                      className="opacity-40 hover:opacity-100 transition-opacity shrink-0 p-1 rounded hover:bg-lia-bg-subtle text-lia-primary"
                      title={`Falar com LIA sobre ${candidate.name}`}
                      aria-label={`Conversar com LIA sobre ${candidate.name}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        openEntityChat({ type: 'candidate', id: String(candidate.id), name: candidate.name })
                      }}
                    >
                      <MessageSquareText className="w-[18px] h-[18px]" />
                    </button>
                    {candidate.is_open_to_work && (
                      <Tooltip>
                        <TooltipTrigger>
                          <CheckCircle className="h-4 w-4 text-status-success" />
                        </TooltipTrigger>
                        <TooltipContent>Aberto a oportunidades</TooltipContent>
                      </Tooltip>
                    )}
                    <Tooltip>
                      <TooltipTrigger>
                        <Chip 
                          variant="neutral" 
                          className={`text-xs ${
                            candidate.source ==="local" 
                              ?"border-lia-border-default bg-lia-bg-secondary text-lia-text-secondary" 
                              :"border-lia-border-default dark:border-lia-border-default bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-primary"
                          }`}
                        >
                          {candidate.source ==="local" ? (
                            <>
                              <Database className="h-3 w-3 mr-1" />
                              Local
                            </>
                          ) : (
                            <>
                              <Globe className="h-3 w-3 mr-1" />
                              Global
                            </>
                          )}
                        </Chip>
                      </TooltipTrigger>
                      <TooltipContent>
                        {candidate.source ==="local" 
                          ?"Candidato da sua base de dados local" 
                          :"Candidato encontrado na busca global (Pearch)"}
                      </TooltipContent>
                    </Tooltip>
                    {candidate.enrichment_source && (
                      <Tooltip>
                        <TooltipTrigger>
                          <Chip 
                            variant="neutral" 
                            className={`text-xs ${
                              candidate.enrichment_source === "apify"
                                ? "border-status-info/30 bg-status-info/10 text-status-info"
                                : candidate.enrichment_source === "pearch"
                                ? "border-wedo-cyan/30 bg-wedo-cyan/10 text-wedo-cyan"
                                : "border-lia-border-default bg-lia-bg-secondary text-lia-text-secondary"
                            }`}
                          >
                            <Zap className="h-3 w-3 mr-1" />
                            {candidate.enrichment_source === "apify" ? "Apify" : candidate.enrichment_source === "pearch" ? "Pearch" : "Local"}
                          </Chip>
                        </TooltipTrigger>
                        <TooltipContent>
                          {candidate.enrichment_source === "apify" 
                            ? "Contatos enriquecidos via Apify ($0.01/candidato)" 
                            : candidate.enrichment_source === "pearch"
                            ? "Contatos obtidos via Pearch"
                            : "Contatos da base local"}
                        </TooltipContent>
                      </Tooltip>
                    )}
                    {candidate.is_enriching && (
                      <Chip density="relaxed" variant="info" className="bg-status-info/10">
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Enriquecendo...
                      </Chip>
                    )}
                    {candidate.is_discovered && (
                      <Tooltip>
                        <TooltipTrigger>
                          <Chip 
                            variant="warning" 
                            className="text-xs"
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            Descoberto
                          </Chip>
                        </TooltipTrigger>
                        <TooltipContent>
                          Candidato descoberto ainda não salvo na sua base local
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-sm text-lia-text-primary mt-0.5">
                    {candidate.current_title && (
                      <span className="flex items-center gap-1 truncate">
                        <Briefcase className="h-3 w-3" />
                        {candidate.current_title}
                        {candidate.current_company && ` @ ${candidate.current_company}`}
                      </span>
                    )}
                    {candidate.location && (
                      <span className="flex items-center gap-1 truncate">
                        <MapPin className="h-3 w-3" />
                        {candidate.location}
                      </span>
                    )}
                  </div>

                  {candidate.skills.length > 0 && (
                    <div className="flex gap-1 mt-1.5 flex-wrap">
                      {candidate.skills.slice(0, 4).map((skill, idx) => (
                        <Chip 
                          key={idx} 
                          variant="neutral" muted 
                          className="text-xs bg-lia-bg-tertiary text-lia-text-secondary font-normal"
                        >
                          {skill}
                        </Chip>
                      ))}
                      {candidate.skills.length > 4 && (
                        <Chip 
                          variant="neutral" muted 
                          className="text-xs bg-lia-bg-tertiary text-lia-text-primary font-normal"
                        >
                          +{candidate.skills.length - 4}
                        </Chip>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <div className="flex items-center gap-1">
                    {candidate.has_email && (
                      <Tooltip>
                        <TooltipTrigger>
                          <Mail className={`h-4 w-4 ${candidate.contact_source === "apify" ? "text-status-info" : "text-lia-text-secondary"}`} />
                        </TooltipTrigger>
                        <TooltipContent>
                          Email disponível
                          {candidate.contact_source === "apify" && " (enriquecido via Apify)"}
                          {candidate.contact_source === "pearch" && " (via Pearch)"}
                        </TooltipContent>
                      </Tooltip>
                    )}
                    {candidate.has_phone && (
                      <Tooltip>
                        <TooltipTrigger>
                          <Phone className={`h-4 w-4 ${candidate.contact_source === "apify" ? "text-status-info" : "text-lia-text-secondary"}`} />
                        </TooltipTrigger>
                        <TooltipContent>
                          Telefone disponível
                          {candidate.contact_source === "apify" && " (enriquecido via Apify)"}
                          {candidate.contact_source === "pearch" && " (via Pearch)"}
                        </TooltipContent>
                      </Tooltip>
                    )}
                    {candidate.linkedin_url && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <a 
                            href={candidate.linkedin_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-lia-text-secondary hover:text-lia-text-primary"
                          >
                            <Linkedin className="h-4 w-4" />
                          </a>
                        </TooltipTrigger>
                        <TooltipContent>Ver LinkedIn</TooltipContent>
                      </Tooltip>
                    )}
                  </div>

                  {candidate.is_discovered && onSaveToBase && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-7 px-2 text-xs border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover"
                          onClick={(e) => {
                            e.stopPropagation()
                            onSaveToBase(candidate.id)
                          }}
                        >
                          <Save className="h-3.5 w-3.5 mr-1" />
                          Salvar na Base
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>
                        Promover este candidato para sua base local
                      </TooltipContent>
                    </Tooltip>
                  )}

                  {candidate.score && (
                    <div className={`flex items-center gap-1 ${getScoreColor(candidate.score)}`}>
                      <Star className="h-4 w-4" />
                      <span className="text-sm font-medium">{Math.round(candidate.score)}%</span>
                    </div>
                  )}

                  <ChevronRight className="h-5 w-5 text-lia-text-disabled" />
                </div>
              </div>
            </TooltipProvider>
          ))}
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-3 border-t border-lia-border-subtle">
            <Button
              variant="ghost"
              size="sm"
              disabled={currentPage === 0}
              onClick={() => setCurrentPage(p => p - 1)}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Anterior
            </Button>
            <span className="text-sm text-lia-text-primary">
              Página {currentPage + 1} de {totalPages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              disabled={currentPage >= totalPages - 1}
              onClick={() => setCurrentPage(p => p + 1)}
            >
              Próximo
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        )}

        {canLoadMore && (
          <div className="mt-3 pt-3 border-t border-lia-border-subtle">
            <Button 
              variant="outline" 
              className="w-full border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-tertiary"
              onClick={onLoadMore}
            >
              <Globe className="h-4 w-4 mr-2" />
              Buscar mais candidatos na Base Global
            </Button>
            {creditsRemaining !== undefined && (
              <p className="text-xs text-center text-lia-text-primary mt-1">
                {creditsRemaining} créditos restantes
              </p>
            )}
          </div>
        )}

        {selectedIds.size > 0 && (
          <div className="mt-3 p-2 bg-lia-bg-secondary rounded-xl text-center">
            <p className="text-sm text-lia-text-secondary">
              Dica: Diga"adicione os selecionados à vaga X" ou"compare os candidatos selecionados"
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default SearchResultsCard
