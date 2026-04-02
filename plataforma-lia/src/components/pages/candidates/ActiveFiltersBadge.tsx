"use client"

import React from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { X } from "lucide-react"

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
  const hasActiveFilters = quickFilters.size > 0 || !!searchTerm || getActiveAdvancedFiltersCount() > 0

  if (!hasActiveFilters) return null

  return (
    <div className="mb-1.5 flex items-center gap-2">
      <Badge className="text-xs bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary border-0">
        filtros ativos
      </Badge>
      {selectedCandidatesForBatch.size > 0 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={deselectAllCandidates}
          className="h-6 px-2 text-xs text-lia-text-primary hover:text-lia-text-primary"
        >
          <X className="w-3 h-3 mr-1" />
          Limpar seleção
        </Button>
      )}
    </div>
  )
}
