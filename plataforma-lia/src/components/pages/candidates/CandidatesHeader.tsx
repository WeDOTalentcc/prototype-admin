"use client"

import React, { memo } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Users, Plus, Filter, ArrowUpDown } from "lucide-react"
import { LIAIcon } from "@/components/ui/lia-icon"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"

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
  return (
    <div className="flex items-center justify-between border-b border-lia-border-subtle dark:border-lia-border-subtle px-6 py-4 bg-white dark:bg-lia-bg-primary">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-lia-text-secondary" />
          <h1 className="text-lg font-semibold text-lia-text-primary">Funil de Talentos</h1>
        </div>
        
        <Badge variant="outline" className="border-lia-border-default dark:border-lia-border-default text-lia-text-secondary">
          {totalCount.toLocaleString()} candidatos
        </Badge>
        
        {selectedCount > 0 && (
          <Badge className="bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
            {selectedCount} selecionados
          </Badge>
        )}
      </div>
      
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleFilters}
 className={showFilters ? "text-lia-text-primary" : "text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"}
        >
          <Filter className="h-4 w-4 mr-2" />
          Filtros
        </Button>
        
        <Button
          onClick={onAddCandidate}
          size="sm"
          className="bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:hover:bg-gray-200 text-white"
        >
          <Plus className="h-4 w-4 mr-2" />
          Adicionar
        </Button>
      </div>
    </div>
  )
})
CandidatesHeader.displayName = 'CandidatesHeader'

export { CandidatesHeader }
