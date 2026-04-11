"use client"

import {
  Search, Target, Plus, Loader2,
  FileText, Lightbulb
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import type { ArchetypeVacancy, SearchSource } from "./smart-search-input"
import { ArchetypeScopeButtons } from "./ArchetypeScopeButtons"
import { ArchetypeCard } from "./ArchetypeCard"
import { ArchetypeCreateTab } from "./ArchetypeCreateTab"

interface SearchModeArchetypesProps {
  archetypeTab: "list" | "create"
  onArchetypeTabChange: (tab: "list" | "create") => void
  archetypeSearch: string
  onArchetypeSearchChange: (v: string) => void
  isLoadingArchetypes: boolean
  filteredArchetypes: ArchetypeVacancy[]
  archetypeVacancies: ArchetypeVacancy[]
  selectedArchetype: ArchetypeVacancy | null
  onSelectArchetype: (arch: ArchetypeVacancy) => void
  expandedArchetypeId: string | null
  onExpandedArchetypeIdChange: (id: string | null) => void
  isDeletingArchetype: string | null
  archetypeSearchPrompt: string
  onArchetypeSearchPromptChange: (v: string) => void
  onOpenEditArchetype: (arch: ArchetypeVacancy, e: React.MouseEvent) => void
  onDeleteArchetype: (archId: string, e: React.MouseEvent) => void
  buildArchetypePrompt: (arch: ArchetypeVacancy) => string
  onSubmit: () => void
  isLoading: boolean
  searchSource?: SearchSource
  onSearchSourceChange?: (source: SearchSource) => void
  onHandleSourceChange?: (source: "hybrid" | "global") => void
  showGlobalSearchOptions: boolean
  requireEmails?: boolean
  onRequireEmailsChange?: (v: boolean) => void
  requirePhoneNumbers?: boolean
  onRequirePhoneNumbersChange?: (v: boolean) => void
  archetypeCreateMode: "job" | "description"
  onArchetypeCreateModeChange: (mode: "job" | "description") => void
  jobSearchQuery: string
  onJobSearchQueryChange: (v: string) => void
  isSearchingJobs: boolean
  jobSearchResults: Array<{
    id: string
    title: string
    department: string | null
    seniority_level: string | null
    status: string
    created_at: string
    description: string | null
    technical_requirements: string[] | null
  }>
  onOpenArchetypeFromJob: (job: { id: string; title: string; department: string | null; seniority_level: string | null; status: string; created_at: string; description: string | null; technical_requirements: string[] | null }) => void
  archetypeDescription: string
  onArchetypeDescriptionChange: (v: string) => void
  isCreatingArchetype: boolean
  onCreateArchetypeFromDescription: (description: string) => void
  onSearchJobsForArchetype: (query: string) => void
}

export function SearchModeArchetypes({
  archetypeTab,
  onArchetypeTabChange,
  archetypeSearch,
  onArchetypeSearchChange,
  isLoadingArchetypes,
  filteredArchetypes,
  archetypeVacancies,
  selectedArchetype,
  onSelectArchetype,
  expandedArchetypeId,
  onExpandedArchetypeIdChange,
  isDeletingArchetype,
  archetypeSearchPrompt,
  onArchetypeSearchPromptChange,
  onOpenEditArchetype,
  onDeleteArchetype,
  buildArchetypePrompt,
  onSubmit,
  isLoading,
  searchSource,
  onSearchSourceChange,
  onHandleSourceChange,
  showGlobalSearchOptions,
  requireEmails,
  onRequireEmailsChange,
  requirePhoneNumbers,
  onRequirePhoneNumbersChange,
  archetypeCreateMode,
  onArchetypeCreateModeChange,
  jobSearchQuery,
  onJobSearchQueryChange,
  isSearchingJobs,
  jobSearchResults,
  onOpenArchetypeFromJob,
  archetypeDescription,
  onArchetypeDescriptionChange,
  isCreatingArchetype,
  onCreateArchetypeFromDescription,
  onSearchJobsForArchetype,
}: SearchModeArchetypesProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <button
          onClick={() => onArchetypeTabChange("list")}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
            archetypeTab === "list"
              ? "bg-lia-bg-tertiary ring-1 ring-lia-border-medium"
              : "bg-lia-bg-primary ring-1 ring-lia-border-subtle hover:bg-lia-bg-secondary"
          , archetypeTab === "list" ? "text-lia-text-primary" : "text-lia-text-tertiary"
          )}
        >
          <Target className="w-3 h-3" />
          Arquétipos
        </button>
        <button
          onClick={() => onArchetypeTabChange("create")}
          className="flex items-center gap-1 h-7 px-3 rounded-xl text-xs font-medium transition-colors motion-reduce:transition-none ring-1 ring-lia-border-default hover:ring-lia-border-medium hover:bg-lia-bg-secondary bg-lia-bg-primary"
        >
          <Plus className="w-3 h-3" />
          Criar Novo
        </button>
      </div>

      {archetypeTab === "list" && (
        <>
          <div className="relative">
            <div className="absolute left-2.5 top-1/2 -translate-y-1/2">
              <Search
                className="w-3.5 h-3.5 text-lia-text-secondary"
              />
            </div>
            <input
              type="text"
              value={archetypeSearch}
              onChange={(e) => onArchetypeSearchChange(e.target.value)}
              placeholder="Buscar arquétipos..."
              className="w-full rounded-xl pl-8 pr-3 py-2 text-xs focus:outline-none focus:ring-2 border border-lia-border-default bg-lia-bg-secondary text-lia-text-primary"
            />
          </div>

          {isLoadingArchetypes ? (
            <div className="flex items-center justify-center py-6" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-primary" />
              <span className="ml-2 text-sm text-lia-text-secondary">
                Carregando arquétipos...
              </span>
            </div>
          ) : filteredArchetypes.length === 0 ? (
            <div className="text-center py-6">
              <Target className="w-8 h-8 mx-auto mb-2 text-lia-text-secondary" />
              <p className="text-sm text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                {archetypeVacancies.length === 0
                  ? "Nenhum arquétipo encontrado"
                  : "Nenhum arquétipo corresponde à busca"}
              </p>
              <Button
                onClick={() => onArchetypeTabChange("create")}
                variant="ghost"
                size="sm"
                className="mt-3 bg-lia-bg-tertiary"
              >
                <Plus className="w-3.5 h-3.5 mr-1" />
                Criar Arquétipo
              </Button>
            </div>
          ) : (
            <div className="max-h-[280px] overflow-y-auto space-y-1">
              {filteredArchetypes.map((arch) => (
                <ArchetypeCard
                  key={arch.id}
                  arch={arch}
                  isExpanded={expandedArchetypeId === arch.id}
                  isSelected={selectedArchetype?.id === arch.id}
                  isDeletingArchetype={isDeletingArchetype}
                  onToggleExpand={onExpandedArchetypeIdChange}
                  onSelectArchetype={onSelectArchetype}
                  onArchetypeSearchPromptChange={onArchetypeSearchPromptChange}
                  buildArchetypePrompt={buildArchetypePrompt}
                  onOpenEditArchetype={onOpenEditArchetype}
                  onDeleteArchetype={onDeleteArchetype}
                />
              ))}
            </div>
          )}

          {selectedArchetype && archetypeSearchPrompt && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-lia-text-primary" />
                  <span className="text-xs font-medium">Preview do prompt de busca</span>
                </div>
                <span className="text-micro text-lia-text-tertiary">editável</span>
              </div>
              <div className="relative">
                <textarea
                  value={archetypeSearchPrompt}
                  onChange={(e) => onArchetypeSearchPromptChange(e.target.value)}
                  placeholder="Descreva o perfil do arquétipo..."
                  className="w-full resize-none rounded-xl px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[60px] transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] text-lia-text-primary"
                  rows={2}
                />
                {onSearchSourceChange && (
                  <div
                    className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1 z-raised"
                  >
                    <ArchetypeScopeButtons
                      searchSource={searchSource}
                      onSearchSourceChange={onSearchSourceChange}
                      onHandleSourceChange={onHandleSourceChange}
                      showGlobalSearchOptions={showGlobalSearchOptions}
                      requireEmails={requireEmails}
                      onRequireEmailsChange={onRequireEmailsChange}
                      requirePhoneNumbers={requirePhoneNumbers}
                      onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
                      selectedArchetype={selectedArchetype}
                      isLoading={isLoading}
                      onSubmit={onSubmit}
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {(!selectedArchetype || !archetypeSearchPrompt) && (
            <div className="relative">
              <textarea
                value={archetypeSearchPrompt}
                onChange={(e) => onArchetypeSearchPromptChange(e.target.value)}
                placeholder={
                  selectedArchetype
                    ? `Buscar perfis similares a "${selectedArchetype.title}"...`
                    : "Selecione um arquétipo acima para buscar..."
                }
                className="w-full resize-none rounded-xl px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-14 transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] text-lia-text-primary"
                rows={2}
                disabled={!selectedArchetype}
              />
              {onSearchSourceChange && (
                <div
                  className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1 z-10"
                >
                  <ArchetypeScopeButtons
                    searchSource={searchSource}
                    onSearchSourceChange={onSearchSourceChange}
                    onHandleSourceChange={onHandleSourceChange}
                    showGlobalSearchOptions={showGlobalSearchOptions}
                    requireEmails={requireEmails}
                    onRequireEmailsChange={onRequireEmailsChange}
                    requirePhoneNumbers={requirePhoneNumbers}
                    onRequirePhoneNumbersChange={onRequirePhoneNumbersChange}
                    selectedArchetype={selectedArchetype}
                    isLoading={isLoading}
                    onSubmit={onSubmit}
                  />
                </div>
              )}
            </div>
          )}

          <div className="p-2.5 rounded-xl bg-white border border-lia-border-subtle">
            <div className="flex items-start gap-2">
              <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-lia-text-secondary" />
              <p className="text-xs text-lia-text-secondary">
                <strong>Dica:</strong> Arquétipos são perfis baseados em contratações bem-sucedidas.
              </p>
            </div>
          </div>
        </>
      )}

      {archetypeTab === "create" && (
        <ArchetypeCreateTab
          archetypeCreateMode={archetypeCreateMode}
          onArchetypeCreateModeChange={onArchetypeCreateModeChange}
          jobSearchQuery={jobSearchQuery}
          onJobSearchQueryChange={onJobSearchQueryChange}
          isSearchingJobs={isSearchingJobs}
          jobSearchResults={jobSearchResults}
          onOpenArchetypeFromJob={onOpenArchetypeFromJob}
          archetypeDescription={archetypeDescription}
          onArchetypeDescriptionChange={onArchetypeDescriptionChange}
          isCreatingArchetype={isCreatingArchetype}
          onCreateArchetypeFromDescription={onCreateArchetypeFromDescription}
          onSearchJobsForArchetype={onSearchJobsForArchetype}
        />
      )}
    </div>
  )
}

export default SearchModeArchetypes
