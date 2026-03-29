"use client"

import { useState, useCallback, useEffect, useMemo, useRef } from "react"
import { 
  X, Settings, MapPin, Briefcase, Building2, Code, GraduationCap, 
  Globe, ChevronRight, Search, RotateCcw, Zap, Mail, Phone, Clock,
  RefreshCw, Filter, AlertCircle, TrendingUp, Save, FolderOpen, History,
  Bookmark, ChevronDown, Check, Home, Crown, Rocket, UserCheck, Eye, HelpCircle,
  Brain, Loader2, Info, List, ArrowUpDown
} from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { CreditConfirmationDialog } from "./credit-confirmation-dialog"
import { calculateCreditsLocally, CreditEstimate } from "@/lib/api/candidate-search"
import { SkillsFilterInput, SkillItem } from "./SkillsFilterInput"
import { ExpertiseAreasInput } from "./ExpertiseAreasInput"
import { CompanyFilterInput, CompanyItem, CompanyTimeFilter } from "./CompanyFilterInput"
import { ExcludedCompaniesInput, ExcludedCompanyItem, ExcludedTimeFilter } from "./ExcludedCompaniesInput"
import { IndustryFilterInput, IndustryTimeFilter } from "./IndustryFilterInput"
import { CompanyTagsInput, CompanyTagItem, CompanyTagsTimeFilter } from "./CompanyTagsInput"
import { CompanyHQLocationsInput, CompanyHQTimeFilter } from "./CompanyHQLocationsInput"
import { FundingStagesInput } from "./FundingStagesInput"
import { UniversitiesFilterInput } from "./UniversitiesFilterInput"
import { ExcludedUniversitiesInput } from "./ExcludedUniversitiesInput"
import { UniversityLocationsInput } from "./UniversityLocationsInput"
import { DegreeRequirementsInput } from "./DegreeRequirementsInput"
import { FieldsOfStudyInput } from "./FieldsOfStudyInput"
import { GraduationYearInput } from "./GraduationYearInput"
import { LanguageFilterInput } from "./LanguageFilterInput"
import { useSemanticSearch } from "@/hooks/useSemanticSearch"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"


import {
  type SaveDestination, type SearchSource, type HideViewedScope, type HideViewedPeriod,
  type SearchFilters, type FilterCategory, saveDestinations,
  categories, experienceLevels, jobRoles, titleScopeOptions, timeInRoleOptions,
  tenureOptions, globalJobPresets, companySizes, degreeTypes, proficiencyLevels,
  hideViewedScopeOptions, hideViewedPeriodOptions, SectionHeader
} from "./advancedFiltersTypes"
export type { SaveDestination, SearchSource, HideViewedScope, HideViewedPeriod, SearchFilters }
export { saveDestinations }



import { convertToPearchFilters, normalizeFiltersFromServer } from "./advancedFiltersUtils"
export { convertToPearchFilters, normalizeFiltersFromServer }


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

