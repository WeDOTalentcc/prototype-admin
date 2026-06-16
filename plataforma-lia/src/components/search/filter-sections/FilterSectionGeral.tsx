"use client"
import React from "react"
import { Eye, AlertCircle, HelpCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { textStyles } from "@/lib/design-tokens"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
import {
  type SearchFilters,
  type HideViewedScope,
  type HideViewedPeriod,
  hideViewedScopeOptions,
  hideViewedPeriodOptions,
} from "../advancedFiltersTypes"

interface FilterSectionGeralProps {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
}

export const FilterSectionGeral = React.memo(function FilterSectionGeral({
  filters,
  updateFilter,
}: FilterSectionGeralProps) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-xs mb-1.5 block">Experiência Mínima (Anos)</Label>
          <Input
            type="number"
            min={0}
            value={filters.general?.minExperience || ""}
            onChange={(e) =>
              updateFilter("general", "minExperience", e.target.value ? parseInt(e.target.value) : null)
            }
            placeholder="Ex: 3 anos"
            className="border border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium"
          />
        </div>
        <div>
          <Label className="text-xs mb-1.5 block">Experiência Máxima (Anos)</Label>
          <Input
            type="number"
            min={0}
            value={filters.general?.maxExperience || ""}
            onChange={(e) =>
              updateFilter("general", "maxExperience", e.target.value ? parseInt(e.target.value) : null)
            }
            placeholder="Ex: 10 anos"
            className="border border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium"
          />
        </div>
      </div>

      <div className="space-y-4 p-4 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-secondary/50">
        <div className="flex items-center gap-2 mb-3">
          <Eye className="w-4 h-4 text-lia-text-secondary" />
          <span className={textStyles.subtitle}>Ocultar Perfis Visualizados ou Shortlistados</span>
          <Popover>
            <PopoverTrigger asChild>
              <button
                type="button"
                className="text-lia-text-tertiary hover:text-lia-text-secondary transition-colors motion-reduce:transition-none"
              >
                <HelpCircle className="w-4 h-4" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-3 bg-lia-bg-elevated border border-lia-border-subtle" side="top">
              <div className="space-y-2">
                <h4 className="font-semibold text-sm text-lia-text-primary">O que significa &quot;Shortlistado&quot;?</h4>
                <p className="text-xs text-lia-text-secondary leading-relaxed">
                  Candidatos <strong>shortlistados</strong> são aqueles que já foram incluídos em vagas e passaram por
                  algum processo de entrevista, seja por você, outros recrutadores ou gestores da organização.
                </p>
                <p className="text-xs text-lia-text-secondary leading-relaxed">
                  Isso inclui entrevistas técnicas, comportamentais, com gestores, ou qualquer outra etapa de seleção
                  registrada no sistema.
                </p>
              </div>
            </PopoverContent>
          </Popover>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-xs mb-1.5 block text-lia-text-secondary">Escopo</Label>
            <Select
              value={filters.general?.hideViewedScope || "dont_hide"}
              onValueChange={(value) => {
                updateFilter("general", "hideViewedScope", value as HideViewedScope)
                updateFilter("general", "hideViewedProfiles", value !== "dont_hide")
              }}
            >
              <SelectTrigger className="border border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium bg-lia-bg-secondary text-xs">
                <SelectValue placeholder="Selecione o escopo" />
              </SelectTrigger>
              <SelectContent className="bg-lia-bg-secondary">
                {hideViewedScopeOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value} className="py-2">
                    <div>
                      <div className="font-medium">{option.label}</div>
                      {option.description && (
                        <div className="text-xs text-lia-text-secondary">{option.description}</div>
                      )}
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="text-xs mb-1.5 block text-lia-text-secondary">Período</Label>
            <Select
              value={filters.general?.hideViewedPeriod || "all_time"}
              onValueChange={(value) => updateFilter("general", "hideViewedPeriod", value as HideViewedPeriod)}
              disabled={filters.general?.hideViewedScope === "dont_hide"}
            >
              <SelectTrigger
                className={cn(
                  "border border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium bg-lia-bg-primary text-xs",
                  filters.general?.hideViewedScope === "dont_hide" && "opacity-50 cursor-not-allowed"
                )}
              >
                <SelectValue placeholder="Selecione o período" />
              </SelectTrigger>
              <SelectContent className="bg-lia-bg-secondary">
                {hideViewedPeriodOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <p className="text-xs text-lia-text-secondary flex items-center gap-1.5">
          <AlertCircle className="w-3 h-3" />
          Remove dos resultados candidatos visualizados ou entrevistados no período selecionado
        </p>
      </div>
    </div>
  )
})
FilterSectionGeral.displayName = "FilterSectionGeral"
