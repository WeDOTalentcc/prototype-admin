"use client"

import React, { memo, useMemo, useCallback } from "react"
import { useTranslations } from "next-intl"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Eye, Mail, Linkedin, Star, Clock } from "lucide-react"
import { UnifiedCandidateTable } from "@/components/tables"
import type { TableColumn, TableCandidate } from "@/components/tables/types"
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
  const t = useTranslations('candidates.table')

  const formatRelativeDate = useCallback((dateStr?: string): string => {
    if (!dateStr) return "—"
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return t('now')
    if (diffMins < 60) return t('minAgo', { min: diffMins })
    if (diffHours < 24) return t('hoursAgo', { hours: diffHours })
    if (diffDays < 7) return t('daysAgo', { days: diffDays })
    if (diffDays < 30) return t('weeksAgo', { weeks: Math.floor(diffDays / 7) })
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })
  }, [t])

  const tableCandidates = useMemo<TableCandidate[]>(() => {
    return candidates.map(c => ({
      id: c.id,
      name: c.name,
      email: c.email,
      phone: c.phone,
      avatar_url: c.avatar_url,
      current_title: c.current_title,
      current_company: c.current_company,
      location: [c.location_city, c.location_state].filter(Boolean).join(", ") || undefined,
      location_city: c.location_city,
      location_state: c.location_state,
      lia_score: c.lia_score,
      technical_skills: c.technical_skills,
      skills: c.technical_skills,
      linkedin_url: c.linkedin_url,
      is_remote: c.is_remote,
      work_model_preference: c.work_model_preference,
      last_activity_at: c.last_activity_at,
      updated_at: c.updated_at,
    } as TableCandidate))
  }, [candidates])

  const columns = useMemo<TableColumn[]>(() => [
    { id: 'name', label: t('candidate'), visible: true, sortable: true, width: 280 },
    { id: 'current_title', label: t('currentPosition'), visible: true, sortable: true, width: 200 },
    { id: 'location', label: t('location'), visible: true, sortable: true, width: 180 },
    { id: 'lia_score', label: t('scoreLia'), visible: true, sortable: true, width: 100, align: 'center' as const },
    { id: 'skills', label: t('skills'), visible: true, sortable: false, width: 200 },
    {
      id: 'activity',
      label: t('activity'),
      visible: true,
      sortable: true,
      width: 120,
      align: 'center' as const,
      render: (candidate: TableCandidate) => {
        const dateStr = (candidate as Record<string, unknown>).last_activity_at as string
          || (candidate as Record<string, unknown>).updated_at as string
        return (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center justify-center gap-1 text-sm text-lia-text-tertiary">
                  <Clock className="h-3.5 w-3.5" />
                  <span>{formatRelativeDate(dateStr)}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p>{dateStr
                  ? t('lastActivity', { date: new Date(dateStr).toLocaleString('pt-BR') })
                  : t('notRegistered')}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )
      }
    },
    {
      id: 'actions',
      label: t('actions'),
      visible: true,
      sortable: false,
      width: 180,
      align: 'right' as const,
      render: (candidate: TableCandidate) => {
        return (
          <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
            <SearchFeedbackButtons
              candidateId={candidate.id}
              candidateName={candidate.name}
              candidateScore={candidate.lia_score}
              initialFeedback={searchFeedbacks?.[candidate.id] || null}
              onFeedbackChange={onSearchFeedback}
              size="sm"
            />
            <div className="w-px h-5 bg-lia-interactive-active dark:bg-lia-bg-elevated mx-1" />
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse">
                    <Eye className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{t('viewProfile')}</TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse">
                    <Mail className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{t('sendEmail')}</TooltipContent>
              </Tooltip>

              {candidate.linkedin_url && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-lia-text-tertiary hover:text-lia-text-secondary"
                      onClick={() => window.open(candidate.linkedin_url, "_blank")}
                    >
                      <Linkedin className="h-4 w-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>{t('viewLinkedin')}</TooltipContent>
                </Tooltip>
              )}

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-lia-text-tertiary hover:text-status-warning">
                    <Star className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>{t('favorite')}</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        )
      }
    },
  ], [searchFeedbacks, onSearchFeedback, t, formatRelativeDate])

  const handleSortChange = useCallback((config: { field: string; direction: 'asc' | 'desc' }) => {
    onSort(config.field)
  }, [onSort])

  const handleSelectionChange = useCallback((newSelection: Set<string>) => {
    const currentIds = new Set(candidates.map(c => c.id))

    const added = [...newSelection].filter(id => !selectedIds.has(id) && currentIds.has(id))
    const removed = [...selectedIds].filter(id => !newSelection.has(id) && currentIds.has(id))

    if (added.length === currentIds.size || removed.length === currentIds.size) {
      onSelectAll()
    } else {
      const changed = added.length > 0 ? added : removed
      changed.forEach(id => onToggleSelect(id))
    }
  }, [candidates, selectedIds, onSelectAll, onToggleSelect])

  const handleCandidateClick = useCallback((tableCandidate: TableCandidate) => {
    const original = candidates.find(c => c.id === tableCandidate.id)
    if (original) onCandidateClick(original)
  }, [candidates, onCandidateClick])

  if (candidates.length === 0 && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-lia-text-secondary bg-lia-bg-primary dark:bg-lia-bg-primary">
        <p className="text-lg">{t('noCandidatesFound')}</p>
        <p className="text-sm mt-2">{t('adjustFilters')}</p>
      </div>
    )
  }

  return (
    <UnifiedCandidateTable
      data-testid="candidates-table"
      candidates={tableCandidates}
      columns={columns}
      selectedIds={selectedIds}
      sortConfig={sortConfig.column ? {
        field: sortConfig.column,
        direction: sortConfig.direction
      } : undefined}
      isLoading={isLoading}
      showCheckboxes={true}
      emptyMessage={t('noCandidatesFound')}
      onCandidateClick={handleCandidateClick}
      onSelectionChange={handleSelectionChange}
      onSortChange={handleSortChange}
    />
  )
})

CandidatesTableComponent.displayName = "CandidatesTable"

export const CandidatesTable = CandidatesTableComponent
