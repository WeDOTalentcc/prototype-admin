"use client"
import React from"react"
import { Globe, Home, RefreshCw, Check, Eye } from"lucide-react"
import { cn } from"@/lib/utils"
import { textStyles } from"@/lib/design-tokens"
import { Chip } from "@/components/ui/chip"
import { Switch } from"@/components/ui/switch"
import { RadioGroup, RadioGroupItem } from"@/components/ui/radio-group"
import { type SearchSource, type SearchFilters } from"../advancedFiltersTypes"

interface FilterSectionOrigemProps {
  searchSource: SearchSource
  setSearchSource: (value: SearchSource) => void
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
}

export const FilterSectionOrigem = React.memo(function FilterSectionOrigem({
  searchSource,
  setSearchSource,
  filters,
  updateFilter,
}: FilterSectionOrigemProps) {
  return (
    <>
      <RadioGroup
        value={searchSource}
        onValueChange={(value) => setSearchSource(value as SearchSource)}
        className="grid grid-cols-3 gap-3"
      >
        <label
          className={cn("relative flex flex-col p-4 rounded-md border-2 cursor-pointer transition-colors bg-lia-bg-primary",
            searchSource ==="local"
              ?"border-lia-border-default bg-lia-bg-secondary"
              :"border-lia-border-subtle hover:border-lia-border-default"
          )}
        >
          <div className="flex items-center gap-2 mb-2">
            <RadioGroupItem value="local" id="local" className="sr-only" />
            <Home className={cn("w-4 h-4", searchSource ==="local" ?"text-lia-text-primary" :"text-lia-text-secondary")} />
            <span className={cn("font-medium text-xs", searchSource ==="local" ?"text-lia-text-primary" :"text-lia-text-primary")}>
              Base Local
            </span>
          </div>
          <p className="text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
            Candidatos já cadastrados na sua base
          </p>
          {searchSource ==="local" && (
            <div className="absolute -top-px -right-px w-5 h-5 rounded-tr-lg rounded-bl-lg flex items-center justify-center bg-lia-btn-primary-bg">
              <Check className="w-3 h-3 text-white" />
            </div>
          )}
        </label>

        <label
          className={cn("relative flex flex-col p-4 pt-8 rounded-md border-2 cursor-pointer transition-colors bg-lia-bg-primary",
            searchSource ==="hybrid"
              ?"border-lia-border-default bg-lia-bg-secondary"
              :"border-lia-border-subtle hover:border-lia-border-default"
          )}
        >
          <Chip variant="neutral" muted
            className="absolute top-2 right-2 text-micro px-1.5 py-0.5 font-medium text-status-warning"
           
          >
            1 CRED + $0.01 APIFY
          </Chip>
          <div className="flex items-center gap-2 mb-2">
            <RadioGroupItem value="hybrid" id="hybrid" className="sr-only" />
            <RefreshCw className={cn("w-4 h-4", searchSource ==="hybrid" ?"text-lia-text-primary" :"text-lia-text-secondary")} />
            <span className={cn("font-medium text-xs", searchSource ==="hybrid" ?"text-lia-text-primary" :"text-lia-text-primary")}>
              Busca Híbrida
            </span>
          </div>
          <p className="text-xs text-lia-text-secondary">Primeiro local, depois expande para global</p>
          {searchSource ==="hybrid" && (
            <div className="absolute -top-px -right-px w-5 h-5 rounded-tr-lg rounded-bl-lg flex items-center justify-center bg-lia-btn-primary-bg">
              <Check className="w-3 h-3 text-white" />
            </div>
          )}
        </label>

        <label
          className={cn("relative flex flex-col p-4 pt-8 rounded-md border-2 cursor-pointer transition-colors bg-lia-bg-primary",
            searchSource ==="global"
              ?"border-lia-border-default bg-lia-bg-secondary"
              :"border-lia-border-subtle hover:border-lia-border-default"
          )}
        >
          <Chip variant="neutral" muted
            className="absolute top-2 right-2 text-micro px-1.5 py-0.5 font-medium text-status-warning"
           
          >
            1 CRED + $0.01 APIFY
          </Chip>
          <div className="flex items-center gap-2 mb-2">
            <RadioGroupItem value="global" id="global" className="sr-only" />
            <Globe className={cn("w-4 h-4", searchSource ==="global" ?"text-lia-text-primary" :"text-lia-text-secondary")} />
            <span className={cn("font-medium text-xs", searchSource ==="global" ?"text-lia-text-primary" :"text-lia-text-primary")}>
              Busca Global
            </span>
          </div>
          <p className="text-xs text-lia-text-secondary">Acesso a +800M de perfis profissionais</p>
          {searchSource ==="global" && (
            <div className="absolute -top-px -right-px w-5 h-5 rounded-tr-lg rounded-bl-lg flex items-center justify-center bg-lia-btn-primary-bg">
              <Check className="w-3 h-3 text-white" />
            </div>
          )}
        </label>
      </RadioGroup>

      {(searchSource ==="local" || searchSource ==="hybrid") && (
        <div className="mt-4 flex items-center justify-between p-3 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary">
          <div className="flex items-center gap-2">
            <Eye className="w-4 h-4 text-status-warning" />
            <div>
              <span className={textStyles.subtitle} aria-live="polite" aria-atomic="true">
                Incluir candidatos descobertos
              </span>
              <p className={textStyles.description} aria-live="polite" aria-atomic="true">
                Mostrar candidatos encontrados em buscas anteriores ainda não salvos na base
              </p>
            </div>
          </div>
          <Switch
            checked={filters.searchOptions?.includeDiscovered ?? true}
            onCheckedChange={(checked: boolean) => updateFilter("searchOptions","includeDiscovered", checked)}
            className="data-[state=checked]:bg-lia-btn-primary-bg dark:data-[state=checked]:bg-lia-bg-tertiary"
          />
        </div>
      )}
    </>
  )
})
FilterSectionOrigem.displayName ="FilterSectionOrigem"
