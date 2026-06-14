"use client"

import { useState, useCallback } from"react"
import { X, Brain, Loader2, Search, Zap } from"lucide-react"
import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { Input } from"@/components/ui/input"
import { useSemanticSearch } from"@/hooks/search/useSemanticSearch"
import { useTagInputState } from"@/hooks/ui/useTagInputState"

interface ExpertiseAreasInputProps {
  value: string[]
  onChange: (expertise: string[]) => void
  placeholder?: string
}

const POPULAR_EXPERTISE = ["Machine Learning","Data Science","DevOps","Cloud Architecture","AI/ML","Full Stack Development","Backend Development","Frontend Development","Mobile Development","iOS Development","Android Development","Data Engineering","Data Analytics","Business Intelligence","Cybersecurity","Network Security","Information Security","Product Management","Project Management","Agile/Scrum","Digital Marketing","Growth Hacking","SEO/SEM","UX Design","UI Design","Product Design","Graphic Design","Sales","Business Development","Account Management","Human Resources","Talent Acquisition","People Operations","Finance","Accounting","Financial Planning","Operations","Supply Chain","Logistics","Customer Success","Customer Support","Technical Support","Quality Assurance","Test Automation","Software Testing","Blockchain","Web3","Smart Contracts","Natural Language Processing","Computer Vision","Deep Learning","Big Data","Hadoop","Spark","ETL","Site Reliability Engineering","Infrastructure","Platform Engineering"
]

export function ExpertiseAreasInput({
  value,
  onChange,
  placeholder ="Digite expertise e pressione Enter (ex: Machine Learning, DevOps, Data Science)"
}: ExpertiseAreasInputProps) {
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
    clearSuggestions
  } = useSemanticSearch({ domain:"expertise", debounceMs: 400 })

  const existingExpertise = value.map(e => e.toLowerCase())

  const filteredSuggestions = inputValue.trim()
    ? POPULAR_EXPERTISE.filter(expertise => 
        expertise.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingExpertise.includes(expertise.toLowerCase())
      ).slice(0, 6)
    : []

  const semanticItems = semanticSuggestions
    .filter(s => !existingExpertise.includes(s.term.toLowerCase()))
    .map(s => ({ type: 'semantic' as const, label: s.term, confidence: s.confidence }))

  const showAskAI = inputValue.trim().length >= 2
  const dropdownItems = [
    ...semanticItems,
    ...(showAskAI && semanticItems.length === 0 ? [{ type: 'ai' as const, label: `Buscar com IA"${inputValue}"`, confidence: 0 }] : []),
    ...filteredSuggestions.map(s => ({ type: 'expertise' as const, label: s, confidence: 0 }))
  ]



  const addExpertise = useCallback((name: string) => {
    const trimmed = name.trim()
    if (!trimmed) return
    if (existingExpertise.includes(trimmed.toLowerCase())) return
    onChange([...value, trimmed])
    setInputValue("")
    closeDropdown()
  }, [value, onChange, existingExpertise, closeDropdown, setInputValue])

  const removeExpertise = useCallback((name: string) => {
    onChange(value.filter(e => e !== name))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const askAIForSimilar = useCallback(async (query: string) => {
    if (!query.trim()) return
    setIsLoadingAI(true)
    setIsDropdownOpen(false)
    
    try {
      const response = await fetch('/api/ai/suggest-expertise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, existing: value })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newExpertise = data.suggestions
            .filter((e: string) => !existingExpertise.includes(e.toLowerCase()))
            .slice(0, 5)
          
          if (!existingExpertise.includes(query.toLowerCase())) {
            onChange([...value, query, ...newExpertise])
          } else {
            onChange([...value, ...newExpertise])
          }
        } else {
          addExpertise(query)
        }
      } else {
        addExpertise(query)
      }
    } catch (error) {
      addExpertise(query)
    } finally {
      setIsLoadingAI(false)
      setInputValue("")
    }
  }, [value, onChange, existingExpertise, addExpertise, setInputValue, setIsDropdownOpen])

  const findSimilarExpertise = useCallback(async () => {
    if (value.length === 0) return
    setIsFindingSimilar(true)
    
    try {
      const response = await fetch('/api/ai/suggest-expertise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: value.join(', '), existing: value, findSimilar: true })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newExpertise = data.suggestions
            .filter((e: string) => !existingExpertise.includes(e.toLowerCase()))
            .slice(0, 6)
          onChange([...value, ...newExpertise])
        }
      }
    } catch (error) {
    } finally {
      setIsFindingSimilar(false)
    }
  }, [value, onChange, existingExpertise])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    handleKeyNavigation(
      e,
      dropdownItems.length,
      (index) => {
        const item = dropdownItems[index]
        if (item.type === 'ai') askAIForSimilar(inputValue)
        else addExpertise(item.label)
      },
      () => inputValue.trim() && addExpertise(inputValue)
    )
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)
    setIsDropdownOpen(newValue.length > 0)
    setFocusedIndex(-1)
    
    if (newValue.trim().length >= 2) {
      searchSemantic(newValue, value)
    } else {
      clearSuggestions()
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {value.length > 0 && (
            <span className="text-xs text-lia-text-secondary">
              {value.length} área{value.length !== 1 ? 's' : ''} selecionada{value.length !== 1 ? 's' : ''}
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
                    addExpertise(item.label)
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
            {value.map(expertise => (
              <Chip variant="neutral" muted
                key={expertise}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
              >
                <Brain className="w-3 h-3 text-wedo-cyan" />
                <span>{expertise}</span>
                <button
                  onClick={() => removeExpertise(expertise)}
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
            onClick={findSimilarExpertise}
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

      <p className="text-xs text-lia-text-secondary">
        Campos de expertise do LinkedIn (complementa skills)
      </p>
    </div>
  )
}

export default ExpertiseAreasInput
