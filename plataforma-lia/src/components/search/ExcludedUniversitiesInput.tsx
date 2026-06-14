"use client"

import { useState, useRef, useEffect, useCallback } from"react"
import { X, Brain, Loader2, Search } from"lucide-react"
import { cn } from"@/lib/utils"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"

interface ExcludedUniversitiesInputProps {
  value: string[]
  onChange: (universities: string[]) => void
  placeholder?: string
}

const POPULAR_UNIVERSITIES = ["Harvard University","Stanford University","MIT (Massachusetts Institute of Technology)","Yale University","Princeton University","Columbia University","University of Pennsylvania","Brown University","Cornell University","Dartmouth College","UC Berkeley","UCLA","University of Michigan","University of Chicago","Oxford University","Cambridge University","Imperial College London","USP (Universidade de São Paulo)","Unicamp","UFRJ","PUC-Rio","FGV","Insper","ITA",
]

export function ExcludedUniversitiesInput({
  value,
  onChange,
  placeholder ="HBCUs, Vanderbilt, All Ivy Leagues, Stanford, etc."
}: ExcludedUniversitiesInputProps) {
  const [inputValue, setInputValue] = useState("")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)
  const requestIdRef = useRef(0)

  const existingUniversities = value.map(u => u.toLowerCase())

  const filteredSuggestions = inputValue.trim()
    ? POPULAR_UNIVERSITIES.filter(university => 
        university.toLowerCase().includes(inputValue.toLowerCase()) &&
        !existingUniversities.includes(university.toLowerCase())
      ).slice(0, 6)
    : []

  const showAskAI = inputValue.trim().length >= 2
  const dropdownItems = showAskAI 
    ? [{ type: 'ai' as const, label: `Ask AI for"${inputValue}"`, university: null }, 
       ...filteredSuggestions.map(u => ({ type: 'university' as const, label: u, university: u }))]
    : filteredSuggestions.map(u => ({ type: 'university' as const, label: u, university: u }))

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
          inputRef.current && !inputRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
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

  const addUniversity = useCallback((university: string) => {
    if (!university.trim()) return
    if (existingUniversities.includes(university.toLowerCase())) return
    onChange([...value, university])
    setInputValue("")
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
  }, [value, onChange, existingUniversities])

  const removeUniversity = useCallback((university: string) => {
    onChange(value.filter(u => u !== university))
  }, [value, onChange])

  const clearAll = useCallback(() => {
    onChange([])
  }, [onChange])

  const askAIForUniversities = useCallback(async (query: string) => {
    if (!query.trim()) return
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    const controller = new AbortController()
    abortControllerRef.current = controller
    const currentRequestId = ++requestIdRef.current
    
    setIsLoadingAI(true)
    setIsDropdownOpen(false)
    
    try {
      const response = await fetch('/api/ai/suggest-universities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, existingUniversities: value }),
        signal: controller.signal
      })
      
      if (currentRequestId !== requestIdRef.current) return
      
      if (response.ok) {
        const data = await response.json()
        if (data.suggestions && data.suggestions.length > 0) {
          const newUniversities = data.suggestions
            .filter((u: string) => !existingUniversities.includes(u.toLowerCase()))
            .slice(0, 6)
          
          onChange([...value, ...newUniversities])
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
      }
    } finally {
      if (currentRequestId === requestIdRef.current) {
        setIsLoadingAI(false)
        setInputValue("")
      }
    }
  }, [value, onChange, existingUniversities])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      if (focusedIndex >= 0 && dropdownItems[focusedIndex]) {
        const item = dropdownItems[focusedIndex]
        if (item.type === 'ai') {
          askAIForUniversities(inputValue)
        } else if (item.university) {
          addUniversity(item.university)
        }
      } else if (inputValue.trim()) {
        addUniversity(inputValue.trim())
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
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value)
    setIsDropdownOpen(e.target.value.length > 0)
    setFocusedIndex(-1)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        {value.length > 0 && (
          <>
            <span className="text-xs text-lia-text-secondary">
              {value.length} universit{value.length !== 1 ? 'ies' : 'y'} excluded
            </span>
            <button
              onClick={clearAll}
              className="text-xs text-lia-text-secondary hover:text-lia-text-primary font-medium"
            >
              Clear all
            </button>
          </>
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
                    askAIForUniversities(inputValue)
                  } else if (item.university) {
                    addUniversity(item.university)
                  }
                }}
                className={cn("w-full text-left px-3 py-2 text-sm transition-colors",
                  focusedIndex === index ?"bg-lia-bg-tertiary" :"hover:bg-lia-bg-secondary",
                  item.type === 'ai' &&""
                )}
              >
                {item.type === 'ai' ? (
                  <div className="flex items-center gap-2 text-wedo-purple-text">
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
        <div className="flex flex-wrap gap-2">
          {value.map(university => (
            <Chip variant="warning" muted
              key={university}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
            >
              <span>{university}</span>
              <button
                onClick={() => removeUniversity(university)}
                className="hover:bg-status-warning/15 rounded-md p-0.5 transition-colors motion-reduce:transition-none ml-1"
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

export default ExcludedUniversitiesInput
