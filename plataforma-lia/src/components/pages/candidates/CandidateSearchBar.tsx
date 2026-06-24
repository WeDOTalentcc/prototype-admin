"use client"

/**
 * CandidateSearchBar — área de busca inteligente do Funil de Talentos.
 *
 * Renderizado quando activeTab === 'search' && !showSearchResults.
 * Sprint F5 — extração de componente de candidates-page.tsx.
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */
import React, { lazy, Suspense } from "react"
import { FileUp, Loader2, ShieldAlert, X } from "lucide-react"
import { LiaPromptHeader } from "@/components/ui/lia-prompt-header"
import { useDynamicGreeting } from "@/hooks/ui/use-dynamic-greeting"
import { useTranslations } from "next-intl"
import type { ParsedEntities } from "@/components/search/smart-search-input"
import type { SearchMode, SearchSource, SearchMetadata } from "@/components/search/smart-search-input"

const SmartSearchInput = lazy(
  () =>
    import("@/components/search/smart-search-input").then((m) => ({
      default: m.SmartSearchInput,
    }))
)

const SearchLoadingAnimation = lazy(
  () =>
    import("@/components/ui/search-loading-animation").then((m) => ({
      default: m.SearchLoadingAnimation,
    }))
)

interface PearchOptions {
  requireEmails: boolean
  requirePhoneNumbers: boolean
}

interface CandidateSearchBarProps {
  isSearchActive: boolean
  isDroppingCV: boolean
  cvUploadLoading: boolean
  searchTerm: string
  isLoading: boolean
  activeFiltersCount: number
  searchSource: SearchSource
  pearchSearchOptions: PearchOptions
  onSearchTermChange: (value: string) => void
  onSubmit: (query: string, entities: ParsedEntities, mode?: SearchMode, metadata?: SearchMetadata) => Promise<void>
  onDrop: (e: React.DragEvent<HTMLDivElement>) => void
  onDragOver: (e: React.DragEvent<HTMLDivElement>) => void
  onDragLeave: (e: React.DragEvent<HTMLDivElement>) => void
  onOpenFilters: () => void
  onGoToResults: () => void
  onSearchSourceChange: (source: SearchSource) => void
  onRequireEmailsChange: (value: boolean) => void
  onRequirePhoneNumbersChange: (value: boolean) => void
  fairnessError?: string | null
  onFairnessErrorDismiss?: () => void
}

export function CandidateSearchBar({
  isSearchActive,
  isDroppingCV,
  cvUploadLoading,
  searchTerm,
  isLoading,
  activeFiltersCount,
  searchSource,
  pearchSearchOptions,
  onSearchTermChange,
  onSubmit,
  onDrop,
  onDragOver,
  onDragLeave,
  onOpenFilters,
  onGoToResults,
  onSearchSourceChange,
  onRequireEmailsChange,
  onRequirePhoneNumbersChange,
  fairnessError,
  onFairnessErrorDismiss,
}: CandidateSearchBarProps) {
  const t = useTranslations('candidates')
  const funnelGreeting = useDynamicGreeting('funnel', t('searchBar.defaultTitle'))
  return (
    <div data-testid="candidate-search-bar" className="min-h-[60vh] flex flex-col items-center justify-center py-8">
      <div className="w-full max-w-3xl mx-auto flex flex-col">
        <LiaPromptHeader
          title={isSearchActive ? t('searchBar.searchingTitle') : funnelGreeting}
          isAnimating={isSearchActive}
        />

        <Suspense fallback={null}>
          <SearchLoadingAnimation isActive={isSearchActive} />
        </Suspense>

        <div
          className="w-full relative"
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
        >
          {isDroppingCV && (
            <div className="absolute inset-0 z-50 bg-lia-btn-primary-bg/10 border-2 border-dashed border-lia-btn-primary-bg dark:border-lia-border-subtle rounded-xl flex items-center justify-center">
              <div className="text-center">
                <FileUp className="w-12 h-12 text-lia-text-primary mx-auto mb-2" />
                <p className="text-sm font-medium text-lia-text-primary">{t('searchBar.dropCvHere')}</p>
                <p className="text-xs text-lia-text-primary">{t('searchBar.fileFormats')}</p>
              </div>
            </div>
          )}

          {cvUploadLoading && (
            <div className="absolute inset-0 z-50 bg-lia-bg-primary/90 dark:bg-lia-bg-primary/90 rounded-xl flex items-center justify-center" role="status" aria-live="polite" aria-label={t('table.loadingAriaLabel')}>
              <div className="text-center" role="status" aria-live="polite" aria-label={t('table.loadingAriaLabel')}>
                <Loader2 className="w-8 h-8 text-lia-text-primary mx-auto mb-2 animate-spin motion-reduce:animate-none" />
                <p className="text-sm font-medium text-lia-text-primary">{t('searchBar.analyzingCv')}</p>
              </div>
            </div>
          )}

          <Suspense fallback={null}>
            <SmartSearchInput
              value={searchTerm}
              onChange={onSearchTermChange}
              onSubmit={onSubmit}
              onCancel={() => onSearchTermChange('')}
              onOpenFilters={onOpenFilters}
              onGoToResults={onGoToResults}
              isLoading={isLoading}
              placeholder={t('searchBar.searchPlaceholder')}
              activeFiltersCount={activeFiltersCount}
              searchSource={searchSource}
              onSearchSourceChange={onSearchSourceChange}
              requireEmails={pearchSearchOptions.requireEmails}
              onRequireEmailsChange={onRequireEmailsChange}
              requirePhoneNumbers={pearchSearchOptions.requirePhoneNumbers}
              onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
            />
          </Suspense>

          {fairnessError && (
            <div
              role="alert"
              className="mt-3 flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-950/40 px-4 py-3 text-sm"
            >
              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden="true" />
              <p className="flex-1 text-amber-800 dark:text-amber-200">{fairnessError}</p>
              {onFairnessErrorDismiss && (
                <button
                  onClick={onFairnessErrorDismiss}
                  aria-label="Fechar aviso"
                  className="shrink-0 text-amber-600 hover:text-amber-800 dark:text-amber-400 dark:hover:text-amber-200 transition-colors"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
