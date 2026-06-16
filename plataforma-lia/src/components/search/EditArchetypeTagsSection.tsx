"use client"

import { X, Tag, Brain, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useAiPersona } from "@/hooks/company/use-ai-persona"

interface SemanticSuggestion {
  term: string
  is_synonym?: boolean
  is_related?: boolean
}

interface EditArchetypeTagsSectionProps {
  editArchetypeTags: string[]
  onEditArchetypeTagsChange: (tags: string[]) => void
  newTagInput: string
  onNewTagInputChange: (v: string) => void
  aiSuggestedTags: string[]
  onAiSuggestedTagsChange: (tags: string[]) => void
  selectedAiTags: string[]
  onSelectedAiTagsChange: (tags: string[]) => void
  isFindingSimilarTags: boolean
  onIsFindingSimilarTagsChange: (v: boolean) => void
  showTagSuggestions: boolean
  onShowTagSuggestionsChange: (v: boolean) => void
  semanticTagSuggestions: SemanticSuggestion[]
  isLoadingSemanticTags: boolean
  searchSemanticTags: (query: string, existing: string[]) => void
  clearSemanticTagSuggestions: () => void
}

export function EditArchetypeTagsSection({
  editArchetypeTags, onEditArchetypeTagsChange,
  newTagInput, onNewTagInputChange,
  aiSuggestedTags, onAiSuggestedTagsChange,
  selectedAiTags, onSelectedAiTagsChange,
  isFindingSimilarTags, onIsFindingSimilarTagsChange,
  showTagSuggestions, onShowTagSuggestionsChange,
  semanticTagSuggestions, isLoadingSemanticTags,
  searchSemanticTags, clearSemanticTagSuggestions,
}: EditArchetypeTagsSectionProps) {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  return (
    <div>
      <label className="text-xs font-medium mb-1 flex items-center gap-1.5 text-lia-text-secondary">
        <Tag className="w-3.5 h-3.5 text-lia-text-primary" />
        Tags
        <span className="text-micro font-normal text-lia-text-tertiary">
          (categorias: liderança, estratégia, backend...)
        </span>
      </label>
      <div className="flex flex-wrap gap-1.5 mb-1.5 min-h-[28px] p-2 rounded-xl border border-lia-border-subtle">
        {editArchetypeTags.map((tag, idx) => (
          <span key={`tag-${idx}`} className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium">
            {tag}
            <button type="button" onClick={() => onEditArchetypeTagsChange(editArchetypeTags.filter((_, i) => i !== idx))} className="hover:bg-lia-border-default rounded-full p-0.5">
              <X className="w-3 h-3 text-lia-text-secondary" />
            </button>
          </span>
        ))}
        {editArchetypeTags.length === 0 && (
          <span className="text-xs text-lia-text-tertiary">Nenhuma tag</span>
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
            onBlur={() => { setTimeout(() => onShowTagSuggestionsChange(false), 200) }}
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
            className="flex-1 rounded-md px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 border border-lia-border-subtle"
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
                      .filter((s: string) => !editArchetypeTags.map((t) => t.toLowerCase()).includes(s.toLowerCase()))
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
            className={`px-2 py-1 rounded-full flex items-center gap-1 text-micro transition-colors motion-reduce:transition-none disabled:opacity-50 ${editArchetypeTags.length > 0 ? "bg-wedo-cyan/15 text-lia-text-primary" : "bg-lia-bg-tertiary text-lia-text-tertiary"}`}
            title={`Buscar tags similares com ${personaName}`}
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
          <div className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-[150px] overflow-y-auto" role="status" aria-live="polite" aria-label="Carregando...">
            {isLoadingSemanticTags && (
              <div className="flex items-center justify-center py-2" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-tertiary" />
              </div>
            )}
            {semanticTagSuggestions.map((suggestion, idx) => (
              <button
                key={`sem-tag-${idx}`}
                type="button"
                className="w-full text-left px-2 py-1.5 text-xs hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none flex items-center gap-1.5"
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
                <Tag className="w-3 h-3 text-lia-text-tertiary" />
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
      {aiSuggestedTags.length > 0 && (
        <div className="mt-2 p-2 rounded-xl bg-wedo-cyan/8 border border-wedo-cyan/30">
          <div className="flex items-center gap-1.5 mb-1.5">
            <Brain className="w-3 h-3 text-wedo-cyan" />
            <span className="text-micro font-medium text-lia-text-primary">{`Sugestões de ${personaName}`}</span>
            <button type="button" onClick={() => { onAiSuggestedTagsChange([]); onSelectedAiTagsChange([]) }} className="ml-auto p-0.5 hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover rounded-xl">
              <X className="w-3 h-3 text-lia-text-primary" />
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
                    "px-1.5 py-0.5 rounded-full text-micro transition-[width,height] cursor-pointer text-lia-text-muted",
                    isSelected ? "ring-2 ring-lia-btn-primary-bg/20 bg-wedo-cyan/25" : "bg-wedo-cyan/15"
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
                onEditArchetypeTagsChange([...editArchetypeTags, ...selectedAiTags.filter((t) => !editArchetypeTags.includes(t))])
                onAiSuggestedTagsChange(aiSuggestedTags.filter((t) => !selectedAiTags.includes(t)))
                onSelectedAiTagsChange([])
              }}
              className="mt-2 w-full py-1 rounded-md text-micro font-medium transition-colors motion-reduce:transition-none bg-lia-btn-primary-bg text-lia-btn-primary-text"
            >
              Adicionar {selectedAiTags.length} Selecionado{selectedAiTags.length > 1 ? "s" : ""}
            </button>
          )}
        </div>
      )}
    </div>
  )
}
