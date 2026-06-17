"use client"
import React from "react"
import { Label } from "@/components/ui/label"
import { UniversitiesFilterInput } from "../UniversitiesFilterInput"
import { ExcludedUniversitiesInput } from "../ExcludedUniversitiesInput"
import { UniversityLocationsInput } from "../UniversityLocationsInput"
import { DegreeRequirementsInput } from "../DegreeRequirementsInput"
import { FieldsOfStudyInput } from "../FieldsOfStudyInput"
import { GraduationYearInput } from "../GraduationYearInput"
import { type SearchFilters } from "../advancedFiltersTypes"

interface FilterSectionFormacaoProps {
  filters: SearchFilters
  setFilters: React.Dispatch<React.SetStateAction<SearchFilters>>
}

export const FilterSectionFormacao = React.memo(function FilterSectionFormacao({
  filters,
  setFilters,
}: FilterSectionFormacaoProps) {
  return (
    <div className="space-y-6">
      <div>
        <Label className="text-xs mb-2 block font-medium">Universidades</Label>
        <UniversitiesFilterInput
          value={filters.education?.universities || []}
          onChange={(universities) =>
            setFilters((prev) => ({
              ...prev,
              education: { ...(prev.education ?? {}), universities },
            }))
          }
          placeholder="Digite universidade e pressione Enter"
          showPresets={true}
        />
        <p className="text-xs mt-2 text-lia-text-secondary">
          Dica: Use &quot;Ask AI&quot; para buscar universidades similares ou por descrição
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-xs mb-1.5 block font-medium">Universidades Excluídas</Label>
          <ExcludedUniversitiesInput
            value={filters.education?.excludedUniversities || []}
            onChange={(excludedUniversities) =>
              setFilters((prev) => ({
                ...prev,
                education: { ...(prev.education ?? {}), excludedUniversities },
              }))
            }
            placeholder="USP, UNICAMP, PUC, FGV, etc."
          />
        </div>

        <div>
          <Label className="text-xs mb-1.5 block font-medium">Localização da Universidade</Label>
          <UniversityLocationsInput
            value={filters.education?.universityLocations || []}
            onChange={(universityLocations) =>
              setFilters((prev) => ({
                ...prev,
                education: { ...(prev.education ?? {}), universityLocations },
              }))
            }
            placeholder="São Paulo / Brasil / RJ / ..."
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label className="text-xs mb-1.5 block font-medium">Grau Acadêmico</Label>
          <DegreeRequirementsInput
            mode={filters.education?.degreeRequirementMode || "regular"}
            onModeChange={(degreeRequirementMode) =>
              setFilters((prev) => ({
                ...prev,
                education: { ...(prev.education ?? {}), degreeRequirementMode },
              }))
            }
            value={filters.education?.degree || null}
            onChange={(degree) =>
              setFilters((prev) => ({
                ...prev,
                education: { ...(prev.education ?? {}), degree },
              }))
            }
          />
        </div>

        <div>
          <Label className="text-xs mb-1.5 block font-medium">Áreas de Estudo</Label>
          <FieldsOfStudyInput
            mode={filters.education?.fieldsOfStudyMode || "regular"}
            onModeChange={(fieldsOfStudyMode) =>
              setFilters((prev) => ({
                ...prev,
                education: { ...(prev.education ?? {}), fieldsOfStudyMode },
              }))
            }
            value={filters.education?.fieldsOfStudy || []}
            onChange={(fieldsOfStudy) =>
              setFilters((prev) => ({
                ...prev,
                education: { ...(prev.education ?? {}), fieldsOfStudy },
              }))
            }
            placeholder="Engenharias, Ciências, Computação, etc."
          />
        </div>
      </div>

      <div>
        <Label className="text-xs mb-1.5 block font-medium">Ano de Formatura</Label>
        <GraduationYearInput
          minYear={filters.education?.graduationYearMin ?? null}
          maxYear={filters.education?.graduationYearMax ?? null}
          onMinYearChange={(graduationYearMin) =>
            setFilters((prev) => ({
              ...prev,
              education: { ...(prev.education ?? {}), graduationYearMin },
            }))
          }
          onMaxYearChange={(graduationYearMax) =>
            setFilters((prev) => ({
              ...prev,
              education: { ...(prev.education ?? {}), graduationYearMax },
            }))
          }
        />
      </div>
    </div>
  )
})
FilterSectionFormacao.displayName = "FilterSectionFormacao"
