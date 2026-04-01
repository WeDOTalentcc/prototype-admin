"use client"

import {
  Check, X, Target, MapPin, Briefcase, Code, Globe,
  Building2, Brain, Loader2, ChevronDown, Tag
} from "lucide-react"
import { cn } from "@/lib/utils"
import { INDUSTRIES, INDUSTRY_CATEGORIES } from "@/lib/industry-constants"
import { useSemanticSearch } from "@/hooks/useSemanticSearch"

interface EditArchetypeModalProps {
  editingArchetype: Record<string, unknown>
  editArchetypeName: string
  onEditArchetypeNameChange: (v: string) => void
  editArchetypeQuery: string
  onEditArchetypeQueryChange: (v: string) => void
  editArchetypeDescription: string
  onEditArchetypeDescriptionChange: (v: string) => void
  editArchetypeEmoji: string
  onEditArchetypeEmojiChange: (v: string) => void
  editArchetypeTags: string[]
  onEditArchetypeTagsChange: (tags: string[]) => void
  editArchetypeSkills: string[]
  onEditArchetypeSkillsChange: (skills: string[]) => void
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
  newTagInput: string
  onNewTagInputChange: (v: string) => void
  newSkillInput: string
  onNewSkillInputChange: (v: string) => void
  isSavingArchetype: boolean
  aiSuggestedSkills: string[]
  onAiSuggestedSkillsChange: (skills: string[]) => void
  selectedAiSkills: string[]
  onSelectedAiSkillsChange: (skills: string[]) => void
  isFindingSimilarSkills: boolean
  onIsFindingSimilarSkillsChange: (v: boolean) => void
  showSkillSuggestions: boolean
  onShowSkillSuggestionsChange: (v: boolean) => void
  aiSuggestedTags: string[]
  onAiSuggestedTagsChange: (tags: string[]) => void
  selectedAiTags: string[]
  onSelectedAiTagsChange: (tags: string[]) => void
  isFindingSimilarTags: boolean
  onIsFindingSimilarTagsChange: (v: boolean) => void
  showTagSuggestions: boolean
  onShowTagSuggestionsChange: (v: boolean) => void
  industrySearchQuery: string
  onIndustrySearchQueryChange: (v: string) => void
  isIndustryDropdownOpen: boolean
  onIsIndustryDropdownOpenChange: (v: boolean) => void
  onClose: () => void
  onSave: () => void
}

