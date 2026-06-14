"use client"

import { useState, useRef } from"react"
import { X, Check, RotateCcw, Save, Zap, Brain, Loader2, List, Info } from"lucide-react"
import { cn } from"@/lib/utils"
import { Input } from"@/components/ui/input"
import { Label } from"@/components/ui/label"
import { Chip } from "@/components/ui/chip"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import { useSemanticSearch } from"@/hooks/search/useSemanticSearch"
import type { SearchFilters } from '../hooks/useAdvancedFiltersCore'

export interface PastTitlesSectionProps {
  filters: SearchFilters
  updateFilter: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string | string[] | number | boolean | null) => void
  addToArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
  removeFromArray: <T extends keyof SearchFilters>(category: T, key: keyof NonNullable<SearchFilters[T]>, value: string) => void
  onOpenPresetsModal: (target:"titles" |"pastTitles") => void
  onOpenSavePresetModal: (target:"titles" |"pastTitles") => void
}

export const PastTitlesSection = ({
  filters,
  updateFilter,
  addToArray,
  removeFromArray,
  onOpenPresetsModal,
  onOpenSavePresetModal,
}: PastTitlesSectionProps) => {
  const [pastTitleInput, setPastTitleInput] = useState("")
  const [isLoadingSimilarPastTitles, setIsLoadingSimilarPastTitles] = useState(false)
  const [aiSuggestedPastTitles, setAiSuggestedPastTitles] = useState<string[]>([])
  const [selectedAiPastTitles, setSelectedAiPastTitles] = useState<string[]>([])
  const [showPastTitleSuggestions, setShowPastTitleSuggestions] = useState(false)
  const pastTitleInputRef = useRef<HTMLInputElement>(null)

  const {
    suggestions: titleSuggestions,
    isLoading: isLoadingTitles,
    search: searchTitles,
    clearSuggestions: clearTitleSuggestions
  } = useSemanticSearch({ domain:"job-titles", debounceMs: 400 })

  const handleAddPastTitle = (title: string) => {
    if (title.trim()) {
      addToArray("job","pastTitles", title.trim())
      setPastTitleInput("")
      clearTitleSuggestions()
      setShowPastTitleSuggestions(false)
    }
  }

  const handlePastTitleInputChange = (value: string) => {
    setPastTitleInput(value)
    if (value.trim().length >= 2) {
      searchTitles(value, filters.job?.pastTitles || [])
      setShowPastTitleSuggestions(true)
    } else {
      clearTitleSuggestions()
      setShowPastTitleSuggestions(false)
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

  const handleFindSimilarPastTitles = async () => {
    const pastTitles = filters.job?.pastTitles || []
    if (pastTitles.length === 0) return

    setIsLoadingSimilarPastTitles(true)
    try {
      const response = await fetch('/api/ai/suggest-similar-titles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ titles: pastTitles })
      })

      if (response.ok) {
        const data = await response.json()
        const suggestions = data.suggestions || []
        setAiSuggestedPastTitles(suggestions.filter((s: string) => !pastTitles.includes(s)))
      } else {
        const similarTitles = generateLocalSimilarTitles(pastTitles)
        setAiSuggestedPastTitles(similarTitles.filter(s => !pastTitles.includes(s)))
      }
    } catch {
      const similarTitles = generateLocalSimilarTitles(pastTitles)
      setAiSuggestedPastTitles(similarTitles.filter(s => !pastTitles.includes(s)))
    }
    setIsLoadingSimilarPastTitles(false)
  }

  const toggleAiPastTitleSelection = (title: string) => {
    if (selectedAiPastTitles.includes(title)) {
      setSelectedAiPastTitles(prev => prev.filter(t => t !== title))
    } else {
      setSelectedAiPastTitles(prev => [...prev, title])
    }
  }

  const handleAddSelectedAiPastTitles = () => {
    selectedAiPastTitles.forEach(title => {
      addToArray("job","pastTitles", title)
    })
    setAiSuggestedPastTitles(prev => prev.filter(t => !selectedAiPastTitles.includes(t)))
    setSelectedAiPastTitles([])
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Label className="text-xs font-medium">Cargos Anteriores</Label>
          <Popover>
            <PopoverTrigger asChild>
              <button className="text-lia-text-tertiary hover:text-lia-text-secondary">
                <Info className="w-3 h-3" />
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-64 p-2 bg-lia-bg-elevated text-xs">
              Buscar candidatos que já tiveram estes cargos em algum momento da carreira
            </PopoverContent>
          </Popover>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => updateFilter("job","pastTitles", [] as string[])}
            disabled={(filters.job?.pastTitles?.length || 0) === 0}
            className="text-xs text-lia-text-secondary hover:text-status-error flex items-center gap-1 transition-colors motion-reduce:transition-none disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RotateCcw className="w-3 h-3" />
            Limpar tudo
          </button>
          <button
            onClick={() => onOpenSavePresetModal("pastTitles")}
            disabled={(filters.job?.pastTitles?.length || 0) === 0}
            className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-3.5 h-3.5" />
            Salvar Preset
          </button>
          <button
            onClick={() => onOpenPresetsModal("pastTitles")}
            className="text-xs text-lia-text-secondary hover:text-lia-text-primary flex items-center gap-1"
          >
            <List className="w-3.5 h-3.5" />
            Presets
          </button>
        </div>
      </div>

      <div className="relative">
        <div className="relative">
          <Input
            ref={pastTitleInputRef}
            value={pastTitleInput}
            onChange={(e) => handlePastTitleInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key ==="Enter" && pastTitleInput.trim()) {
                e.preventDefault()
                handleAddPastTitle(pastTitleInput)
              } else if (e.key ==="Escape") {
                setShowPastTitleSuggestions(false)
              }
            }}
            onFocus={() => pastTitleInput.length >= 2 && setShowPastTitleSuggestions(true)}
            onBlur={() => setTimeout(() => setShowPastTitleSuggestions(false), 200)}
            placeholder="Digite cargo anterior e pressione Enter"
            className="border border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium pr-10"
          />
          {isLoadingTitles && showPastTitleSuggestions && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
            </div>
          )}
        </div>

        {/* Semantic Suggestions Dropdown for Past Titles */}
        {showPastTitleSuggestions && titleSuggestions.length > 0 && (
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
                  handleAddPastTitle(suggestion.term)
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

      {(filters.job?.pastTitles?.length || 0) > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {filters.job?.pastTitles?.map((title) => {
            const isAiSuggested = aiSuggestedPastTitles.includes(title)
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
                  onClick={() => removeFromArray("job","pastTitles", title)}
                  className="ml-1 hover:bg-lia-border-default rounded-md p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </Chip>
            )
          })}

          <button
            onClick={handleFindSimilarPastTitles}
            disabled={isLoadingSimilarPastTitles || (filters.job?.pastTitles?.length || 0) === 0}
            className={cn("px-3 py-1 rounded-full text-xs border flex items-center gap-1.5 transition-[width,height]","border-wedo-purple/30  hover:bg-wedo-purple/15","disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {isLoadingSimilarPastTitles ? (
              <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
            ) : (
              <Brain className="w-3 h-3 text-wedo-cyan" />
            )}
            Buscar Similares
          </button>
        </div>
      )}

      {aiSuggestedPastTitles.length > 0 && (
        <div className="p-3 rounded-xl border border-wedo-purple/30 bg-wedo-purple/10/50">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-wedo-purple" />
              <span className="text-xs font-medium text-wedo-purple-text">Sugestões da LIA</span>
              <span className="text-micro text-wedo-purple-text">
                (clique para selecionar múltiplos)
              </span>
            </div>
            {selectedAiPastTitles.length > 0 && (
              <button
                onClick={handleAddSelectedAiPastTitles}
                className="px-2 py-1 rounded-md text-xs bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none flex items-center gap-1"
              >
                <Check className="w-3 h-3" />
                Adicionar {selectedAiPastTitles.length} selecionado{selectedAiPastTitles.length > 1 ? 's' : ''}
              </button>
            )}
          </div>
          <div className="flex flex-wrap gap-1.5">
            {aiSuggestedPastTitles.slice(0, 10).map((title) => {
              const isSelected = selectedAiPastTitles.includes(title)
              return (
                <button
                  key={title}
                  onClick={() => toggleAiPastTitleSelection(title)}
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
