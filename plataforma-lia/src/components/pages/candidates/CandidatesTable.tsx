"use client"

import React, { memo } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { 
  Eye, Mail, Phone, Linkedin, Star, MapPin, 
  Building, Briefcase, ArrowUpDown, ArrowUp, ArrowDown, Clock 
} from "lucide-react"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import { SearchFeedbackButtons } from "@/components/search/SearchFeedbackButtons"
import type { Candidate, SortConfig } from "./types"

interface CandidatesTableProps {
  candidates: Candidate[]
  selectedIds: Set<string>
  onToggleSelect: (candidateId: string) => void
  onSelectAll: () => void
  onCandidateClick: (candidate: Candidate) => void
  sortConfig: SortConfig
  onSort: (column: string) => void
  isLoading: boolean
  searchFeedbacks?: Record<string, 'like' | 'dislike'>
  onSearchFeedback?: (candidateId: string, feedback: 'like' | 'dislike' | null) => void
}

function formatRelativeDate(dateStr?: string): string {
  if (!dateStr) return "—"
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return "Agora"
  if (diffMins < 60) return `${diffMins}min atrás`
  if (diffHours < 24) return `${diffHours}h atrás`
  if (diffDays < 7) return `${diffDays}d atrás`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}sem atrás`
  return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse motion-reduce:animate-none">
      <td className="w-12 py-3 px-3">
        <div className="h-4 w-4 bg-gray-200 dark:bg-lia-bg-elevated rounded-md" />
      </td>
      <td className="py-3 px-3">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-gray-200 dark:bg-lia-bg-elevated rounded-full" />
          <div className="space-y-2">
            <div className="h-4 w-32 bg-gray-200 dark:bg-lia-bg-elevated rounded-md" />
            <div className="h-3 w-40 bg-gray-100 dark:bg-lia-bg-secondary rounded-md" />
          </div>
        </div>
      </td>
      <td className="py-3 px-3">
        <div className="space-y-2">
          <div className="h-4 w-28 bg-gray-200 dark:bg-lia-bg-elevated rounded-md" />
          <div className="h-3 w-20 bg-gray-100 dark:bg-lia-bg-secondary rounded-md" />
        </div>
      </td>
      <td className="py-3 px-3">
        <div className="h-4 w-24 bg-gray-200 dark:bg-lia-bg-elevated rounded-md" />
      </td>
      <td className="py-3 px-3 text-center">
        <div className="h-6 w-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-md mx-auto" />
      </td>
      <td className="py-3 px-3">
        <div className="flex gap-1">
          <div className="h-5 w-14 bg-gray-200 dark:bg-lia-bg-elevated rounded-full" />
          <div className="h-5 w-12 bg-gray-200 dark:bg-lia-bg-elevated rounded-full" />
          <div className="h-5 w-16 bg-gray-200 dark:bg-lia-bg-elevated rounded-full" />
        </div>
      </td>
      <td className="py-3 px-3">
        <div className="h-4 w-16 bg-gray-200 dark:bg-lia-bg-elevated rounded-md" />
      </td>
      <td className="py-3 px-3">
        <div className="flex justify-end gap-1">
          <div className="h-8 w-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-md" />
          <div className="h-8 w-8 bg-gray-200 dark:bg-lia-bg-elevated rounded-md" />
        </div>
      </td>
    </tr>
  )
}

const CandidatesTableComponent = memo(function CandidatesTable({
  candidates,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  onCandidateClick,
  sortConfig,
  onSort,
  isLoading,
  searchFeedbacks,
  onSearchFeedback,
}: CandidatesTableProps) {
  const allSelected = candidates.length > 0 && candidates.every((c) => selectedIds.has(c.id))
  const someSelected = candidates.some((c) => selectedIds.has(c.id)) && !allSelected

  const getSortIcon = (column: string) => {
    if (sortConfig.column !== column) {
      return <ArrowUpDown className="h-4 w-4 text-lia-text-disabled dark:text-lia-text-tertiary" />
    }
    return sortConfig.direction === "asc" 
      ? <ArrowUp className="h-4 w-4 text-lia-text-primary dark:text-lia-text-primary" />
      : <ArrowDown className="h-4 w-4 text-lia-text-primary dark:text-lia-text-primary" />
  }

  const formatScore = (score: number) => {
    return Math.round(score)
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-status-success dark:text-status-success"
    if (score >= 60) return "text-status-warning dark:text-status-warning"
    return "text-status-error dark:text-status-error"
  }

  if (isLoading) {
    return (
      <div className="overflow-auto max-h-full border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-primary">
        <table className="w-full">
          <thead className="sticky top-0 z-10 bg-white dark:bg-lia-bg-primary" style={{ boxShadow: '0 1px 0 #e5e7eb' }}>
            <tr>
              <th className="w-12 py-3 px-3"><div className="h-4 w-4 bg-gray-200 dark:bg-lia-bg-elevated rounded-md" /></th>
              <th className="text-left py-3 px-3"><span className="text-sm font-medium text-lia-text-disabled">Candidato</span></th>
              <th className="text-left py-3 px-3"><span className="text-sm font-medium text-lia-text-disabled">Cargo Atual</span></th>
              <th className="text-left py-3 px-3"><span className="text-sm font-medium text-lia-text-disabled">Localização</span></th>
              <th className="text-center py-3 px-3"><span className="text-sm font-medium text-lia-text-disabled">Score LIA</span></th>
              <th className="text-left py-3 px-3"><span className="text-sm font-medium text-lia-text-disabled">Skills</span></th>
              <th className="text-center py-3 px-3"><span className="text-sm font-medium text-lia-text-disabled">Atividade</span></th>
              <th className="text-right py-3 px-3"><span className="text-sm font-medium text-lia-text-disabled">Ações</span></th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <SkeletonRow key={i} />
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  if (candidates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-lia-text-secondary dark:text-lia-text-tertiary bg-white dark:bg-lia-bg-primary">
        <p className="text-lg">Nenhum candidato encontrado</p>
        <p className="text-sm mt-2">Tente ajustar os filtros ou fazer uma nova busca</p>
      </div>
    )
  }

  return (
    <div className="overflow-auto max-h-full border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-white dark:bg-lia-bg-primary">
      <table className="w-full">
        <thead className="sticky top-0 z-10 bg-white dark:bg-lia-bg-primary" style={{ boxShadow: '0 1px 0 #e5e7eb' }}>
          <tr>
            <th className="w-12 py-3 px-3 text-center">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={() => onSelectAll()}
                className="w-4 h-4 rounded-md"
              />
            </th>
            <th className="text-left py-3 px-3">
              <button 
                onClick={() => onSort("name")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Candidato
                {getSortIcon("name")}
              </button>
            </th>
            <th className="text-left py-3 px-3">
              <button 
                onClick={() => onSort("current_title")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Cargo Atual
                {getSortIcon("current_title")}
              </button>
            </th>
            <th className="text-left py-3 px-3">
              <button 
                onClick={() => onSort("location")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Localização
                {getSortIcon("location")}
              </button>
            </th>
            <th className="text-center py-3 px-3">
              <button 
                onClick={() => onSort("lia_score")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Score LIA
                {getSortIcon("lia_score")}
              </button>
            </th>
            <th className="text-left py-3 px-3">
              <span className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary">Skills</span>
            </th>
            <th className="text-center py-3 px-3">
              <button 
                onClick={() => onSort("last_activity_at")}
                className="flex items-center gap-2 text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
              >
                Atividade
                {getSortIcon("last_activity_at")}
              </button>
            </th>
            <th className="text-right py-3 px-3">
              <span className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary">Ações</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => (
            <tr
              key={candidate.id}
              className="border-b border-lia-border-subtle dark:border-lia-border-subtle hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors motion-reduce:transition-none"
              onClick={() => onCandidateClick(candidate)}
            >
              <td className="w-12 py-3 px-3 text-center" onClick={(e) => e.stopPropagation()}>
                <input
                  type="checkbox"
                  checked={selectedIds.has(candidate.id)}
                  onChange={() => onToggleSelect(candidate.id)}
                  className="w-4 h-4 rounded-md"
                />
              </td>
              <td className="py-3 px-3">
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarImage src={candidate.avatar_url} alt={candidate.name} />
                    <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-secondary">
                      {candidate.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium text-lia-text-primary dark:text-lia-text-primary">{candidate.name}</div>
                    <div className="text-sm text-lia-text-tertiary dark:text-lia-text-tertiary">{candidate.email}</div>
                  </div>
                </div>
              </td>
              <td className="py-3 px-3">
                <div className="flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-lia-text-disabled dark:text-lia-text-tertiary" />
                  <span className="text-lia-text-primary dark:text-lia-text-primary">{candidate.current_title || "Não informado"}</span>
                </div>
                {candidate.current_company && (
                  <div className="flex items-center gap-2 mt-1">
                    <Building className="h-3 w-3 text-lia-text-disabled dark:text-lia-text-tertiary" />
                    <span className="text-sm text-lia-text-tertiary dark:text-lia-text-tertiary">{candidate.current_company}</span>
                  </div>
                )}
              </td>
              <td className="py-3 px-3">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-lia-text-disabled dark:text-lia-text-tertiary" />
                  <span className="text-lia-text-primary dark:text-lia-text-primary">{candidate.location || "Não informado"}</span>
                </div>
                {candidate.is_remote && (
                  <Badge variant="outline" className="mt-1 text-xs border-lia-border-default dark:border-lia-border-default text-lia-text-secondary dark:text-lia-text-tertiary">
                    Remoto
                  </Badge>
                )}
              </td>
              <td className="py-3 px-3 text-center">
                {candidate.lia_score ? (
                  <div className={`text-lg font-bold ${getScoreColor(candidate.lia_score)}`}>
                    {formatScore(candidate.lia_score)}
                  </div>
                ) : (
                  <span className="text-lia-text-disabled dark:text-lia-text-tertiary">-</span>
                )}
              </td>
              <td className="py-3 px-3">
                <div className="flex flex-wrap gap-1 max-w-sidebar-content">
                  {candidate.technical_skills?.slice(0, 3).map((skill) => (
                    <Badge 
                      key={skill} 
                      variant="outline" 
                      className="text-xs border-lia-border-default dark:border-lia-border-default text-lia-text-secondary dark:text-lia-text-secondary"
                    >
                      {skill}
                    </Badge>
                  ))}
                  {(candidate.technical_skills?.length || 0) > 3 && (
                    <Badge variant="outline" className="text-xs border-lia-border-default dark:border-lia-border-default text-lia-text-tertiary dark:text-lia-text-tertiary">
                      +{(candidate.technical_skills?.length || 0) - 3}
                    </Badge>
                  )}
                </div>
              </td>
              <td className="py-3 px-3 text-center">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center justify-center gap-1 text-sm text-lia-text-tertiary dark:text-lia-text-tertiary">
                        <Clock className="h-3.5 w-3.5" />
                        <span>{formatRelativeDate(candidate.last_activity_at || candidate.updated_at)}</span>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Última atividade: {candidate.last_activity_at || candidate.updated_at 
                        ? new Date(candidate.last_activity_at || candidate.updated_at || '').toLocaleString('pt-BR') 
                        : 'Não registrada'}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </td>
              <td className="py-3 px-3" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-end gap-1">
                  <SearchFeedbackButtons
                    candidateId={candidate.id}
                    candidateName={candidate.name}
                    candidateScore={candidate.lia_score}
                    initialFeedback={searchFeedbacks?.[candidate.id] || null}
                    onFeedbackChange={onSearchFeedback}
                    size="sm"
                  />
                  <div className="w-px h-5 bg-gray-200 dark:bg-lia-bg-elevated mx-1" />
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-lia-text-tertiary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Ver perfil</TooltipContent>
                    </Tooltip>
                    
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-lia-text-tertiary dark:text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse">
                          <Mail className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Enviar email</TooltipContent>
                    </Tooltip>
                    
                    {candidate.linkedin_url && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="icon" 
                            className="h-8 w-8 text-lia-text-tertiary dark:text-lia-text-tertiary hover:text-lia-text-secondary"
                            onClick={() => window.open(candidate.linkedin_url, "_blank")}
                          >
                            <Linkedin className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Ver LinkedIn</TooltipContent>
                      </Tooltip>
                    )}
                    
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-lia-text-tertiary dark:text-lia-text-tertiary hover:text-status-warning">
                          <Star className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Favoritar</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
})

CandidatesTableComponent.displayName = "CandidatesTable"

export const CandidatesTable = CandidatesTableComponent
