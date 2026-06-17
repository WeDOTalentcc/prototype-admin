"use client"

import {
  X, MapPin, Briefcase, Globe,
  Building2, ChevronDown
} from "lucide-react"
import { INDUSTRIES, INDUSTRY_CATEGORIES } from "@/lib/industry-constants"

interface EditArchetypeRequirementsProps {
  editArchetypeSeniority: string
  onEditArchetypeSeniorityChange: (v: string) => void
  editArchetypeIndustry: string
  onEditArchetypeIndustryChange: (v: string) => void
  editArchetypeExperienceMin: number | null
  onEditArchetypeExperienceMinChange: (v: number | null) => void
  editArchetypeLocation: string
  onEditArchetypeLocationChange: (v: string) => void
  editArchetypeWorkModel: string
  onEditArchetypeWorkModelChange: (v: string) => void
  editArchetypeLanguages: string[]
  onEditArchetypeLanguagesChange: (langs: string[]) => void
  editArchetypeEmploymentType: string
  onEditArchetypeEmploymentTypeChange: (v: string) => void
  newLanguageInput: string
  onNewLanguageInputChange: (v: string) => void
  industrySearchQuery: string
  onIndustrySearchQueryChange: (v: string) => void
  isIndustryDropdownOpen: boolean
  onIsIndustryDropdownOpenChange: (v: boolean) => void
}

