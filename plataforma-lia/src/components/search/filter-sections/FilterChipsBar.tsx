"use client"
import React from"react"
import { X } from"lucide-react"
import { Chip } from "@/components/ui/chip"
import { type SearchFilters } from"../advancedFiltersTypes"

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
    <div className="px-6 py-2 border-t border-lia-border-subtle dark:border-lia-border-strong bg-lia-bg-secondary/50 dark:bg-lia-bg-primary/50">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-micro text-lia-text-secondary font-medium">Filtros ativos:</span>
        {filters.general?.minExperience && (
          <Chip variant="neutral" className="text-micro py-0 h-5 gap-1">
            Exp. mín: {filters.general.minExperience}a
            <button onClick={() => updateFilter("general","minExperience", null)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
          </Chip>
        )}
        {filters.general?.maxExperience && (
          <Chip variant="neutral" className="text-micro py-0 h-5 gap-1">
            Exp. máx: {filters.general.maxExperience}a
            <button onClick={() => updateFilter("general","maxExperience", null)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
          </Chip>
        )}
        {filters.job?.titles?.map(t => (
          <Chip key={t} variant="neutral" className="text-micro py-0 h-5 gap-1">
            {t}
            <button onClick={() => removeFromArray("job","titles", t)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
          </Chip>
        ))}
        {filters.skills?.skillItems?.map(s => (
          <Chip key={s.name} variant="neutral" className="text-micro py-0 h-5 gap-1">
            {s.name}
            <button onClick={() => {
              const items = filters.skills?.skillItems?.filter(i => i.name !== s.name) || []
              setFilters(prev => ({ ...prev, skills: { ...prev.skills, skillItems: items } }))
            }} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
          </Chip>
        ))}
        {filters.company?.companyItems?.map(c => (
          <Chip key={c.name} variant="neutral" className="text-micro py-0 h-5 gap-1">
            {c.name}
            <button onClick={() => {
              const items = filters.company?.companyItems?.filter(i => i.name !== c.name) || []
              setFilters(prev => ({ ...prev, company: { ...prev.company, companyItems: items } }))
            }} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
          </Chip>
        ))}
        {filters.languages?.languages?.map(l => (
          <Chip key={l} variant="neutral" className="text-micro py-0 h-5 gap-1">
            {l}
            <button onClick={() => removeFromArray("languages","languages", l)} className="ml-0.5 hover:text-status-error"><X className="h-2.5 w-2.5" /></button>
          </Chip>
        ))}
      </div>
    </div>
  )
})

FilterChipsBar.displayName ="FilterChipsBar"
