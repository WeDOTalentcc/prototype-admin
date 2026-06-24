"use client"

/**
 * useSearchAutocomplete — Sugestões de autocomplete para o campo de busca natural.
 *
 * Extraído de ExpandableAIPrompt (P1-E).
 * Gerencia: sugestões, visibilidade, índice selecionado, flag de habilitação,
 * cache em memória e navegação por teclado.
 *
 * Portabilidade Vue: mapeia para composable useSearchAutocomplete().
 */

import { useState, useRef, useCallback } from "react"
import type { AutocompleteSuggestion } from "@/components/search/expandable-ai-prompt.types"

export interface UseSearchAutocompleteResult {
  autocompleteSuggestions: AutocompleteSuggestion[]
  showAutocomplete: boolean
  setShowAutocomplete: (v: boolean) => void
  selectedAutocompleteIndex: number
  setSelectedAutocompleteIndex: (n: number) => void
  autocompleteEnabled: boolean
  setAutocompleteEnabled: (v: boolean) => void
  fetchAutocomplete: (query: string) => Promise<void>
  /** Teclado: Arrow/Tab/Enter/Escape. onSelect chamado ao confirmar sugestão com o texto de inserção. */
  handleAutocompleteKeyDown: (e: React.KeyboardEvent, onSelect: (insertText: string) => void) => void
}

export function useSearchAutocomplete(): UseSearchAutocompleteResult {
  const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<AutocompleteSuggestion[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedAutocompleteIndex, setSelectedAutocompleteIndex] = useState(0)
  const [autocompleteEnabled, setAutocompleteEnabled] = useState(true)

  const autocompleteCache = useRef<Map<string, AutocompleteSuggestion[]>>(new Map())

  const fetchAutocomplete = useCallback(async (query: string) => {
    if (!query.trim() || query.length < 2) {
      setAutocompleteSuggestions([])
      setShowAutocomplete(false)
      return
    }

    const cacheKey = query.toLowerCase().trim()
    if (autocompleteCache.current.has(cacheKey)) {
      setAutocompleteSuggestions(autocompleteCache.current.get(cacheKey) || [])
      setShowAutocomplete(true)
      return
    }

    try {
      const res = await fetch(`/api/backend-proxy/search-assistant/autocomplete/?query=${encodeURIComponent(query)}`)
      if (res.ok) {
        const data = await res.json()
        const items = data.items || []
        const suggestions: AutocompleteSuggestion[] = items.map((item: AutocompleteSuggestion & { insert_text?: string }) => ({
          text: item.text,
          category: item.category,
          icon: item.icon,
          description: item.description,
          insert_text: item.insert_text || item.text,
        }))
        autocompleteCache.current.set(cacheKey, suggestions)
        setAutocompleteSuggestions(suggestions)
        setShowAutocomplete(suggestions.length > 0)
      }
    } catch (error) {
      console.error("[use-search-autocomplete] Error:", error)
    }
  }, [])

  const handleAutocompleteKeyDown = useCallback(
    (e: React.KeyboardEvent, onSelect: (insertText: string) => void) => {
      if (!showAutocomplete || autocompleteSuggestions.length === 0) return

      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedAutocompleteIndex(prev =>
          prev < autocompleteSuggestions.length - 1 ? prev + 1 : 0
        )
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedAutocompleteIndex(prev =>
          prev > 0 ? prev - 1 : autocompleteSuggestions.length - 1
        )
      } else if (e.key === 'Tab' || e.key === 'Enter') {
        if (autocompleteSuggestions[selectedAutocompleteIndex]) {
          e.preventDefault()
          const selected = autocompleteSuggestions[selectedAutocompleteIndex]
          onSelect(selected.insert_text || selected.text)
          setShowAutocomplete(false)
        }
      } else if (e.key === 'Escape') {
        setShowAutocomplete(false)
      }
    },
    [showAutocomplete, autocompleteSuggestions, selectedAutocompleteIndex],
  )

  return {
    autocompleteSuggestions,
    showAutocomplete,
    setShowAutocomplete,
    selectedAutocompleteIndex,
    setSelectedAutocompleteIndex,
    autocompleteEnabled,
    setAutocompleteEnabled,
    fetchAutocomplete,
    handleAutocompleteKeyDown,
  }
}
