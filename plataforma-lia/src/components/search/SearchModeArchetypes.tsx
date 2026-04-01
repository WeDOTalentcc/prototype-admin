// @ts-nocheck
"use client"

import {
  Check, Search, Target, Plus, Loader2, Pencil, Trash2,
  ChevronUp, ChevronDown, FileText, Lightbulb, Briefcase,
  Brain, Home, Zap, Globe, Mail, Phone
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import type { ArchetypeVacancy, SearchSource } from "./smart-search-input"

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
      {/* Tabs: Lista / Criar */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => onArchetypeTabChange("list")}
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
            archetypeTab === "list"
              ? "bg-gray-100 ring-1 ring-gray-400"
              : "bg-lia-bg-primary ring-1 ring-gray-200 hover:bg-gray-50"
          , archetypeTab === "list" ? "lia-text-950" : "lia-text-400"
          )}
        >
          <Target className="w-3 h-3" />
          Arquétipos
        </button>
        <button
          onClick={() => onArchetypeTabChange("create")}
          className="flex items-center gap-1 h-7 px-3 rounded-md text-xs font-medium transition-colors motion-reduce:transition-none ring-1 ring-gray-300 hover:ring-gray-400 hover:bg-gray-50 bg-lia-bg-primary"
        >
          <Plus className="w-3 h-3" />
          Criar Novo
        </button>
      </div>

      {/* Lista de Arquétipos */}
      {archetypeTab === "list" && (
        <>
          <div className="relative">
            <div className="absolute left-2.5 top-1/2 -translate-y-1/2">
              <Search
                className="w-3.5 h-3.5 lia-text-500 dark:text-lia-text-tertiary"
              />
            </div>
            <input
              type="text"
              value={archetypeSearch}
              onChange={(e) => onArchetypeSearchChange(e.target.value)}
              placeholder="Buscar arquétipos..."
              className="w-full rounded-md pl-8 pr-3 py-2 text-xs focus:outline-none focus:ring-2 border border-lia-border-default bg-gray-50 lia-text-800"
            />
          </div>

          {isLoadingArchetypes ? (
            <div className="flex items-center justify-center py-6" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none lia-text-700" />
              <span className="ml-2 text-sm lia-text-500 dark:text-lia-text-tertiary">
                Carregando arquétipos...
              </span>
            </div>
          ) : filteredArchetypes.length === 0 ? (
            <div className="text-center py-6">
              <Target className="w-8 h-8 mx-auto mb-2 lia-text-500 dark:text-lia-text-tertiary" />
              <p className="text-sm lia-text-500 dark:text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                {archetypeVacancies.length === 0
                  ? "Nenhum arquétipo encontrado"
                  : "Nenhum arquétipo corresponde à busca"}
              </p>
              <Button
                onClick={() => onArchetypeTabChange("create")}
                variant="ghost"
                size="sm"
                className="mt-3 bg-gray-100"
              >
                <Plus className="w-3.5 h-3.5 mr-1" />
                Criar Arquétipo
              </Button>
            </div>
          ) : (
            <div className="max-h-[280px] overflow-y-auto space-y-1">
              {filteredArchetypes.map((arch) => {
                const isExpanded = expandedArchetypeId === arch.id
                return (
                  <div
                    key={arch.id}
                    className={cn(
                      "group relative w-full rounded-md text-left transition-colors cursor-pointer border",
                      isExpanded
                        ? "bg-gray-50 ring-1 ring-gray-900/20 border-lia-border-default"
                        : selectedArchetype?.id === arch.id
                        ? "bg-gray-50 ring-1 ring-gray-900/20 border-lia-border-default"
                        : "bg-lia-bg-primary hover:bg-gray-50 border-lia-border-subtle"
                    )}
                  >
                    <div
                      className="px-3 py-2.5"
                      onClick={() => {
                        onExpandedArchetypeIdChange(isExpanded ? null : arch.id)
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-base-ui flex-shrink-0">{arch.emoji || "🎯"}</span>
                        <span className="font-semibold text-xs truncate lia-text-800">
                          {arch.name || arch.title}
                        </span>
                        {arch.is_default && (
                          <span
                            className="text-micro px-1.5 py-0.5 rounded-full flex-shrink-0 font-medium bg-wedo-cyan/15"
                          >
                            Padrão
                          </span>
                        )}
                        {!isExpanded && arch.tags && arch.tags.length > 0 && (
                          <div className="flex items-center gap-1 ml-auto flex-shrink-0 group-hover:hidden">
                            {arch.tags.slice(0, 2).map((tag: string) => (
                              <span
                                key={tag}
                                className="text-micro px-1.5 py-0.5 rounded-full bg-gray-100"
                              >
                                {tag}
                              </span>
                            ))}
                            {arch.tags.length > 2 && (
                              <span className="text-micro px-1 py-0.5 lia-text-400">
                                +{arch.tags.length - 2}
                              </span>
                            )}
                          </div>
                        )}
                        <div className="ml-auto flex items-center gap-1 flex-shrink-0">
                          {isExpanded ? (
                            <ChevronUp className="w-3.5 h-3.5 lia-text-700" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 lia-text-400" />
                          )}
                        </div>
                      </div>
                      {!isExpanded && arch.description && (
                        <p className="mt-1 pl-5 text-micro line-clamp-1"> {/* [OPT-022] px arbitrário — sem canônico Tailwind */}
                          {arch.description}
                        </p>
                      )}
                    </div>

                    {isExpanded && (
                      <div
                        className="px-3 pb-3 space-y-2 border-t border-t-gray-200 pt-2.5"
                      >
                        {arch.description && (
                          <p className="text-micro">{arch.description}</p>
                        )}

                        <div className="space-y-1">
                          <span className="text-micro font-medium lia-text-400">Query de Busca</span>
                          <p className="text-xs p-2 rounded-md">
                            {arch.query || "Sem query definida"}
                          </p>
                        </div>

                        {arch.tags && arch.tags.length > 0 && (
                          <div className="space-y-1">
                            <span className="text-micro font-medium lia-text-400">Tags</span>
                            <div className="flex flex-wrap gap-1">
                              {arch.tags.map((tag: string) => (
                                <span
                                  key={tag}
                                  className="text-micro px-1.5 py-0.5 rounded-full bg-gray-100"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {(arch.filters as any)?.skills && (arch.filters as any).skills.length > 0 && (
                          <div className="space-y-1">
                            <span className="text-micro font-medium lia-text-400">Skills</span>
                            <div className="flex flex-wrap gap-1">
                              {(arch.filters as any).skills.map((skill: string) => (
                                <span
                                  key={skill}
                                  className="text-micro px-1.5 py-0.5 rounded-full bg-gray-100"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="flex flex-wrap gap-2 text-micro">
                          {arch.seniority && (
                            <div className="flex items-center gap-1">
                              <span className="lia-text-400">Senioridade:</span>
                              <span className="font-medium capitalize lia-text-700">
                                {arch.seniority}
                              </span>
                            </div>
                          )}
                          {arch.industry && (
                            <div className="flex items-center gap-1">
                              <span className="lia-text-400">Indústria:</span>
                              <span className="font-medium capitalize lia-text-700">
                                {arch.industry}
                              </span>
                            </div>
                          )}
                          {arch.filters?.experience_years_min && (
                            <div className="flex items-center gap-1">
                              <span className="lia-text-400">Experiência:</span>
                              <span className="font-medium lia-text-700">
                                {(arch.filters as any).experience_years_min}+ anos
                              </span>
                            </div>
                          )}
                          {arch.filters?.location && (
                            <div className="flex items-center gap-1">
                              <span className="lia-text-400">Localização:</span>
                              <span className="font-medium lia-text-700">{(arch.filters as any).location}</span>
                            </div>
                          )}
                          {arch.filters?.work_model && (
                            <div className="flex items-center gap-1">
                              <span className="lia-text-400">Modelo:</span>
                              <span className="font-medium lia-text-700">
                                {(arch.filters as any).work_model === "remote"
                                  ? "Remoto"
                                  : (arch.filters as any).work_model === "hybrid"
                                  ? "Híbrido"
                                  : (arch.filters as any).work_model === "onsite"
                                  ? "Presencial"
                                  : (arch.filters as any).work_model}
                              </span>
                            </div>
                          )}
                          {arch.filters?.employment_type && (
                            <div className="flex items-center gap-1">
                              <span className="lia-text-400">Contrato:</span>
                              <span className="font-medium lia-text-700">
                                {(arch.filters as any).employment_type === "clt"
                                  ? "CLT"
                                  : (arch.filters as any).employment_type === "pj"
                                  ? "PJ"
                                  : (arch.filters as any).employment_type === "intern"
                                  ? "Estágio"
                                  : (arch.filters as any).employment_type === "temporary"
                                  ? "Temporário"
                                  : (arch.filters as any).employment_type === "freelancer"
                                  ? "Freelancer"
                                  : (arch.filters as any).employment_type}
                              </span>
                            </div>
                          )}
                        </div>

                        {(arch.filters as any)?.languages && (arch.filters as any).languages.length > 0 && (
                          <div className="space-y-1">
                            <span className="text-micro font-medium lia-text-400">Idiomas</span>
                            <div className="flex flex-wrap gap-1">
                              {(arch.filters as any).languages.map((lang: string) => (
                                <span
                                  key={lang}
                                  className="px-1.5 py-0.5 rounded-full text-micro bg-gray-100"
                                >
                                  {lang}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="flex items-center gap-2 pt-2 mt-1 border-t border-t-gray-100">
                          <Button
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              onSelectArchetype(arch)
                              onArchetypeSearchPromptChange(buildArchetypePrompt(arch))
                              onExpandedArchetypeIdChange(null)
                            }}
                            className="flex-1 text-xs h-8 bg-gray-800 text-white"
                          >
                            <Check className="w-3 h-3 mr-1" />
                            Usar Arquétipo
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={(e) => onOpenEditArchetype(arch, e)}
                            className="text-xs h-8"
                          >
                            <Pencil className="w-3 h-3 mr-1" />
                            Editar
                          </Button>
                          {!arch.is_default && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => onDeleteArchetype(arch.id, e)}
                              disabled={isDeletingArchetype === arch.id}
                              className="text-xs px-2 text-status-error"
                            >
                              {isDeletingArchetype === arch.id ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                              ) : (
                                <Trash2 className="w-3.5 h-3.5" />
                              )}
                            </Button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}

          {/* Preview/Edit do Prompt com arquétipo selecionado */}
          {selectedArchetype && archetypeSearchPrompt && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 lia-text-700" />
                  <span className="text-xs font-medium">Preview do prompt de busca</span>
                </div>
                <span className="text-micro lia-text-400">editável</span>
              </div>
              <div className="relative">
                <textarea
                  value={archetypeSearchPrompt}
                  onChange={(e) => onArchetypeSearchPromptChange(e.target.value)}
                  placeholder="Descreva o perfil do arquétipo..."
                  className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-[60px] transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] lia-text-950"
                  rows={2}
                />
                {onSearchSourceChange && (
                  <div
                    className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1 z-[10]"
                  >
                    <ScopeButtons
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

          {/* Prompt vazio quando arquétipo não selecionado */}
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
                className="w-full resize-none rounded-md px-4 py-3 pr-28 text-base-ui focus:outline-none min-h-14 transition-colors motion-reduce:transition-none border bg-[var(--lia-bg-primary)] lia-text-950"
                rows={2}
                disabled={!selectedArchetype}
              />
              {onSearchSourceChange && (
                <div
                  className="absolute right-3 bottom-2.5 flex flex-col items-end gap-1 z-10"
                >
                  <ScopeButtons
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

          {/* Dica */}
          <div className="px-2 py-1.5 rounded-md bg-gray-50 border border-lia-border-subtle">
            <div className="flex items-center gap-1.5">
              <Lightbulb className="w-3 h-3 flex-shrink-0 lia-text-700" />
              <p className="text-xs lia-text-800 dark:text-lia-text-primary">
                <strong>Dica:</strong> Arquétipos são perfis baseados em contratações bem-sucedidas.
              </p>
            </div>
          </div>
        </>
      )}

      {/* Criar Novo Arquétipo */}
      {archetypeTab === "create" && (
        <div className="space-y-3">
          {/* Sub-tabs: Vaga Fechada / Descrição */}
          <div className="flex gap-2">
            <button
              onClick={() => onArchetypeCreateModeChange("job")}
              className={cn(
                "flex-1 px-3 py-2 rounded-md text-xs font-medium transition-colors border border-lia-border-subtle",
                archetypeCreateMode === "job"
                  ? "bg-gray-100 ring-1 ring-gray-400 lia-text-800"
                  : "bg-lia-bg-primary hover:bg-gray-50 lia-text-500"
              )}
            >
              <Briefcase className="w-3.5 h-3.5 inline mr-1.5" />
              A partir de Vaga
            </button>
            <button
              onClick={() => onArchetypeCreateModeChange("description")}
              className={cn(
                "flex-1 px-3 py-2 rounded-md text-xs font-medium transition-colors border border-lia-border-subtle",
                archetypeCreateMode === "description"
                  ? "bg-gray-100 ring-1 ring-gray-400 lia-text-800"
                  : "bg-lia-bg-primary hover:bg-gray-50 lia-text-500"
              )}
            >
              <FileText className="w-3.5 h-3.5 inline mr-1.5" />
              A partir de Descrição
            </button>
          </div>

          {/* A partir de Vaga */}
          {archetypeCreateMode === "job" && (
            <div className="space-y-2">
              <p className="text-xs lia-text-500 dark:text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                Busque por nome ou ID da vaga para criar um arquétipo:
              </p>

              <div className="relative">
                <Search
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 lia-text-400"
                />
                <input
                  type="text"
                  value={jobSearchQuery}
                  onChange={(e) => {
                    onJobSearchQueryChange(e.target.value)
                    onSearchJobsForArchetype(e.target.value)
                  }}
                  placeholder="Buscar vaga por nome ou ID..."
                  className="w-full pl-8 pr-3 py-2 rounded-md text-xs focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-lia-border-subtle"
                />
                {isSearchingJobs && (
                  <Loader2 className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 animate-spin motion-reduce:animate-none lia-text-700" />
                )}
              </div>

              {jobSearchQuery.trim() && (
                <div className="max-h-[200px] overflow-y-auto space-y-1.5 rounded-md border border-lia-border-subtle" role="status" aria-live="polite" aria-label="Carregando...">
                  {isSearchingJobs ? (
                    <div className="flex items-center justify-center py-4" role="status" aria-live="polite" aria-label="Carregando...">
                      <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none lia-text-700" />
                      <span className="ml-2 text-xs lia-text-500 dark:text-lia-text-tertiary" aria-live="polite" aria-atomic="true">
                        Buscando vagas...
                      </span>
                    </div>
                  ) : jobSearchResults.length === 0 ? (
                    <div className="text-center py-4 px-3">
                      <Briefcase className="w-5 h-5 mx-auto mb-1.5" />
                      <p className="text-xs lia-text-400" aria-live="polite" aria-atomic="true">
                        Nenhuma vaga encontrada para "{jobSearchQuery}"
                      </p>
                    </div>
                  ) : (
                    jobSearchResults.map((job) => (
                      <button
                        key={job.id}
                        onClick={() => onOpenArchetypeFromJob(job)}
                        className="w-full p-2.5 text-left transition-colors motion-reduce:transition-none hover:bg-gray-50 border-b border-lia-border-subtle last:border-b-0"
                      >
                        <div className="flex items-start gap-2">
                          <Briefcase className="w-4 h-4 mt-0.5 flex-shrink-0 lia-text-600" />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <p
                                className="font-medium text-xs truncate lia-text-950"
                              >
                                {job.title}
                              </p>
                              <span
                                className="px-1.5 py-0.5 rounded-full text-micro font-medium"
                                style={{backgroundColor:
                                    job.status === "Publicada"
                                      ? "var(--status-success-bg-15)"
                                      : job.status === "Encerrada"
                                      ? "var(--gray-light-bg-20)"
                                      : "var(--status-warning-bg-15)",
                                  color:
                                    job.status === "Publicada"
                                      ? "var(--status-success)"
                                      : job.status === "Encerrada"
                                      ? "var(--gray-400)"
                                      : "var(--status-warning)"}}
                              >
                                {job.status}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className="text-micro lia-text-400">
                                ID: {job.id.slice(0, 8)}...
                              </span>
                              {job.department && (
                                <>
                                  <span className="text-micro lia-text-300">
                                    •
                                  </span>
                                  <span className="text-micro lia-text-400">
                                    {job.department}
                                  </span>
                                </>
                              )}
                              {job.seniority_level && (
                                <>
                                  <span className="text-micro lia-text-300">
                                    •
                                  </span>
                                  <span className="text-micro lia-text-400">
                                    {job.seniority_level}
                                  </span>
                                </>
                              )}
                            </div>
                            <p className="text-micro mt-0.5 lia-text-400">
                              Criada em {new Date(job.created_at).toLocaleDateString("pt-BR")}
                            </p>
                            {job.description && (
                              <p className="text-micro mt-1 line-clamp-2 lia-text-400">
                                {job.description.slice(0, 120)}
                                {job.description.length > 120 ? "..." : ""}
                              </p>
                            )}
                          </div>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              )}

              {!jobSearchQuery.trim() && (
                <div className="text-center py-4 px-3 rounded-md border border-dashed border-lia-border-subtle">
                  <Search className="w-5 h-5 mx-auto mb-1.5" />
                  <p className="text-xs lia-text-400" aria-live="polite" aria-atomic="true">
                    Digite o nome ou ID da vaga para buscar
                  </p>
                </div>
              )}

              <div className="p-2.5 rounded-md bg-gray-50 border border-lia-border-subtle">
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 lia-text-700" />
                  <p className="text-xs lia-text-800 dark:text-lia-text-primary">
                    <strong>Dica:</strong> Selecione uma vaga para preencher automaticamente os dados do
                    arquétipo. Você poderá editar antes de salvar.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* A partir de Descrição */}
          {archetypeCreateMode === "description" && (
            <div className="space-y-2">
              <p className="text-xs lia-text-500 dark:text-lia-text-tertiary">
                Descreva o perfil ideal que deseja buscar:
              </p>
              <textarea
                value={archetypeDescription}
                onChange={(e) => onArchetypeDescriptionChange(e.target.value)}
                placeholder="Ex: Desenvolvedor Python sênior com experiência em machine learning e cloud AWS, preferencialmente com background em fintechs..."
                rows={3}
                className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 resize-none border border-lia-border-default bg-gray-50 lia-text-800"
              />
              <Button
                onClick={() => onCreateArchetypeFromDescription(archetypeDescription)}
                disabled={archetypeDescription.length < 20 || isCreatingArchetype}
                size="sm"
                className={cn("w-full", archetypeDescription.length >= 20 ? "bg-gray-950 text-white" : "bg-gray-100 lia-text-500")}
              >
                {isCreatingArchetype ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1 animate-spin motion-reduce:animate-none" />
                    Criando...
                  </>
                ) : (
                  <>
                    <Brain className="w-4 h-4 mr-1 text-wedo-cyan" />
                    Criar Arquétipo com LIA
                  </>
                )}
              </Button>

              <div className="p-2.5 rounded-md bg-gray-50 border border-lia-border-subtle">
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 lia-text-700" />
                  <p className="text-xs lia-text-800 dark:text-lia-text-primary">
                    <strong>Dica:</strong> Descreva o perfil ideal e a LIA vai extrair automaticamente cargo,
                    senioridade e skills para criar o arquétipo.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Sub-componente interno para botões de escopo (evita duplicação)
interface ScopeButtonsProps {
  searchSource?: SearchSource
  onSearchSourceChange: (source: SearchSource) => void
  onHandleSourceChange?: (source: "hybrid" | "global") => void
  showGlobalSearchOptions: boolean
  requireEmails?: boolean
  onRequireEmailsChange?: (v: boolean) => void
  requirePhoneNumbers?: boolean
  onRequirePhoneNumbersChange?: (v: boolean) => void
  selectedArchetype: ArchetypeVacancy | null
  isLoading: boolean
  onSubmit: () => void
}

function ScopeButtons({
  searchSource,
  onSearchSourceChange,
  onHandleSourceChange,
  showGlobalSearchOptions,
  requireEmails,
  onRequireEmailsChange,
  requirePhoneNumbers,
  onRequirePhoneNumbersChange,
  selectedArchetype,
  isLoading,
  onSubmit,
}: ScopeButtonsProps) {
  return (
    <>
      <div className="flex items-center gap-1">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  onSearchSourceChange("local")
                }}
                className={cn(
                  "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                  searchSource === "local"
                    ? "bg-wedo-green/15 ring-1 ring-wedo-green"
                    : "hover:bg-gray-100"
                , searchSource === "local" ? "text-wedo-green" : "lia-text-400"
                )}
              >
                <Home className="w-4 h-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent
              side="bottom"
              className="!animate-none !duration-0"
            >
              <p className="text-xs font-medium">Seu banco de talentos</p>
              <p className="text-xs lia-text-300">Gratuito • Local</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        {showGlobalSearchOptions && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    onHandleSourceChange?.("hybrid")
                  }}
                  className={cn(
                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                    searchSource === "hybrid"
                      ? "bg-wedo-orange/15 ring-1 ring-wedo-orange"
                      : "hover:bg-gray-100"
                  , searchSource === "hybrid" ? "text-wedo-orange" : "lia-text-400"
                  )}
                >
                  <Zap className="w-4 h-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent
                side="bottom"
                className="!animate-none !duration-0"
              >
                <p className="text-xs font-medium">Expanda sua busca</p>
                <p className="text-xs lia-text-300" aria-live="polite" aria-atomic="true">Local + Global • 1 crédito/candidato</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {showGlobalSearchOptions && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    onHandleSourceChange?.("global")
                  }}
                  className={cn(
                    "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                    searchSource === "global"
                      ? "bg-wedo-cyan/15 ring-1 ring-gray-900/20"
                      : "hover:bg-gray-100"
                  , searchSource === "global" ? "lia-text-950" : "lia-text-400"
                  )}
                >
                  <Globe className="w-4 h-4" />
                </button>
              </TooltipTrigger>
              <TooltipContent
                side="bottom"
                className="!animate-none !duration-0"
              >
                <p className="text-xs font-medium">Alcance global</p>
                <p className="text-xs lia-text-300" aria-live="polite" aria-atomic="true">800M+ candidatos • 1 crédito/candidato</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {(searchSource === "global" || searchSource === "hybrid") &&
          onRequireEmailsChange &&
          onRequirePhoneNumbersChange && (
            <>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        onRequireEmailsChange(!requireEmails)
                      }}
                      className={cn(
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                        requireEmails
                          ? "bg-wedo-green/15 ring-1 ring-wedo-green"
                          : "hover:bg-gray-100"
                      , requireEmails ? "text-wedo-green" : "lia-text-400"
                      )}
                    >
                      <Mail className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent
                    side="bottom"
                    className="!animate-none !duration-0"
                  >
                    <p className="text-xs font-medium">Apenas com Email</p>
                    <p className="text-xs lia-text-300">
                      {requireEmails ? "Ativo (+1 crédito)" : "Clique para ativar (+1 crédito)"}
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.preventDefault()
                        e.stopPropagation()
                        onRequirePhoneNumbersChange(!requirePhoneNumbers)
                      }}
                      className={cn(
                        "flex items-center justify-center p-1.5 rounded-md text-xs transition-colors",
                        requirePhoneNumbers
                          ? "bg-wedo-green/15 ring-1 ring-wedo-green"
                          : "hover:bg-gray-100"
                      , requirePhoneNumbers ? "text-wedo-green" : "lia-text-400"
                      )}
                    >
                      <Phone className="w-3.5 h-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent
                    side="bottom"
                    className="!animate-none !duration-0"
                  >
                    <p className="text-xs font-medium">Apenas com Telefone</p>
                    <p className="text-xs lia-text-300">
                      {requirePhoneNumbers ? "Ativo (+1 crédito)" : "Clique para ativar (+1 crédito)"}
                    </p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </>
          )}

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                type="button"
                onClick={onSubmit}
                disabled={!selectedArchetype || isLoading}
                className={cn(
                  "flex items-center justify-center p-1.5 rounded-md transition-colors",
                  selectedArchetype ? "hover:bg-gray-100" : "opacity-50 cursor-not-allowed"
                , selectedArchetype ? "lia-text-400" : "lia-text-200"
                )}
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
                ) : (
                  <Search className="w-4 h-4" />
                )}
              </button>
            </TooltipTrigger>
            <TooltipContent
              side="bottom"
              className="!animate-none !duration-0"
            >
              <p className="text-xs font-medium">Buscar Arquétipo</p>
              <p className="text-xs lia-text-300">Encontra perfis similares ao arquétipo</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      <span className="text-micro lia-text-400 italic">buscar arquétipo</span>
    </>
  )
}

export default SearchModeArchetypes
