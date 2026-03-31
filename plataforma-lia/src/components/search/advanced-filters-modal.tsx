"use client"

import { useState } from "react"
import {
  X, Settings, Briefcase, Building2, Code, GraduationCap,
  Globe, Search, RotateCcw, Zap,
  Save, Bookmark, ChevronDown, Check,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

import {
  type SaveDestination, type SearchSource, type HideViewedScope, type HideViewedPeriod,
  type SearchFilters, saveDestinations,
  SectionHeader, companySizes,
} from "./advancedFiltersTypes"
export type { SaveDestination, SearchSource, HideViewedScope, HideViewedPeriod, SearchFilters }
export { saveDestinations }

import { convertToPearchFilters, normalizeFiltersFromServer } from "./advancedFiltersUtils"
export { convertToPearchFilters, normalizeFiltersFromServer }

import { CreditConfirmationDialog } from "./credit-confirmation-dialog"
import { JobFiltersSection } from "./JobFiltersSection"

import {
  FilterSectionOrigem,
  FilterSectionOpcoes,
  FilterSectionGeral,
  FilterSectionPerfil,
  FilterSectionHabilidades,
  FilterSectionFormacao,
  FilterSectionIdiomas,
} from "./filter-sections"

import { useAdvancedFiltersCore } from "./hooks/useAdvancedFiltersCore"

// Company section imports
import { CompanyFilterInput } from "./CompanyFilterInput"
import { ExcludedCompaniesInput } from "./ExcludedCompaniesInput"
import { IndustryFilterInput } from "./IndustryFilterInput"
import { CompanyTagsInput } from "./CompanyTagsInput"
import { CompanyHQLocationsInput } from "./CompanyHQLocationsInput"
import { FundingStagesInput } from "./FundingStagesInput"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

interface AdvancedFiltersModalProps {
  isOpen: boolean
  onClose: () => void
  onApply: (filters: SearchFilters, options?: { searchSource?: SearchSource }) => void
  onSave?: (filters: SearchFilters, destination: SaveDestination) => void
  initialFilters?: SearchFilters
  estimatedMatches?: number
  candidateLimit?: number
  defaultSaveDestination?: SaveDestination
  sortBy?: string
  onSortByChange?: (value: string) => void
}

export function AdvancedFiltersModal(props: AdvancedFiltersModalProps) {
  const { isOpen } = props
  const {
    activeSection, addToArray, candidateLimit, creditEstimate, filters, getActiveFiltersCount, handleApply, handleConfirmSearch,
    isDestinationOpen, isLocalSearch, isSearching, onClose, onSave, removeFromArray, resetFilters,
    saveDestination, scrollContainerRef, scrollToSection, searchSource, sectionRefs, setFilters, setIsDestinationOpen, setSaveDestination,
    setSearchSource, setShowCreditConfirm, showCreditConfirm, sidebarCategories, updateFilter,
  } = useAdvancedFiltersCore(props)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-[1px]"
        onClick={onClose}
      />

      <div
        className="relative w-full max-w-4xl max-h-[85vh] rounded-md overflow-hidden border border-lia-border-subtle flex flex-col bg-white dark:bg-lia-bg-secondary dark:border-lia-border-subtle"
      >
        <div className="flex flex-col overflow-hidden flex-1">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle dark:border-lia-border-subtle">
            <div>
              <h2 className={textStyles.title}>Filtros Avançados</h2>
              <p className={`${textStyles.description} mt-0.5`}>
                Refine sua busca com filtros compatíveis com a Base Global
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                {onSave && (
                  <Popover open={isDestinationOpen} onOpenChange={setIsDestinationOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        size="sm"
                        variant="outline"
                        className="gap-1.5 border-gray-500 lia-text-700 dark:text-lia-text-secondary"
                      >
                        <Save className="w-4 h-4" />
                        Salvar
                        <ChevronDown className="w-3 h-3" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent align="end" className="w-72 p-2 bg-lia-bg-elevated border border-lia-border-subtle dark:border-lia-border-subtle">
                      <div className="space-y-1">
                        <p className="text-xs font-medium px-2 py-1.5 lia-text-600">Salvar busca em:</p>
                        {saveDestinations.map((dest) => (
                          <button
                            key={dest.key}
                            onClick={() => {
                              setSaveDestination(dest.key)
                              setIsDestinationOpen(false)
                              onSave(filters, dest.key)
                            }}
                            className={cn(
                              "w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-left transition-colors",
                              saveDestination === dest.key ? "bg-gray-100" : "hover:bg-gray-50"
                            )}
                          >
                            <dest.icon
                              className={cn(
                                "w-4 h-4 flex-shrink-0",
                                saveDestination === dest.key ? "lia-text-800 dark:text-lia-text-primary" : "lia-text-500"
                              )}
                            />
                            <div className="flex-1 min-w-0">
                              <div className={cn("text-xs font-medium", saveDestination === dest.key ? "lia-text-800" : "lia-text-800")}>
                                {dest.label}
                              </div>
                              <div className="text-xs lia-text-600">{dest.description}</div>
                            </div>
                            {saveDestination === dest.key && (
                              <Check className="w-4 h-4 flex-shrink-0 lia-text-700 dark:text-lia-text-secondary" />
                            )}
                          </button>
                        ))}
                      </div>
                    </PopoverContent>
                  </Popover>
                )}
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-md hover:bg-gray-100 lia-text-400 hover:lia-text-600 transition-colors motion-reduce:transition-none"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Main Content Area with Sidebar and Scrollable Content */}
          <div className="flex flex-1 overflow-hidden">
            {/* Left Sidebar Menu */}
            <div className="w-sidebar-content flex-shrink-0 border-r border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50/50 dark:bg-lia-bg-secondary/50 overflow-y-auto">
              <nav className="py-3">
                {sidebarCategories.map((category) => {
                  const Icon = category.icon
                  const isActive = activeSection === category.key
                  return (
                    <button
                      key={category.key}
                      onClick={() => scrollToSection(category.key)}
                      className={cn(
                        "w-full flex items-center gap-2.5 px-4 py-2.5 text-left text-xs transition-colors",
                        isActive
                          ? "bg-gray-100 dark:bg-lia-bg-elevated lia-text-900 dark:text-lia-text-primary border-r-2 border-gray-900 dark:border-lia-border-subtle font-medium"
                          : "lia-text-600 hover:bg-gray-100 hover:lia-text-800"
                      )}
                    >
                      <Icon className={cn("w-4 h-4", isActive ? "lia-text-900 dark:text-lia-text-primary" : "lia-text-400")} />
                      <span className="truncate">{category.label}</span>
                    </button>
                  )
                })}
              </nav>
            </div>

            {/* Scrollable Filter Sections */}
            <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-6 space-y-8">

              {/* Section: Origem da Busca */}
              <div ref={(el) => { sectionRefs.current.searchSource = el }}>
                <SectionHeader icon={Search} title="Origem da Busca" description="Selecione de onde buscar candidatos" />
                <FilterSectionOrigem
                  searchSource={searchSource}
                  setSearchSource={setSearchSource}
                  filters={filters}
                  updateFilter={updateFilter}
                />
              </div>

              {/* Section: Opções de Busca */}
              <div ref={(el) => { sectionRefs.current.ppiOptions = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Zap} title="Opções de Busca" description="Controle de qualidade e custo" />
                <FilterSectionOpcoes
                  filters={filters}
                  updateFilter={updateFilter}
                  searchSource={searchSource}
                  creditEstimate={creditEstimate}
                />
              </div>

              {/* Section: Geral */}
              <div ref={(el) => { sectionRefs.current.general = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Settings} title="Geral" description="Experiência e perfis" />
                <FilterSectionGeral
                  filters={filters}
                  updateFilter={updateFilter}
                />
              </div>

              {/* Section: Perfil Profissional */}
              <div ref={(el) => { sectionRefs.current.profile = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Search} title="Perfil Profissional" description="Indicadores de perfil" />
                <FilterSectionPerfil
                  filters={filters}
                  updateFilter={updateFilter}
                  isLocalSearch={isLocalSearch}
                />
              </div>

              {/* Section: Cargo */}
              <div ref={(el) => { sectionRefs.current.job = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Briefcase} title="Cargo" description="Títulos e níveis" />
                <JobFiltersSection
                  filters={filters}
                  updateFilter={updateFilter}
                  addToArray={addToArray}
                  removeFromArray={removeFromArray}
                />
              </div>

              {/* Section: Empresa */}
              <div ref={(el) => { sectionRefs.current.company = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Building2} title="Empresa" description="Empresas e setores" />
                <div className="space-y-6">
                  <div>
                    <Label className="text-xs mb-2 block">Empresas</Label>
                    <CompanyFilterInput
                      value={filters.company?.companyItems || []}
                      onChange={(companyItems) => setFilters(prev => ({
                        ...prev,
                        company: { ...(prev.company ?? {}), companyItems }
                      }))}
                      timeFilter={filters.company?.companyTimeFilter || "current_past"}
                      onTimeFilterChange={(companyTimeFilter) => updateFilter("company", "companyTimeFilter", companyTimeFilter)}
                      specificYears={filters.company?.specificYears}
                      onSpecificYearsChange={(specificYears) => setFilters(prev => ({ ...prev, company: { ...(prev.company ?? {}), specificYears } }))}
                      fundingStages={filters.company?.fundingStages}
                      onFundingStagesChange={(fundingStages) => updateFilter("company", "fundingStages", fundingStages)}
                      placeholder="Digite empresa e pressione Enter (ex: Google, Microsoft, Nubank)"
                    />
                    <p className="text-xs mt-2 lia-text-500">
                      Dica: Use &quot;Ask AI&quot; para buscar empresas similares ou por descrição (ex: &quot;fintechs em São Paulo&quot;)
                    </p>
                  </div>

                  <div>
                    <Label className="text-xs mb-2 block">Empresas Excluídas</Label>
                    <ExcludedCompaniesInput
                      value={filters.company?.excludedCompanyItems || []}
                      onChange={(excludedCompanyItems) => setFilters(prev => ({
                        ...prev,
                        company: { ...(prev.company ?? {}), excludedCompanyItems }
                      }))}
                      timeFilter={filters.company?.excludedTimeFilter || "current_only"}
                      onTimeFilterChange={(excludedTimeFilter) => updateFilter("company", "excludedTimeFilter", excludedTimeFilter)}
                      placeholder="Empresas para NÃO incluir nos resultados"
                    />
                    <p className="text-xs mt-1 text-status-warning">
                      Filtro aplicado localmente após Busca Global
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs mb-1.5 block font-medium">Setores da Empresa</Label>
                      <IndustryFilterInput
                        value={filters.company?.industries || []}
                        onChange={(industries) => setFilters(prev => ({
                          ...prev,
                          company: { ...(prev.company ?? {}), industries }
                        }))}
                        timeFilter={filters.company?.industryTimeFilter || "current_past"}
                        onTimeFilterChange={(industryTimeFilter) => updateFilter("company", "industryTimeFilter", industryTimeFilter)}
                        placeholder="Digite setor e pressione Enter"
                      />
                    </div>

                    <div>
                      <Label className="text-xs mb-1.5 block font-medium">Tags da Empresa</Label>
                      <CompanyTagsInput
                        value={filters.company?.companyTags || []}
                        onChange={(companyTags) => setFilters(prev => ({
                          ...prev,
                          company: { ...(prev.company ?? {}), companyTags }
                        }))}
                        timeFilter={filters.company?.companyTagsTimeFilter || "current_past"}
                        onTimeFilterChange={(companyTagsTimeFilter) => updateFilter("company", "companyTagsTimeFilter", companyTagsTimeFilter)}
                        placeholder="Digite tag e pressione Enter"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className={cn(isLocalSearch && "opacity-50 cursor-not-allowed")}>
                            <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "lia-text-400")}>
                              Sede da Empresa
                              {isLocalSearch && <span className="ml-1 text-status-warning">(apenas busca global)</span>}
                            </Label>
                            <CompanyHQLocationsInput
                              value={filters.company?.companyHQLocations || []}
                              disabled={isLocalSearch}
                              onChange={(companyHQLocations) => {
                                if (isLocalSearch) return
                                setFilters(prev => ({
                                  ...prev,
                                  company: { ...(prev.company ?? {}), companyHQLocations }
                                }))
                              }}
                              timeFilter={filters.company?.companyHQTimeFilter || "current_past"}
                              onTimeFilterChange={(companyHQTimeFilter) => updateFilter("company", "companyHQTimeFilter", companyHQTimeFilter)}
                              placeholder="Ex: São Paulo / Brasil / RJ / ..."
                            />
                          </div>
                        </TooltipTrigger>
                        {isLocalSearch && (
                          <TooltipContent side="top">
                            <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                          </TooltipContent>
                        )}
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className={cn(isLocalSearch && "opacity-50 cursor-not-allowed")}>
                            <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "lia-text-400")}>
                              Porte da Empresa
                              {isLocalSearch && <span className="ml-1 text-status-warning">(apenas busca global)</span>}
                            </Label>
                            <div className={cn("flex flex-wrap gap-2", isLocalSearch && "pointer-events-none")}>
                              {companySizes.map(size => {
                                const isSelected = filters.company?.companySizes?.includes(size.value)
                                return (
                                  <button
                                    key={size.value}
                                    disabled={isLocalSearch}
                                    onClick={() => {
                                      if (isLocalSearch) return
                                      if (isSelected) {
                                        removeFromArray("company", "companySizes", size.value)
                                      } else {
                                        addToArray("company", "companySizes", size.value)
                                      }
                                    }}
                                    className={cn(
                                      "px-3 py-1.5 rounded-full text-xs border transition-[width,height]",
                                      isLocalSearch
                                        ? "border-lia-border-subtle bg-gray-100 lia-text-400 cursor-not-allowed"
                                        : isSelected
                                          ? "border-gray-500 bg-gray-100 dark:bg-lia-bg-elevated lia-text-900 dark:text-lia-text-primary"
                                          : "border-lia-border-subtle bg-lia-bg-primary lia-text-600 hover:border-lia-border-default"
                                    )}
                                  >
                                    {size.label}
                                  </button>
                                )
                              })}
                            </div>
                          </div>
                        </TooltipTrigger>
                        {isLocalSearch && (
                          <TooltipContent side="top">
                            <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                          </TooltipContent>
                        )}
                      </Tooltip>
                    </TooltipProvider>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className={cn(isLocalSearch && "opacity-50 cursor-not-allowed")}>
                            <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "lia-text-400")}>
                              Empresa Fundada Após
                              {isLocalSearch && <span className="ml-1 text-status-warning">(apenas busca global)</span>}
                            </Label>
                            <div className="relative">
                              <Input
                                type="number"
                                min={1800}
                                max={new Date().getFullYear()}
                                value={filters.company?.companyFoundedAfter || ""}
                                disabled={isLocalSearch}
                                onChange={(e) => {
                                  if (isLocalSearch) return
                                  const year = e.target.value ? parseInt(e.target.value) : null
                                  updateFilter("company", "companyFoundedAfter", year)
                                }}
                                placeholder="Ano de Fundação"
                                className={cn(
                                  "border-lia-border-subtle focus:ring-1 focus:ring-gray-400 focus:border-gray-500 pr-10",
                                  isLocalSearch && "bg-gray-100 cursor-not-allowed"
                                )}
                              />
                              <div className={cn("absolute right-3 top-1/2 transform -translate-y-1/2", isLocalSearch ? "lia-text-300" : "lia-text-400")}>
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                              </div>
                            </div>
                            <p className={cn("text-xs mt-1", isLocalSearch ? "lia-text-400" : "lia-text-500")}>
                              Filtrar empresas fundadas após este ano
                            </p>
                          </div>
                        </TooltipTrigger>
                        {isLocalSearch && (
                          <TooltipContent side="top">
                            <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                          </TooltipContent>
                        )}
                      </Tooltip>
                    </TooltipProvider>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className={cn(isLocalSearch && "opacity-50 cursor-not-allowed")}>
                            <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "lia-text-400")}>
                              Estágio de Funding
                              {isLocalSearch && <span className="ml-1 text-status-warning">(apenas busca global)</span>}
                            </Label>
                            <FundingStagesInput
                              value={filters.company?.fundingStages || []}
                              disabled={isLocalSearch}
                              onChange={(fundingStages) => {
                                if (isLocalSearch) return
                                setFilters(prev => ({
                                  ...prev,
                                  company: { ...(prev.company ?? {}), fundingStages }
                                }))
                              }}
                            />
                          </div>
                        </TooltipTrigger>
                        {isLocalSearch && (
                          <TooltipContent side="top">
                            <p className="text-xs">Disponível apenas em busca Híbrida ou Global</p>
                          </TooltipContent>
                        )}
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </div>
              </div>

              {/* Section: Habilidades */}
              <div ref={(el) => { sectionRefs.current.skills = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Code} title="Habilidades" description="Skills técnicas" />
                <FilterSectionHabilidades
                  filters={filters}
                  setFilters={setFilters}
                />
              </div>

              {/* Section: Formação */}
              <div ref={(el) => { sectionRefs.current.education = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={GraduationCap} title="Formação" description="Universidades e cursos" />
                <FilterSectionFormacao
                  filters={filters}
                  setFilters={setFilters}
                />
              </div>

              {/* Section: Idiomas */}
              <div ref={(el) => { sectionRefs.current.languages = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Globe} title="Idiomas" description="Línguas e proficiência" />
                <FilterSectionIdiomas
                  filters={filters}
                  updateFilter={updateFilter}
                  addToArray={addToArray}
                  removeFromArray={removeFromArray}
                />
              </div>

            </div>
          </div>

          {/* Active Filters Chips */}
          {getActiveFiltersCount() > 0 && (
            <div className="px-6 py-2 border-t border-lia-border-subtle dark:lia-border-800 bg-gray-50/50 dark:bg-lia-bg-primary/50">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-micro lia-text-500 font-medium">Filtros ativos:</span>
                {filters.general?.minExperience && (
                  <Badge variant="outline" className="text-micro py-0 h-5 gap-1">
                    Exp. mín: {filters.general.minExperience}a
                    <button onClick={() => updateFilter("general", "minExperience", null)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                )}
                {filters.general?.maxExperience && (
                  <Badge variant="outline" className="text-micro py-0 h-5 gap-1">
                    Exp. máx: {filters.general.maxExperience}a
                    <button onClick={() => updateFilter("general", "maxExperience", null)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                )}
                {filters.job?.titles?.map(t => (
                  <Badge key={t} variant="outline" className="text-micro py-0 h-5 gap-1">
                    {t}
                    <button onClick={() => removeFromArray("job", "titles", t)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                ))}
                {filters.skills?.skillItems?.map(s => (
                  <Badge key={s.name} variant="outline" className="text-micro py-0 h-5 gap-1">
                    {s.name}
                    <button onClick={() => {
                      const items = filters.skills?.skillItems?.filter(i => i.name !== s.name) || []
                      setFilters(prev => ({ ...prev, skills: { ...prev.skills, skillItems: items } }))
                    }} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                ))}
                {filters.company?.companyItems?.map(c => (
                  <Badge key={c.name} variant="outline" className="text-micro py-0 h-5 gap-1">
                    {c.name}
                    <button onClick={() => {
                      const items = filters.company?.companyItems?.filter(i => i.name !== c.name) || []
                      setFilters(prev => ({ ...prev, company: { ...prev.company, companyItems: items } }))
                    }} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                ))}
                {filters.languages?.languages?.map(l => (
                  <Badge key={l} variant="outline" className="text-micro py-0 h-5 gap-1">
                    {l}
                    <button onClick={() => removeFromArray("languages", "languages", l)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-3 border-t border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-primary dark:border-lia-border-subtle">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={resetFilters}
                className="text-xs lia-text-500"
              >
                <RotateCcw className="w-3 h-3 mr-1" />
                Limpar filtros
              </Button>
              {onSave && (
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs bg-gray-100 dark:bg-lia-bg-elevated lia-text-700 dark:text-lia-text-secondary">
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
                className="bg-gray-900 hover:bg-gray-800 text-white dark:lia-bg-100 dark:lia-text-900 dark:hover:bg-gray-200"
              >
                Aplicar Filtros
              </Button>
            </div>
          </div>
        </div>
      </div>

      <CreditConfirmationDialog
        open={showCreditConfirm}
        onOpenChange={setShowCreditConfirm}
        onConfirm={handleConfirmSearch}
        candidateLimit={candidateLimit}
        creditPerCandidate={creditEstimate.cost_per_candidate}
        searchType={searchSource === "hybrid" ? "sourcing" : "general"}
        isLoading={isSearching}
      />
    </div>
  )
}

export default AdvancedFiltersModal
