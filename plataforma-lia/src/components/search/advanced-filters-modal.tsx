"use client"

import {
  X, Settings, Briefcase, Building2, Code, GraduationCap,
  Globe, Search, Zap,
  Save, ChevronDown, Check,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles } from "@/lib/design-tokens"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

import {
  type SaveDestination, type SearchSource, type HideViewedScope, type HideViewedPeriod,
  type SearchFilters, saveDestinations,
  SectionHeader,
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
  FilterSectionEmpresa,
  FilterChipsBar,
  ModalFooterActions,
} from "./filter-sections"

import { useAdvancedFiltersCore } from "./hooks/useAdvancedFiltersCore"

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
      <div className="absolute inset-0 bg-lia-overlay backdrop-blur-[1px]" onClick={onClose} />

      <div className="relative w-full max-w-4xl max-h-[85vh] rounded-xl overflow-hidden border border-lia-border-subtle flex flex-col bg-lia-bg-primary dark:bg-lia-bg-secondary dark:border-lia-border-subtle">
        <div className="flex flex-col overflow-hidden flex-1">

          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 dark:border-lia-border-subtle">
            <div>
              <h2 className={textStyles.title}>Filtros Avan&ccedil;ados</h2>
              <p className={`${textStyles.description} mt-0.5`}>Refine sua busca com filtros compat&iacute;veis com a Base Global</p>
            </div>
            <div className="flex items-center gap-2">
              {onSave && (
                <Popover open={isDestinationOpen} onOpenChange={setIsDestinationOpen}>
                  <PopoverTrigger asChild>
                    <Button size="sm" variant="outline" className="gap-1.5 border-lia-border-medium text-lia-text-primary">
                      <Save className="w-4 h-4" />
                      Salvar
                      <ChevronDown className="w-3 h-3" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent align="end" className="w-72 p-2 bg-lia-bg-elevated border border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="space-y-1">
                      <p className="text-xs font-medium px-2 py-1.5 text-lia-text-secondary">Salvar busca em:</p>
                      {saveDestinations.map((dest) => (
                        <button
                          key={dest.key}
                          onClick={() => { setSaveDestination(dest.key); setIsDestinationOpen(false); onSave(filters, dest.key) }}
                          className={cn("w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-left transition-colors", saveDestination === dest.key ? "bg-lia-bg-tertiary" : "hover:bg-lia-bg-secondary")}
                        >
                          <dest.icon className={cn("w-4 h-4 flex-shrink-0", saveDestination === dest.key ? "text-lia-text-primary" : "text-lia-text-secondary")} />
                          <div className="flex-1 min-w-0">
                            <div className={cn("text-xs font-medium", "text-lia-text-primary")}>{dest.label}</div>
                            <div className="text-xs text-lia-text-secondary">{dest.description}</div>
                          </div>
                          {saveDestination === dest.key && <Check className="w-4 h-4 flex-shrink-0 text-lia-text-primary" />}
                        </button>
                      ))}
                    </div>
                  </PopoverContent>
                </Popover>
              )}
              <button onClick={onClose} className="p-1.5 rounded-xl hover:bg-lia-bg-tertiary text-lia-text-tertiary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none">
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Main Content: Sidebar Nav + Scrollable Sections */}
          <div className="flex flex-1 overflow-hidden">
            <div className="w-sidebar-content flex-shrink-0 border-r border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary/50 dark:bg-lia-bg-secondary/50 overflow-y-auto">
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
                          ? "bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary border-r-2 border-lia-btn-primary-bg dark:border-lia-border-subtle font-medium"
                          : "text-lia-text-secondary hover:bg-lia-bg-tertiary hover:text-lia-text-primary"
                      )}
                    >
                      <Icon className={cn("w-4 h-4", isActive ? "text-lia-text-primary" : "text-lia-text-tertiary")} />
                      <span className="truncate">{category.label}</span>
                    </button>
                  )
                })}
              </nav>
            </div>

            <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-6 space-y-8">
              <div ref={(el) => { sectionRefs.current.searchSource = el }}>
                <SectionHeader icon={Search} title="Origem da Busca" description="Selecione de onde buscar candidatos" />
                <FilterSectionOrigem searchSource={searchSource} setSearchSource={setSearchSource} filters={filters} updateFilter={updateFilter} />
              </div>
              <div ref={(el) => { sectionRefs.current.ppiOptions = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Zap} title="Op&ccedil;&otilde;es de Busca" description="Controle de qualidade e custo" />
                <FilterSectionOpcoes filters={filters} updateFilter={updateFilter} searchSource={searchSource} creditEstimate={creditEstimate} />
              </div>
              <div ref={(el) => { sectionRefs.current.general = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Settings} title="Geral" description="Experi&ecirc;ncia e perfis" />
                <FilterSectionGeral filters={filters} updateFilter={updateFilter} />
              </div>
              <div ref={(el) => { sectionRefs.current.profile = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Search} title="Perfil Profissional" description="Indicadores de perfil" />
                <FilterSectionPerfil filters={filters} updateFilter={updateFilter} isLocalSearch={isLocalSearch} />
              </div>
              <div ref={(el) => { sectionRefs.current.job = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Briefcase} title="Cargo" description="T&iacute;tulos e n&iacute;veis" />
                <JobFiltersSection filters={filters} updateFilter={updateFilter} addToArray={addToArray} removeFromArray={removeFromArray} />
              </div>
              <div ref={(el) => { sectionRefs.current.company = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Building2} title="Empresa" description="Empresas e setores" />
                <FilterSectionEmpresa filters={filters} updateFilter={updateFilter} setFilters={setFilters} addToArray={addToArray} removeFromArray={removeFromArray} isLocalSearch={isLocalSearch} />
              </div>
              <div ref={(el) => { sectionRefs.current.skills = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Code} title="Habilidades" description="Skills t&eacute;cnicas" />
                <FilterSectionHabilidades filters={filters} setFilters={setFilters} />
              </div>
              <div ref={(el) => { sectionRefs.current.education = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={GraduationCap} title="Forma&ccedil;&atilde;o" description="Universidades e cursos" />
                <FilterSectionFormacao filters={filters} setFilters={setFilters} />
              </div>
              <div ref={(el) => { sectionRefs.current.languages = el }} className="border-t border-lia-border-subtle dark:border-lia-border-subtle pt-6">
                <SectionHeader icon={Globe} title="Idiomas" description="L&iacute;nguas e profici&ecirc;ncia" />
                <FilterSectionIdiomas filters={filters} updateFilter={updateFilter} addToArray={addToArray} removeFromArray={removeFromArray} />
              </div>
            </div>
          </div>

          {/* Active Filter Chips */}
          {getActiveFiltersCount() > 0 && (
            <FilterChipsBar filters={filters} updateFilter={updateFilter} setFilters={setFilters} removeFromArray={removeFromArray} />
          )}

          {/* Footer */}
          <ModalFooterActions
            getActiveFiltersCount={getActiveFiltersCount}
            resetFilters={resetFilters}
            onSave={onSave}
            saveDestination={saveDestination}
            onClose={onClose}
            handleApply={handleApply}
          />
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
