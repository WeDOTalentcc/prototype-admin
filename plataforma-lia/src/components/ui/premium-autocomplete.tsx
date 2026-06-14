"use client"

import React, { useState, useEffect, useCallback, useRef } from "react"
import { cn } from "@/lib/utils"
import { Clock, TrendingUp, Star, Search, Users } from "lucide-react"

interface PremiumSuggestion {
  text: string
  category: "recent" | "popular" | "team" | "recommended"
  count?: number
  lastUsed?: string
  icon?: React.ReactNode
}

interface PremiumAutocompleteProps {
  query: string
  companyId?: string
  userId?: string
  onSelect: (suggestion: string) => void
  isOpen: boolean
  onClose: () => void
  className?: string
}

const CATEGORY_CONFIG = {
  recent: {
    label: "Recentes",
    icon: Clock,
    color: "text-lia-text-secondary",
    bgColor: "bg-lia-bg-tertiary dark:bg-lia-bg-secondary",
  },
  popular: {
    label: "Populares na empresa",
    icon: TrendingUp,
    color: "text-status-success",
    bgColor: "bg-status-success/10",
  },
  team: {
    label: "Usados pelo time",
    icon: Users,
    color: "text-lia-text-secondary",
    bgColor: "bg-wedo-purple/10",
  },
  recommended: {
    label: "Recomendados pela LIA",
    icon: Star,
    color: "text-status-warning",
    bgColor: "bg-status-warning/10",
  },
}

export function PremiumAutocomplete({
  query,
  companyId = "demo",
  userId = "default_user",
  onSelect,
  isOpen,
  onClose,
  className,
}: PremiumAutocompleteProps) {
  const [suggestions, setSuggestions] = useState<PremiumSuggestion[]>([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  const fetchSuggestions = useCallback(async () => {
    if (!query || query.length < 2) {
      setSuggestions([])
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(
        `/api/backend-proxy/search/autocomplete/premium?` +
          new URLSearchParams({
            query,
            company_id: companyId,
            user_id: userId,
          })
      )

      if (response.ok) {
        const data = await response.json()
        setSuggestions(data.suggestions || [])
      } else {
        setSuggestions(generateFallbackSuggestions(query))
      }
    } catch (error) {
      setSuggestions(generateFallbackSuggestions(query))
    } finally {
      setIsLoading(false)
    }
  }, [query, companyId, userId])

  useEffect(() => {
    const debounce = setTimeout(fetchSuggestions, 300)
    return () => clearTimeout(debounce)
  }, [fetchSuggestions])

  useEffect(() => {
    setSelectedIndex(0)
  }, [suggestions])

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!isOpen || suggestions.length === 0) return

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault()
          setSelectedIndex((prev) =>
            prev < suggestions.length - 1 ? prev + 1 : 0
          )
          break
        case "ArrowUp":
          e.preventDefault()
          setSelectedIndex((prev) =>
            prev > 0 ? prev - 1 : suggestions.length - 1
          )
          break
        case "Enter":
        case "Tab":
          if (suggestions[selectedIndex]) {
            e.preventDefault()
            onSelect(suggestions[selectedIndex].text)
            onClose()
          }
          break
        case "Escape":
          onClose()
          break
      }
    },
    [isOpen, suggestions, selectedIndex, onSelect, onClose]
  )

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [handleKeyDown])

  if (!isOpen || suggestions.length === 0) {
    return null
  }

  const groupedSuggestions = suggestions.reduce((acc, suggestion) => {
    if (!acc[suggestion.category]) {
      acc[suggestion.category] = []
    }
    acc[suggestion.category].push(suggestion)
    return acc
  }, {} as Record<string, PremiumSuggestion[]>)

  return (
    <div
      ref={containerRef}
      className={cn(
 "absolute z-50 w-full mt-1 bg-lia-bg-primary border border-lia-border-subtle rounded-md overflow-hidden",
        className
      )}
    >
      {Object.entries(groupedSuggestions).map(([category, items]) => {
        const config = CATEGORY_CONFIG[category as keyof typeof CATEGORY_CONFIG]
        if (!config) return null

        const CategoryIcon = config.icon

        return (
          <div key={category}>
            <div
              className={cn(
 "flex items-center gap-2 px-3 py-1.5 text-micro font-medium uppercase tracking-wide",
                config.bgColor,
                config.color
              )}
            >
              <CategoryIcon className="h-3 w-3" />
              {config.label}
            </div>
            {items.map((suggestion, idx) => {
              const globalIndex = suggestions.findIndex(
                (s) => s.text === suggestion.text
              )
              const isSelected = globalIndex === selectedIndex

              return (
                <button
                  key={`${category}-${idx}`}
                  onClick={() => {
                    onSelect(suggestion.text)
                    onClose()
                  }}
                  className={cn(
 "w-full flex items-center justify-between px-3 py-2 text-left text-sm transition-colors",
                    isSelected
                      ? "bg-lia-interactive-hover text-lia-text-primary"
                      : "text-lia-text-primary hover:bg-lia-interactive-hover"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Search className="h-3.5 w-3.5 text-lia-text-secondary" />
                    <span>{suggestion.text}</span>
                  </div>
                  {suggestion.count && (
                    <span className="text-xs text-lia-text-secondary">
                      {suggestion.count}x
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        )
      })}
    </div>
  )
}

function generateFallbackSuggestions(query: string): PremiumSuggestion[] {
  const queryLower = query.toLowerCase()

  const suggestions: PremiumSuggestion[] = []

  if (queryLower.includes("python") || queryLower.includes("dev")) {
    suggestions.push(
      { text: "Python Developer Sênior São Paulo", category: "popular", count: 15 },
      { text: "Python AWS Data Engineer", category: "team", count: 8 }
    )
  }

  if (queryLower.includes("data") || queryLower.includes("eng")) {
    suggestions.push(
      { text: "Data Engineer Pleno Fintech", category: "popular", count: 12 },
      { text: "Data Scientist Machine Learning", category: "recommended" }
    )
  }

  if (queryLower.includes("front") || queryLower.includes("react")) {
    suggestions.push(
      { text: "Frontend React TypeScript", category: "popular", count: 20 },
      { text: "React Developer Pleno Remoto", category: "team", count: 5 }
    )
  }

  suggestions.push({
    text: query,
    category: "recent",
    lastUsed: "agora",
  })

  return suggestions.slice(0, 8)
}
