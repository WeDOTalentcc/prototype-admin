"use client"

import React, { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip"
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
  Eye
} from "lucide-react"

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
  source: "local" | "pearch"
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
  onLoadMore,
  onSelectCandidate,
  onAddToJob,
  onCompare,
  onSaveAsArchetype,
  onSaveToBase,
  threadId
}: SearchResultsCardProps) {
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
    const parts = name.split(" ")
    return parts.length > 1 
      ? `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
      : name.slice(0, 2).toUpperCase()
  }

  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-600"
    if (score >= 80) return "text-status-success"
    if (score >= 60) return "text-status-warning"
    return "text-wedo-orange"
  }

  return (
    <Card className="w-full border border-gray-200">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Search className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <CardTitle className="text-lg font-semibold text-gray-800">
              Resultados da busca
            </CardTitle>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200">
            {localCount > 0 && (
              <Badge variant="outline" className="border-gray-300 bg-gray-50">
                <Database className="h-3 w-3 mr-1" />
                {localCount} local
              </Badge>
            )}
            {pearchCount > 0 && (
              <Badge variant="outline" className="border-gray-300 bg-gray-50 text-gray-800 dark:text-gray-200">
                <Globe className="h-3 w-3 mr-1" />
                {pearchCount} Pearch
              </Badge>
            )}
          </div>
        </div>
        <div className="flex items-center justify-between mt-1">
          <p className="text-sm text-gray-800 dark:text-gray-200">
            "{query}" - {totalCount} candidatos encontrados
            {searchTimeSeconds && ` em ${searchTimeSeconds.toFixed(2)}s`}
          </p>
          {onSaveAsArchetype && totalCount > 0 && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs gap-1.5 text-gray-800 dark:text-gray-200 hover:text-gray-800 hover:bg-gray-100"
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

      <CardContent className="pt-0">
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2 mb-3 p-2 bg-gray-50 rounded-md border border-gray-200">
            <span className="text-sm text-gray-600">
              {selectedIds.size} selecionado(s)
            </span>
            <div className="flex-1" />
            {onAddToJob && (
              <Button 
                size="sm" 
                variant="outline"
                className="border-gray-200 text-gray-800 dark:text-gray-200 hover:bg-gray-100"
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
                className="border-gray-300"
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
                className={`flex items-center gap-3 p-3 rounded-md border transition-colors cursor-pointer
                  ${selectedIds.has(candidate.id) 
                    ? "bg-gray-50 border-gray-300" 
                    : "bg-white border-gray-100 hover:bg-gray-50"
                  }`}
                onClick={() => onSelectCandidate?.(candidate)}
              >
                <Checkbox
                  checked={selectedIds.has(candidate.id)}
                  onCheckedChange={() => toggleSelection(candidate.id)}
                  onClick={(e) => e.stopPropagation()}
                  className="data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900 dark:data-[state=checked]:bg-gray-50 dark:data-[state=checked]:border-gray-50"
                />

                <Avatar className="h-10 w-10 flex-shrink-0">
                  {candidate.picture_url ? (
                    <AvatarImage src={candidate.picture_url} alt={candidate.name} />
                  ) : null}
                  <AvatarFallback className="bg-gray-100 text-gray-600 text-sm">
                    {getInitials(candidate.name)}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-800 truncate">
                      {candidate.name}
                    </span>
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
                        <Badge 
                          variant="outline" 
                          className={`text-xs ${
                            candidate.source === "local" 
                              ? "border-gray-300 bg-gray-50 text-gray-600" 
                              : "border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-50"
                          }`}
                        >
                          {candidate.source === "local" ? (
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
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        {candidate.source === "local" 
                          ? "Candidato da sua base de dados local" 
                          : "Candidato encontrado na busca global (Pearch)"}
                      </TooltipContent>
                    </Tooltip>
                    {candidate.is_discovered && (
                      <Tooltip>
                        <TooltipTrigger>
                          <Badge 
                            variant="outline" 
                            className="text-xs border-status-warning/30 bg-status-warning/10 text-status-warning"
                          >
                            <Eye className="h-3 w-3 mr-1" />
                            Descoberto
                          </Badge>
                        </TooltipTrigger>
                        <TooltipContent>
                          Candidato descoberto ainda não salvo na sua base local
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-sm text-gray-800 dark:text-gray-200 mt-0.5">
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
                        <Badge 
                          key={idx} 
                          variant="secondary" 
                          className="text-xs bg-gray-100 text-gray-600 font-normal"
                        >
                          {skill}
                        </Badge>
                      ))}
                      {candidate.skills.length > 4 && (
                        <Badge 
                          variant="secondary" 
                          className="text-xs bg-gray-100 text-gray-800 dark:text-gray-200 font-normal"
                        >
                          +{candidate.skills.length - 4}
                        </Badge>
                      )}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <div className="flex items-center gap-1">
                    {candidate.has_email && (
                      <Tooltip>
                        <TooltipTrigger>
                          <Mail className="h-4 w-4 text-gray-600" />
                        </TooltipTrigger>
                        <TooltipContent>Email disponível</TooltipContent>
                      </Tooltip>
                    )}
                    {candidate.has_phone && (
                      <Tooltip>
                        <TooltipTrigger>
                          <Phone className="h-4 w-4 text-gray-600" />
                        </TooltipTrigger>
                        <TooltipContent>Telefone disponível</TooltipContent>
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
                            className="text-gray-600 hover:text-gray-700"
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
                          className="h-7 px-2 text-xs border-gray-900 dark:border-gray-50 text-gray-900 dark:text-gray-50 hover:bg-gray-100 dark:hover:bg-gray-800"
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

                  <ChevronRight className="h-5 w-5 text-gray-300" />
                </div>
              </div>
            </TooltipProvider>
          ))}
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
            <Button
              variant="ghost"
              size="sm"
              disabled={currentPage === 0}
              onClick={() => setCurrentPage(p => p - 1)}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Anterior
            </Button>
            <span className="text-sm text-gray-800 dark:text-gray-200">
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
          <div className="mt-3 pt-3 border-t border-gray-100">
            <Button 
              variant="outline" 
              className="w-full border-gray-200 text-gray-800 dark:text-gray-200 hover:bg-gray-100"
              onClick={onLoadMore}
            >
              <Globe className="h-4 w-4 mr-2" />
              Buscar mais candidatos na Base Global
            </Button>
            {creditsRemaining !== undefined && (
              <p className="text-xs text-center text-gray-800 dark:text-gray-200 mt-1">
                {creditsRemaining} créditos restantes
              </p>
            )}
          </div>
        )}

        {selectedIds.size > 0 && (
          <div className="mt-3 p-2 bg-gray-50 rounded text-center">
            <p className="text-sm text-gray-600">
              Dica: Diga "adicione os selecionados à vaga X" ou "compare os candidatos selecionados"
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default SearchResultsCard
