"use client"

import { useState, useRef, useEffect, useMemo } from "react"
import { Search, Brain, Loader2, ChevronDown, X } from "lucide-react"
import { cn } from "@/lib/utils"
import {
  INDUSTRIES,
  INDUSTRY_CATEGORIES,
  searchIndustries,
  type Industry,
  type IndustryCategory
} from "@/lib/industry-constants"

interface IndustrySingleSelectProps {
  value: string
  onChange: (industry: string) => void
  placeholder?: string
  error?: boolean
  className?: string
}

export function IndustrySingleSelect({
  value,
  onChange,
  placeholder = "Digite para buscar setor...",
  error = false,
  className
}: IndustrySingleSelectProps) {
  const [inputValue, setInputValue] = useState("")
  const [isOpen, setIsOpen] = useState(false)
  const [isLoadingAI, setIsLoadingAI] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([])
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const selectedIndustry = useMemo(() => {
    if (!value) return null
    return INDUSTRIES.find(
      ind => ind.key.toLowerCase() === value.toLowerCase() ||
             ind.labelPt.toLowerCase() === value.toLowerCase() ||
             ind.labelEn.toLowerCase() === value.toLowerCase()
    )
  }, [value])

  const filteredSuggestions = useMemo(() => {
    if (!inputValue.trim()) {
      return INDUSTRIES.slice(0, 10)
    }
    return searchIndustries(inputValue).slice(0, 8)
  }, [inputValue])

  const filteredAISuggestions = aiSuggestions.filter(
    s => !filteredSuggestions.some(f => f.labelPt.toLowerCase() === s.toLowerCase())
  )

  const showAskAI = inputValue.trim().length >= 2
  const dropdownItems = [
    ...filteredAISuggestions.map(i => ({ type: 'ai-suggestion' as const, label: i, industry: null })),
    ...(showAskAI && !isLoadingAI ? [{ type: 'ai' as const, label: `Buscar com IA "${inputValue}"`, industry: null }] : []),
    ...filteredSuggestions.map(i => ({ type: 'industry' as const, label: i.labelPt, industry: i }))
  ]

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current && !inputRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false)
        setAiSuggestions([])
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
    if (inputValue.trim().length < 3) return

    const timer = setTimeout(() => {
      fetchAISuggestions(inputValue.trim())
    }, 600)

    return () => clearTimeout(timer)
  }, [inputValue])

  const fetchAISuggestions = async (query: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()
    setIsLoadingAI(true)

    try {
      const response = await fetch("/api/ai/suggest-industries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: 5 }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) throw new Error("Failed to fetch")

      const data = await response.json()
      if (data.industries && Array.isArray(data.industries)) {
        setAiSuggestions(data.industries)
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
      }
    } finally {
      setIsLoadingAI(false)
    }
  }

  const handleSelect = (item: typeof dropdownItems[0]) => {
    if (item.type === 'ai') {
      fetchAISuggestions(inputValue.trim())
      return
    }

    const selectedValue = item.industry?.labelPt || item.label
    onChange(selectedValue)
    setInputValue("")
    setIsOpen(false)
    setAiSuggestions([])
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'Enter') {
        setIsOpen(true)
      }
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setFocusedIndex(prev => Math.min(prev + 1, dropdownItems.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setFocusedIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        if (focusedIndex >= 0 && focusedIndex < dropdownItems.length) {
          handleSelect(dropdownItems[focusedIndex])
        }
        break
      case 'Escape':
        setIsOpen(false)
        setFocusedIndex(-1)
        break
    }
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onChange("")
    setInputValue("")
    inputRef.current?.focus()
  }

  return (
    <div className={cn("relative", className)}>
      <div
        className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-md border bg-lia-bg-primary dark:bg-lia-bg-primary transition-colors cursor-text",
          error ? "border-status-error/30" : "border-lia-border-subtle dark:border-lia-border-subtle",
          isOpen && "ring-2 ring-lia-btn-primary-bg/20 border-lia-border-medium"
        )}
        onClick={() => {
          inputRef.current?.focus()
          setIsOpen(true)
        }}
      >
        <Search className="w-3.5 h-3.5 text-lia-text-tertiary flex-shrink-0" />
        
        {selectedIndustry && !isOpen ? (
          <div className="flex-1 flex items-center justify-between">
            <span className="text-sm text-lia-text-primary">
              {selectedIndustry.labelPt}
            </span>
            <button
              onClick={handleClear}
              className="p-0.5 hover:bg-lia-bg-tertiary dark:hover:bg-lia-bg-inverse rounded-full transition-colors motion-reduce:transition-none"
            >
              <X className="w-3.5 h-3.5 text-lia-text-tertiary" />
            </button>
          </div>
        ) : (
          <>
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value)
                setIsOpen(true)
                setFocusedIndex(-1)
              }}
              onFocus={() => setIsOpen(true)}
              onKeyDown={handleKeyDown}
              placeholder={selectedIndustry ? selectedIndustry.labelPt : placeholder}
              className="flex-1 text-sm bg-transparent outline-none text-lia-text-primary placeholder:text-lia-text-tertiary"
             
            />
            {isLoadingAI && (
              <Loader2 className="w-3.5 h-3.5 text-lia-text-secondary animate-spin motion-reduce:animate-none flex-shrink-0" />
            )}
            <ChevronDown className={cn(
              "w-3.5 h-3.5 text-lia-text-tertiary transition-transform flex-shrink-0",
              isOpen && "rotate-180"
            )} />
          </>
        )}
      </div>

      {isOpen && dropdownItems.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute z-50 w-full mt-1 py-1 bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl max-h-64 overflow-y-auto"
        >
          {dropdownItems.map((item, idx) => (
            <button
              key={`${item.type}-${item.label}-${idx}`}
              onClick={() => handleSelect(item)}
              className={cn(
                "w-full px-3 py-2 text-left text-sm flex items-center gap-2 transition-colors",
                focusedIndex === idx
                  ? "bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary"
                  : "hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse text-lia-text-primary",
                item.type === 'ai' && "border-t border-lia-border-subtle dark:border-lia-border-subtle"
              )}
             
            >
              {item.type === 'ai' && (
                <Brain className="w-3.5 h-3.5 text-status-warning flex-shrink-0" />
              )}
              {item.type === 'ai-suggestion' && (
                <Brain className="w-3 h-3 text-wedo-cyan flex-shrink-0" />
              )}
              <span className="truncate">{item.label}</span>
              {item.industry && (
                <span className="ml-auto text-micro text-lia-text-tertiary px-1.5 py-0.5 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-full">
                  {INDUSTRY_CATEGORIES[item.industry.category as IndustryCategory]?.labelPt}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