export function EditArchetypeModal({
  editingArchetype,
  editArchetypeName,
  onEditArchetypeNameChange,
  editArchetypeQuery,
  onEditArchetypeQueryChange,
  editArchetypeDescription,
  onEditArchetypeDescriptionChange,
  editArchetypeEmoji,
  onEditArchetypeEmojiChange,
  editArchetypeTags,
  onEditArchetypeTagsChange,
  editArchetypeSkills,
  onEditArchetypeSkillsChange,
  editArchetypeSeniority,
  onEditArchetypeSeniorityChange,
  editArchetypeIndustry,
  onEditArchetypeIndustryChange,
  editArchetypeExperienceMin,
  onEditArchetypeExperienceMinChange,
  editArchetypeLocation,
  onEditArchetypeLocationChange,
  editArchetypeWorkModel,
  onEditArchetypeWorkModelChange,
  editArchetypeLanguages,
  onEditArchetypeLanguagesChange,
  editArchetypeEmploymentType,
  onEditArchetypeEmploymentTypeChange,
  newLanguageInput,
  onNewLanguageInputChange,
  newTagInput,
  onNewTagInputChange,
  newSkillInput,
  onNewSkillInputChange,
  isSavingArchetype,
  aiSuggestedSkills,
  onAiSuggestedSkillsChange,
  selectedAiSkills,
  onSelectedAiSkillsChange,
  isFindingSimilarSkills,
  onIsFindingSimilarSkillsChange,
  showSkillSuggestions,
  onShowSkillSuggestionsChange,
  aiSuggestedTags,
  onAiSuggestedTagsChange,
  selectedAiTags,
  onSelectedAiTagsChange,
  isFindingSimilarTags,
  onIsFindingSimilarTagsChange,
  showTagSuggestions,
  onShowTagSuggestionsChange,
  industrySearchQuery,
  onIndustrySearchQueryChange,
  isIndustryDropdownOpen,
  onIsIndustryDropdownOpenChange,
  onClose,
  onSave,
}: EditArchetypeModalProps) {
  const {
    suggestions: semanticSkillSuggestions,
    isLoading: isLoadingSemanticSkills,
    search: searchSemanticSkills,
    clearSuggestions: clearSemanticSkillSuggestions,
  } = useSemanticSearch({ domain: "skills", debounceMs: 400 })

  const {
    suggestions: semanticTagSuggestions,
    isLoading: isLoadingSemanticTags,
    search: searchSemanticTags,
    clearSuggestions: clearSemanticTagSuggestions,
  } = useSemanticSearch({ domain: "roles", debounceMs: 400 })

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
    >
      <div
        className="bg-lia-bg-primary rounded-md w-full max-w-[700px] mx-3 max-h-[85vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border border-lia-border-subtle">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 bg-wedo-cyan/15"
          >
            <Target className="w-5 h-5 lia-text-700" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold" style={{color: "var(--gray-950)"}}>
              {editingArchetype?.id ? "Editar Arquétipo" : "Criar Arquétipo"}
            </h3>
            <p className="text-xs truncate" aria-live="polite" aria-atomic="true">
              {editArchetypeName || "Novo perfil de candidato ideal"}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-gray-100 transition-colors motion-reduce:transition-none"
          >
            <X className="w-4 h-4 lia-text-500" />
          </button>
        </div>

        {/* Content */}
        <div className="px-5 py-4 space-y-4">
          {/* Seção 1: Identificação */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-base-ui font-semibold lia-text-700">1</span>
              <h4 className="text-xs font-semibold lia-text-800">Identificação do Arquétipo</h4>
            </div>

            {/* Nome e Emoji */}
            <div className="flex gap-2">
              <div className="w-14">
                <label className="text-micro font-medium mb-0.5 block lia-text-500">Emoji</label>
                <input
                  type="text"
                  value={editArchetypeEmoji}
                  onChange={(e) => onEditArchetypeEmojiChange(e.target.value)}
                  maxLength={4}
                  className="w-full rounded-md px-2 py-1.5 text-center text-base focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-lia-border-subtle"
                />
              </div>
              <div className="flex-1">
                <label className="text-micro font-medium mb-0.5 block lia-text-500">
                  Nome do Arquétipo
                </label>
                <input
                  type="text"
                  value={editArchetypeName}
                  onChange={(e) => onEditArchetypeNameChange(e.target.value)}
                  placeholder="Ex: Tech Lead, Product Manager..."
                  className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-lia-border-subtle"
                />
              </div>
            </div>

            {/* Query de Busca */}
            <div>
              <label className="text-micro font-medium mb-0.5 block lia-text-500">
                Query de Busca
              </label>
              <textarea
                value={editArchetypeQuery}
                onChange={(e) => onEditArchetypeQueryChange(e.target.value)}
                placeholder="Ex: Tech Lead com experiência em gestão de equipes, arquitetura de sistemas, 8+ anos em desenvolvimento"
                rows={2}
                className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 resize-none border border-lia-border-subtle"
              />
            </div>

            {/* Descrição */}
            <div>
              <label className="text-micro font-medium mb-0.5 block lia-text-500">Descrição</label>
              <textarea
                value={editArchetypeDescription}
                onChange={(e) => onEditArchetypeDescriptionChange(e.target.value)}
                placeholder="Líder técnico com experiência em gestão de equipes e arquitetura de sistemas"
                rows={2}
                className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 resize-none border border-lia-border-subtle"
              />
            </div>
          </div>

          {/* Seção 2: Requisitos */}
          <div className="space-y-3 pt-2 border-t border-t-gray-100">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base-ui font-semibold lia-text-700">2</span>
              <h4 className="text-xs font-semibold lia-text-800">Requisitos do Perfil</h4>
            </div>

            {/* Grid de 2 colunas: (Senioridade + Exp Min) | (Indústria) */}
            <div className="grid grid-cols-2 gap-4">
              {/* Coluna 1: Senioridade + Experiência */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-xs font-medium mb-1 block lia-text-500">Senioridade</label>
                  <select
                    value={editArchetypeSeniority}
                    onChange={(e) => onEditArchetypeSeniorityChange(e.target.value)}
                    className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-lia-border-subtle"
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
                  <label className="text-xs font-medium mb-1 block lia-text-500">Exp. Mínima</label>
                  <input
                    type="number"
                    min={0}
                    max={30}
                    value={editArchetypeExperienceMin ?? ""}
                    onChange={(e) =>
                      onEditArchetypeExperienceMinChange(e.target.value ? parseInt(e.target.value) : null)
                    }
                    placeholder="Anos"
                    className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-lia-border-subtle"
                  />
                </div>
              </div>

              {/* Coluna 2: Indústria (searchable dropdown) */}
              <div className="relative">
                <label className="text-xs font-medium mb-1 block lia-text-500">Indústria</label>
                <button
                  type="button"
                  onClick={() => onIsIndustryDropdownOpenChange(!isIndustryDropdownOpen)}
                  className="w-full rounded-md px-2 py-1.5 text-xs text-left flex items-center justify-between focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-lia-border-subtle"
                >
                  <span style={{color: editArchetypeIndustry ? "var(--gray-950)" : "var(--gray-400)"}}>
                    {editArchetypeIndustry
                      ? (INDUSTRIES.find((i) => i.key === editArchetypeIndustry)?.labelPt || editArchetypeIndustry)
                      : "Selecionar..."}
                  </span>
                  <ChevronDown className="w-3 h-3" style={{color: "var(--gray-400)"}} />
                </button>
                {isIndustryDropdownOpen && (
                  <div className="absolute z-10 mt-1 w-full bg-lia-bg-primary rounded-md border border-lia-border-subtle max-h-[200px] overflow-hidden">
                    <div className="p-2 border-b border-lia-border-subtle sticky top-0 bg-lia-bg-primary">
                      <input
                        type="text"
                        value={industrySearchQuery}
                        onChange={(e) => onIndustrySearchQueryChange(e.target.value)}
                        placeholder="Buscar setor..."
                        className="w-full rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-lia-border-subtle"
                        autoFocus
                      />
                    </div>
                    <div className="max-h-[150px] overflow-y-auto">
                      <button
                        type="button"
                        onClick={() => {
                          onEditArchetypeIndustryChange("")
                          onIsIndustryDropdownOpenChange(false)
                          onIndustrySearchQueryChange("")
                        }}
                        className="w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50"
                        style={{color: "var(--gray-400)"}}
                      >
                        - Nenhum -
                      </button>
                      {Object.entries(INDUSTRY_CATEGORIES).map(([catKey, catLabel]) => {
                        const categoryIndustries = INDUSTRIES.filter((i) => i.category === catKey).filter(
                          (i) =>
                            !industrySearchQuery.trim() ||
                            i.labelPt.toLowerCase().includes(industrySearchQuery.toLowerCase()) ||
                            i.key.toLowerCase().includes(industrySearchQuery.toLowerCase())
                        )
                        if (categoryIndustries.length === 0) return null
                        return (
                          <div key={catKey}>
                            <div className="px-3 py-1 text-micro font-semibold uppercase tracking-wide bg-gray-50">
                              {catLabel.labelPt}
                            </div>
                            {categoryIndustries.map((industry) => (
                              <button
                                key={industry.key}
                                type="button"
                                onClick={() => {
                                  onEditArchetypeIndustryChange(industry.key)
                                  onIsIndustryDropdownOpenChange(false)
                                  onIndustrySearchQueryChange("")
                                }}
                                className={`w-full px-3 py-1.5 text-left text-xs hover:bg-gray-50 ${
                                  editArchetypeIndustry === industry.key ? "bg-gray-100 dark:bg-lia-bg-secondary" : ""
                                }`}
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

            {/* Localização e Modelo de Trabalho */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium mb-1 flex items-center gap-1 lia-text-500">
                  <MapPin className="w-3 h-3 lia-text-700" />
                  Localização
                </label>
                <input
                  type="text"
                  value={editArchetypeLocation}
                  onChange={(e) => onEditArchetypeLocationChange(e.target.value)}
                  placeholder="São Paulo, Brasil..."
                  className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-lia-border-subtle"
                />
              </div>
              <div>
                <label className="text-xs font-medium mb-1 flex items-center gap-1 lia-text-500">
                  <Building2 className="w-3 h-3 lia-text-700" />
                  Modelo de Trabalho
                </label>
                <select
                  value={editArchetypeWorkModel}
                  onChange={(e) => onEditArchetypeWorkModelChange(e.target.value)}
                  className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-lia-border-subtle"
                >
                  <option value="">Qualquer</option>
                  <option value="remote">Remoto</option>
                  <option value="hybrid">Híbrido</option>
                  <option value="onsite">Presencial</option>
                </select>
              </div>
            </div>

            {/* Idiomas e Tipo de Contrato */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-medium mb-1 flex items-center gap-1 lia-text-500">
                  <Globe className="w-3 h-3 lia-text-700" />
                  Idiomas
                </label>
                <div className="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px] p-2 rounded-md border border-lia-border-subtle">
                  {editArchetypeLanguages.map((lang, idx) => (
                    <span
                      key={`lang-${idx}`}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-wedo-cyan/15"
                    >
                      {lang}
                      <button
                        type="button"
                        onClick={() =>
                          onEditArchetypeLanguagesChange(editArchetypeLanguages.filter((_, i) => i !== idx))
                        }
                        className="hover:bg-gray-100 dark:bg-lia-bg-secondary rounded-full p-0.5"
                      >
                        <X className="w-3 h-3 lia-text-700" />
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
                  className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-lia-border-subtle"
                />
              </div>
              <div>
                <label className="text-xs font-medium mb-1 flex items-center gap-1 lia-text-500">
                  <Briefcase className="w-3 h-3 lia-text-600" />
                  Tipo de Contrato
                </label>
                <select
                  value={editArchetypeEmploymentType}
                  onChange={(e) => onEditArchetypeEmploymentTypeChange(e.target.value)}
                  className="w-full rounded-md px-2.5 py-2 text-xs focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400 border border-lia-border-subtle"
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

          {/* Seção 3: Competências */}
          <div className="space-y-3 pt-2 border-t border-t-gray-100">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base-ui font-semibold lia-text-700">3</span>
              <h4 className="text-xs font-semibold lia-text-800">Competências Técnicas</h4>
            </div>

            {/* Skills */}
            <div>
              <label className="text-xs font-medium mb-1 flex items-center gap-1.5 lia-text-500">
                <Code className="w-3.5 h-3.5 lia-text-700" />
                Skills
                <span className="text-micro font-normal lia-text-400">
                  (habilidades técnicas: Python, React, AWS...)
                </span>
              </label>
              <div className="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px] p-2 rounded-md border border-lia-border-subtle">
                {editArchetypeSkills.map((skill, idx) => (
                  <span
                    key={`skill-${idx}`}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-wedo-cyan/15"
                  >
                    {skill}
                    <button
                      type="button"
                      onClick={() =>
                        onEditArchetypeSkillsChange(editArchetypeSkills.filter((_, i) => i !== idx))
                      }
                      className="hover:bg-gray-100 dark:bg-lia-bg-secondary rounded-full p-0.5"
                    >
                      <X className="w-3 h-3 lia-text-700" />
                    </button>
                  </span>
                ))}
                {editArchetypeSkills.length === 0 && (
                  <span className="text-xs lia-text-400">Nenhuma skill</span>
                )}
              </div>
              <div className="relative">
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    value={newSkillInput}
                    onChange={(e) => {
                      onNewSkillInputChange(e.target.value)
                      if (e.target.value.length >= 2) {
                        searchSemanticSkills(e.target.value, editArchetypeSkills)
                        onShowSkillSuggestionsChange(true)
                      } else {
                        clearSemanticSkillSuggestions()
                        onShowSkillSuggestionsChange(false)
                      }
                    }}
                    onFocus={() => {
                      if (newSkillInput.length >= 2 && semanticSkillSuggestions.length > 0) {
                        onShowSkillSuggestionsChange(true)
                      }
                    }}
                    onBlur={() => {
                      setTimeout(() => onShowSkillSuggestionsChange(false), 200)
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && newSkillInput.trim()) {
                        e.preventDefault()
                        if (!editArchetypeSkills.includes(newSkillInput.trim())) {
                          onEditArchetypeSkillsChange([...editArchetypeSkills, newSkillInput.trim()])
                        }
                        onNewSkillInputChange("")
                        clearSemanticSkillSuggestions()
                        onShowSkillSuggestionsChange(false)
                      }
                    }}
                    placeholder="Digite e pressione Enter..."
                    className="flex-1 rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-lia-border-subtle"
                  />
                  <button
                    type="button"
                    onClick={async () => {
                      if (editArchetypeSkills.length === 0) return
                      onIsFindingSimilarSkillsChange(true)
                      onAiSuggestedSkillsChange([])
                      onSelectedAiSkillsChange([])
                      try {
                        const response = await fetch("/api/ai/suggest-similar-skills", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ skills: editArchetypeSkills }),
                        })
                        if (response.ok) {
                          const data = await response.json()
                          if (data.suggestions?.length > 0) {
                            const newSkills = data.suggestions
                              .filter(
                                (s: string) =>
                                  !editArchetypeSkills.map((sk) => sk.toLowerCase()).includes(s.toLowerCase())
                              )
                              .slice(0, 10)
                            onAiSuggestedSkillsChange(newSkills)
                          }
                        }
                      } catch (error) {
                      } finally {
                        onIsFindingSimilarSkillsChange(false)
                      }
                    }}
                    disabled={editArchetypeSkills.length === 0 || isFindingSimilarSkills}
                    className={`px-2 py-1 rounded-full flex items-center gap-1 text-micro transition-colors motion-reduce:transition-none disabled:opacity-50 ${editArchetypeSkills.length > 0 ? "bg-wedo-cyan/15 lia-text-950" : "bg-gray-100 lia-text-400"}`}
                    title="Buscar skills similares com IA"
                  >
                    {isFindingSimilarSkills ? (
                      <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                    ) : (
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                    )}
                    Similares
                  </button>
                </div>
                {showSkillSuggestions && semanticSkillSuggestions.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-md max-h-[150px] overflow-y-auto" role="status" aria-live="polite" aria-label="Carregando...">
                    {isLoadingSemanticSkills && (
                      <div className="flex items-center justify-center py-2" role="status" aria-live="polite" aria-label="Carregando...">
                        <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none lia-text-400" />
                      </div>
                    )}
                    {semanticSkillSuggestions.map((suggestion, idx) => (
                      <button
                        key={`sem-skill-${idx}`}
                        type="button"
                        className="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-50 transition-colors motion-reduce:transition-none flex items-center gap-1.5"
                        onMouseDown={(e) => {
                          e.preventDefault()
                          if (!editArchetypeSkills.includes(suggestion.term)) {
                            onEditArchetypeSkillsChange([...editArchetypeSkills, suggestion.term])
                          }
                          onNewSkillInputChange("")
                          clearSemanticSkillSuggestions()
                          onShowSkillSuggestionsChange(false)
                        }}
                      >
                        <Code className="w-3 h-3 lia-text-400" />
                        <span style={{color: "var(--gray-950)"}}>{suggestion.term}</span>
                        {suggestion.is_synonym && (
                          <span className="text-micro px-1 py-0.5 rounded-full bg-gray-100 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary">
                            sinônimo
                          </span>
                        )}
                        {suggestion.is_related && (
                          <span className="text-micro px-1 py-0.5 rounded-full bg-status-success/10 text-status-success">
                            relacionado
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {aiSuggestedSkills.length > 0 && (
                <div className="mt-2 p-2 rounded-md bg-wedo-cyan/8 border border-wedo-cyan/30">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Brain className="w-3 h-3 text-wedo-cyan" />
                    <span className="text-micro font-medium lia-text-700">Sugestões de IA</span>
                    <button
                      type="button"
                      onClick={() => {
                        onAiSuggestedSkillsChange([])
                        onSelectedAiSkillsChange([])
                      }}
                      className="ml-auto p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                    >
                      <X className="w-3 h-3 lia-text-700" />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {aiSuggestedSkills.map((skill, idx) => {
                      const isSelected = selectedAiSkills.includes(skill)
                      return (
                        <button
                          key={`ai-skill-${idx}`}
                          type="button"
                          onClick={() => {
                            if (isSelected) {
                              onSelectedAiSkillsChange(selectedAiSkills.filter((s) => s !== skill))
                            } else {
                              onSelectedAiSkillsChange([...selectedAiSkills, skill])
                            }
                          }}
                          className={cn(
                            "px-1.5 py-0.5 rounded-full text-micro transition-[width,height] cursor-pointer text-wedo-cyan-dark",
                            isSelected ? "ring-2 ring-gray-900/20 bg-wedo-cyan/25" : "bg-wedo-cyan/15"
                          )}
                        >
                          {skill}
                        </button>
                      )
                    })}
                  </div>
                  {selectedAiSkills.length > 0 && (
                    <button
                      type="button"
                      onClick={() => {
                        onEditArchetypeSkillsChange([
                          ...editArchetypeSkills,
                          ...selectedAiSkills.filter((s) => !editArchetypeSkills.includes(s)),
                        ])
                        onAiSuggestedSkillsChange(aiSuggestedSkills.filter((s) => !selectedAiSkills.includes(s)))
                        onSelectedAiSkillsChange([])
                      }}
                      className="mt-2 w-full py-1 rounded-md text-micro font-medium transition-colors motion-reduce:transition-none bg-gray-900 text-white"
                    >
                      Adicionar {selectedAiSkills.length} Selecionado
                      {selectedAiSkills.length > 1 ? "s" : ""}
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Tags */}
            <div>
              <label className="text-xs font-medium mb-1 flex items-center gap-1.5 lia-text-500">
                <Tag className="w-3.5 h-3.5 lia-text-700" />
                Tags
                <span className="text-micro font-normal lia-text-400">
                  (categorias: liderança, estratégia, backend...)
                </span>
              </label>
              <div className="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px] p-2 rounded-md border border-lia-border-subtle">
                {editArchetypeTags.map((tag, idx) => (
                  <span
                    key={`tag-${idx}`}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium"
                  >
                    {tag}
                    <button
                      type="button"
                      onClick={() =>
                        onEditArchetypeTagsChange(editArchetypeTags.filter((_, i) => i !== idx))
                      }
                      className="hover:bg-gray-300 rounded-full p-0.5"
                    >
                      <X className="w-3 h-3 lia-text-500" />
                    </button>
                  </span>
                ))}
                {editArchetypeTags.length === 0 && (
                  <span className="text-xs lia-text-400">Nenhuma tag</span>
                )}
              </div>
              <div className="relative">
                <div className="flex gap-1.5">
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => {
                      onNewTagInputChange(e.target.value)
                      if (e.target.value.length >= 2) {
                        searchSemanticTags(e.target.value, editArchetypeTags)
                        onShowTagSuggestionsChange(true)
                      } else {
                        clearSemanticTagSuggestions()
                        onShowTagSuggestionsChange(false)
                      }
                    }}
                    onFocus={() => {
                      if (newTagInput.length >= 2 && semanticTagSuggestions.length > 0) {
                        onShowTagSuggestionsChange(true)
                      }
                    }}
                    onBlur={() => {
                      setTimeout(() => onShowTagSuggestionsChange(false), 200)
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && newTagInput.trim()) {
                        e.preventDefault()
                        if (!editArchetypeTags.includes(newTagInput.trim())) {
                          onEditArchetypeTagsChange([...editArchetypeTags, newTagInput.trim()])
                        }
                        onNewTagInputChange("")
                        clearSemanticTagSuggestions()
                        onShowTagSuggestionsChange(false)
                      }
                    }}
                    placeholder="Digite e pressione Enter..."
                    className="flex-1 rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 border border-lia-border-subtle"
                  />
                  <button
                    type="button"
                    onClick={async () => {
                      if (editArchetypeTags.length === 0) return
                      onIsFindingSimilarTagsChange(true)
                      onAiSuggestedTagsChange([])
                      onSelectedAiTagsChange([])
                      try {
                        const response = await fetch("/api/ai/suggest-similar-skills", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({ skills: editArchetypeTags }),
                        })
                        if (response.ok) {
                          const data = await response.json()
                          if (data.suggestions?.length > 0) {
                            const newTags = data.suggestions
                              .filter(
                                (s: string) =>
                                  !editArchetypeTags.map((t) => t.toLowerCase()).includes(s.toLowerCase())
                              )
                              .slice(0, 10)
                            onAiSuggestedTagsChange(newTags)
                          }
                        }
                      } catch (error) {
                      } finally {
                        onIsFindingSimilarTagsChange(false)
                      }
                    }}
                    disabled={editArchetypeTags.length === 0 || isFindingSimilarTags}
                    className={`px-2 py-1 rounded-full flex items-center gap-1 text-micro transition-colors motion-reduce:transition-none disabled:opacity-50 ${editArchetypeTags.length > 0 ? "bg-wedo-cyan/15 lia-text-950" : "bg-gray-100 lia-text-400"}`}
                    title="Buscar tags similares com IA"
                  >
                    {isFindingSimilarTags ? (
                      <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
                    ) : (
                      <Brain className="w-3 h-3 text-wedo-cyan" />
                    )}
                    Similares
                  </button>
                </div>
                {showTagSuggestions && semanticTagSuggestions.length > 0 && (
                  <div className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-md max-h-[150px] overflow-y-auto" role="status" aria-live="polite" aria-label="Carregando...">
                    {isLoadingSemanticTags && (
                      <div className="flex items-center justify-center py-2" role="status" aria-live="polite" aria-label="Carregando...">
                        <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none lia-text-400" />
                      </div>
                    )}
                    {semanticTagSuggestions.map((suggestion, idx) => (
                      <button
                        key={`sem-tag-${idx}`}
                        type="button"
                        className="w-full text-left px-2 py-1.5 text-xs hover:bg-gray-50 transition-colors motion-reduce:transition-none flex items-center gap-1.5"
                        onMouseDown={(e) => {
                          e.preventDefault()
                          if (!editArchetypeTags.includes(suggestion.term)) {
                            onEditArchetypeTagsChange([...editArchetypeTags, suggestion.term])
                          }
                          onNewTagInputChange("")
                          clearSemanticTagSuggestions()
                          onShowTagSuggestionsChange(false)
                        }}
                      >
                        <Tag className="w-3 h-3 lia-text-400" />
                        <span style={{color: "var(--gray-950)"}}>{suggestion.term}</span>
                        {suggestion.is_synonym && (
                          <span className="text-micro px-1 py-0.5 rounded-full bg-gray-100 dark:bg-lia-bg-secondary lia-text-600 dark:text-lia-text-tertiary">
                            sinônimo
                          </span>
                        )}
                        {suggestion.is_related && (
                          <span className="text-micro px-1 py-0.5 rounded-full bg-status-success/10 text-status-success">
                            relacionado
                          </span>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              {aiSuggestedTags.length > 0 && (
                <div className="mt-2 p-2 rounded-md bg-wedo-cyan/8 border border-wedo-cyan/30">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Brain className="w-3 h-3 text-wedo-cyan" />
                    <span className="text-micro font-medium lia-text-700">Sugestões de IA</span>
                    <button
                      type="button"
                      onClick={() => {
                        onAiSuggestedTagsChange([])
                        onSelectedAiTagsChange([])
                      }}
                      className="ml-auto p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                    >
                      <X className="w-3 h-3 lia-text-700" />
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {aiSuggestedTags.map((tag, idx) => {
                      const isSelected = selectedAiTags.includes(tag)
                      return (
                        <button
                          key={`ai-tag-${idx}`}
                          type="button"
                          onClick={() => {
                            if (isSelected) {
                              onSelectedAiTagsChange(selectedAiTags.filter((t) => t !== tag))
                            } else {
                              onSelectedAiTagsChange([...selectedAiTags, tag])
                            }
                          }}
                          className={cn(
                            "px-1.5 py-0.5 rounded-full text-micro transition-[width,height] cursor-pointer text-wedo-cyan-dark",
                            isSelected ? "ring-2 ring-gray-900/20 bg-wedo-cyan/25" : "bg-wedo-cyan/15"
                          )}
                        >
                          {tag}
                        </button>
                      )
                    })}
                  </div>
                  {selectedAiTags.length > 0 && (
                    <button
                      type="button"
                      onClick={() => {
                        onEditArchetypeTagsChange([
                          ...editArchetypeTags,
                          ...selectedAiTags.filter((t) => !editArchetypeTags.includes(t)),
                        ])
                        onAiSuggestedTagsChange(aiSuggestedTags.filter((t) => !selectedAiTags.includes(t)))
                        onSelectedAiTagsChange([])
                      }}
                      className="mt-2 w-full py-1 rounded-md text-micro font-medium transition-colors motion-reduce:transition-none bg-gray-900 text-white"
                    >
                      Adicionar {selectedAiTags.length} Selecionado
                      {selectedAiTags.length > 1 ? "s" : ""}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t bg-gray-50">
          <p className="text-xs lia-text-500">Campos obrigatórios: Nome e Query</p>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-md text-xs font-medium transition-colors motion-reduce:transition-none hover:bg-gray-200 border border-lia-border-subtle bg-transparent"
            >
              Cancelar
            </button>
            <button
              onClick={onSave}
              disabled={isSavingArchetype || !editArchetypeName || !editArchetypeQuery}
              className="px-4 py-2 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors motion-reduce:transition-none disabled:opacity-50"
              style={{backgroundColor:
                  editArchetypeName && editArchetypeQuery ? "var(--gray-800)" : "var(--gray-200)",
                color: editArchetypeName && editArchetypeQuery ? "white" : "var(--gray-400)"}}
            >
              {isSavingArchetype ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
                  {editingArchetype?.id ? "Salvando..." : "Criando..."}
                </>
              ) : (
                <>
                  <Check className="w-3.5 h-3.5" />
                  {editingArchetype?.id ? "Salvar" : "Criar Arquétipo"}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EditArchetypeModal
