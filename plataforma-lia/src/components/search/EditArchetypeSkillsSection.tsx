"use client"

import { X, Code, Brain, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

interface SemanticSuggestion {
  term: string
  is_synonym?: boolean
  is_related?: boolean
}

interface EditArchetypeSkillsSectionProps {
  editArchetypeSkills: string[]
  onEditArchetypeSkillsChange: (skills: string[]) => void
  newSkillInput: string
  onNewSkillInputChange: (v: string) => void
  aiSuggestedSkills: string[]
  onAiSuggestedSkillsChange: (skills: string[]) => void
  selectedAiSkills: string[]
  onSelectedAiSkillsChange: (skills: string[]) => void
  isFindingSimilarSkills: boolean
  onIsFindingSimilarSkillsChange: (v: boolean) => void
  showSkillSuggestions: boolean
  onShowSkillSuggestionsChange: (v: boolean) => void
  semanticSkillSuggestions: SemanticSuggestion[]
  isLoadingSemanticSkills: boolean
  searchSemanticSkills: (query: string, existing: string[]) => void
  clearSemanticSkillSuggestions: () => void
}

export function EditArchetypeSkillsSection({
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  editArchetypeSkills, onEditArchetypeSkillsChange,
  newSkillInput, onNewSkillInputChange,
  aiSuggestedSkills, onAiSuggestedSkillsChange,
  selectedAiSkills, onSelectedAiSkillsChange,
  isFindingSimilarSkills, onIsFindingSimilarSkillsChange,
  showSkillSuggestions, onShowSkillSuggestionsChange,
  semanticSkillSuggestions, isLoadingSemanticSkills,
  searchSemanticSkills, clearSemanticSkillSuggestions,
}: EditArchetypeSkillsSectionProps) {
  return (
    <div>
      <label className="text-xs font-medium mb-1 flex items-center gap-1.5 text-lia-text-secondary">
        <Code className="w-3.5 h-3.5 text-lia-text-primary" />
        Skills
        <span className="text-micro font-normal text-lia-text-tertiary">
          (habilidades técnicas: Python, React, AWS...)
        </span>
      </label>
      <div className="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px] p-2 rounded-xl border border-lia-border-subtle">
        {editArchetypeSkills.map((skill, idx) => (
          <span key={`skill-${idx}`} className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-wedo-cyan/15">
            {skill}
            <button type="button" onClick={() => onEditArchetypeSkillsChange(editArchetypeSkills.filter((_, i) => i !== idx))} className="hover:bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-full p-0.5">
              <X className="w-3 h-3 text-lia-text-primary" />
            </button>
          </span>
        ))}
        {editArchetypeSkills.length === 0 && (
          <span className="text-xs text-lia-text-tertiary">Nenhuma skill</span>
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
            onBlur={() => { setTimeout(() => onShowSkillSuggestionsChange(false), 200) }}
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
            className="flex-1 rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 border border-lia-border-subtle"
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
                      .filter((s: string) => !editArchetypeSkills.map((sk) => sk.toLowerCase()).includes(s.toLowerCase()))
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
            className={`px-2 py-1 rounded-full flex items-center gap-1 text-micro transition-colors motion-reduce:transition-none disabled:opacity-50 ${editArchetypeSkills.length > 0 ? "bg-wedo-cyan/15 text-lia-text-primary" : "bg-lia-bg-tertiary text-lia-text-tertiary"}`}
            title=`Buscar skills similares com ${personaName}`
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
          <div className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-[150px] overflow-y-auto" role="status" aria-live="polite" aria-label="Carregando...">
            {isLoadingSemanticSkills && (
              <div className="flex items-center justify-center py-2" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
              </div>
            )}
            {semanticSkillSuggestions.map((suggestion, idx) => (
              <button
                key={`sem-skill-${idx}`}
                type="button"
                className="w-full text-left px-2 py-1.5 text-xs hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none flex items-center gap-1.5"
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
                <Code className="w-3 h-3 text-lia-text-tertiary" />
                <span>{suggestion.term}</span>
                {suggestion.is_synonym && (
                  <span className="text-micro px-1 py-0.5 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary">sinônimo</span>
                )}
                {suggestion.is_related && (
                  <span className="text-micro px-1 py-0.5 rounded-full bg-status-success/10 text-status-success">relacionado</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
      {aiSuggestedSkills.length > 0 && (
        <div className="mt-2 p-2 rounded-xl bg-wedo-cyan/8 border border-wedo-cyan/30">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Brain className="w-3 h-3 text-wedo-cyan" />
            <span className="text-micro font-medium text-lia-text-primary">{`Sugestões de ${personaName}`}</span>
            <button type="button" onClick={() => { onAiSuggestedSkillsChange([]); onSelectedAiSkillsChange([]) }} className="ml-auto p-0.5 hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-xl">
              <X className="w-3 h-3 text-lia-text-primary" />
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
                    "px-1.5 py-0.5 rounded-full text-micro transition-[width,height] cursor-pointer text-lia-text-muted",
                    isSelected ? "ring-2 ring-lia-btn-primary-bg/20 bg-wedo-cyan/25" : "bg-wedo-cyan/15"
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
                onEditArchetypeSkillsChange([...editArchetypeSkills, ...selectedAiSkills.filter((s) => !editArchetypeSkills.includes(s))])
                onAiSuggestedSkillsChange(aiSuggestedSkills.filter((s) => !selectedAiSkills.includes(s)))
                onSelectedAiSkillsChange([])
              }}
              className="mt-2 w-full py-1 rounded-md text-micro font-medium transition-colors motion-reduce:transition-none bg-lia-btn-primary-bg text-lia-btn-primary-text"
            >
              Adicionar {selectedAiSkills.length} Selecionado{selectedAiSkills.length > 1 ? "s" : ""}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
