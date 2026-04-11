"use client"
import React from "react"
import { RotateCcw, Bookmark } from "lucide-react"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { type SaveDestination, saveDestinations } from "../advancedFiltersTypes"

interface ModalFooterActionsProps {
  getActiveFiltersCount: () => number
  resetFilters: () => void
  onSave?: ((filters: import("../advancedFiltersTypes").SearchFilters, destination: SaveDestination) => void) | undefined
  saveDestination: SaveDestination
  onClose: () => void
  handleApply: () => void
}

export const ModalFooterActions = React.memo(function ModalFooterActions({
  getActiveFiltersCount,
  resetFilters,
  onSave,
  saveDestination,
  onClose,
  handleApply,
}: ModalFooterActionsProps) {
  return (
    <div className="flex items-center justify-between px-6 py-3 border-t border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary dark:border-lia-border-subtle">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={resetFilters}
          className="text-xs text-lia-text-secondary"
        >
          <RotateCcw className="w-3 h-3 mr-1" />
          Limpar filtros
        </Button>
        {onSave && (
          <div className="flex items-center gap-1.5 px-2 py-1 rounded-xl text-xs bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary">
            {(() => {
              const dest = saveDestinations.find(d => d.key === saveDestination)
              const Icon = dest?.icon || Bookmark
              return (
                <>
                  <Icon className="w-3 h-3" />
                  <span>Salvará em: {dest?.label}</span>
                </>
              )
            })()}
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className={textStyles.description}>
          {getActiveFiltersCount()} filtros ativos
        </span>
        <Button variant="outline" size="sm" onClick={onClose}>
          Cancelar
        </Button>
        <Button
          size="sm"
          onClick={handleApply}
          className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
        >
          Aplicar Filtros
        </Button>
      </div>
    </div>
  )
})

ModalFooterActions.displayName = "ModalFooterActions"