import { useAdvancedFiltersCore } from './hooks/useAdvancedFiltersCore'
import { JobFiltersSection } from './JobFiltersSection'

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
        className="relative w-full max-w-4xl max-h-[85vh] rounded-md overflow-hidden border border-gray-200 flex flex-col bg-white dark:bg-gray-800 dark:border-gray-700"
       
      >
        <div className="flex flex-col overflow-hidden flex-1">
          <div 
            className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700"
          >
            <div>
              <h2 className={textStyles.title}>
                Filtros Avançados
              </h2>
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
                        className="gap-1.5 border-gray-500 text-gray-700 dark:text-gray-300"
                      >
                        <Save className="w-4 h-4" />
                        Salvar
                        <ChevronDown className="w-3 h-3" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent align="end" className="w-72 p-2 bg-white border border-gray-200 dark:border-gray-700">
                      <div className="space-y-1">
                        <p className="text-xs font-medium px-2 py-1.5 text-gray-600">
                          Salvar busca em:
                        </p>
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
                              saveDestination === dest.key 
                                ? "bg-gray-100" 
                                : "hover:bg-gray-50"
                            )}
                          >
                            <dest.icon 
                              className={cn(
                                "w-4 h-4 flex-shrink-0",
                                saveDestination === dest.key ? "text-gray-800 dark:text-gray-200" : "text-gray-500"
                              )}
                            />
                            <div className="flex-1 min-w-0">
                              <div 
                                className={cn(
                                  "text-xs font-medium",
                                  saveDestination === dest.key ? "text-gray-800" : "text-gray-800"
                                )}
                              >
                                {dest.label}
                              </div>
                              <div className="text-xs text-gray-600">
                                {dest.description}
                              </div>
                            </div>
                            {saveDestination === dest.key && (
                              <Check className="w-4 h-4 flex-shrink-0 text-gray-700 dark:text-gray-300" />
                            )}
                          </button>
                        ))}
                      </div>
                    </PopoverContent>
                  </Popover>
                )}
                <button
                  onClick={onClose}
                  className="p-1.5 rounded-md hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Main Content Area with Sidebar and Scrollable Content */}
          <div className="flex flex-1 overflow-hidden">
            {/* Left Sidebar Menu */}
            <div className="w-sidebar-content flex-shrink-0 border-r border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 overflow-y-auto">
              <nav className="py-3">
                {sidebarCategories.map((category) => {
                  const Icon = category.icon
                  const isActive = activeSection === category.key
                  return (
                    <button
                      key={category.key}
                      onClick={() => scrollToSection(category.key)}
                      className={cn(
                        "w-full flex items-center gap-2.5 px-4 py-2.5 text-left text-xs transition-all",
                        isActive
 ? "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-r-2 border-gray-900 dark:border-gray-700 font-medium"
                          : "text-gray-600 hover:bg-gray-100 hover:text-gray-800"
                      )}
                    >
                      <Icon className={cn("w-4 h-4", isActive ? "text-gray-900 dark:text-gray-100" : "text-gray-400")} />
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
                
                <RadioGroup 
                  value={searchSource} 
                  onValueChange={(value) => setSearchSource(value as SearchSource)}
                  className="grid grid-cols-3 gap-3"
                >
                  <label 
                    className={cn(
                      "relative flex flex-col p-4 rounded-md border-2 cursor-pointer transition-all bg-white",
                      searchSource === "local" 
                        ? "border-gray-300 bg-gray-50" 
                        : "border-gray-200 hover:border-gray-300"
                    )}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <RadioGroupItem value="local" id="local" className="sr-only" />
                      <Home className={cn("w-4 h-4", searchSource === "local" ? "text-gray-800 dark:text-gray-200" : "text-gray-500")} />
                      <span 
                        className={cn("font-medium text-xs", searchSource === "local" ? "text-gray-800" : "text-gray-800")}
                      >
                        Base Local
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Candidatos já cadastrados na sua base
                    </p>
                    {searchSource === "local" && (
                      <div 
                        className="absolute -top-px -right-px w-5 h-5 rounded-tr-lg rounded-bl-lg flex items-center justify-center bg-gray-900 dark:bg-gray-100"
                      >
                        <Check className="w-3 h-3 text-white dark:text-gray-900" />
                      </div>
                    )}
                  </label>

                  <label 
                    className={cn(
                      "relative flex flex-col p-4 pt-8 rounded-md border-2 cursor-pointer transition-all bg-white",
                      searchSource === "hybrid" 
                        ? "border-gray-300 bg-gray-50" 
                        : "border-gray-200 hover:border-gray-300"
                    )}
                  >
                    <Badge 
                      className="absolute top-2 right-2 text-micro px-1.5 py-0.5 font-medium"
                      style={{backgroundColor: "var(--gray-100)", color: "var(--status-warning)", border: "none"}}
                    >
                      1 CRÉDITO/CAND.
                    </Badge>
                    <div className="flex items-center gap-2 mb-2">
                      <RadioGroupItem value="hybrid" id="hybrid" className="sr-only" />
                      <RefreshCw className={cn("w-4 h-4", searchSource === "hybrid" ? "text-gray-800 dark:text-gray-200" : "text-gray-500")} />
                      <span 
                        className={cn("font-medium text-xs", searchSource === "hybrid" ? "text-gray-800" : "text-gray-800")}
                      >
                        Busca Híbrida
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Primeiro local, depois expande para global
                    </p>
                    {searchSource === "hybrid" && (
                      <div 
                        className="absolute -top-px -right-px w-5 h-5 rounded-tr-lg rounded-bl-lg flex items-center justify-center bg-gray-900 dark:bg-gray-100"
                      >
                        <Check className="w-3 h-3 text-white dark:text-gray-900" />
                      </div>
                    )}
                  </label>

                  <label 
                    className={cn(
                      "relative flex flex-col p-4 pt-8 rounded-md border-2 cursor-pointer transition-all bg-white",
                      searchSource === "global" 
                        ? "border-gray-300 bg-gray-50" 
                        : "border-gray-200 hover:border-gray-300"
                    )}
                  >
                    <Badge 
                      className="absolute top-2 right-2 text-micro px-1.5 py-0.5 font-medium"
                      style={{backgroundColor: "var(--gray-100)", color: "var(--status-warning)", border: "none"}}
                    >
                      1 CRÉDITO/CAND.
                    </Badge>
                    <div className="flex items-center gap-2 mb-2">
                      <RadioGroupItem value="global" id="global" className="sr-only" />
                      <Globe className={cn("w-4 h-4", searchSource === "global" ? "text-gray-800 dark:text-gray-200" : "text-gray-500")} />
                      <span 
                        className={cn("font-medium text-xs", searchSource === "global" ? "text-gray-800" : "text-gray-800")}
                      >
                        Busca Global
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">
                      Acesso a +800M de perfis profissionais
                    </p>
                    {searchSource === "global" && (
                      <div 
                        className="absolute -top-px -right-px w-5 h-5 rounded-tr-lg rounded-bl-lg flex items-center justify-center bg-gray-900 dark:bg-gray-100"
                      >
                        <Check className="w-3 h-3 text-white dark:text-gray-900" />
                      </div>
                    )}
                  </label>
                </RadioGroup>

                {(searchSource === "local" || searchSource === "hybrid") && (
                  <div className="mt-4 flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700 bg-white">
                    <div className="flex items-center gap-2">
                      <Eye className="w-4 h-4 text-status-warning" />
                      <div>
                        <span className={textStyles.subtitle}>
                          Incluir candidatos descobertos
                        </span>
                        <p className={textStyles.description}>
                          Mostrar candidatos encontrados em buscas anteriores ainda não salvos na base
                        </p>
                      </div>
                    </div>
                    <Switch
                      checked={filters.searchOptions?.includeDiscovered ?? true}
                      onCheckedChange={(checked: boolean) => updateFilter("searchOptions", "includeDiscovered", checked)}
                      className="data-[state=checked]:bg-gray-900 dark:data-[state=checked]:bg-gray-100"
                    />
                  </div>
                )}
              </div>
              {/* Section: Opções de Busca */}
              <div ref={(el) => { sectionRefs.current.ppiOptions = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Zap} title="Opções de Busca" description="Controle de qualidade e custo" />
              <div className="space-y-6">
                {(searchSource === "global" || searchSource === "hybrid") && (
                <div 
                  className="p-4 rounded-md border bg-gray-50 border-gray-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Zap className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                      <span className="font-medium text-xs">Custo Estimado</span>
                    </div>
                    <Badge variant="outline" className="text-xs px-1.5 py-0.5 border-gray-500 text-gray-700 dark:text-gray-300">
                      Tempo Real
                    </Badge>
                  </div>
                  
                  <div className="flex items-end justify-between">
                    <div>
                      <div className="text-base font-bold text-gray-900 dark:text-gray-100">
                        {creditEstimate.cost_per_candidate}
                      </div>
                      <div className="text-xs text-gray-600">
                        créditos por candidato
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={textStyles.title}>
                        {creditEstimate.total_estimated}
                      </div>
                      <div className="text-xs text-gray-600">
                        total ({creditEstimate.limit} candidatos)
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-wedo-cyan/20 space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-600">
                        Base ({creditEstimate.pearch_type === "fast" ? "Rápida" : "Profissional"})
                      </span>
                      <span className="font-medium">{creditEstimate.base_cost}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-gray-600">Insights + Scoring</span>
                      <span className="font-medium">+{creditEstimate.insights_cost}</span>
                    </div>
                    {creditEstimate.freshness_cost > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">Dados Atualizados</span>
                        <span className="font-medium">+{creditEstimate.freshness_cost}</span>
                      </div>
                    )}
                    {creditEstimate.email_cost > 0 && (
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-600">Opções de Email</span>
                        <span className="font-medium">+{creditEstimate.email_cost}</span>
                      </div>
                    )}
                    {creditEstimate.phone_cost > 0 && (
                      <div className="flex justify-between text-xs text-status-warning">
                        <span className="flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          Opções de Telefone
                        </span>
                        <span className="font-medium">+{creditEstimate.phone_cost}</span>
                      </div>
                    )}
                    
                    <div className="flex justify-between text-xs pt-1.5 border-t border-wedo-cyan/15">
                      <span className="flex items-center gap-1 font-medium text-gray-800">
                        <TrendingUp className="w-3 h-3" />
                        Total por Candidato
                      </span>
                      <span className="font-bold text-gray-900 dark:text-gray-100">
                        {creditEstimate.cost_per_candidate}
                      </span>
                    </div>
                  </div>

                  {creditEstimate.warnings.length > 0 && (
                    <div className="mt-3 p-2 bg-status-warning/10 rounded-md border border-status-warning/30">
                      {creditEstimate.warnings.map((warning, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-xs text-status-warning">
                          <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                          <span>{warning}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                )}

                <div className="space-y-3">
                  <Label className="text-xs font-medium block">Informações de Contato</Label>

                  <div className="flex items-center justify-between p-2.5 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-gray-500" />
                      <div>
                        <div className="text-xs font-medium">Apenas com Email</div>
                        <div className="text-xs text-gray-600">
                          Filtrar candidatos com email
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.requireEmails || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "requireEmails", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between p-2.5 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2">
                      <Mail className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                      <div>
                        <div className="text-xs font-medium">Mostrar Emails</div>
                        <div className="text-xs text-gray-600">
                          Exibir emails nos resultados
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.showEmails || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "showEmails", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                      <Phone className="w-4 h-4 text-gray-500" />
                      <div>
                        <div className="text-xs font-medium">Apenas com Telefone</div>
                        <div className="text-xs text-gray-600">
                          Filtrar candidatos com telefone
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.requirePhoneNumbers || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "requirePhoneNumbers", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                      <Phone className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <div>
                        <div className="text-xs font-medium">Mostrar Telefones</div>
                        <div className="text-xs text-gray-600">
                          Exibir telefones nos resultados
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.showPhoneNumbers || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "showPhoneNumbers", checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                      <Mail className="w-4 h-4 text-gray-500" />
                      <Phone className="w-4 h-4 -ml-2 text-gray-500" />
                      <div>
                        <div className="text-xs font-medium">Email OU Telefone</div>
                        <div className="text-xs text-gray-500">
                          Pelo menos um contato
                        </div>
                      </div>
                    </div>
                    <Switch
                      checked={filters.ppiOptions?.requirePhonesOrEmails || false}
                      onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "requirePhonesOrEmails", checked)}
                    />
                  </div>
                </div>
              </div>
            </div>

              {/* Section: Geral */}
              <div ref={(el) => { sectionRefs.current.general = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Settings} title="Geral" description="Experiência e perfis" />
              <div className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs mb-1.5 block">Experiência Mínima (Anos)</Label>
                    <Input
                      type="number"
                      min={0}
                      value={filters.general?.minExperience || ""}
                      onChange={(e) => updateFilter("general", "minExperience", e.target.value ? parseInt(e.target.value) : undefined)}
                      placeholder="Ex: 3 anos"
                      className="border border-gray-200 focus:ring-1 focus:ring-gray-400"
                    />
                  </div>
                  <div>
                    <Label className="text-xs mb-1.5 block">Experiência Máxima (Anos)</Label>
                    <Input
                      type="number"
                      min={0}
                      value={filters.general?.maxExperience || ""}
                      onChange={(e) => updateFilter("general", "maxExperience", e.target.value ? parseInt(e.target.value) : undefined)}
                      placeholder="Ex: 10 anos"
                      className="border border-gray-200 focus:ring-1 focus:ring-gray-400"
                    />
                  </div>
                </div>

                <div className="space-y-4 p-4 rounded-md border border-gray-200 dark:border-gray-700 bg-gray-50/50">
                  <div className="flex items-center gap-2 mb-3">
                    <Eye className="w-4 h-4 text-gray-600" />
                    <span className={textStyles.subtitle}>
                      Ocultar Perfis Visualizados ou Shortlistados
                    </span>
                    <Popover>
                      <PopoverTrigger asChild>
                        <button 
                          type="button"
                          className="text-gray-400 hover:text-gray-600 transition-colors"
                        >
                          <HelpCircle className="w-4 h-4" />
                        </button>
                      </PopoverTrigger>
                      <PopoverContent className="w-80 p-3 bg-white border border-gray-200" side="top">
                        <div className="space-y-2">
                          <h4 className="font-semibold text-sm text-gray-800">O que significa "Shortlistado"?</h4>
                          <p className="text-xs text-gray-600 leading-relaxed">
                            Candidatos <strong>shortlistados</strong> são aqueles que já foram incluídos em vagas e passaram por algum processo de entrevista, seja por você, outros recrutadores ou gestores da organização.
                          </p>
                          <p className="text-xs text-gray-500 leading-relaxed">
                            Isso inclui entrevistas técnicas, comportamentais, com gestores, ou qualquer outra etapa de seleção registrada no sistema.
                          </p>
                        </div>
                      </PopoverContent>
                    </Popover>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs mb-1.5 block text-gray-600">Escopo</Label>
                      <Select
                        value={filters.general?.hideViewedScope || "dont_hide"}
                        onValueChange={(value) => {
                          updateFilter("general", "hideViewedScope", value as HideViewedScope)
                          updateFilter("general", "hideViewedProfiles", value !== "dont_hide")
                        }}
                      >
                        <SelectTrigger className="border border-gray-200 focus:ring-1 focus:ring-gray-400 bg-white text-xs">
                          <SelectValue placeholder="Selecione o escopo" />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          {hideViewedScopeOptions.map(option => (
                            <SelectItem 
                              key={option.value} 
                              value={option.value}
                              className="py-2"
                            >
                              <div>
                                <div className="font-medium">{option.label}</div>
                                {option.description && (
                                  <div className="text-xs text-gray-500">{option.description}</div>
                                )}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label className="text-xs mb-1.5 block text-gray-600">Período</Label>
                      <Select
                        value={filters.general?.hideViewedPeriod || "all_time"}
                        onValueChange={(value) => updateFilter("general", "hideViewedPeriod", value as HideViewedPeriod)}
                        disabled={filters.general?.hideViewedScope === "dont_hide"}
                      >
                        <SelectTrigger 
                          className={cn(
                            "border border-gray-200 focus:ring-1 focus:ring-gray-400 bg-white text-xs",
                            filters.general?.hideViewedScope === "dont_hide" && "opacity-50 cursor-not-allowed"
                          )}
                        >
                          <SelectValue placeholder="Selecione o período" />
                        </SelectTrigger>
                        <SelectContent className="bg-white">
                          {hideViewedPeriodOptions.map(option => (
                            <SelectItem key={option.value} value={option.value}>
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <p className="text-xs text-gray-500 flex items-center gap-1.5">
                    <AlertCircle className="w-3 h-3" />
                    Remove dos resultados candidatos visualizados ou entrevistados no período selecionado
                  </p>
                </div>
              </div>
            </div>

              {/* Section: Perfil Profissional */}
              <div ref={(el) => { sectionRefs.current.profile = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={UserCheck} title="Perfil Profissional" description="Indicadores de perfil" />
              <div className="space-y-3">
                {isLocalSearch && (
                  <div className="flex items-center gap-2 p-2.5 rounded-md bg-status-warning/10 border border-status-warning/30 mb-3">
                    <Info className="w-4 h-4 text-status-warning flex-shrink-0" />
                    <p className="text-xs text-status-warning">
                      Estes filtros estão disponíveis apenas em busca Híbrida ou Global
                    </p>
                  </div>
                )}
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className={cn(
                        "flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700",
                        isLocalSearch && "opacity-50 cursor-not-allowed bg-gray-50"
                      )}>
                        <div className="flex items-center gap-3">
                          <Briefcase className={cn("w-4 h-4", isLocalSearch ? "text-gray-400" : "text-status-success")} />
                          <div>
                            <div className={cn("text-xs font-medium", isLocalSearch && "text-gray-400")}>Aberto a Oportunidades</div>
                            <div className="text-xs text-gray-500">
                              Candidatos sinalizando interesse em novas propostas
                            </div>
                          </div>
                        </div>
                        <Switch
                          checked={filters.ppiOptions?.openToWorkOnly || false}
                          onCheckedChange={(checked: boolean) => updateFilter("ppiOptions", "openToWorkOnly", checked)}
                          disabled={isLocalSearch}
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
                      <div className={cn(
                        "flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700",
                        isLocalSearch && "opacity-50 cursor-not-allowed bg-gray-50"
                      )}>
                        <div className="flex items-center gap-3">
                          <Crown className={cn("w-4 h-4", isLocalSearch ? "text-gray-400" : "text-status-warning")} />
                          <div>
                            <div className={cn("text-xs font-medium", isLocalSearch && "text-gray-400")}>Decisor / Líder</div>
                            <div className="text-xs text-gray-500">
                              Profissionais em posições de liderança
                            </div>
                          </div>
                        </div>
                        <Switch
                          checked={filters.profile?.isDecisionMaker || false}
                          onCheckedChange={(checked: boolean) => updateFilter("profile", "isDecisionMaker", checked)}
                          disabled={isLocalSearch}
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
                      <div className={cn(
                        "flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700",
                        isLocalSearch && "opacity-50 cursor-not-allowed bg-gray-50"
                      )}>
                        <div className="flex items-center gap-3">
                          <GraduationCap className={cn("w-4 h-4", isLocalSearch ? "text-gray-400" : "text-gray-600 dark:text-gray-400")} />
                          <div>
                            <div className={cn("text-xs font-medium", isLocalSearch && "text-gray-400")}>Top Universidades</div>
                            <div className="text-xs text-gray-500">
                              Formados em universidades de elite
                            </div>
                          </div>
                        </div>
                        <Switch
                          checked={filters.profile?.isTopUniversities || false}
                          onCheckedChange={(checked: boolean) => updateFilter("profile", "isTopUniversities", checked)}
                          disabled={isLocalSearch}
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
                      <div className={cn(
                        "flex items-center justify-between p-3 rounded-md border border-gray-200 dark:border-gray-700",
                        isLocalSearch && "opacity-50 cursor-not-allowed bg-gray-50"
                      )}>
                        <div className="flex items-center gap-3">
                          <Rocket className={cn("w-4 h-4", isLocalSearch ? "text-gray-400" : "text-wedo-purple")} />
                          <div>
                            <div className={cn("text-xs font-medium", isLocalSearch && "text-gray-400")}>Experiência em Startup</div>
                            <div className="text-xs text-gray-500">
                              Trabalhou em startups (cultura ágil)
                            </div>
                          </div>
                        </div>
                        <Switch
                          checked={filters.profile?.isStartup || false}
                          onCheckedChange={(checked: boolean) => updateFilter("profile", "isStartup", checked)}
                          disabled={isLocalSearch}
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

              {/* Section: Cargo */}
              <div ref={(el) => { sectionRefs.current.job = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Briefcase} title="Cargo" description="Títulos e níveis" />
              <JobFiltersSection 
                filters={filters}
                updateFilter={updateFilter}
                addToArray={addToArray}
                removeFromArray={removeFromArray}
              />
            </div>

              {/* Section: Empresa */}
              <div ref={(el) => { sectionRefs.current.company = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Building2} title="Empresa" description="Empresas e setores" />
              <div className="space-y-6">
                <div>
                  <Label className="text-xs mb-2 block">Empresas</Label>
                  <CompanyFilterInput
                    value={filters.company?.companyItems || []}
                    onChange={(companyItems) => setFilters(prev => ({
                      ...prev,
                      company: {
                        ...(prev.company ?? {}),
                        companyItems
                      }
                    }))}
                    timeFilter={filters.company?.companyTimeFilter || 'current_past'}
                    onTimeFilterChange={(companyTimeFilter) => updateFilter("company", "companyTimeFilter", companyTimeFilter)}
                    specificYears={filters.company?.specificYears}
                    onSpecificYearsChange={(specificYears) => updateFilter("company", "specificYears", specificYears)}
                    fundingStages={filters.company?.fundingStages}
                    onFundingStagesChange={(fundingStages) => updateFilter("company", "fundingStages", fundingStages)}
                    placeholder="Digite empresa e pressione Enter (ex: Google, Microsoft, Nubank)"
                  />
                  <p className="text-xs mt-2 text-gray-500">
                    Dica: Use "Ask AI" para buscar empresas similares ou por descrição (ex: "fintechs em São Paulo")
                  </p>
                </div>

                <div>
                  <Label className="text-xs mb-2 block">Empresas Excluídas</Label>
                  <ExcludedCompaniesInput
                    value={filters.company?.excludedCompanyItems || []}
                    onChange={(excludedCompanyItems) => setFilters(prev => ({
                      ...prev,
                      company: {
                        ...(prev.company ?? {}),
                        excludedCompanyItems
                      }
                    }))}
                    timeFilter={filters.company?.excludedTimeFilter || 'current_only'}
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
                        company: {
                          ...(prev.company ?? {}),
                          industries
                        }
                      }))}
                      timeFilter={filters.company?.industryTimeFilter || 'current_past'}
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
                        company: {
                          ...(prev.company ?? {}),
                          companyTags
                        }
                      }))}
                      timeFilter={filters.company?.companyTagsTimeFilter || 'current_past'}
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
                          <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-gray-400")}>
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
                                company: {
                                  ...(prev.company ?? {}),
                                  companyHQLocations
                                }
                              }))
                            }}
                            timeFilter={filters.company?.companyHQTimeFilter || 'current_past'}
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
                          <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-gray-400")}>
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
                                    "px-3 py-1.5 rounded-full text-xs border transition-all",
                                    isLocalSearch
                                      ? "border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed"
                                      : isSelected 
                                        ? "border-gray-500 bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100" 
                                        : "border-gray-200 bg-white text-gray-600 hover:border-gray-300"
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
                          <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-gray-400")}>
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
                                const year = e.target.value ? parseInt(e.target.value) : undefined
                                updateFilter("company", "companyFoundedAfter", year)
                              }}
                              placeholder="Ano de Fundação"
                              className={cn(
                                "border-gray-200 focus:ring-1 focus:ring-gray-400 focus:border-gray-500 pr-10",
                                isLocalSearch && "bg-gray-100 cursor-not-allowed"
                              )}
                            />
                            <div className={cn("absolute right-3 top-1/2 transform -translate-y-1/2", isLocalSearch ? "text-gray-300" : "text-gray-400")}>
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                            </div>
                          </div>
                          <p className={cn("text-xs mt-1", isLocalSearch ? "text-gray-400" : "text-gray-500")}>
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
                          <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-gray-400")}>
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
                                company: {
                                  ...(prev.company ?? {}),
                                  fundingStages
                                }
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
              <div ref={(el) => { sectionRefs.current.skills = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Code} title="Habilidades" description="Skills técnicas" />
              <div className="space-y-6">
                <div>
                  <Label className="text-xs mb-1.5 block">Habilidades Técnicas</Label>
                  <SkillsFilterInput
                    value={filters.skills?.skillItems || []}
                    onChange={(skillItems) => setFilters(prev => ({
                      ...prev,
                      skills: {
                        ...(prev.skills ?? {}),
                        skillItems
                      }
                    }))}
                    placeholder="Digite skill e pressione Enter (ex: Python, React, AWS, SQL)"
                  />
                  <p className="text-xs mt-2 text-gray-500">
                    Dica: Use o ícone de pin para marcar skills obrigatórias. O botão "Find Similar" sugere skills relacionadas via IA.
                  </p>
                </div>

                <div className="mt-4">
                  <Label className="text-xs mb-1.5 block">Áreas de Expertise</Label>
                  <ExpertiseAreasInput
                    value={filters.skills?.expertise || []}
                    onChange={(expertise) => setFilters(prev => ({
                      ...prev,
                      skills: {
                        ...(prev.skills ?? {}),
                        expertise
                      }
                    }))}
                    placeholder="Digite expertise e pressione Enter (ex: Machine Learning, DevOps, Data Science)"
                  />
                </div>
              </div>
            </div>

              {/* Section: Formação */}
              <div ref={(el) => { sectionRefs.current.education = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={GraduationCap} title="Formação" description="Universidades e cursos" />
              <div className="space-y-6">
                <div>
                  <Label className="text-xs mb-2 block font-medium">Universidades</Label>
                  <UniversitiesFilterInput
                    value={filters.education?.universities || []}
                    onChange={(universities) => setFilters(prev => ({
                      ...prev,
                      education: {
                        ...(prev.education ?? {}),
                        universities
                      }
                    }))}
                    placeholder="Digite universidade e pressione Enter"
                    showPresets={true}
                  />
                  <p className="text-xs mt-2 text-gray-500">
                    Dica: Use "Ask AI" para buscar universidades similares ou por descrição
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Universidades Excluídas</Label>
                    <ExcludedUniversitiesInput
                      value={filters.education?.excludedUniversities || []}
                      onChange={(excludedUniversities) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          excludedUniversities
                        }
                      }))}
                      placeholder="USP, UNICAMP, PUC, FGV, etc."
                    />
                  </div>

                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Localização da Universidade</Label>
                    <UniversityLocationsInput
                      value={filters.education?.universityLocations || []}
                      onChange={(universityLocations) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          universityLocations
                        }
                      }))}
                      placeholder="São Paulo / Brasil / RJ / ..."
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Grau Acadêmico</Label>
                    <DegreeRequirementsInput
                      mode={filters.education?.degreeRequirementMode || 'regular'}
                      onModeChange={(degreeRequirementMode) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          degreeRequirementMode
                        }
                      }))}
                      value={filters.education?.degree || null}
                      onChange={(degree) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          degree
                        }
                      }))}
                    />
                  </div>

                  <div>
                    <Label className="text-xs mb-1.5 block font-medium">Áreas de Estudo</Label>
                    <FieldsOfStudyInput
                      mode={filters.education?.fieldsOfStudyMode || 'regular'}
                      onModeChange={(fieldsOfStudyMode) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          fieldsOfStudyMode
                        }
                      }))}
                      value={filters.education?.fieldsOfStudy || []}
                      onChange={(fieldsOfStudy) => setFilters(prev => ({
                        ...prev,
                        education: {
                          ...(prev.education ?? {}),
                          fieldsOfStudy
                        }
                      }))}
                      placeholder="Engenharias, Ciências, Computação, etc."
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-xs mb-1.5 block font-medium">Ano de Formatura</Label>
                  <GraduationYearInput
                    minYear={filters.education?.graduationYearMin ?? null}
                    maxYear={filters.education?.graduationYearMax ?? null}
                    onMinYearChange={(graduationYearMin) => setFilters(prev => ({
                      ...prev,
                      education: {
                        ...(prev.education ?? {}),
                        graduationYearMin
                      }
                    }))}
                    onMaxYearChange={(graduationYearMax) => setFilters(prev => ({
                      ...prev,
                      education: {
                        ...(prev.education ?? {}),
                        graduationYearMax
                      }
                    }))}
                  />
                </div>
              </div>
            </div>

              {/* Section: Idiomas */}
              <div ref={(el) => { sectionRefs.current.languages = el }} className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <SectionHeader icon={Globe} title="Idiomas" description="Línguas e proficiência" />
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <Label className="text-xs">Idiomas</Label>
                    <Select
                      value={filters.languages?.proficiencyLevel || "any"}
                      onValueChange={(value) => updateFilter("languages", "proficiencyLevel", value)}
                    >
                      <SelectTrigger className="w-auto h-7 px-2 py-1 text-xs border border-gray-200 focus:ring-1 focus:ring-gray-400 gap-1">
                        <SelectValue placeholder="Qualquer Nível" />
                      </SelectTrigger>
                      <SelectContent>
                        {proficiencyLevels.map(level => (
                          <SelectItem key={level.value} value={level.value} className="text-xs">
                            {level.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <LanguageFilterInput
                    value={filters.languages?.languages || []}
                    onAdd={(val) => addToArray("languages", "languages", val)}
                    onRemove={(val) => removeFromArray("languages", "languages", val)}
                    placeholder="Ex: English, Spanish, Mandarin, etc."
                    showPresets={false}
                  />
                </div>
              </div>
            </div>

          </div>
          </div>

          {/* Active Filters Chips */}
          {getActiveFiltersCount() > 0 && (
            <div className="px-6 py-2 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50 dark:bg-gray-900/50">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-micro text-gray-500 font-medium">Filtros ativos:</span>
                {filters.general?.minExperience && (
                  <Badge variant="outline" className="text-micro py-0 h-5 gap-1">
                    Exp. mín: {filters.general.minExperience}a
                    <button onClick={() => updateFilter("general", "minExperience", undefined)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
                  </Badge>
                )}
                {filters.general?.maxExperience && (
                  <Badge variant="outline" className="text-micro py-0 h-5 gap-1">
                    Exp. máx: {filters.general.maxExperience}a
                    <button onClick={() => updateFilter("general", "maxExperience", undefined)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
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

          <div 
            className="flex items-center justify-between px-6 py-3 border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700"
          >
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={resetFilters}
                className="text-xs text-gray-500"
              >
                <RotateCcw className="w-3 h-3 mr-1" />
                Limpar filtros
              </Button>
              {onSave && (
                <div 
                  className="flex items-center gap-1.5 px-2 py-1 rounded-md text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
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
              <Button
                variant="outline"
                size="sm"
                onClick={onClose}
              >
                Cancelar
              </Button>
              <Button
                size="sm"
                onClick={handleApply}
                className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200"
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

