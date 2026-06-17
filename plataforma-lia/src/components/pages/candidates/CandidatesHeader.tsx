"use client"

import React, { memo } from"react"
import { useTranslations } from "next-intl"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Users, Plus, Filter, ArrowUpDown } from"lucide-react"
import { LIAIcon } from"@/components/ui/lia-icon"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from"@/lib/design-tokens"

interface CandidatesHeaderProps {
  totalCount: number
  selectedCount: number
  onAddCandidate: () => void
  onToggleFilters: () => void
  showFilters: boolean
}

const CandidatesHeader = memo(function CandidatesHeader({
  totalCount,
  selectedCount,
  onAddCandidate,
  onToggleFilters,
  showFilters,
}: CandidatesHeaderProps) {
  const t = useTranslations('candidates')
  return (
    <div data-testid="candidates-header" className="flex items-center justify-between dark:border-lia-border-subtle px-6 py-4 bg-lia-bg-primary dark:bg-lia-bg-primary">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-lia-text-secondary" />
          <h1 className="text-lg font-semibold text-lia-text-primary">{t('header.title')}</h1>
        </div>
        
        <Chip data-testid="candidates-total-count" variant="neutral" className="border-lia-border-default dark:border-lia-border-default text-lia-text-secondary">
          {t('pageHeader.candidatesCount', { count: totalCount.toLocaleString() })}
        </Chip>
        
        {selectedCount > 0 && (
          <Chip variant="neutral" muted data-testid="candidates-selected-count" className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
            {t('pageHeader.selectedCount', { count: selectedCount })}
          </Chip>
        )}
      </div>
      
      <div className="flex items-center gap-2">
        <Button
          data-testid="toggle-filters-btn"
          variant="ghost"
          size="sm"
          onClick={onToggleFilters}
 className={showFilters ?"text-lia-text-primary" :"text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"}
        >
          <Filter className="h-4 w-4 mr-2" />
          {t('pageHeader.filters')}
        </Button>
        
        <Button
          data-testid="add-candidate-btn"
          onClick={onAddCandidate}
          size="sm"
          className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          {t('pageHeader.add')}
        </Button>
      </div>
    </div>
  )
})
CandidatesHeader.displayName = 'CandidatesHeader'

export { CandidatesHeader }
