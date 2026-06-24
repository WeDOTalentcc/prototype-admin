"use client"

import { useState, useEffect, useCallback, useMemo, useRef } from"react"
import { X, Search, ChevronDown, Brain, Loader2, AlertCircle, Zap } from"lucide-react"
import { cn } from"@/lib/utils"
import { useTagInputState } from"@/hooks/ui/useTagInputState"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import {
  INDUSTRIES,
  searchIndustries,
  getCanonicalKey,
  type Industry
} from"@/lib/industry-constants"
import { useSemanticSearch } from"@/hooks/search/useSemanticSearch"

export type IndustryTimeFilter = 'current_past' | 'current_only'

interface IndustryFilterInputProps {
  value: string[]
  onChange: (industries: string[]) => void
  timeFilter?: IndustryTimeFilter
  onTimeFilterChange?: (filter: IndustryTimeFilter) => void
  placeholder?: string
}

const POPULAR_INDUSTRIES = INDUSTRIES.map(i => i.key)

const TIME_FILTER_OPTIONS: { 
  value: IndustryTimeFilter
  label: string
  description: string
}[] = [
  { 
    value: 'current_past', 
    label: 'Atual + Anterior',
    description: 'Encontrar pessoas que trabalham ou já trabalharam nos setores selecionados'
  },
  { 
    value: 'current_only', 
    label: 'Apenas Atual',
    description: 'Encontrar pessoas que trabalham atualmente nos setores selecionados'
  },
]

