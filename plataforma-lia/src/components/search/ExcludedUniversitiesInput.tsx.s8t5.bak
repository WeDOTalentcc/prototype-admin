"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { X, Brain, Loader2, Search } from "lucide-react"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"

interface ExcludedUniversitiesInputProps {
  value: string[]
  onChange: (universities: string[]) => void
  placeholder?: string
}

const POPULAR_UNIVERSITIES = [
  "Harvard University",
  "Stanford University",
  "MIT (Massachusetts Institute of Technology)",
  "Yale University",
  "Princeton University",
  "Columbia University",
  "University of Pennsylvania",
  "Brown University",
  "Cornell University",
  "Dartmouth College",
  "UC Berkeley",
  "UCLA",
  "University of Michigan",
  "University of Chicago",
  "Oxford University",
  "Cambridge University",
  "Imperial College London",
  "USP (Universidade de São Paulo)",
  "Unicamp",
  "UFRJ",
  "PUC-Rio",
  "FGV",
  "Insper",
  "ITA",
]

export function ExcludedUniversitiesInput({
  value,
  onChange,
  placeholder = "HBCUs, Vanderbilt, All Ivy Leagues, Stanford, etc."
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
    ? [{ type: 'ai' as const, label: `Ask AI for "${inputValue}"`, university: null }, 
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
            <span className="text-xs text-gray-500">
              {value.length} universit{value.length !== 1 ? 'ies' : 'y'} excluded
            </span>
            <button
              onClick={clearAll}
              className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 font-medium"
            >
              Clear all
            </button>
          </>
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
            disabled={isLoadingAI}
          />
          {isLoadingAI && (
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
              <Loader2 className="w-4 h-4 animate-spin text-gray-600 dark:text-gray-400" />
            </div>
          )}
        </div>

        {isDropdownOpen && dropdownItems.length > 0 && (
          <div 
            ref={dropdownRef}
            className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md max-h-64 overflow-y-auto"
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
                ) : (
                  <span className="text-gray-800 dark:text-gray-200">{item.label}</span>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map(university => (
            <Badge
              key={university}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-status-warning/10 text-status-warning border border-status-warning/30"
            >
              <span>{university}</span>
              <button
                onClick={() => removeUniversity(university)}
                className="hover:bg-status-warning/15 rounded-md p-0.5 transition-colors ml-1"
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

export default ExcludedUniversitiesInput
