"use client"
import React from "react"
import { Briefcase, Crown, GraduationCap, Rocket, Info } from "lucide-react"
import { cn } from "@/lib/utils"
import { Switch } from "@/components/ui/switch"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { type SearchFilters } from "../advancedFiltersTypes"

interface FilterSectionPerfilProps {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
  isLocalSearch: boolean
}

export const FilterSectionPerfil = React.memo(function FilterSectionPerfil({
  filters,
  updateFilter,
  isLocalSearch,
}: FilterSectionPerfilProps) {
  const profileItems = [
    {
      field: "ppiOptions" as const,
      key: "openToWorkOnly",
      icon: Briefcase,
      iconColor: "text-status-success",
      label: "Aberto a Oportunidades",
      description: "Candidatos sinalizando interesse em novas propostas",
      value: filters.ppiOptions?.openToWorkOnly || false,
    },
    {
      field: "profile" as const,
      key: "isDecisionMaker",
      icon: Crown,
      iconColor: "text-status-warning",
      label: "Decisor / Líder",
      description: "Profissionais em posições de liderança",
      value: filters.profile?.isDecisionMaker || false,
    },
    {
      field: "profile" as const,
      key: "isTopUniversities",
      icon: GraduationCap,
      iconColor: "text-lia-text-secondary",
      label: "Top Universidades",
      description: "Formados em universidades de elite",
      value: filters.profile?.isTopUniversities || false,
    },
    {
      field: "profile" as const,
      key: "isStartup",
      icon: Rocket,
      iconColor: "text-wedo-purple-text",
      label: "Experiência em Startup",
      description: "Trabalhou em startups (cultura ágil)",
      value: filters.profile?.isStartup || false,
    },
  ]

  return (
    <div className="space-y-3">
      {isLocalSearch && (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-status-warning/10 border border-status-warning/30 mb-3">
          <Info className="w-4 h-4 text-status-warning flex-shrink-0" />
          <p className="text-xs text-status-warning">
            Estes filtros estão disponíveis apenas em busca Híbrida ou Global
          </p>
        </div>
      )}

      {profileItems.map((item) => (
        <TooltipProvider key={item.key}>
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className={cn(
                  "flex items-center justify-between p-3 rounded-md border border-lia-border-subtle dark:border-lia-border-subtle",
                  isLocalSearch && "opacity-50 cursor-not-allowed bg-lia-bg-secondary"
                )}
              >
                <div className="flex items-center gap-3">
                  <item.icon className={cn("w-4 h-4", isLocalSearch ? "text-lia-text-tertiary" : item.iconColor)} />
                  <div>
                    <div className={cn("text-xs font-medium", isLocalSearch && "text-lia-text-tertiary")}>{item.label}</div>
                    <div className="text-xs text-lia-text-secondary">{item.description}</div>
                  </div>
                </div>
                <Switch
                  checked={item.value}
                  onCheckedChange={(checked: boolean) => updateFilter(item.field as keyof SearchFilters, item.key as never, checked)}
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
      ))}
    </div>
  )
})
FilterSectionPerfil.displayName = "FilterSectionPerfil"