export function IndustryFilterInput({
  value,
  onChange,
  timeFilter = 'current_past',
  onTimeFilterChange,
  placeholder ="Type industry name and press Enter"
}: IndustryFilterInputProps) {
  const {
    inputValue, setInputValue,
    isDropdownOpen, setIsDropdownOpen,
    focusedIndex, setFocusedIndex,
    inputRef, dropdownRef,
    closeDropdown,
  } = useTagInputState()
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([])
  const [aiError, setAiError] = useState<string | null>(null)
  const [isTimeFilterOpen, setIsTimeFilterOpen] = useState(false)
  const requestIdRef = useRef(0)
  const abortControllerRef = useRef<AbortController | null>(null)

  const { 
    suggestions: semanticSuggestions, 
    isLoading: isSemanticLoading, 
    search: searchSemantic,
    clearSuggestions
  } = useSemanticSearch({ domain:"industries", debounceMs: 400 })

  const existingIndustries = value.map(i => i.toLowerCase())

  const filteredSuggestions = useMemo(() => {
    if (!inputValue.trim()) return []
    
    const matchingIndustries = searchIndustries(inputValue)
    return matchingIndustries
      .filter(industry => !existingIndustries.includes(industry.key.toLowerCase()))
      .slice(0, 6)
  }, [inputValue, existingIndustries])

  const semanticItems = semanticSuggestions
    .filter(s => !existingIndustries.includes(s.term.toLowerCase()) &&
                 !filteredSuggestions.map(f => f.key.toLowerCase()).includes(s.term.toLowerCase()))
    .map(s => ({ type: 'semantic' as const, label: s.term, labelPt: s.term, industry: s.term, confidence: s.confidence }))

  const filteredAISuggestions = aiSuggestions.filter(
    s => !existingIndustries.includes(s.toLowerCase()) &&
         !filteredSuggestions.map(f => f.key.toLowerCase()).includes(s.toLowerCase())
  )

  const showAskAI = inputValue.trim().length >= 2
  const dropdownItems = [
    ...semanticItems,
    ...filteredAISuggestions.map(i => ({ type: 'ai-suggestion' as const, label: i, labelPt: i, industry: i, confidence: 0 })),
    ...(showAskAI && semanticItems.length === 0 && filteredAISuggestions.length === 0 ? [{ type: 'ai' as const, label: `Buscar com IA"${inputValue}"`, labelPt: null, industry: null, confidence: 0 }] : []),
    ...filteredSuggestions.map(i => ({ 
      type: 'industry' as const, 
      label: i.key,
      labelPt: i.labelPt,
      industry: i.key,
      confidence: 0
    }))
  ]

  useEffect(() => {
    if (!isDropdownOpen) {
      setAiSuggestions([])
      setAiError(null)
    }
  }, [isDropdownOpen])

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const fetchAISuggestions = useCallback(async (query: string) => {
    if (!query || query.length < 3) return
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()
    
    const currentRequestId = ++requestIdRef.current
    setIsLoadingAI(true)
    setAiError(null)
    
    try {
      const response = await fetch('/api/ai/suggest-industries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: query,
          existingIndustries: existingIndustries 
        }),
        signal: abortControllerRef.current.signal
      })
      
      if (currentRequestId !== requestIdRef.current) return
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newSuggestions = data.suggestions
            .filter((s: string) => !existingIndustries.includes(s.toLowerCase()))
            .slice(0, 6)
          if (newSuggestions.length > 0) {
            setAiSuggestions(newSuggestions)
            setAiError(null)
          } else {
            setAiError('No AI suggestions found for this query')
          }
        } else {
          setAiError('No AI suggestions found for this query')
        }
      } else {
        setAiError('Failed to fetch AI suggestions')
      }
    } catch (error) {
      if ((error as Error).name === 'AbortError') return
      if (currentRequestId !== requestIdRef.current) return
      setAiError('Error fetching AI suggestions')
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setIsLoadingAI(false)
      }
    }
  }, [existingIndustries])

  useEffect(() => {
    if (inputValue.trim().length < 3) {
      return
    }

    const timer = setTimeout(() => {
      fetchAISuggestions(inputValue.trim())
    }, 500)

    return () => clearTimeout(timer)
  }, [inputValue, fetchAISuggestions])

  const addIndustry = useCallback((industry: string) => {
    const trimmed = industry.trim()
    if (!trimmed) return
    if (existingIndustries.includes(trimmed.toLowerCase())) return
    onChange([...value, trimmed])
    setInputValue("")
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
    setAiSuggestions([])
  }, [value, onChange, existingIndustries, setInputValue, setIsDropdownOpen, setFocusedIndex])

  const removeIndustry = useCallback((industry: string) => {
    onChange(value.filter(i => i !== industry))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const askAIForIndustries = useCallback(async (query: string) => {
    if (!query.trim()) return
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()
    
    const currentRequestId = ++requestIdRef.current
    setIsLoadingAI(true)
    setAiError(null)
    
    try {
      const response = await fetch('/api/ai/suggest-industries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: query.trim(),
          existingIndustries: existingIndustries 
        }),
        signal: abortControllerRef.current.signal
      })
      
      if (currentRequestId !== requestIdRef.current) return
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newSuggestions = data.suggestions
            .filter((s: string) => !existingIndustries.includes(s.toLowerCase()))
            .slice(0, 6)
          
          if (newSuggestions.length > 0) {
            setAiSuggestions(newSuggestions)
            setAiError(null)
          } else {
            addIndustry(query)
          }
        } else {
          addIndustry(query)
        }
      } else {
        addIndustry(query)
      }
    } catch (error) {
      if ((error as Error).name === 'AbortError') return
      if (currentRequestId !== requestIdRef.current) return
      addIndustry(query)
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setIsLoadingAI(false)
      }
    }
  }, [existingIndustries, addIndustry])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (focusedIndex >= 0 && dropdownItems[focusedIndex]) {
        const item = dropdownItems[focusedIndex]
        if (item.type === 'ai') {
          askAIForIndustries(inputValue)
        } else if (item.industry) {
          addIndustry(item.industry)
        }
      } else if (inputValue.trim()) {
        addIndustry(inputValue)
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setFocusedIndex(prev => Math.min(prev + 1, dropdownItems.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setFocusedIndex(prev => Math.max(prev - 1, -1))
    } else if (e.key === 'Escape') {
      setIsDropdownOpen(false)
      setFocusedIndex(-1)
      setAiSuggestions([])
      setAiError(null)
    }
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

  const currentTimeOption = TIME_FILTER_OPTIONS.find(o => o.value === timeFilter)

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Popover open={isTimeFilterOpen} onOpenChange={setIsTimeFilterOpen}>
          <PopoverTrigger asChild>
            <button className="flex items-center gap-2 px-2.5 py-1 rounded-xl border border-lia-border-subtle text-xs hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none">
              <span className="text-lia-text-primary">{currentTimeOption?.label}</span>
              <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />
            </button>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-0" align="start">
            <div className="py-1">
              {TIME_FILTER_OPTIONS.map(option => (
                <button
                  key={option.value}
                  onClick={() => {
                    onTimeFilterChange?.(option.value)
                    setIsTimeFilterOpen(false)
                  }}
                  className={cn("w-full text-left px-3 py-2 hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none",
                    timeFilter === option.value &&"bg-lia-bg-secondary"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-lia-text-primary">{option.label}</span>
                    {timeFilter === option.value && (
                      <div className="w-2 h-2 rounded-full bg-lia-btn-primary-bg" />
                    )}
                  </div>
                  <p className="text-xs text-lia-text-secondary mt-0.5">{option.description}</p>
                </button>
              ))}
            </div>
          </PopoverContent>
        </Popover>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {value.length > 0 && (
            <span className="text-xs text-lia-text-secondary">
              {value.length} setor{value.length !== 1 ? 'es' : ''} selecionado{value.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        {value.length > 0 && (
          <button
            onClick={clearAll}
            className="text-xs text-lia-text-secondary hover:text-lia-text-primary font-medium"
          >
            Limpar tudo
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
          />
          {isLoadingAI && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
          )}
        </div>

        {isDropdownOpen && (dropdownItems.length > 0 || aiError) && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-xl max-h-64 overflow-y-auto"
          >
            {aiError && (
              <div className="px-3 py-2 text-sm text-status-warning flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                <span>{aiError}</span>
              </div>
            )}
            {dropdownItems.map((item, index) => (
              <button
                key={`${item.type}-${item.label}`}
                onClick={() => {
                  if (item.type === 'ai') {
                    askAIForIndustries(inputValue)
                  } else if (item.industry) {
                    addIndustry(item.industry)
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
                ) : item.type === 'ai-suggestion' ? (
                  <div className="flex items-center gap-2 text-lia-text-primary">
                    <Brain className="w-3 h-3 text-wedo-purple" />
                    <span>{item.label}</span>
                    <span className="text-micro px-1.5 py-0.5  rounded-full ml-auto">AI</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between text-lia-text-primary">
                    <span>{item.labelPt}</span>
                    {item.labelPt !== item.label && (
                      <span className="text-xs text-lia-text-tertiary ml-2">{item.label}</span>
                    )}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map(industry => (
            <Chip variant="neutral" muted
              key={industry}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
            >
              <span>{industry}</span>
              <button
                onClick={() => removeIndustry(industry)}
                className="hover:bg-lia-interactive-active rounded-md p-0.5 transition-colors motion-reduce:transition-none ml-1"
                title="Remove"
              >
                <X className="w-3 h-3" />
              </button>
            </Chip>
          ))}
        </div>
      )}
    </div>
  )
}

export default IndustryFilterInput
