"use client"

import React from"react"
import { useTranslations } from "next-intl"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { X } from"lucide-react"

export interface ActiveFiltersBadgeProps {
  quickFilters: Set<string>
  searchTerm: string
  getActiveAdvancedFiltersCount: () => number
  selectedCandidatesForBatch: Set<string>
  deselectAllCandidates: () => void
}

export function ActiveFiltersBadge({
  quickFilters,
  searchTerm,
  getActiveAdvancedFiltersCount,
  selectedCandidatesForBatch,
  deselectAllCandidates,
}: ActiveFiltersBadgeProps) {
  const t = useTranslations('candidates')
  const hasActiveFilters = quickFilters.size > 0 || !!searchTerm || getActiveAdvancedFiltersCount() > 0

  if (!hasActiveFilters) return null

  return (
    <div data-testid="active-filters-badge" className="mb-1.5 flex items-center gap-2">
      <Chip density="relaxed" variant="neutral" muted data-testid="active-filters-indicator" className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-0">
        {t('activeFiltersBadge.activeFilters')}
      </Chip>
      {selectedCandidatesForBatch.size > 0 && (
        <Button
          data-testid="clear-selection-btn"
          variant="ghost"
          size="sm"
          onClick={deselectAllCandidates}
          className="h-6 px-2 text-xs text-lia-text-primary hover:text-lia-text-primary"
        >
          <X className="w-3 h-3 mr-1" />
          {t('activeFiltersBadge.clearSelection')}
        </Button>
      )}
    </div>
  )
}
