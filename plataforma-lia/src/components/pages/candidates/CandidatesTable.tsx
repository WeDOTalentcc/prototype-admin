"use client"

import React from "react"
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
    <tr className="border-b border-gray-200 dark:border-gray-700 animate-pulse">
      <td className="w-12 p-4">
        <div className="h-4 w-4 bg-gray-200 dark:bg-gray-700 rounded" />
      </td>
      <td className="p-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded-full" />
          <div className="space-y-2">
            <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded" />
            <div className="h-3 w-40 bg-gray-100 dark:bg-gray-800 rounded" />
          </div>
        </div>
      </td>
      <td className="p-4">
        <div className="space-y-2">
          <div className="h-4 w-28 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="h-3 w-20 bg-gray-100 dark:bg-gray-800 rounded" />
        </div>
      </td>
      <td className="p-4">
        <div className="h-4 w-24 bg-gray-200 dark:bg-gray-700 rounded" />
      </td>
      <td className="p-4 text-center">
        <div className="h-6 w-8 bg-gray-200 dark:bg-gray-700 rounded mx-auto" />
      </td>
      <td className="p-4">
        <div className="flex gap-1">
          <div className="h-5 w-14 bg-gray-200 dark:bg-gray-700 rounded-full" />
          <div className="h-5 w-12 bg-gray-200 dark:bg-gray-700 rounded-full" />
          <div className="h-5 w-16 bg-gray-200 dark:bg-gray-700 rounded-full" />
        </div>
      </td>
      <td className="p-4">
        <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded" />
      </td>
      <td className="p-4">
        <div className="flex justify-end gap-1">
          <div className="h-8 w-8 bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="h-8 w-8 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      </td>
    </tr>
  )
}

