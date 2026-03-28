"use client"

import React from "react"
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

export function CandidatesHeader({
  totalCount,
  selectedCount,
  onAddCandidate,
  onToggleFilters,
  showFilters,
}: CandidatesHeaderProps) {
  return (
    <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 px-6 py-4 bg-white dark:bg-gray-900">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-gray-600 dark:text-gray-400" />
          <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-50">Funil de Talentos</h1>
        </div>
        
        <Badge variant="outline" className="border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400">
          {totalCount.toLocaleString()} candidatos
        </Badge>
        
        {selectedCount > 0 && (
          <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700">
            {selectedCount} selecionados
          </Badge>
        )}
      </div>
      
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleFilters}
 className={showFilters ? "text-gray-900" : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-50"}
        >
          <Filter className="h-4 w-4 mr-2" />
          Filtros
        </Button>
        
        <Button
          onClick={onAddCandidate}
          size="sm"
          className="bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:hover:bg-gray-200 text-white dark:text-gray-900"
        >
          <Plus className="h-4 w-4 mr-2" />
          Adicionar
        </Button>
      </div>
    </div>
  )
}
