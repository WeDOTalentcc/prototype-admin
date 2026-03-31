"use client"
import React from "react"
import { X } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { type SearchFilters } from "../advancedFiltersTypes"

interface FilterChipsBarProps {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string | string[] | number | boolean | null
  ) => void
  setFilters: React.Dispatch<React.SetStateAction<SearchFilters>>
  removeFromArray: <T extends keyof SearchFilters>(
    category: T,
    key: keyof NonNullable<SearchFilters[T]>,
    value: string
  ) => void
}

export const FilterChipsBar = React.memo(function FilterChipsBar({
  filters,
  updateFilter,
  setFilters,
  removeFromArray,
}: FilterChipsBarProps) {
  return (
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
  )
})

FilterChipsBar.displayName = "FilterChipsBar"
