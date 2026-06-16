"use client"

import {
  Check, X, Target, Loader2
} from "lucide-react"
import { useSemanticSearch } from "@/hooks/search/useSemanticSearch"
import { EditArchetypeRequirements } from "./EditArchetypeRequirements"
import { EditArchetypeSkillsSection } from "./EditArchetypeSkillsSection"
import { EditArchetypeTagsSection } from "./EditArchetypeTagsSection"

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
  editArchetypeName, onEditArchetypeNameChange,
  editArchetypeQuery, onEditArchetypeQueryChange,
  editArchetypeDescription, onEditArchetypeDescriptionChange,
  editArchetypeEmoji, onEditArchetypeEmojiChange,
  editArchetypeTags, onEditArchetypeTagsChange,
  editArchetypeSkills, onEditArchetypeSkillsChange,
  editArchetypeSeniority, onEditArchetypeSeniorityChange,
  editArchetypeIndustry, onEditArchetypeIndustryChange,
  editArchetypeExperienceMin, onEditArchetypeExperienceMinChange,
  editArchetypeLocation, onEditArchetypeLocationChange,
  editArchetypeWorkModel, onEditArchetypeWorkModelChange,
  editArchetypeLanguages, onEditArchetypeLanguagesChange,
  editArchetypeEmploymentType, onEditArchetypeEmploymentTypeChange,
  newLanguageInput, onNewLanguageInputChange,
  newTagInput, onNewTagInputChange,
  newSkillInput, onNewSkillInputChange,
  isSavingArchetype,
  aiSuggestedSkills, onAiSuggestedSkillsChange,
  selectedAiSkills, onSelectedAiSkillsChange,
  isFindingSimilarSkills, onIsFindingSimilarSkillsChange,
  showSkillSuggestions, onShowSkillSuggestionsChange,
  aiSuggestedTags, onAiSuggestedTagsChange,
  selectedAiTags, onSelectedAiTagsChange,
  isFindingSimilarTags, onIsFindingSimilarTagsChange,
  showTagSuggestions, onShowTagSuggestionsChange,
  industrySearchQuery, onIndustrySearchQueryChange,
  isIndustryDropdownOpen, onIsIndustryDropdownOpenChange,
  onClose, onSave,
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-lia-overlay" onClick={onClose}>
      <div className="bg-lia-bg-primary rounded-xl w-full max-w-[700px] mx-3 max-h-[85vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 px-5 py-4 border border-lia-border-subtle">
          <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 bg-wedo-cyan/15">
            <Target className="w-5 h-5 text-lia-text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold">
              {editingArchetype?.id ? "Editar Arquétipo" : "Criar Arquétipo"}
            </h3>
            <p className="text-xs truncate" aria-live="polite" aria-atomic="true">
              {editArchetypeName || "Novo perfil de candidato ideal"}
            </p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-xl hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none">
            <X className="w-4 h-4 text-lia-text-secondary" />
          </button>
        </div>

        <div className="px-5 py-4 space-y-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-base-ui font-semibold text-lia-text-primary">1</span>
              <h4 className="text-xs font-semibold text-lia-text-primary">Identificação do Arquétipo</h4>
            </div>
            <div className="flex gap-2">
              <div className="w-14">
                <label className="text-micro font-medium mb-0.5 block text-lia-text-secondary">Emoji</label>
                <input type="text" value={editArchetypeEmoji} onChange={(e) => onEditArchetypeEmojiChange(e.target.value)} maxLength={4} className="w-full rounded-md px-2 py-1.5 text-center text-base focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium border border-lia-border-subtle" />
              </div>
              <div className="flex-1">
                <label className="text-micro font-medium mb-0.5 block text-lia-text-secondary">Nome do Arquétipo</label>
                <input type="text" value={editArchetypeName} onChange={(e) => onEditArchetypeNameChange(e.target.value)} placeholder="Ex: Tech Lead, Product Manager..." className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium border border-lia-border-subtle" />
              </div>
            </div>
            <div>
              <label className="text-micro font-medium mb-0.5 block text-lia-text-secondary">Query de Busca</label>
              <textarea value={editArchetypeQuery} onChange={(e) => onEditArchetypeQueryChange(e.target.value)} placeholder="Ex: Tech Lead com experiência em gestão de equipes, arquitetura de sistemas, 8+ anos em desenvolvimento" rows={2} className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium resize-none border border-lia-border-subtle" />
            </div>
            <div>
              <label className="text-micro font-medium mb-0.5 block text-lia-text-secondary">Descrição</label>
              <textarea value={editArchetypeDescription} onChange={(e) => onEditArchetypeDescriptionChange(e.target.value)} placeholder="Líder técnico com experiência em gestão de equipes e arquitetura de sistemas" rows={2} className="w-full rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium resize-none border border-lia-border-subtle" />
            </div>
          </div>

          <EditArchetypeRequirements
            editArchetypeSeniority={editArchetypeSeniority} onEditArchetypeSeniorityChange={onEditArchetypeSeniorityChange}
            editArchetypeIndustry={editArchetypeIndustry} onEditArchetypeIndustryChange={onEditArchetypeIndustryChange}
            editArchetypeExperienceMin={editArchetypeExperienceMin} onEditArchetypeExperienceMinChange={onEditArchetypeExperienceMinChange}
            editArchetypeLocation={editArchetypeLocation} onEditArchetypeLocationChange={onEditArchetypeLocationChange}
            editArchetypeWorkModel={editArchetypeWorkModel} onEditArchetypeWorkModelChange={onEditArchetypeWorkModelChange}
            editArchetypeLanguages={editArchetypeLanguages} onEditArchetypeLanguagesChange={onEditArchetypeLanguagesChange}
            editArchetypeEmploymentType={editArchetypeEmploymentType} onEditArchetypeEmploymentTypeChange={onEditArchetypeEmploymentTypeChange}
            newLanguageInput={newLanguageInput} onNewLanguageInputChange={onNewLanguageInputChange}
            industrySearchQuery={industrySearchQuery} onIndustrySearchQueryChange={onIndustrySearchQueryChange}
            isIndustryDropdownOpen={isIndustryDropdownOpen} onIsIndustryDropdownOpenChange={onIsIndustryDropdownOpenChange}
          />

          <div className="space-y-3 pt-2 border-t border-t-lia-border-subtle">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-base-ui font-semibold text-lia-text-primary">3</span>
              <h4 className="text-xs font-semibold text-lia-text-primary">Competências Técnicas</h4>
            </div>

            <EditArchetypeSkillsSection
              editArchetypeSkills={editArchetypeSkills} onEditArchetypeSkillsChange={onEditArchetypeSkillsChange}
              newSkillInput={newSkillInput} onNewSkillInputChange={onNewSkillInputChange}
              aiSuggestedSkills={aiSuggestedSkills} onAiSuggestedSkillsChange={onAiSuggestedSkillsChange}
              selectedAiSkills={selectedAiSkills} onSelectedAiSkillsChange={onSelectedAiSkillsChange}
              isFindingSimilarSkills={isFindingSimilarSkills} onIsFindingSimilarSkillsChange={onIsFindingSimilarSkillsChange}
              showSkillSuggestions={showSkillSuggestions} onShowSkillSuggestionsChange={onShowSkillSuggestionsChange}
              semanticSkillSuggestions={semanticSkillSuggestions} isLoadingSemanticSkills={isLoadingSemanticSkills}
              searchSemanticSkills={searchSemanticSkills} clearSemanticSkillSuggestions={clearSemanticSkillSuggestions}
            />

            <EditArchetypeTagsSection
              editArchetypeTags={editArchetypeTags} onEditArchetypeTagsChange={onEditArchetypeTagsChange}
              newTagInput={newTagInput} onNewTagInputChange={onNewTagInputChange}
              aiSuggestedTags={aiSuggestedTags} onAiSuggestedTagsChange={onAiSuggestedTagsChange}
              selectedAiTags={selectedAiTags} onSelectedAiTagsChange={onSelectedAiTagsChange}
              isFindingSimilarTags={isFindingSimilarTags} onIsFindingSimilarTagsChange={onIsFindingSimilarTagsChange}
              showTagSuggestions={showTagSuggestions} onShowTagSuggestionsChange={onShowTagSuggestionsChange}
              semanticTagSuggestions={semanticTagSuggestions} isLoadingSemanticTags={isLoadingSemanticTags}
              searchSemanticTags={searchSemanticTags} clearSemanticTagSuggestions={clearSemanticTagSuggestions}
            />
          </div>
        </div>

        <div className="flex items-center justify-between px-5 py-4 border-t bg-lia-bg-secondary">
          <p className="text-xs text-lia-text-secondary">Campos obrigatórios: Nome e Query</p>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 rounded-xl text-xs font-medium transition-colors motion-reduce:transition-none hover:bg-lia-interactive-active border border-lia-border-subtle bg-transparent">Cancelar</button>
            <button
              onClick={onSave}
              disabled={isSavingArchetype || !editArchetypeName || !editArchetypeQuery}
              className={`px-4 py-2 rounded-md text-xs font-medium flex items-center gap-1.5 transition-colors motion-reduce:transition-none disabled:opacity-50 ${editArchetypeName && editArchetypeQuery ? 'bg-lia-text-primary text-white' : 'bg-lia-border-subtle text-lia-text-tertiary'}`}
            >
              {isSavingArchetype ? (
                <><Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />{editingArchetype?.id ? "Salvando..." : "Criando..."}</>
              ) : (
                <><Check className="w-3.5 h-3.5" />{editingArchetype?.id ? "Salvar" : "Criar Arquétipo"}</>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EditArchetypeModal
