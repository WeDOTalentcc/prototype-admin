"use client"

import { Button } from "@/components/ui/button"
import { ChevronDown, Loader2 } from "lucide-react"
import { useTranslations } from "next-intl"
import { LOAD_MORE_STEP } from "@/stores/candidates-store"

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
  const t = useTranslations('candidates')
  return (
    <>
      {showSearchResults && displayedResultsCount < sortedCandidatesLength && (
        <div className="flex-shrink-0 bg-lia-bg-primary dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle py-3 px-4">
          <div data-testid="load-more-container" className="flex flex-col items-center gap-1.5">
            <Button
              data-testid="load-more-btn"
              variant="outline"
              className="w-full max-w-md h-10 gap-2 text-sm font-medium hover:bg-lia-interactive-hover transition-colors cursor-pointer"
              onClick={onLoadMore}
              disabled={isLoadingMore}
            >
              {isLoadingMore ? (
                <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
              {isLoadingMore ? t('loadMore.loading') : t('loadMore.loadMoreCandidates', { count: LOAD_MORE_STEP })}
            </Button>
            <span className="text-xs text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
              {t('loadMore.showingOf', { displayed: Math.min(displayedResultsCount, sortedCandidatesLength), total: sortedCandidatesLength })}
            </span>
          </div>
        </div>
      )}
      {showSearchResults && displayedResultsCount >= sortedCandidatesLength && sortedCandidatesLength > 10 && (
        <p className="flex-shrink-0 text-center text-sm text-lia-text-tertiary py-3" aria-live="polite" aria-atomic="true">
          {t('loadMore.allLoaded', { total: sortedCandidatesLength })}
        </p>
      )}
    </>
  )
}
