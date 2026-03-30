"use client"

/**
 * CandidateSearchBar — área de busca inteligente do Funil de Talentos.
 *
 * Renderizado quando activeTab === 'search' && !showSearchResults.
 * Sprint F5 — extração de componente de candidates-page.tsx.
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */
import React, { lazy, Suspense } from "react"
import { FileUp, Loader2 } from "lucide-react"
import { LiaPromptHeader } from "@/components/ui/lia-prompt-header"
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
}: CandidateSearchBarProps) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center py-8">
      <div className="w-full max-w-3xl mx-auto flex flex-col">
        <LiaPromptHeader
          title={isSearchActive ? 'LIA está buscando...' : 'Vamos buscar de forma inteligente?'}
          isAnimating={isSearchActive}
        />

        {/* Loading Animation */}
        <Suspense fallback={null}>
          <SearchLoadingAnimation isActive={isSearchActive} />
        </Suspense>

        {/* Smart Search Input com CV Dropzone */}
        <div
          className="w-full relative"
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
        >
          {/* CV Drop Overlay */}
          {isDroppingCV && (
            <div className="absolute inset-0 z-50 bg-gray-900/10 border-2 border-dashed border-gray-900 dark:border-lia-border-subtle rounded-md flex items-center justify-center">
              <div className="text-center">
                <FileUp className="w-12 h-12 text-gray-900 dark:text-lia-text-primary mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-900 dark:text-lia-text-primary">Solte o CV aqui</p>
                <p className="text-xs text-gray-800">PDF, DOC, DOCX ou TXT</p>
              </div>
            </div>
          )}

          {/* CV Upload Loading */}
          {cvUploadLoading && (
            <div className="absolute inset-0 z-50 bg-white/90 dark:bg-lia-bg-primary/90 rounded-md flex items-center justify-center">
              <div className="text-center">
                <Loader2 className="w-8 h-8 text-gray-900 dark:text-lia-text-primary mx-auto mb-2 animate-spin" />
                <p className="text-sm font-medium text-gray-950 dark:text-gray-50">Analisando CV...</p>
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
              placeholder="Ex: Desenvolvedores Python com 5+ anos em São Paulo..."
              activeFiltersCount={activeFiltersCount}
              searchSource={searchSource}
              onSearchSourceChange={onSearchSourceChange}
              requireEmails={pearchSearchOptions.requireEmails}
              onRequireEmailsChange={onRequireEmailsChange}
              requirePhoneNumbers={pearchSearchOptions.requirePhoneNumbers}
              onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
            />
          </Suspense>
        </div>
      </div>
    </div>
  )
}
