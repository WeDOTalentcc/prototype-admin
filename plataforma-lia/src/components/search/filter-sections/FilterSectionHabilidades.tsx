"use client"
import React from "react"
import { Label } from "@/components/ui/label"
import { SkillsFilterInput } from "../SkillsFilterInput"
import { ExpertiseAreasInput } from "../ExpertiseAreasInput"
import { type SearchFilters } from "../advancedFiltersTypes"

interface FilterSectionHabilidadesProps {
  filters: SearchFilters
  setFilters: React.Dispatch<React.SetStateAction<SearchFilters>>
}

export const FilterSectionHabilidades = React.memo(function FilterSectionHabilidades({
  filters,
  setFilters,
}: FilterSectionHabilidadesProps) {
  return (
    <div className="space-y-6">
      <div>
        <Label className="text-xs mb-1.5 block">Habilidades Técnicas</Label>
        <SkillsFilterInput
          value={filters.skills?.skillItems || []}
          onChange={(skillItems) =>
            setFilters((prev) => ({
              ...prev,
              skills: {
                ...(prev.skills ?? {}),
                skillItems,
              },
            }))
          }
          placeholder="Digite skill e pressione Enter (ex: Python, React, AWS, SQL)"
        />
        <p className="text-xs mt-2 text-lia-text-secondary">
          Dica: Use o ícone de pin para marcar skills obrigatórias. O botão &quot;Find Similar&quot; sugere skills relacionadas via IA.
        </p>
      </div>

      <div className="mt-4">
        <Label className="text-xs mb-1.5 block">Áreas de Expertise</Label>
        <ExpertiseAreasInput
          value={filters.skills?.expertise || []}
          onChange={(expertise) =>
            setFilters((prev) => ({
              ...prev,
              skills: {
                ...(prev.skills ?? {}),
                expertise,
              },
            }))
          }
          placeholder="Digite expertise e pressione Enter (ex: Machine Learning, DevOps, Data Science)"
        />
      </div>
    </div>
  )
})
FilterSectionHabilidades.displayName = "FilterSectionHabilidades"
