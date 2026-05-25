"use client"

import React, { useState, useEffect, useRef, useCallback } from "react"
import { X, Search, Home, Globe, Loader2, Plus, Check } from "lucide-react"
import { cn } from "@/lib/utils"

export interface FilterSuggestion {
  value: string
  label: string
  local_count: number
  global_count?: number | null
  aliases: string[]
  source: string
}

interface FilterAutocompleteProps {
  category: string
  placeholder?: string
  selectedValues: string[]
  onSelect: (values: string[]) => void
  onAdd: (value: string) => void
  onRemove: (value: string) => void
  disabled?: boolean
  maxSelections?: number
  showCounts?: boolean
  className?: string
}

export function FilterAutocomplete({
  category,
  placeholder = "Digite para buscar...",
  selectedValues = [],
  onSelect,
  onAdd,
  onRemove,
  disabled = false,
  maxSelections,
  showCounts = true,
  className
}: FilterAutocompleteProps) {
  const [query, setQuery] = useState("")
  const [suggestions, setSuggestions] = useState<FilterSuggestion[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isFocused, setIsFocused] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const debounceRef = useRef<NodeJS.Timeout | null>(null)

  const fetchSuggestions = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSuggestions([])
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/backend-proxy/search/suggestions/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category,
          query: searchQuery,
          limit: 10,
          include_global: false
        })
      })

      if (!response.ok) {
        throw new Error('Falha ao buscar sugestões')
      }

      const data = await response.json()
      setSuggestions(data.suggestions || [])
    } catch (err) {
      setError('Erro ao buscar sugestões')
      setSuggestions([])
    } finally {
      setIsLoading(false)
    }
  }, [category])

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }

    if (query.trim().length >= 2) {
      debounceRef.current = setTimeout(() => {
        fetchSuggestions(query)
      }, 300)
    } else {
      setSuggestions([])
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current)
      }
    }
  }, [query, fetchSuggestions])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsFocused(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (suggestion: FilterSuggestion) => {
    if (maxSelections && selectedValues.length >= maxSelections) {
      return
    }

    if (!selectedValues.includes(suggestion.value)) {
      onAdd(suggestion.value)
    }
    setQuery("")
    setSuggestions([])
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && query.trim()) {
      e.preventDefault()
      if (suggestions.length > 0) {
        handleSelect(suggestions[0])
      } else if (query.trim().length >= 2) {
        if (!selectedValues.includes(query.trim())) {
          onAdd(query.trim())
        }
        setQuery("")
      }
    } else if (e.key === 'Backspace' && !query && selectedValues.length > 0) {
      onRemove(selectedValues[selectedValues.length - 1])
    } else if (e.key === 'Escape') {
      setIsFocused(false)
      setSuggestions([])
    }
  }

  const showDropdown = isFocused && (suggestions.length > 0 || isLoading || (query.length >= 2 && !isLoading))

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <div 
        className={cn(
          "flex flex-wrap items-center gap-1.5 p-2 min-h-[38px] rounded-md border bg-lia-bg-primary dark:bg-lia-bg-secondary transition-colors",
          isFocused ? "border-lia-border-default ring-2 ring-lia-border-subtle" : "border-lia-border-subtle dark:border-lia-border-subtle",
          disabled && "opacity-50 cursor-not-allowed"
        )}
        onClick={() => inputRef.current?.focus()}
      >
        {selectedValues.map((value) => (
          <span
            key={value}
            className="inline-flex items-center gap-1 px-2 py-0.5 text-micro rounded-full bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
          >
            {value}
            <button
              onClick={(e) => {
                e.stopPropagation()
                onRemove(value)
              }}
              className="hover:text-status-error transition-colors motion-reduce:transition-none"
              disabled={disabled}
            >
              <X className="w-3 h-3" />
            </button>
          </span>
        ))}
        
        <div className="flex-1 min-w-[120px] relative">
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onKeyDown={handleKeyDown}
            placeholder={selectedValues.length === 0 ? placeholder : "Adicionar..."}
            disabled={disabled || (maxSelections !== undefined && selectedValues.length >= maxSelections)}
            className="w-full bg-transparent text-xs text-lia-text-primary placeholder-lia-text-tertiary focus:outline-none"
           
          />
          {isLoading && (
            <div className="absolute right-0 top-1/2 -translate-y-1/2" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-3 h-3 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
            </div>
          )}
        </div>
      </div>

      {showDropdown && (
        <div className="absolute z-50 w-full mt-1 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl max-h-60 overflow-auto" role="status" aria-live="polite" aria-label="Carregando...">
          {isLoading ? (
            <div className="flex items-center justify-center gap-2 p-3 text-xs text-lia-text-primary" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
              <span>Buscando...</span>
            </div>
          ) : suggestions.length > 0 ? (
            <div className="py-1">
              {suggestions.map((suggestion, index) => {
                const isSelected = selectedValues.includes(suggestion.value)
                return (
                  <button
                    key={`${suggestion.value}-${index}`}
                    onClick={() => handleSelect(suggestion)}
                    disabled={isSelected}
                    className={cn(
                      "w-full flex items-center justify-between px-3 py-2 text-left transition-colors",
                      isSelected
                        ? "bg-lia-bg-tertiary text-lia-text-primary"
                        : "hover:bg-lia-bg-secondary dark:hover:bg-lia-bg-inverse"
                    )}
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {isSelected ? (
                        <Check className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                      ) : (
                        <Plus className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-medium text-lia-text-primary truncate block">
                          {suggestion.label}
                        </span>
                        {suggestion.aliases && suggestion.aliases.length > 0 && (
                          <span className="text-xs text-lia-text-secondary truncate block">
                            Também: {suggestion.aliases.slice(0, 2).join(", ")}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    {showCounts && (
                      <div className="flex items-center gap-2 ml-2 flex-shrink-0">
                        {suggestion.local_count > 0 && (
                          <span className="flex items-center gap-0.5 text-xs text-status-success font-medium">
                            <Home className="w-3 h-3" />
                            {suggestion.local_count}
                          </span>
                        )}
                        {suggestion.global_count && suggestion.global_count > 0 && (
                          <span className="flex items-center gap-0.5 text-xs text-lia-text-secondary font-medium">
                            <Globe className="w-3 h-3" />
                            +{suggestion.global_count > 1000 ? `${(suggestion.global_count / 1000).toFixed(1)}K` : suggestion.global_count}
                          </span>
                        )}
                        {suggestion.source === "suggested" && suggestion.local_count === 0 && (
                          <span className="text-micro text-lia-text-secondary px-1.5 py-0.5 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated">
                            Sugerido
                          </span>
                        )}
                      </div>
                    )}
                  </button>
                )
              })}
            </div>
          ) : query.length >= 2 ? (
            <div className="p-3 text-center">
              <p className="text-xs text-lia-text-primary mb-2" aria-live="polite" aria-atomic="true">Nenhum resultado encontrado</p>
              <button
                onClick={() => {
                  if (!selectedValues.includes(query.trim())) {
                    onAdd(query.trim())
                  }
                  setQuery("")
                  setSuggestions([])
                }}
                className="text-xs text-lia-text-primary hover:underline"
              >
                Adicionar "{query}" mesmo assim
              </button>
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}

export function TagInput({
  value = [],
  onAdd,
  onRemove,
  placeholder = "Digite e pressione Enter...",
  disabled = false,
  className
}: {
  value: string[]
  onAdd: (val: string) => void
  onRemove: (val: string) => void
  placeholder?: string
  disabled?: boolean
  className?: string
}) {
  const [inputValue, setInputValue] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && inputValue.trim()) {
      e.preventDefault()
      if (!value.includes(inputValue.trim())) {
        onAdd(inputValue.trim())
      }
      setInputValue("")
    } else if (e.key === 'Backspace' && !inputValue && value.length > 0) {
      onRemove(value[value.length - 1])
    }
  }

  return (
    <div 
      className={cn(
        "flex flex-wrap items-center gap-1.5 p-2 min-h-[38px] rounded-md border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary focus-within:border-lia-border-default focus-within:ring-2 focus-within:ring-lia-border-subtle transition-colors",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      onClick={() => inputRef.current?.focus()}
    >
      {value.map((val) => (
        <span
          key={val}
          className="inline-flex items-center gap-1 px-2 py-0.5 text-micro rounded-full bg-lia-bg-tertiary text-lia-text-primary border border-lia-border-subtle"
        >
          {val}
          <button
            onClick={(e) => {
              e.stopPropagation()
              onRemove(val)
            }}
            className="hover:text-status-error transition-colors motion-reduce:transition-none"
            disabled={disabled}
          >
            <X className="w-3 h-3" />
          </button>
        </span>
      ))}
      
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={value.length === 0 ? placeholder : ""}
        disabled={disabled}
        className="flex-1 min-w-[100px] bg-transparent text-xs text-lia-text-primary placeholder-lia-text-tertiary focus:outline-none"
       
      />
    </div>
  )
}