export function EditArchetypeRequirements({
  editArchetypeSeniority, onEditArchetypeSeniorityChange,
  editArchetypeIndustry, onEditArchetypeIndustryChange,
  editArchetypeExperienceMin, onEditArchetypeExperienceMinChange,
  editArchetypeLocation, onEditArchetypeLocationChange,
  editArchetypeWorkModel, onEditArchetypeWorkModelChange,
  editArchetypeLanguages, onEditArchetypeLanguagesChange,
  editArchetypeEmploymentType, onEditArchetypeEmploymentTypeChange,
  newLanguageInput, onNewLanguageInputChange,
  industrySearchQuery, onIndustrySearchQueryChange,
  isIndustryDropdownOpen, onIsIndustryDropdownOpenChange,
}: EditArchetypeRequirementsProps) {
  return (
    <div className="space-y-3 pt-2 border-t border-t-lia-border-subtle">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-base-ui font-semibold text-lia-text-primary">2</span>
        <h4 className="text-xs font-semibold text-lia-text-primary">Requisitos do Perfil</h4>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs font-medium mb-1 block text-lia-text-secondary">Senioridade</label>
            <select
              value={editArchetypeSeniority}
              onChange={(e) => onEditArchetypeSeniorityChange(e.target.value)}
              className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium border border-lia-border-subtle"
            >
              <option value="">-</option>
              <option value="junior">Júnior</option>
              <option value="pleno">Pleno</option>
              <option value="senior">Sênior</option>
              <option value="lead">Lead</option>
              <option value="staff">Staff</option>
              <option value="principal">Principal</option>
              <option value="manager">Gerente</option>
              <option value="director">Diretor</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium mb-1 block text-lia-text-secondary">Exp. Mínima</label>
            <input
              type="number"
              min={0}
              max={30}
              value={editArchetypeExperienceMin ?? ""}
              onChange={(e) => onEditArchetypeExperienceMinChange(e.target.value ? parseInt(e.target.value) : null)}
              placeholder="Anos"
              className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium border border-lia-border-subtle"
            />
          </div>
        </div>

        <div className="relative">
          <label className="text-xs font-medium mb-1 block text-lia-text-secondary">Indústria</label>
          <button
            type="button"
            onClick={() => onIsIndustryDropdownOpenChange(!isIndustryDropdownOpen)}
            className="w-full rounded-md px-2 py-1.5 text-xs text-left flex items-center justify-between focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 border border-lia-border-subtle"
          >
            <span className={editArchetypeIndustry ? "text-lia-btn-primary-bg" : "text-lia-text-tertiary"}>
              {editArchetypeIndustry
                ? (INDUSTRIES.find((i) => i.key === editArchetypeIndustry)?.labelPt || editArchetypeIndustry)
                : "Selecionar..."}
            </span>
            <ChevronDown className="w-3 h-3" />
          </button>
          {isIndustryDropdownOpen && (
            <div className="absolute z-10 mt-1 w-full bg-lia-bg-primary rounded-xl border border-lia-border-subtle max-h-chart-sm overflow-hidden">
              <div className="p-2 border-b border-lia-border-subtle sticky top-0 bg-lia-bg-primary">
                <input
                  type="text"
                  value={industrySearchQuery}
                  onChange={(e) => onIndustrySearchQueryChange(e.target.value)}
                  placeholder="Buscar setor..."
                  className="w-full rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 border border-lia-border-subtle"
                  autoFocus
                />
              </div>
              <div className="max-h-[150px] overflow-y-auto">
                <button
                  type="button"
                  onClick={() => { onEditArchetypeIndustryChange(""); onIsIndustryDropdownOpenChange(false); onIndustrySearchQueryChange("") }}
                  className="w-full px-3 py-1.5 text-left text-xs hover:bg-lia-bg-secondary"
                 
                >
                  - Nenhum -
                </button>
                {Object.entries(INDUSTRY_CATEGORIES).map(([catKey, catLabel]) => {
                  const categoryIndustries = INDUSTRIES.filter((i) => i.category === catKey).filter(
                    (i) => !industrySearchQuery.trim() || i.labelPt.toLowerCase().includes(industrySearchQuery.toLowerCase()) || i.key.toLowerCase().includes(industrySearchQuery.toLowerCase())
                  )
                  if (categoryIndustries.length === 0) return null
                  return (
                    <div key={catKey}>
                      <div className="px-3 py-1 text-micro font-semibold uppercase tracking-wide bg-lia-bg-secondary">{catLabel.labelPt}</div>
                      {categoryIndustries.map((industry) => (
                        <button
                          key={industry.key}
                          type="button"
                          onClick={() => { onEditArchetypeIndustryChange(industry.key); onIsIndustryDropdownOpenChange(false); onIndustrySearchQueryChange("") }}
                          className={`w-full px-3 py-1.5 text-left text-xs hover:bg-lia-bg-secondary ${editArchetypeIndustry === industry.key ? "bg-lia-bg-tertiary dark:bg-lia-bg-secondary" : ""}`}
                        >
                          {industry.labelPt}
                        </button>
                      ))}
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium mb-1 flex items-center gap-1 text-lia-text-secondary">
            <MapPin className="w-3 h-3 text-lia-text-primary" />
            Localização
          </label>
          <input
            type="text"
            value={editArchetypeLocation}
            onChange={(e) => onEditArchetypeLocationChange(e.target.value)}
            placeholder="São Paulo, Brasil..."
            className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium border border-lia-border-subtle"
          />
        </div>
        <div>
          <label className="text-xs font-medium mb-1 flex items-center gap-1 text-lia-text-secondary">
            <Building2 className="w-3 h-3 text-lia-text-primary" />
            Modelo de Trabalho
          </label>
          <select
            value={editArchetypeWorkModel}
            onChange={(e) => onEditArchetypeWorkModelChange(e.target.value)}
            className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium border border-lia-border-subtle"
          >
            <option value="">Qualquer</option>
            <option value="remote">Remoto</option>
            <option value="hybrid">Híbrido</option>
            <option value="onsite">Presencial</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-xs font-medium mb-1 flex items-center gap-1 text-lia-text-secondary">
            <Globe className="w-3 h-3 text-lia-text-primary" />
            Idiomas
          </label>
          <div className="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px] p-2 rounded-xl border border-lia-border-subtle">
            {editArchetypeLanguages.map((lang, idx) => (
              <span key={`lang-${idx}`} className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-wedo-cyan/15">
                {lang}
                <button type="button" onClick={() => onEditArchetypeLanguagesChange(editArchetypeLanguages.filter((_, i) => i !== idx))} className="hover:bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full p-0.5">
                  <X className="w-3 h-3 text-lia-text-primary" />
                </button>
              </span>
            ))}
          </div>
          <input
            type="text"
            value={newLanguageInput}
            onChange={(e) => onNewLanguageInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && newLanguageInput.trim()) {
                e.preventDefault()
                if (!editArchetypeLanguages.includes(newLanguageInput.trim())) {
                  onEditArchetypeLanguagesChange([...editArchetypeLanguages, newLanguageInput.trim()])
                }
                onNewLanguageInputChange("")
              }
            }}
            placeholder="Inglês, Espanhol..."
            className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium border border-lia-border-subtle"
          />
        </div>
        <div>
          <label className="text-xs font-medium mb-1 flex items-center gap-1 text-lia-text-secondary">
            <Briefcase className="w-3 h-3 text-lia-text-secondary" />
            Tipo de Contrato
          </label>
          <select
            value={editArchetypeEmploymentType}
            onChange={(e) => onEditArchetypeEmploymentTypeChange(e.target.value)}
            className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium border border-lia-border-subtle"
          >
            <option value="">Qualquer</option>
            <option value="clt">CLT</option>
            <option value="pj">PJ</option>
            <option value="intern">Estágio</option>
            <option value="temporary">Temporário</option>
            <option value="freelancer">Freelancer</option>
          </select>
        </div>
      </div>
    </div>
  )
}
