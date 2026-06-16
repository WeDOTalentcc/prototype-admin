"use client"

import { useState, useRef } from"react"
import { X, Check, RotateCcw, Save, Zap, Brain, Loader2, List } from"lucide-react"
import { cn } from"@/lib/utils"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Chip } from "@/components/ui/chip"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import { useSemanticSearch } from"@/hooks/search/useSemanticSearch"
import type { SearchFilters } from '../hooks/useAdvancedFiltersCore'
import { titleScopeOptions } from '../advancedFiltersTypes'
import { globalJobPresets } from '../advancedFiltersTypes'
import { useAiPersona } from "@/hooks/company/use-ai-persona"

export interface JobTitlesSectionProps {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
  addToArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
  removeFromArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
  // Presets modal triggers
  onOpenPresetsModal: (target:"titles" |"pastTitles") => void
  onOpenSavePresetModal: (target:"titles" |"pastTitles") => void
}

export const JobTitlesSection = ({
  filters,
  updateFilter,
  addToArray,
  removeFromArray,
  onOpenPresetsModal,
  onOpenSavePresetModal,
}: JobTitlesSectionProps) => {
  const [titleInput, setTitleInput] = useState("")
  const [isLoadingSimilar, setIsLoadingSimilar] = useState(false)
  const [aiSuggestedTitles, setAiSuggestedTitles] = useState<string[]>([])
  const [selectedAiTitles, setSelectedAiTitles] = useState<string[]>([])
  const [showTitleSuggestions, setShowTitleSuggestions] = useState(false)
  const titleInputRef = useRef<HTMLInputElement>(null)

  const {
    suggestions: titleSuggestions,
    isLoading: isLoadingTitles,
    search: searchTitles,
    clearSuggestions: clearTitleSuggestions
  } = useSemanticSearch({ domain:"job-titles", debounceMs: 400 })

  const handleAddTitle = (title: string) => {
    if (title.trim()) {
      addToArray("job","titles", title.trim())
      setTitleInput("")
      clearTitleSuggestions()
      setShowTitleSuggestions(false)
    }
  }

  const handleTitleInputChange = (value: string) => {
    setTitleInput(value)
    if (value.trim().length >= 2) {
      searchTitles(value, filters.job?.titles || [])
      setShowTitleSuggestions(true)
    } else {
      clearTitleSuggestions()
      setShowTitleSuggestions(false)
    }
  }

  const generateLocalSimilarTitles = (titles: string[]): string[] => {
    const suggestions: string[] = []
    const seniorityPrefixes = ["Junior","Senior","Staff","Principal","Lead","Head of"]

    titles.forEach(title => {
      const cleanTitle = title.replace(/^(Junior|Senior|Staff|Principal|Lead|Head of)\s*/i,"")
      seniorityPrefixes.forEach(prefix => {
        const newTitle = `${prefix} ${cleanTitle}`
        if (!titles.includes(newTitle) && !suggestions.includes(newTitle)) {
          suggestions.push(newTitle)
        }
      })
    })

    return suggestions.slice(0, 8)
  }

  const handleFindSimilar = async () => {
    const currentTitles = filters.job?.titles || []
    if (currentTitles.length === 0) return

    setIsLoadingSimilar(true)
    try {
      const response = await fetch('/api/ai/suggest-similar-titles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titles: currentTitles })
      })

      if (response.ok) {
        const data = await response.json()
        const suggestions = data.suggestions || []
        setAiSuggestedTitles(suggestions.filter((s: string) => !currentTitles.includes(s)))
      } else {
        const similarTitles = generateLocalSimilarTitles(currentTitles)
        setAiSuggestedTitles(similarTitles.filter(s => !currentTitles.includes(s)))
      }
    } catch {
      const similarTitles = generateLocalSimilarTitles(currentTitles)
      setAiSuggestedTitles(similarTitles.filter(s => !currentTitles.includes(s)))
    }
    setIsLoadingSimilar(false)
  }

  const toggleAiTitleSelection = (title: string) => {
    if (selectedAiTitles.includes(title)) {
      setSelectedAiTitles(prev => prev.filter(t => t !== title))
    } else {
      setSelectedAiTitles(prev => [...prev, title])
    }
  }

  const handleAddSelectedAiTitles = () => {
    selectedAiTitles.forEach(title => {
      addToArray("job","titles", title)
    })
    setAiSuggestedTitles(prev => prev.filter(t => !selectedAiTitles.includes(t)))
    setSelectedAiTitles([])
  }

  const handleClearAll = () => {
    updateFilter("job","titles", [] as string[])
    setAiSuggestedTitles([])
    setSelectedAiTitles([])
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Label className="text-xs font-medium">Cargos Atuais</Label>
          <Select
            value={filters.job?.titleScope ||"current_only"}
            onValueChange={(value) => updateFilter("job","titleScope", value as"current_only" |"current_recent" |"current_past")}
          >
            <SelectTrigger className="h-7 w-[150px] text-xs border-lia-border-subtle">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-lia-bg-secondary">
              {titleScopeOptions.map(option => (
                <SelectItem key={option.value} value={option.value} className="text-xs">
                  <div>
                    <div className="font-medium">{option.label}</div>
                    <div className="text-micro text-lia-text-secondary">{option.description}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleClearAll}
            className="text-xs text-lia-text-secondary hover:text-status-error flex items-center gap-1 transition-colors motion-reduce:transition-none"
          >
            <RotateCcw className="w-3 h-3" />
            Limpar tudo
          </button>
          <button
            onClick={() => onOpenSavePresetModal("titles")}
            disabled={(filters.job?.titles?.length || 0) === 0}
            className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-3.5 h-3.5" />
            Salvar Preset
          </button>
          <button
            onClick={() => onOpenPresetsModal("titles")}
            className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1"
          >
            <List className="w-3.5 h-3.5" />
            Presets
          </button>
        </div>
      </div>

      {/* Title Input */}
      <div className="relative">
        <div className="relative">
          <Input
            ref={titleInputRef}
            value={titleInput}
            onChange={(e) => handleTitleInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key ==="Enter" && titleInput.trim()) {
                e.preventDefault()
                handleAddTitle(titleInput)
              } else if (e.key ==="Escape") {
                setShowTitleSuggestions(false)
              }
            }}
            onFocus={() => titleInput.length >= 2 && setShowTitleSuggestions(true)}
            onBlur={() => setTimeout(() => setShowTitleSuggestions(false), 200)}
            placeholder="Digite cargo e pressione Enter (ex: Software Engineer, Product Manager)"
            className="border border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium pr-10"
          />
          {isLoadingTitles && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
            </div>
          )}
        </div>

        {/* Semantic Suggestions Dropdown */}
        {showTitleSuggestions && titleSuggestions.length > 0 && (
          <div className="absolute z-50 mt-1 w-full bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-48 overflow-y-auto">
            <div className="p-1.5 dark:border-lia-border-subtle">
              <div className="flex items-center gap-1.5 text-micro text-lia-text-secondary">
                <Zap className="w-3 h-3" />
                <span>Sugestões semânticas</span>
              </div>
            </div>
            {titleSuggestions.map((suggestion) => (
              <button
                key={suggestion.term}
                onMouseDown={(e) => {
                  e.preventDefault()
                  handleAddTitle(suggestion.term)
                }}
                className="w-full text-left px-3 py-2 text-sm hover:bg-lia-bg-secondary flex items-center justify-between gap-2"
              >
                <span>{suggestion.term}</span>
                <span className="text-micro text-lia-text-tertiary">
                  {Math.round(suggestion.confidence * 100)}%
                </span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Selected Titles */}
      {(filters.job?.titles?.length || 0) > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {filters.job?.titles?.map((title) => {
            const isAiSuggested = aiSuggestedTitles.includes(title)
            return (
              <Chip
                key={title}
                variant="neutral" muted
                className={cn("pl-2 pr-1 py-1 flex items-center gap-1",
                  isAiSuggested
                    ?"bg-wedo-purple/10 border border-wedo-purple/30 text-wedo-purple-text"
                    :"bg-lia-bg-tertiary text-lia-text-primary"
                )}
              >
                {isAiSuggested && <Brain className="w-3 h-3 text-wedo-purple-text" />}
                <span className="text-xs">{title}</span>
                <button
                  onClick={() => removeFromArray("job","titles", title)}
                  className="ml-1 hover:bg-lia-border-default rounded-md p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </Chip>
            )
          })}

          {/* Find Similar Button */}
          <button
            onClick={handleFindSimilar}
            disabled={isLoadingSimilar || (filters.job?.titles?.length || 0) === 0}
            className={cn("px-3 py-1 rounded-full text-xs border flex items-center gap-1.5 transition-[width,height]","border-wedo-purple/30  hover:bg-wedo-purple/15","disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {isLoadingSimilar ? (
              <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
            ) : (
              <Brain className="w-3 h-3 text-wedo-cyan" />
            )}
            Buscar Similares
          </button>
        </div>
      )}

      {/* AI Suggestions with Multi-Select */}
      {aiSuggestedTitles.length > 0 && (
        <div className="p-3 rounded-xl border border-wedo-purple/30 bg-wedo-purple/10/50">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-wedo-purple" />
              <span className="text-xs font-medium text-wedo-purple-text">{`Sugestões de ${personaName}`}</span>
              <span className="text-micro text-lia-text-muted">
                (clique para selecionar múltiplos)
              </span>
            </div>
            {selectedAiTitles.length > 0 && (
              <button
                onClick={handleAddSelectedAiTitles}
                className="px-2 py-1 rounded-md text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none flex items-center gap-1"
              >
                <Check className="w-3 h-3" />
                Adicionar {selectedAiTitles.length} selecionado{selectedAiTitles.length > 1 ? 's' : ''}
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {aiSuggestedTitles.slice(0, 10).map((title) => {
              const isSelected = selectedAiTitles.includes(title)
              return (
                <button
                  key={title}
                  onClick={() => toggleAiTitleSelection(title)}
                  className={cn("px-2 py-1 rounded-md text-xs border transition-colors flex items-center gap-1",
                    isSelected
                      ?"border-wedo-purple/30  font-medium"
                      :"border-wedo-purple/30 bg-lia-bg-primary text-wedo-purple-text hover:bg-wedo-purple/10"
                  )}
                >
                  {isSelected && <Check className="w-3 h-3" />}
                  {!isSelected && <span className="text-wedo-purple-text">+</span>}
                  {title}
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
