// @ts-nocheck
"use client"

import { Button } from "@/components/ui/button"
import { ChevronDown, Loader2 } from "lucide-react"

interface CandidatesLoadMoreFooterProps {
  showSearchResults: boolean
  displayedResultsCount: number
  sortedCandidatesLength: number
  isLoadingMore: boolean
  onLoadMore: () => void
}

export function CandidatesLoadMoreFooter({
  showSearchResults,
  displayedResultsCount,
  sortedCandidatesLength,
  isLoadingMore,
  onLoadMore,
}: CandidatesLoadMoreFooterProps) {
  return (
    <>
      {showSearchResults && displayedResultsCount < sortedCandidatesLength && (
        <div className="flex-shrink-0 bg-white dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle py-3 px-4">
          <div className="flex flex-col items-center gap-1.5">
            <Button
              variant="outline"
              className="w-full max-w-md h-10 gap-2 text-sm font-medium"
              onClick={onLoadMore}
              disabled={isLoadingMore}
            >
              {isLoadingMore ? (
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
              {isLoadingMore ? "Carregando..." : "Carregar mais 10 candidatos"}
            </Button>
            <span className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
              {Math.min(displayedResultsCount, sortedCandidatesLength)} de {sortedCandidatesLength} candidatos
            </span>
          </div>
        </div>
      )}
      {showSearchResults && displayedResultsCount >= sortedCandidatesLength && sortedCandidatesLength > 10 && (
        <p className="flex-shrink-0 text-center text-sm text-lia-text-tertiary py-3" aria-live="polite" aria-atomic="true">
          Todos os {sortedCandidatesLength} candidatos carregados
        </p>
      )}
    </>
  )
}
