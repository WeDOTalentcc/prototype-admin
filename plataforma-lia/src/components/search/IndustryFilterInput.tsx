"use client"

import { useState, useRef, useEffect, useCallback, useMemo } from "react"
import { X, Search, ChevronDown, Brain, Loader2, AlertCircle, Zap } from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  INDUSTRIES,
  searchIndustries,
  getCanonicalKey,
  type Industry
} from "@/lib/industry-constants"
import { useSemanticSearch } from "@/hooks/useSemanticSearch"

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
  placeholder = "Type industry name and press Enter"
}: IndustryFilterInputProps) {
  const [inputValue, setInputValue] = useState("")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([])
  const [aiError, setAiError] = useState<string | null>(null)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const [isTimeFilterOpen, setIsTimeFilterOpen] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const requestIdRef = useRef(0)
  const abortControllerRef = useRef<AbortController | null>(null)

  const { 
    suggestions: semanticSuggestions, 
    isLoading: isSemanticLoading, 
    search: searchSemantic,
    clearSuggestions
  } = useSemanticSearch({ domain: "industries", debounceMs: 400 })

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
    ...(showAskAI && semanticItems.length === 0 && filteredAISuggestions.length === 0 ? [{ type: 'ai' as const, label: `Buscar com IA "${inputValue}"`, labelPt: null, industry: null, confidence: 0 }] : []),
    ...filteredSuggestions.map(i => ({ 
      type: 'industry' as const, 
      label: i.key,
      labelPt: i.labelPt,
      industry: i.key,
      confidence: 0
    }))
  ]

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
        setAiSuggestions([])
        setAiError(null)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])
  
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  useEffect(() => {
    if (inputValue.trim().length < 3) {
      return
    }

    const timer = setTimeout(() => {
      fetchAISuggestions(inputValue.trim())
    }, 500)

    return () => clearTimeout(timer)
  }, [inputValue])

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

  const addIndustry = useCallback((industry: string) => {
    const trimmed = industry.trim()
    if (!trimmed) return
    if (existingIndustries.includes(trimmed.toLowerCase())) return
    onChange([...value, trimmed])
    setInputValue("")
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
    setAiSuggestions([])
  }, [value, onChange, existingIndustries])

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
            <button className="flex items-center gap-2 px-2.5 py-1 rounded-md border border-gray-200 text-xs hover:bg-gray-50 transition-colors">
              <span className="text-gray-800 dark:text-gray-200">{currentTimeOption?.label}</span>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
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
                  className={cn(
                    "w-full text-left px-3 py-2 hover:bg-gray-50 transition-colors",
                    timeFilter === option.value && "bg-gray-50"
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-gray-800 dark:text-gray-200">{option.label}</span>
                    {timeFilter === option.value && (
                      <div className="w-2 h-2 rounded-full bg-gray-900 dark:bg-gray-50" />
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{option.description}</p>
                </button>
              ))}
            </div>
          </PopoverContent>
        </Popover>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {value.length > 0 && (
            <span className="text-xs text-gray-500">
              {value.length} setor{value.length !== 1 ? 'es' : ''} selecionado{value.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        {value.length > 0 && (
          <button
            onClick={clearAll}
            className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 font-medium"
          >
            Limpar tudo
          </button>
        )}
      </div>

      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            ref={inputRef}
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => inputValue.length > 0 && setIsDropdownOpen(true)}
            placeholder={placeholder}
            className="pl-9 pr-3 border-gray-200 focus:ring-1 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-gray-400"
          />
          {isLoadingAI && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <Loader2 className="w-4 h-4 animate-spin text-gray-600 dark:text-gray-400" />
            </div>
          )}
        </div>

        {isDropdownOpen && (dropdownItems.length > 0 || aiError) && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md max-h-64 overflow-y-auto"
          >
            {aiError && (
              <div className="px-3 py-2 text-sm text-status-warning flex items-center gap-2 border-b border-gray-100">
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
                className={cn(
                  "w-full text-left px-3 py-2 text-sm transition-colors",
                  focusedIndex === index ? "bg-gray-100" : "hover:bg-gray-50",
                  item.type === 'ai' && "border-b border-gray-100"
                )}
              >
                {item.type === 'ai' ? (
                  <div className="flex items-center gap-2 text-wedo-purple">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span>{item.label}</span>
                  </div>
                ) : item.type === 'ai-suggestion' ? (
                  <div className="flex items-center gap-2 text-gray-800 dark:text-gray-200">
                    <Brain className="w-3 h-3 text-wedo-purple" />
                    <span>{item.label}</span>
                    <span className="text-micro px-1.5 py-0.5 bg-wedo-purple/15 text-wedo-purple rounded-full ml-auto">AI</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-between text-gray-800 dark:text-gray-200">
                    <span>{item.labelPt}</span>
                    {item.labelPt !== item.label && (
                      <span className="text-xs text-gray-400 ml-2">{item.label}</span>
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
            <Badge
              key={industry}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:text-gray-200 border border-gray-200"
            >
              <span>{industry}</span>
              <button
                onClick={() => removeIndustry(industry)}
                className="hover:bg-gray-200 rounded p-0.5 transition-colors ml-1"
                title="Remove"
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}

export default IndustryFilterInput