export function CandidatesTable({
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
      return <ArrowUpDown className="h-4 w-4 text-gray-400 dark:text-gray-500" />
    }
    return sortConfig.direction === "asc" 
      ? <ArrowUp className="h-4 w-4 text-gray-900 dark:text-gray-50" />
      : <ArrowDown className="h-4 w-4 text-gray-900 dark:text-gray-50" />
  }

  const formatScore = (score: number) => {
    return Math.round(score)
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-600 dark:text-emerald-400"
    if (score >= 60) return "text-amber-600 dark:text-amber-400"
    return "text-red-600 dark:text-red-400"
  }

  if (isLoading) {
    return (
      <div className="overflow-x-auto bg-white dark:bg-gray-900">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <tr>
              <th className="w-12 p-4"><div className="h-4 w-4 bg-gray-200 dark:bg-gray-700 rounded" /></th>
              <th className="text-left p-4"><span className="text-sm font-medium text-gray-400">Candidato</span></th>
              <th className="text-left p-4"><span className="text-sm font-medium text-gray-400">Cargo Atual</span></th>
              <th className="text-left p-4"><span className="text-sm font-medium text-gray-400">Localização</span></th>
              <th className="text-center p-4"><span className="text-sm font-medium text-gray-400">Score LIA</span></th>
              <th className="text-left p-4"><span className="text-sm font-medium text-gray-400">Skills</span></th>
              <th className="text-center p-4"><span className="text-sm font-medium text-gray-400">Atividade</span></th>
              <th className="text-right p-4"><span className="text-sm font-medium text-gray-400">Ações</span></th>
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
      <div className="flex flex-col items-center justify-center py-20 text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-900">
        <p className="text-lg">Nenhum candidato encontrado</p>
        <p className="text-sm mt-2">Tente ajustar os filtros ou fazer uma nova busca</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto bg-white dark:bg-gray-900">
      <table className="w-full">
        <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <tr>
            <th className="w-12 p-4">
              <Checkbox
                checked={allSelected}
                onCheckedChange={onSelectAll}
                className="border-gray-300 dark:border-gray-600"
              />
            </th>
            <th className="text-left p-4">
              <button 
                onClick={() => onSort("name")}
                className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Candidato
                {getSortIcon("name")}
              </button>
            </th>
            <th className="text-left p-4">
              <button 
                onClick={() => onSort("current_title")}
                className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Cargo Atual
                {getSortIcon("current_title")}
              </button>
            </th>
            <th className="text-left p-4">
              <button 
                onClick={() => onSort("location")}
                className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Localização
                {getSortIcon("location")}
              </button>
            </th>
            <th className="text-center p-4">
              <button 
                onClick={() => onSort("lia_score")}
                className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Score LIA
                {getSortIcon("lia_score")}
              </button>
            </th>
            <th className="text-left p-4">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Skills</span>
            </th>
            <th className="text-center p-4">
              <button 
                onClick={() => onSort("last_activity_at")}
                className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
              >
                Atividade
                {getSortIcon("last_activity_at")}
              </button>
            </th>
            <th className="text-right p-4">
              <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Ações</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => (
            <tr
              key={candidate.id}
              className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
              onClick={() => onCandidateClick(candidate)}
            >
              <td className="w-12 p-4" onClick={(e) => e.stopPropagation()}>
                <Checkbox
                  checked={selectedIds.has(candidate.id)}
                  onCheckedChange={() => onToggleSelect(candidate.id)}
                  className="border-gray-300 dark:border-gray-600"
                />
              </td>
              <td className="p-4">
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarImage src={candidate.avatar_url} alt={candidate.name} />
                    <AvatarFallback className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                      {candidate.name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium text-gray-900 dark:text-gray-50">{candidate.name}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">{candidate.email}</div>
                  </div>
                </div>
              </td>
              <td className="p-4">
                <div className="flex items-center gap-2">
                  <Briefcase className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  <span className="text-gray-800 dark:text-gray-200">{candidate.current_title || "Não informado"}</span>
                </div>
                {candidate.current_company && (
                  <div className="flex items-center gap-2 mt-1">
                    <Building className="h-3 w-3 text-gray-400 dark:text-gray-500" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">{candidate.current_company}</span>
                  </div>
                )}
              </td>
              <td className="p-4">
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-gray-400 dark:text-gray-500" />
                  <span className="text-gray-800 dark:text-gray-200">{candidate.location || "Não informado"}</span>
                </div>
                {candidate.is_remote && (
                  <Badge variant="outline" className="mt-1 text-xs border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400">
                    Remoto
                  </Badge>
                )}
              </td>
              <td className="p-4 text-center">
                {candidate.lia_score ? (
                  <div className={`text-lg font-bold ${getScoreColor(candidate.lia_score)}`}>
                    {formatScore(candidate.lia_score)}
                  </div>
                ) : (
                  <span className="text-gray-400 dark:text-gray-500">-</span>
                )}
              </td>
              <td className="p-4">
                <div className="flex flex-wrap gap-1 max-w-[200px]">
                  {candidate.technical_skills?.slice(0, 3).map((skill) => (
                    <Badge 
                      key={skill} 
                      variant="outline" 
                      className="text-xs border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
                    >
                      {skill}
                    </Badge>
                  ))}
                  {(candidate.technical_skills?.length || 0) > 3 && (
                    <Badge variant="outline" className="text-xs border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400">
                      +{(candidate.technical_skills?.length || 0) - 3}
                    </Badge>
                  )}
                </div>
              </td>
              <td className="p-4 text-center">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center justify-center gap-1 text-sm text-gray-500 dark:text-gray-400">
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
              <td className="p-4" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center justify-end gap-1">
                  <SearchFeedbackButtons
                    candidateId={candidate.id}
                    candidateName={candidate.name}
                    candidateScore={candidate.lia_score}
                    initialFeedback={searchFeedbacks?.[candidate.id] || null}
                    onFeedbackChange={onSearchFeedback}
                    size="sm"
                  />
                  <div className="w-px h-5 bg-gray-200 dark:bg-gray-700 mx-1" />
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-50">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Ver perfil</TooltipContent>
                    </Tooltip>
                    
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-50">
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
                            className="h-8 w-8 text-gray-500 dark:text-gray-400 hover:text-gray-600"
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
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 dark:text-gray-400 hover:text-amber-500">
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
}
