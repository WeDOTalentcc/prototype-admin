"use client"
import React from "react"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { LanguageFilterInput } from "../LanguageFilterInput"
import { type SearchFilters, proficiencyLevels } from "../advancedFiltersTypes"

interface FilterSectionIdiomasProps {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
  addToArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
  removeFromArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
}

export const FilterSectionIdiomas = React.memo(function FilterSectionIdiomas({
  filters,
  updateFilter,
  addToArray,
  removeFromArray,
}: FilterSectionIdiomasProps) {
  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <Label className="text-xs">Idiomas</Label>
          <Select
            value={filters.languages?.proficiencyLevel || "any"}
            onValueChange={(value) => updateFilter("languages", "proficiencyLevel", value)}
          >
            <SelectTrigger className="w-auto h-7 px-2 py-1 text-xs border border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium gap-1">
              <SelectValue placeholder="Qualquer Nível" />
            </SelectTrigger>
            <SelectContent>
              {proficiencyLevels.map((level) => (
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
  )
})
FilterSectionIdiomas.displayName = "FilterSectionIdiomas"
