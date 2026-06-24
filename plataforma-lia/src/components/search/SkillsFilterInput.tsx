"use client"

import { useState, useCallback } from"react"
import { X, Pin, Brain, Loader2, Search, Zap } from"lucide-react"
import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { useSemanticSearch, type SemanticSuggestion } from"@/hooks/search/useSemanticSearch"
import { useTagInputState } from"@/hooks/ui/useTagInputState"

export interface SkillItem {
  name: string
  isPinned: boolean
}

interface SkillsFilterInputProps {
  value: SkillItem[]
  onChange: (skills: SkillItem[]) => void
  placeholder?: string
}

const POPULAR_SKILLS = ["Python","JavaScript","TypeScript","React","Node.js","Java","C#","SQL","AWS","Docker","Kubernetes","Machine Learning","Data Science","Project Management","Agile","Scrum","Leadership","Communication","Excel","Power BI","Tableau","Figma","Adobe XD","UI Design","UX Design","Go","Rust","Ruby","PHP","Swift","Kotlin","Terraform","Azure","GCP","MongoDB","PostgreSQL","Redis","Elasticsearch","GraphQL","REST API","Git","Linux","Microservices","DevOps","CI/CD","TDD","Clean Code"
]

export function SkillsFilterInput({
  value,
  onChange,
  placeholder ="Digite skill e pressione Enter (ex: Python, React, AWS)"
}: SkillsFilterInputProps) {
  const {
    inputValue, setInputValue,
    isDropdownOpen, setIsDropdownOpen,
    focusedIndex, setFocusedIndex,
    inputRef, dropdownRef,
    handleKeyNavigation, closeDropdown
  } = useTagInputState()
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const [isFindingSimilar, setIsFindingSimilar] = useState(false)

  const { 
    suggestions: semanticSuggestions, 
    isLoading: isSemanticLoading, 
    search: searchSemantic,
    clearSuggestions,
    cached: isCached
  } = useSemanticSearch({ domain:"skills", debounceMs: 400 })

  const existingSkillNames = value.map(s => s.name.toLowerCase())

  const filteredSuggestions = inputValue.trim()
    ? POPULAR_SKILLS.filter(skill => 
        skill.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingSkillNames.includes(skill.toLowerCase())
      ).slice(0, 6)
    : []

  const semanticItems = semanticSuggestions
    .filter(s => !existingSkillNames.includes(s.term.toLowerCase()))
    .map(s => ({ 
      type: 'semantic' as const, 
      label: s.term, 
      confidence: s.confidence,
      is_synonym: s.is_synonym,
      is_related: s.is_related
    }))

  const showAskAI = inputValue.trim().length >= 2
  const dropdownItems = [
    ...semanticItems,
    ...(showAskAI && semanticItems.length === 0 ? [{ type: 'ai' as const, label: `Buscar com IA"${inputValue}"`, confidence: 0, is_synonym: false, is_related: false }] : []),
    ...filteredSuggestions.map(s => ({ type: 'skill' as const, label: s, confidence: 0, is_synonym: false, is_related: false }))
  ]



  const addSkill = useCallback((name: string, isPinned: boolean = false) => {
    const trimmed = name.trim()
    if (!trimmed) return
    if (existingSkillNames.includes(trimmed.toLowerCase())) return
    onChange([...value, { name: trimmed, isPinned }])
    setInputValue("")
    closeDropdown()
  }, [value, onChange, existingSkillNames, closeDropdown, setInputValue])

  const removeSkill = useCallback((name: string) => {
    onChange(value.filter(s => s.name !== name))
  }, [value, onChange])

  const togglePin = useCallback((name: string) => {
    onChange(value.map(s => 
      s.name === name ? { ...s, isPinned: !s.isPinned } : s
    ))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const askAIForSimilar = useCallback(async (query: string) => {
    if (!query.trim()) return
    setIsLoadingAI(true)
    setIsDropdownOpen(false)
    
    try {
      const response = await fetch('/api/ai/suggest-similar-skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skills: [query] })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newSkills = data.suggestions
            .filter((s: string) => !existingSkillNames.includes(s.toLowerCase()))
            .slice(0, 5)
            .map((s: string) => ({ name: s, isPinned: false }))
          
          const originalSkill = { name: query, isPinned: false }
          if (!existingSkillNames.includes(query.toLowerCase())) {
            onChange([...value, originalSkill, ...newSkills])
          } else {
            onChange([...value, ...newSkills])
          }
        } else {
          addSkill(query)
        }
      } else {
        addSkill(query)
      }
    } catch (error) {
      addSkill(query)
    } finally {
      setIsLoadingAI(false)
      setInputValue("")
    }
  }, [value, onChange, existingSkillNames, addSkill, setInputValue, setIsDropdownOpen])

  const findSimilarSkills = useCallback(async () => {
    if (value.length === 0) return
    setIsFindingSimilar(true)
    
    try {
      const skillNames = value.map(s => s.name)
      const response = await fetch('/api/ai/suggest-similar-skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skills: skillNames })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newSkills = data.suggestions
            .filter((s: string) => !existingSkillNames.includes(s.toLowerCase()))
            .slice(0, 6)
            .map((s: string) => ({ name: s, isPinned: false }))
          onChange([...value, ...newSkills])
        }
      }
    } catch (error) {
    } finally {
      setIsFindingSimilar(false)
    }
  }, [value, onChange, existingSkillNames])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    handleKeyNavigation(
      e,
      dropdownItems.length,
      (index) => {
        const item = dropdownItems[index]
        if (item.type === 'ai') askAIForSimilar(inputValue)
        else addSkill(item.label)
      },
      () => inputValue.trim() && addSkill(inputValue)
    )
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setIsDropdownOpen(newValue.length > 0)
    setFocusedIndex(-1)
    
    if (newValue.trim().length >= 2) {
      searchSemantic(newValue, value.map(s => s.name))
    } else {
      clearSuggestions()
    }
  }

  const pinnedSkills = value.filter(s => s.isPinned)
  const regularSkills = value.filter(s => !s.isPinned)

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {value.length > 0 && (
            <span className="text-xs text-lia-text-secondary">
              {value.length} skill{value.length !== 1 ? 's' : ''} selecionada{value.length !== 1 ? 's' : ''}
              {pinnedSkills.length > 0 && ` (${pinnedSkills.length} obrigatória${pinnedSkills.length !== 1 ? 's' : ''})`}
            </span>
          )}
        </div>
        {value.length > 0 && (
          <button
            onClick={clearAll}
            className="text-xs text-lia-text-primary hover:text-lia-text-primary font-medium"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-tertiary" />
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => inputValue.length > 0 && setIsDropdownOpen(true)}
            placeholder={placeholder}
            className="pl-9 pr-3 border-lia-border-subtle focus:ring-1 focus:ring-lia-btn-primary-bg/20 dark:focus:ring-lia-border-subtle/20 focus:border-lia-border-medium"
            disabled={isLoadingAI}
          />
          {isLoadingAI && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
          )}
        </div>

        {isDropdownOpen && dropdownItems.length > 0 && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-64 overflow-y-auto"
          >
            {dropdownItems.map((item, index) => (
              <button
                key={`${item.type}-${item.label}`}
                onClick={() => {
                  if (item.type === 'ai') {
                    askAIForSimilar(inputValue)
                  } else {
                    addSkill(item.label)
                  }
                }}
                className={cn("w-full text-left px-3 py-2 text-sm transition-colors",
                  focusedIndex === index ?"bg-lia-bg-tertiary" :"hover:bg-lia-bg-secondary",
                  item.type === 'ai' &&""
                )}
              >
                {item.type === 'ai' ? (
                  <div className="flex items-center gap-2 text-lia-text-secondary">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span>{item.label}</span>
                  </div>
                ) : (
                  <span className="text-lia-text-primary">{item.label}</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {value.length > 0 && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2">
            {pinnedSkills.map(skill => (
              <Chip variant="neutral" muted
                key={skill.name}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-inverse text-white border border-lia-border-strong"
              >
                <button
                  onClick={() => togglePin(skill.name)}
                  className="hover:bg-lia-border-medium rounded-md p-0.5 transition-colors motion-reduce:transition-none"
                  title="Desmarcar como obrigatória"
                >
                  <Pin className="w-3 h-3 fill-current" />
                </button>
                <span>{skill.name}</span>
                <button
                  onClick={() => removeSkill(skill.name)}
                  className="hover:bg-lia-border-medium rounded-md p-0.5 transition-colors motion-reduce:transition-none"
                  title="Remover"
                >
                  <X className="w-3 h-3" />
                </button>
              </Chip>
            ))}
            {regularSkills.map(skill => (
              <Chip variant="neutral" muted
                key={skill.name}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
              >
                <button
                  onClick={() => togglePin(skill.name)}
                  className="hover:bg-lia-interactive-active rounded-md p-0.5 transition-colors motion-reduce:transition-none"
                  title="Marcar como obrigatória"
                >
                  <Pin className="w-3 h-3" />
                </button>
                <span>{skill.name}</span>
                <button
                  onClick={() => removeSkill(skill.name)}
                  className="hover:bg-lia-interactive-active rounded-md p-0.5 transition-colors motion-reduce:transition-none"
                  title="Remover"
                >
                  <X className="w-3 h-3" />
                </button>
              </Chip>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={findSimilarSkills}
            disabled={isFindingSimilar || value.length === 0}
            className="text-xs gap-1.5 border-lia-btn-primary-bg dark:border-lia-border-subtle text-lia-text-primary hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover"
          >
            {isFindingSimilar ? (
              <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none" />
            ) : (
              <Brain className="w-3 h-3 text-wedo-cyan" />
            )}
            Find Similar
          </Button>
        </div>
      )}
    </div>
  )
}

export default SkillsFilterInput
