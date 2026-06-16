"use client"
import React from "react"
import { cn } from "@/lib/utils"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { type SearchFilters, companySizes } from "../advancedFiltersTypes"
import { CompanyFilterInput } from "../CompanyFilterInput"
import { ExcludedCompaniesInput } from "../ExcludedCompaniesInput"
import { IndustryFilterInput } from "../IndustryFilterInput"
import { CompanyTagsInput } from "../CompanyTagsInput"
import { CompanyHQLocationsInput } from "../CompanyHQLocationsInput"
import { FundingStagesInput } from "../FundingStagesInput"

interface FilterSectionEmpresaProps {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string | string[] | number | boolean | null
  ) => void
  setFilters: React.Dispatch<React.SetStateAction<SearchFilters>>
  addToArray: <T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string
  ) => void
  removeFromArray: <T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string
  ) => void
  isLocalSearch: boolean
}

export const FilterSectionEmpresa = React.memo(function FilterSectionEmpresa({
  filters,
  updateFilter,
  setFilters,
  addToArray,
  removeFromArray,
  isLocalSearch,
}: FilterSectionEmpresaProps) {
  return (
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
        <p className="text-xs mt-2 text-lia-text-secondary">
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
                <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-lia-text-tertiary")}>
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
                <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-lia-text-tertiary")}>
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
                            ? "border-lia-border-subtle bg-lia-bg-tertiary text-lia-text-tertiary cursor-not-allowed"
                            : isSelected
                              ? "border-lia-border-medium bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-primary"
                              : "border-lia-border-subtle bg-lia-bg-primary text-lia-text-secondary hover:border-lia-border-default"
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
                <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-lia-text-tertiary")}>
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
                      "border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium focus:border-lia-border-medium pr-10",
                      isLocalSearch && "bg-lia-bg-tertiary cursor-not-allowed"
                    )}
                  />
                  <div className={cn("absolute right-3 top-1/2 transform -translate-y-1/2", isLocalSearch ? "text-lia-text-disabled" : "text-lia-text-tertiary")}>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
                <p className={cn("text-xs mt-1", isLocalSearch ? "text-lia-text-tertiary" : "text-lia-text-secondary")}>
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
                <Label className={cn("text-xs mb-1.5 block font-medium", isLocalSearch && "text-lia-text-tertiary")}>
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
  )
})

FilterSectionEmpresa.displayName = "FilterSectionEmpresa"
